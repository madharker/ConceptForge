# ConceptForge 桌面端

ConceptForge 的 PyWebView 桌面端应用。后端逻辑内嵌本地运行，LLM API 由用户在设置页自接入，无 key 时走 mock 开箱即用。彻底绕开 Web 部署的备案/域名/HTTPS/超时问题。

## 架构

```
desktop/main.py (PyWebView 入口)
  ├── 后台线程: uvicorn desktop.app:app (127.0.0.1:随机端口)
  ├── 写入 __port__.js 注入端口到前端
  ├── 加载持久化 LLM 配置注入 llm_client
  └── 打开 WebView 窗口加载 desktop/assets/index.html

desktop/app.py (FastAPI)
  ├── 挂载 backend/app/routers (topics, submissions)
  └── 新增 /api/settings (GET/PUT) + /api/settings/test (POST)

desktop/frontend/ (Vite + React)
  ├── 复用 Web 端组件 (TopicView/ResearchFlow/ResultsView)
  ├── 新增 SettingsView (LLM 配置 + 测试连接)
  └── api.js 读取 window.__CF_PORT__
```

## 快速开始（普通使用，无需 Node.js）

仓库已包含构建好的前端产物 `desktop/assets/`，普通用户只需装 Python 和 Git 即可运行。

### 前置条件
- **Git**（用于克隆仓库和更新版本）
  - Linux: `sudo apt install git`（Debian/Ubuntu）或 `sudo dnf install git`（Fedora）
  - macOS: `brew install git` 或安装 Xcode Command Line Tools（`xcode-select --install`）
  - Windows: 从 https://git-scm.com/download/win 下载安装，安装时一路默认即可
- **Python 3.10+**（https://www.python.org/downloads/）
  - Windows 安装时务必勾选 "Add Python to PATH"
- 桌面环境（PyWebView 需要图形界面）

### 获取代码

```bash
git clone https://github.com/madharker/ConceptForge.git
cd ConceptForge
git checkout desktop
```

> 也可在仓库页面点 "Code → Download ZIP" 解压，无需 Git，但后续更新需重新下载。

### 一键安装

提供跨平台安装脚本，自动创建虚拟环境并安装依赖：

**Linux / macOS:**
```bash
bash desktop/setup.sh
```

**Windows:**
双击 `desktop/setup.bat`，或命令行执行：
```cmd
desktop\setup.bat
```

脚本会自动：
1. 检查 Python 3.10+
2. 创建虚拟环境 `.venv`
3. 安装 `requirements.txt` 中所有依赖
4. Linux 检测 WebKitGTK 系统依赖（缺失时给出安装命令）
5. 检查前端构建产物是否就绪

> Linux 用户若脚本提示 WebKitGTK 缺失，需手动安装：
> ```bash
> sudo apt install libwebkit2gtk-4.1-dev   # Ubuntu/Debian
> ```
> Windows 无额外系统依赖（Win10+ 自带 Edge WebView2）。

### 运行

安装完成后，用启动脚本即可，**无需手动激活虚拟环境**：

**Linux / macOS:**
```bash
bash desktop/run.sh
```

**Windows:**
双击 `desktop/run.bat`，或命令行执行：
```cmd
desktop\run.bat
```

启动脚本会自动调用 `.venv` 中的 Python 运行 `main.py`，无需 `source activate`。

> 首次启动为 mock 模式，可直接体验完整流程。接入 LLM 见下方"使用流程"。

### 手动安装（不想用脚本）

如跳过脚本手动安装：
```bash
python -m venv desktop/.venv
source desktop/.venv/bin/activate   # Windows: desktop\.venv\Scripts\activate
pip install -r desktop/requirements.txt
bash desktop/run.sh                 # Windows: desktop\run.bat
```

## 更新到新版本

推荐直接删除整个目录重新拉取安装，最简单无副作用：

**Linux / macOS:**
```bash
cd ..                                    # 退出 ConceptForge 目录
rm -rf ConceptForge                      # 删除整个项目
git clone https://github.com/madharker/ConceptForge.git
cd ConceptForge
git checkout desktop
bash desktop/setup.sh
bash desktop/run.sh
```

**Windows（PowerShell 或 CMD）:**
```cmd
cd ..
rmdir /s /q ConceptForge
git clone https://github.com/madharker/ConceptForge.git
cd ConceptForge
git checkout desktop
desktop\setup.bat
desktop\run.bat
```

> 设置页保存的 LLM 配置存储在系统目录（Windows: `%APPDATA%\ConceptForge`，Linux: `~/.config/ConceptForge`，macOS: `~/Library/Application Support/ConceptForge`），删除项目目录不会丢失，重装后自动读取。

## 开发模式（修改前端源码时才需要）

仅当你需要修改 `desktop/frontend/` 下的 React 源码并重新构建时，才需要 Node.js。普通使用请跳过本节。

