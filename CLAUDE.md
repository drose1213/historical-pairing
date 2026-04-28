# 项目全局说明
<!-- 请先读取并完整理解项目根目录的 CLAUDE.md，基于项目现有规则、已完成功能和历史决策，接续开发，不要重复询问基础项目信息 -->

## 1 基础信息
项目名称：历史配对（historical-pairing）
技术栈：Python FastAPI + Vue 3 + TypeScript + MySQL
运行环境：本地 Windows 开发
项目目标：实现一个历史关键词配对小游戏 MVP，支持 AI 实时出题、提交判分、结果解释展示，以及基础配置管理

## 2 目录结构&核心模块
- 核心业务目录：
  - `server/app/main.py`：FastAPI 入口、路由、判分、配置接口
  - `server/app/generator.py`：题目生成、AI 调用、MiniMax/OpenAI 兼容解析、兜底题库
  - `server/app/models.py`：`games / game_pairs / game_answers / system_configs`
  - `server/app/schemas.py`：请求响应模型、配置项常量、提交校验
  - `client/src/App.vue`：主页面、题目生成、配对、提交、结果展示
  - `client/src/Settings.vue`：API 设置弹层
  - `client/src/api.ts`：前端 API 封装
  - `start.ps1`：Windows 一键启动脚本
- 配置文件位置：
  - 根目录 `.env`
  - 根目录 `.env.example`
  - 页面右上角 API 设置会写入数据库 `system_configs`，并优先于 `.env`
- 数据库相关：
  - 连接配置见 `server/app/config.py`
  - 表由 `server/app/database.py -> init_db()` 自动创建
  - 默认使用 MySQL，开发时通过 `docker-compose.yml` 启动
- 工具类/公共组件：
  - `server/app/database.py`：数据库引擎、会话、初始化
  - `client/src/styles.css`：全局样式

## 3 编码规范
1. 命名风格：后端 Python 使用清晰语义命名，前端沿用现有 camelCase；仅在必要处加简短注释
2. 数据库操作：禁止全表误删；当前 `GameAnswer` 删除仅限单局 `game_id`
3. 异常处理：接口使用 `HTTPException` 返回可读错误；AI 调用失败和解析失败要明确区分
4. 日志规范：关键操作打印日志，如创建游戏、提交答案、配置更新、AI 调用失败

## 4 已完成功能
- 历史关键词生成 5 组配对题
- 左右配对、提交判分、结果解释展示
- 游戏、题目、用户答案落库
- 内置兜底题库：三国、唐朝、秦始皇、法国大革命、工业革命
- API 设置面板，支持在页面中配置 `openai_api_key / openai_base_url / openai_model`
- 兼容 OpenAI-compatible 提供方，已处理 MiniMax 返回 `<think>...</think>` 的场景
- Windows 一键启动脚本，自动清理旧后端进程、拉起 MySQL/后端/前端

## 5 当前待优化/待开发
- 待改Bug：
  - 进一步确认本机历史残留 `uvicorn` 进程场景是否已被完全规避
  - 当前未补接口级自动化测试，回归依赖手工验证
- 新增需求：
  - 可考虑增加历史记录页 / 最近对局回看
  - 可考虑增加管理员级配置入口和更细的权限控制
- 性能优化点：
  - AI 出题结果可考虑缓存
  - 配置读取当前每次请求都查数据库，可视情况做轻量缓存

## 6 历史会话关键决策（跨模型共用记忆）
> 每次换模型、续任务，AI 优先看这里
1. 配置优先级：数据库 `system_configs` 高于 `.env`；页面设置过 API 后，即使 `.env` 为空也会走数据库配置
2. 安全修复已做：`/api/configs` 仅允许本机访问；`openai_api_key` 不再回显给前端，设置页只显示“已配置”
3. MiniMax 兼容已做：`generator.py` 会清理 `<think>...</think>`、代码块及前后缀文本，再提取 JSON
4. 启动策略已调整：`start.ps1` 启动前清理本项目旧 `uvicorn` 进程，后端改为单实例稳定模式，不再用 `--reload`
5. 根目录脚本已修复：`npm run typecheck` 与 `npm run build` 现显式指向 `client/tsconfig.json` 和 `vite.config.ts`

## 7 常用命令&环境指令
- 一键启动：
  - `powershell -ExecutionPolicy Bypass -File .\start.ps1`
- 手动启动后端：
  - `cd server`
  - `.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8787 --app-dir .`
- 手动启动前端：
  - `npm run dev:client`
- 类型检查：
  - `npm run typecheck`
- 打包命令：
  - `npm run build`
- 后端语法检查：
  - `python -m compileall server\app`
- 本地调试接口：
  - `http://localhost:8787/api/health`
  - `POST http://localhost:8787/api/games`

## 8 禁止操作清单（避坑）
- 不要擅自大改原有架构
- 不要随意删除历史业务代码
- 修改前先说明改动范围
- 不要忽略数据库配置优先级，排查 AI 出题问题时先查页面设置和 `system_configs`
- 不要默认使用旧的 `npm run dev` 作为唯一启动方式，当前更推荐 `.\start.ps1`
