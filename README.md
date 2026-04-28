# 历史配对

Python FastAPI + Vue + MySQL 的历史配对小游戏 MVP。

## 功能

- 输入历史关键词，生成 4 组配对题
- 点击左侧，再点击右侧完成配对
- 后端判分，前端展示正确答案和解释
- 游戏、题目、用户答案写入 MySQL
- 配置 `OPENAI_API_KEY` 后走 AI 实时生成；不配置时使用内置生成器兜底
- 兼容 OpenAI 和 MiniMax 一类 OpenAI-compatible 接口

## 启动

### 一键启动

先确保 Docker Desktop 已启动，或者本机已有可访问的 MySQL（默认 `127.0.0.1:3306`）。

`start.ps1` 现在会在启动前自动清理当前项目残留的旧后端进程，并额外按端口清理 `8787` 的监听进程，避免旧的 `uvicorn` 实例占住端口导致页面拿到过期代码，或启动时报 `10048` 端口占用错误。

1. 安装前端依赖

```bash
npm install
```

2. 准备环境变量

```bash
copy .env.example .env
```

3. 执行一键启动脚本

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

脚本会完成这些动作：

- 读取根目录 `.env`
- 尝试启动 `docker compose` 中的 MySQL
- 自动创建 `server/.venv` 并安装后端依赖
- 启动单实例 FastAPI 后端
- 启动 Vite 前端
- 如果 `8787` 仍被占用，会在启动前直接提示并中止，而不是等到 uvicorn 报错

### 手动启动

1. 安装后端依赖

```bash
cd server
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..
```

说明：

- 当前依赖中已包含 `cryptography`
- 这是为了兼容 MySQL 8 默认的 `caching_sha2_password / sha256_password` 认证方式
- 如果你之前已经创建过 `.venv`，请重新执行一次 `pip install -r requirements.txt`

2. 启动 MySQL

```bash
docker compose up -d mysql
```

3. 启动前后端

```bash
cd server
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8787 --app-dir .
```

另开一个终端：

```bash
npm run dev:client
```

说明：

- 手动启动后端时，建议只保留一个 `uvicorn` 实例
- 如你之前已经启动过旧后端，先关闭旧的 PowerShell / Python 进程再重启
- 当前更推荐使用 `.\start.ps1`，因为它会自动处理旧进程残留问题

前端地址：http://localhost:5173

后端地址：http://localhost:8787/api/health

## AI 配置

- `.env` 里的 `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL` 只是默认值
- 页面右上角“API 设置”保存的配置会写入数据库，并优先于 `.env`
- 如果 `.env` 为空但页面里配置过 API，后端仍会调用数据库中的配置
- `OPENAI_BASE_URL=https://api.minimax.chat/v1` 时可直接对接 MiniMax

## 常见问题

### 1. API 健康检查正常，但页面点“生成题目”没反应

先看页面是否出现红色错误提示。如果提示类似：

```text
题目生成失败：Expecting value: line 1 column 1 (char 0)
```

通常有两类原因：

- 当前后端仍是旧进程，没加载到最新代码
- 你配置的是 MiniMax，返回体前面带了推理内容，旧解析逻辑无法直接 `json.loads`

处理方式：

1. 关闭所有旧的后端 PowerShell 窗口
2. 重新运行 `.\start.ps1`
3. 刷新浏览器页面后再试

### 2. `.env` 明明没配 API，为什么还会调用大模型

因为页面“API 设置”保存到数据库后，会覆盖 `.env` 默认值。要排查时，优先检查页面右上角配置。

### 3. 后端启动时报 `cryptography package is required`

这是因为当前连接的是 MySQL 8，默认认证插件需要 `cryptography` 支持。

重新安装后端依赖即可：

```bash
cd server
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. 页面还是不出题，怎么快速确认是前端还是后端

可以直接访问：

- `http://localhost:8787/api/health`

如果健康检查正常，再手动调用：

```powershell
$body = @{ keyword = '三国' } | ConvertTo-Json
Invoke-RestMethod http://localhost:8787/api/games -Method Post -ContentType 'application/json' -Body $body
```

- 如果这里能返回 `leftItems/rightItems`，说明后端正常，问题在页面刷新或浏览器缓存
- 如果这里直接报错，优先检查后端日志和 API 配置

## 数据库表

FastAPI 启动时会自动创建：

- `games`
- `game_pairs`
- `game_answers`

## API

### 创建游戏

`POST /api/games`

```json
{
  "keyword": "三国"
}
```

### 提交答案

`POST /api/games/{gameId}/submit`

```json
{
  "matches": [
    {
      "leftId": "左侧题目 ID",
      "rightId": "右侧选项 ID"
    }
  ]
}
```