### 额外前置条件
- Node.js 18+（仅重建前端时需要）

### Node.js PATH 问题提示
Windows 安装 Node.js 后，若在新开的终端中 `npm` 命令仍不可用，常见原因：
- 安装时未勾选 "Add to PATH" → 重装并勾选，或手动将 `%AppData%\npm` 和 Node.js 安装目录加入系统 PATH
- 安装后未重启终端 → **关闭所有终端窗口后重新打开**（PATH 变更对新开的终端生效）
- 仍不行 → 注销或重启 Windows

Linux/macOS 若 `npm` 不可用，确认 Node.js 安装路径在 `$PATH` 中（通常 `/usr/local/bin` 或 `~/.nvm/versions/node/*/bin`）。

### 重新构建前端
```bash
python desktop/build_frontend.py
```
或手动:
```bash
cd desktop/frontend
npm install
npm run build   # 产物输出到 desktop/assets/
```

## 使用流程

1. **首次启动**：应用以 mock 模式运行，可直接体验完整流程（课题→5步研究→评定+对齐+按需风格总结）
2. **接入 LLM**：点击 header 的"设置" → 填入 Base URL / API Key / Model → 测试连接 → 保存
3. **使用真实 LLM**：保存后立即生效，无需重启；配置持久化，下次启动自动加载

支持的 LLM 服务（OpenAI 兼容）：
- OpenAI: `https://api.openai.com/v1` + `sk-xxx` + `gpt-4o-mini`
- DeepSeek: `https://api.deepseek.com/v1` + `sk-xxx` + `deepseek-chat`
- 其他兼容服务同理

## 打包

### Windows
```bash
pip install pyinstaller
pyinstaller desktop/build.spec
# 产物: dist/ConceptForge/ConceptForge.exe
```
双击 `ConceptForge.exe` 运行。可打包成 zip 分发。

### Linux
```bash
pip install pyinstaller
pyinstaller desktop/build.spec
# 产物: dist/ConceptForge/ConceptForge
```
运行 `./dist/ConceptForge/ConceptForge`。需目标机器有 WebKitGTK。

如需 AppImage 格式，额外用 appimagetool 转换。

## 文件结构

```
desktop/
├── main.py              # PyWebView 入口
├── app.py               # FastAPI 应用 (挂载后端 + settings 端点)
├── config.py            # 用户配置持久化 (跨平台路径)
├── build_frontend.py    # 前端构建脚本
├── build.spec           # PyInstaller 打包配置
├── setup.sh             # 一键安装脚本 (Linux/macOS)
├── setup.bat            # 一键安装脚本 (Windows)
├── requirements.txt     # Python 依赖
├── assets/              # 前端构建产物 (npm run build 生成)
│   ├── index.html
│   ├── __port__.js      # 运行时生成，注入后端端口
│   └── assets/
└── frontend/            # 前端源码 (Vite + React)
    ├── src/
    │   ├── components/
    │   │   ├── TopicView.jsx       # 复用自 Web 端
    │   │   ├── ResearchFlow.jsx    # 复用自 Web 端
    │   │   ├── ResultsView.jsx     # 复用自 Web 端 (含按需风格总结)
    │   │   └── SettingsView.jsx    # 桌面端新增
    │   ├── App.jsx
    │   ├── api.js
    │   └── styles.css
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## 配置文件位置

LLM 配置持久化在用户目录:
- **Windows**: `%APPDATA%\ConceptForge\config.json`
- **Linux**: `~/.config/conceptforge/config.json`
- **macOS**: `~/Library/Application Support/ConceptForge/config.json`

## 排错

**窗口打开但白屏**
- 确认 `desktop/assets/index.html` 存在（运行过 `build_frontend.py`）
- 确认 `__port__.js` 存在（`main.py` 运行时自动生成）

**API 请求失败**
- 检查后端是否启动（看是否有控制台输出，可临时改 `console=True` 在 build.spec）
- 检查端口注入：浏览器调试模式下看 `window.__CF_PORT__`

**LLM 调用失败**
- 设置页点"测试连接"验证配置
- 确认 Base URL 格式（OpenAI 兼容，通常以 `/v1` 结尾）
- 无 key 时自动走 mock，不影响流程体验

**打包后体积大**
- PyInstaller 目录模式约 80-120MB（含 Python + PyWebView + FastAPI）
- 可用 UPX 压缩（build.spec 已启用 `upx=True`）

## 与 Web 端的关系

桌面端与 Web 端 (`/workspace/frontend/` + `/workspace/backend/`) 独立并存:
- 桌面端复用 Web 端的 React 组件和后端 skills，但不修改它们
- Web 端仍可独立部署（Vercel + 云服务器）
- 桌面端适合无网络/无服务器的演示场景
