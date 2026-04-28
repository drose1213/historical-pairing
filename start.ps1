# 历史配对 - 一键启动脚本
# 用法: .\start.ps1
# 可选环境变量: $env:MYSQL_HOST, $env:CLIENT_ORIGIN

param(
    [string]$OpenAiKey,
    [string]$OpenAiBaseUrl,
    [string]$OpenAiModel
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PowerShellExe = (Get-Command powershell.exe -ErrorAction Stop).Source

function Set-DefaultEnvVar {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $current = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($current)) {
        Set-Item -Path "env:$Name" -Value $Value -Force
    }
}

function Test-CommandExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $script:ErrorActionPreference = "Continue"
        $output = & $Command 2>$null
        return [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output   = $output
        }
    } finally {
        $script:ErrorActionPreference = $previousErrorActionPreference
    }
}

function Test-TcpPort {
    param(
        [Parameter(Mandatory = $true)]
        [string]$HostName,
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [int]$TimeoutMs = 1500
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $asyncResult = $client.BeginConnect($HostName, $Port, $null, $null)
        if (-not $asyncResult.AsyncWaitHandle.WaitOne($TimeoutMs, $false)) {
            return $false
        }

        $client.EndConnect($asyncResult) | Out-Null
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Stop-ProjectBackendProcesses {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootPath
    )

    $escapedRoot = [Regex]::Escape($RootPath)
    $targets = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -in @("python.exe", "powershell.exe") -and
        $_.CommandLine -match $escapedRoot -and
        $_.CommandLine -match "uvicorn app\.main:app"
    }

    foreach ($target in $targets) {
        Stop-Process -Id $target.ProcessId -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep -Seconds 2
}

function Stop-ListeningProcessOnPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep -Seconds 2
}

function Wait-UntilPortReleased {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [int]$TimeoutSeconds = 10
    )

    for ($i = 0; $i -lt $TimeoutSeconds; $i++) {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if (-not $connections) {
            return $true
        }
        Start-Sleep -Seconds 1
    }

    return $false
}

# 读取 .env 文件（如果存在）
$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Write-Host "[env] 加载 .env 文件" -ForegroundColor Cyan
    Get-Content $envFile -Encoding UTF8 | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            if (-not [string]::IsNullOrEmpty($name)) {
                Set-Item -Path "env:$name" -Value $value -Force
            }
        }
    }
}

# 覆盖 env 文件中的配置（如果脚本参数传入）
if ($OpenAiKey) { $env:OPENAI_API_KEY = $OpenAiKey }
if ($OpenAiBaseUrl) { $env:OPENAI_BASE_URL = $OpenAiBaseUrl }
if ($OpenAiModel) { $env:OPENAI_MODEL = $OpenAiModel }

# 默认值
Set-DefaultEnvVar -Name "MYSQL_HOST" -Value "127.0.0.1"
Set-DefaultEnvVar -Name "MYSQL_PORT" -Value "3306"
Set-DefaultEnvVar -Name "MYSQL_USER" -Value "history_user"
Set-DefaultEnvVar -Name "MYSQL_PASSWORD" -Value "history_pass"
Set-DefaultEnvVar -Name "MYSQL_DATABASE" -Value "historical_pairing"
Set-DefaultEnvVar -Name "PORT" -Value "8787"
Set-DefaultEnvVar -Name "CLIENT_ORIGIN" -Value "http://localhost:5173"

if (-not (Test-CommandExists -Name "python")) {
    throw "未找到 python，请先安装 Python 并确保已加入 PATH。"
}

if (-not (Test-CommandExists -Name "npm")) {
    throw "未找到 npm，请先安装 Node.js 并确保已加入 PATH。"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  历史配对 - 启动中" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

Write-Host "[0/3] 清理旧后端进程..." -ForegroundColor Yellow
Stop-ProjectBackendProcesses -RootPath $ProjectRoot
Stop-ListeningProcessOnPort -Port ([int]$env:PORT)

if (-not (Wait-UntilPortReleased -Port ([int]$env:PORT))) {
    Write-Host ""
    Write-Host "端口 $($env:PORT) 仍被占用，请先关闭旧的后端进程后再重试。" -ForegroundColor Red
    Write-Host "可手动执行：Get-NetTCPConnection -LocalPort $($env:PORT) | Select-Object LocalAddress,LocalPort,State,OwningProcess" -ForegroundColor Red
    return
}

# 1. 启动 MySQL (docker compose)
Write-Host "[1/3] 启动 MySQL..." -ForegroundColor Yellow
if (Test-CommandExists -Name "docker") {
    $dockerUp = Invoke-NativeCommand { docker compose up -d mysql }
    if ($dockerUp.ExitCode -eq 0) {
        Write-Host "  MySQL 已启动 (localhost:3306)" -ForegroundColor Green
    } else {
        Write-Host "  Docker 可执行文件已找到，但 Docker Desktop 未启动或 MySQL 启动失败，继续..." -ForegroundColor DarkYellow
    }

    if ($dockerUp.ExitCode -eq 0) {
        # 等待 MySQL 就绪
        Write-Host "  等待 MySQL 就绪..." -ForegroundColor DarkGray
        $maxWait = 30
        for ($i = 0; $i -lt $maxWait; $i++) {
            Start-Sleep -Seconds 1
            $readyCheck = Invoke-NativeCommand { docker compose exec -T mysql mysqladmin ping -h localhost -u $env:MYSQL_USER -p"$env:MYSQL_PASSWORD" }
            $ready = ($readyCheck.Output | Out-String).Trim()
            if ($ready -eq "mysqld is alive") { break }
            if ($i % 5 -eq 0) { Write-Host "  已等待 $($i + 1)s..." -ForegroundColor DarkGray }
        }

        if ($i -ge $maxWait) {
            Write-Host "  MySQL 未就绪，继续启动（可能不影响）" -ForegroundColor DarkYellow
        }
    }
} else {
    Write-Host "  未检测到 docker，跳过容器启动；如你本机已有 MySQL，可继续。" -ForegroundColor DarkYellow
}

$mysqlReachable = Test-TcpPort -HostName $env:MYSQL_HOST -Port ([int]$env:MYSQL_PORT)
if (-not $mysqlReachable) {
    Write-Host ""
    Write-Host "数据库仍不可连接：$($env:MYSQL_HOST):$($env:MYSQL_PORT)" -ForegroundColor Red
    Write-Host "请先启动 Docker Desktop，或确保本机 / .env 指向的 MySQL 已可访问后再重试。" -ForegroundColor Red
    return
}

# 2. 启动后端
Write-Host ""
Write-Host "[2/3] 启动后端 (FastAPI :8787)..." -ForegroundColor Yellow
$backendRoot = Join-Path $ProjectRoot "server"
$backendCommand = @'
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port $env:PORT --app-dir .
'@

Start-Process -FilePath $PowerShellExe `
    -WorkingDirectory $backendRoot `
    -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand) `
    -WindowStyle Normal

# 3. 启动前端
Write-Host "[3/3] 启动前端 (Vite :5173)..." -ForegroundColor Yellow
$frontendCommand = @'
if (-not (Test-Path "node_modules")) {
    npm.cmd install
}
npm.cmd run dev:client
'@

Start-Process -FilePath $PowerShellExe `
    -WorkingDirectory $ProjectRoot `
    -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand) `
    -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  已启动！" -ForegroundColor Magenta
Write-Host "  前端: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  后端: http://localhost:8787/api/health" -ForegroundColor Cyan
Write-Host "  点击右上角齿轮设置 MiniMax API" -ForegroundColor DarkGray
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
