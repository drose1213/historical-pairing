# 全局共享上下文｜Claude Code + Codex 双插件通用

## 核心固定规则
全程承接本项目所有历史需求、代码逻辑、开发约定、对话上下文；
切换模型、切换插件不丢失记忆，不重置规则、不重复询问、不跑偏；

开发流水线：
1. 日常业务开发、快速迭代：优先直接改代码并验证，不只停留在分析
2. 代码审查、Bug修复、性能优化、安全加固：重点看接口契约、配置优先级、启动链路、实际可运行性
3. 输出代码需完整可直接运行，说明关键修复点、验证结果和已知风险

## 项目技术栈
- 后端：Python + FastAPI + SQLAlchemy + MySQL + OpenAI SDK
- 前端：Vue 3 + TypeScript + Vite
- 运行环境：本地 Windows 开发
- 当前阶段：历史配对小游戏 MVP，可生成题目、提交判分、保存结果、配置 AI 出题接口

## 目录结构&核心模块
- `server/app/main.py`
  - API 入口
  - 创建游戏、提交答案、配置接口、健康检查
- `server/app/generator.py`
  - AI 出题逻辑
  - 内置兜底题库
  - MiniMax / OpenAI-compatible 响应兼容解析
- `server/app/models.py`
  - `Game / GamePair / GameAnswer / SystemConfig`
- `server/app/schemas.py`
  - Pydantic 模型
  - 提交唯一性校验
  - 配置项常量
- `client/src/App.vue`
  - 主界面、生成题目、配对、提交、结果展示
- `client/src/Settings.vue`
  - 页面右上角 API 设置弹层
- `client/src/api.ts`
  - 前端 API 请求层
- `start.ps1`
  - 一键启动和清理旧后端进程

## 编码与开发约束
1. 不擅自大改架构，尽量做小步可验证修复
2. 修改前先说明改动范围；修改后尽量补验证
3. 关键接口错误信息要可读，便于前端直接展示
4. 关键操作保留日志：创建游戏、提交答案、配置更新、AI 调用失败、解析失败
5. 遇到“API 正常但页面不出题”时，优先排查旧进程、数据库配置、AI 响应格式

## 已完成功能
- 关键词生成 5 组历史配对题
- 左右配对、提交判分、结果解释
- 游戏、题目、答案持久化到 MySQL
- 页面设置 AI 配置
- 根目录构建/类型检查脚本修复
- 配置接口安全收紧：
  - 仅允许本机访问
  - 不回显 `openai_api_key`
- MiniMax 返回 `<think>` 内容时的 JSON 提取兼容
- `start.ps1` 启动前自动清理本项目旧 `uvicorn` 进程

## 当前待优化/待开发
- 增加自动化测试：
  - `generator.py` 的 JSON 提取与兜底逻辑
  - `/api/games` 与 `/api/games/{id}/submit`
- 若继续扩展，可补：
  - 对局历史记录页
  - 更明确的管理员配置入口
  - AI 出题缓存
- 如需继续排查启动问题，优先关注端口 `8787` 是否被旧 `uvicorn` 占用

## 历史会话关键决策（跨模型共用记忆）
1. `.env` 仅是默认配置；数据库 `system_configs` 优先级更高
2. 页面设置过 API 后，即使 `.env` 是空，后端仍会调用数据库中的配置
3. MiniMax 通过 `https://api.minimax.chat/v1` 接入时，可能返回带 `<think>...</think>` 的文本，不能直接整段 `json.loads`
4. 页面不显示题目时，不要先怀疑前端模板，先确认：
   - `POST /api/games` 是否已成功返回 `leftItems/rightItems`
   - 当前 `8787` 是否命中旧后端进程
5. 当前更推荐通过 `.\start.ps1` 启动项目，而不是依赖历史残留终端手动重跑

## 常用命令&环境指令
- 一键启动：
  - `powershell -ExecutionPolicy Bypass -File .\start.ps1`
- 前端启动：
  - `npm run dev:client`
- 手动后端启动：
  - `cd server`
  - `.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8787 --app-dir .`
- 类型检查：
  - `npm run typecheck`
- 生产构建：
  - `npm run build`
- 后端语法检查：
  - `python -m compileall server\app`
- 接口快速验证：
  - `Invoke-RestMethod http://localhost:8787/api/health`
  - `Invoke-RestMethod http://localhost:8787/api/games -Method Post -ContentType 'application/json' -Body (@{ keyword = '三国' } | ConvertTo-Json)`

## 禁止操作清单（避坑）
- 不要随意删除历史业务代码
- 不要忽略数据库里的 API 配置
- 不要在未确认监听进程的情况下反复叠加启动多个后端
- 不要把“页面不出题”直接归因给前端；先确认接口返回和端口占用

## 近期已处理变动压缩记录
- 修复 `/api/configs` 安全问题，限制为本机访问并隐藏密钥回显
- 修复 `/api/health` 数据库异常时错误地返回 200 的问题
- 修复答案提交唯一性和“必须属于当前游戏”的校验
- 修复 MiniMax 返回思维链导致 JSON 解析失败的问题
- 修复根目录 `build/typecheck` 脚本路径错误
- 更新 `README.md`，补充启动方式、配置说明和常见问题排查
- 更新 `start.ps1`，启动前清理旧后端进程、按端口清理 `8787` 监听，并改为单实例启动
- 补充 `server/requirements.txt` 中的 `cryptography`，兼容 MySQL 8 默认认证方式
