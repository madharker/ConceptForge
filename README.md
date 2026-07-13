# 概念锻造器 ConceptForge

```
   ______                            __  ______
  / ____/___  ____  ________  ____  / /_/ ____/___  _________ ____
 / /   / __ \/ __ \/ ___/ _ \/ __ \/ __/ /_  / __ \/ ___/ __ `/ _ \
/ /___/ /_/ / / / / /__/  __/ /_/ / /_/ __/ / /_/ / /  / /_/ /  __/
\____/\____/_/ /_/\___/\___/ .___/\__/_/    \____/_/   \__, /\___/
                          /_/                         /____/
```

先研究、后定义的研究式学习平台。让学习者像研究者一样思考——从原始猜想到严谨定义，AI 全程陪伴并给出过程性评定。

---

## 这是什么

很多概念学完就忘，是因为直接接受了"标准答案"，没有经历自己提出假设、找证据、撞矛盾、再修正的完整过程。ConceptForge 把这个过程结构化为 **5 步研究流程**，并由 LLM 在过程中给出五维评定与主流语境对齐，让学习者真正"锻造"出自己的概念理解。

**完整闭环**：课题生成 → 5 步研究 → AI 五维评定 → 三层表述对齐 → 风格与质量总结

## 两种使用方式

### 1. 桌面端（推荐普通用户）

无需服务器、无需域名备案、无需配置环境变量。下载即用。

- **Windows 下载**：[Releases 页](https://github.com/madharker/ConceptForge/releases) 下载 zip，解压双击 `ConceptForge.exe`
- **源码运行**（Linux/macOS/Windows）：见 [desktop/README.md](desktop/README.md)

桌面端特点：
- PyWebView + FastAPI 本地运行，LLM 调用直连用户自接入的 API
- 无 API key 时自动走 **mock 模式**，开箱即可体验完整流程
- LLM 配置持久化在用户目录，重启不丢
- 流式调用 + 空闲超时检测，模型卡住时前端可见
- LLM 调用日志面板（设置页），实时观测输入输出与异常

### 2. Web 端（适合自部署/演示）

前后端分离，可独立部署。见 [frontend/README.md](frontend/README.md) 与 [backend/README.md](backend/README.md)。

## 研究流程

```
课题（AI 生成或指定主题）
  ↓
1. 原始猜想    你先写下对这个概念的理解
2. 收集证据    查阅、观察、记录支持或反驳你猜想的材料
3. 遇到矛盾    哪些证据与你的猜想冲突？
4. 修正理解    根据矛盾，调整你的定义
5. 临时结论    给出当前阶段最严谨的表述
  ↓
AI 评定（五维：问题理解 / 证据质量 / 推理链条 / 概念边界 / 矛盾处理）
  ↓
三层表述对齐（你的表达 → 严谨改写 → 主流定义 + 差异说明）
  ↓
风格与质量总结（按需展开：表达风格 / 思维特征 / 质量总评 / 改进建议）
```

## 快速开始（桌面端源码）

```bash
git clone https://github.com/madharker/ConceptForge.git
cd ConceptForge
git checkout desktop

# Linux / macOS
bash desktop/setup.sh
bash desktop/run.sh

# Windows
desktop\setup.bat
desktop\run.bat
```

首次启动为 mock 模式。接入真实 LLM：应用内点"设置" → 填 Base URL / API Key / Model → 测试连接 → 保存。

**支持的 LLM 服务**（OpenAI 兼容）：
- OpenAI: `https://api.openai.com/v1` + `gpt-4o-mini`
- DeepSeek: `https://api.deepseek.com/v1` + `deepseek-chat`
- 其他兼容服务同理

## 项目结构

```
ConceptForge/
├── backend/              # FastAPI 后端 (harness + skills + LLM client)
│   └── app/
│       ├── skills/       # 课题/收集/评定/对齐/风格总结
│       ├── routers/      # REST 端点
│       └── llm_client.py # OpenAI 兼容客户端 + mock 回退 + 流式超时
├── desktop/              # PyWebView 桌面端 (复用 backend)
│   ├── main.py           # 入口：起后端线程 + 注入端口 + 开窗口
│   ├── app.py            # FastAPI app + /api/settings + /api/llm/logs
│   ├── frontend/         # Vite + React 源码
│   ├── assets/           # 前端构建产物（已包含，普通用户无需 Node.js）
│   ├── build.spec        # PyInstaller 打包配置
│   ├── setup.sh/.bat     # 一键安装
│   └── run.sh/.bat       # 一键运行
├── frontend/             # Web 端前端（独立部署用）
└── .github/workflows/    # Windows EXE 自动构建
```

## 从源码构建 Windows EXE

```bash
# 本地构建（需 Windows + Python 3.10+ + Node.js 22+）
python desktop/build_frontend.py    # 构建前端
pyinstaller desktop/build.spec      # 打包
# 产物: dist/ConceptForge/ConceptForge.exe
```

或用 GitHub Actions 自动构建：打 tag 触发。

```bash
git tag v0.x.x
git push origin v0.x.x
# 自动构建并发布 Release，zip 附在 Release 页
```

## 配置文件位置

桌面端 LLM 配置持久化在用户目录（删除项目目录不丢失）：
- **Windows**: `%APPDATA%\ConceptForge\config.json`
- **Linux**: `~/.config/conceptforge/config.json`
- **macOS**: `~/Library/Application Support/ConceptForge/config.json`

## 技术栈

- **后端**：Python 3.10+ / FastAPI / uvicorn / OpenAI SDK（兼容接口）
- **前端**：Vite + React（JavaScript）/ 纯 CSS 深色衬线主题
- **桌面端**：PyWebView（Windows 用 Edge WebView2，Linux 用 WebKitGTK，macOS 用 WebKit）
- **打包**：PyInstaller（目录模式）+ GitHub Actions（Windows 自动构建）

## Vibe Coding 声明

本项目代码由 AI 辅助生成（vibe coding），但**所有代码均经过人工审计**：

- 架构设计、技术选型、关键逻辑由人工决策
- 每个模块提交前均经人工阅读与校验
- 后端 API 契约、前端交互流程、PyInstaller 打包路径均经实际运行验证
- 安全相关（配置持久化、API key 处理、CORS）经人工审查
（其实这个readme也是ai写的*小声）
## License

MIT
