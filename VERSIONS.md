# 版本说明

## 稳定版（无已知 bug）

| 版本 | 说明 |
|------|------|
| **v0.1.15** | 首个测试通过的稳定版。修复 v0.1.0-v0.1.14 全部 10 个打包 bug |

## Bug 版本（请勿使用，仅作历史记录）

以下版本均有已知打包 bug，请使用 **v0.1.15** 或更新版本。

| 版本 | Bug | 状态 |
|------|-----|------|
| v0.1.0 | 首次打包，UPX 压缩导致启动 ACCESS_VIOLATION | ❌ 不可用 |
| v0.1.1 | 图标替换，UPX 问题未修 | ❌ 不可用 |
| v0.1.2 | 禁用 UPX，但 desktop 命名空间包未收集 → ModuleNotFoundError: desktop.config | ❌ 不可用 |
| v0.1.3 | 修命名空间包，但 app 模块未收集 → ModuleNotFoundError: app | ❌ 不可用 |
| v0.1.4 | 修 app 收集，但 collect_submodules 返回空 → 仍缺模块 | ❌ 不可用 |
| v0.1.5 | 源码作 fallback，但后端线程异常被吞 → 控制台无报错 | ❌ 不可用 |
| v0.1.6 | 暴露后端错误，但 stdin race 导致闪退 | ❌ 不可用 |
| v0.1.7 | 修 stdin race，但 pythonnet 崩溃 → RuntimeError: Python.Runtime.Loader.Initialize | ❌ 不可用 |
| v0.1.8 | 打包 pythonnet DLL → 仍无法初始化 | ❌ 不可用 |
| v0.1.9 | 强制 EdgeChromium backend → 仍走 WinForms/pythonnet 路径 | ❌ 不可用 |
| v0.1.10 | 改用 Edge --app 模式绕过 pythonnet，但缺 httpx → LLM 调用失败 | ❌ 不可用 |
| v0.1.11 | 补 httpx，但前端 new URL() 抛 Invalid URL + 缺 distro | ❌ 不可用 |
| v0.1.12 | 修 Invalid URL + 补 distro，但 index.html 遗留 __port__.js 404 + pywebview 被打包 | ❌ 不可用 |
| v0.1.13 | 删 __port__.js + 排除 pywebview，但 workflow 缺 pyinstaller → 构建失败 | ❌ 不可用 |
| v0.1.14 | 修 workflow + 补全 openai 依赖，测试通过 | ⚠️ 可用但已被 v0.1.15 取代 |

## 双脚本方案

双脚本方案（`desktop-scripts` 分支）走原生 Python + pywebview，不经 PyInstaller 打包，**上述打包 bug 均不影响双脚本方案**。如遇 EXE 问题，请改用双脚本：

```bash
git clone https://github.com/madharker/ConceptForge.git
cd ConceptForge
git checkout desktop-scripts
desktop\setup.bat    # 首次运行
desktop\run.bat      # 以后启动
```
