# 概念锻造器 ConceptForge · 前端

研究式学习平台前端 —— 消费后端 API，渲染 5 步研究流程与 AI 评定 / 主流对齐结果。
对应 Spec Task 7（搭建前端学习流程页面）。

## 技术栈

- Vite + React（JavaScript）
- 纯 CSS（深色衬线阅读风格，色板继承自落地页）
- 后端 API 基址通过环境变量 `VITE_API_BASE` 配置，默认 `http://localhost:8000`

## 运行

```bash
npm install
npm run dev      # 启动开发服务器，默认 http://localhost:5173
```

生产构建：

```bash
npm run build    # 产物输出到 dist/
npm run preview  # 本地预览构建产物
```

## 配置后端地址

在项目根目录创建 `.env.local`：

```bash
VITE_API_BASE=http://localhost:8000
```

后端未启动时，前端会正常渲染界面，仅在调用接口时展示错误提示与「重新尝试」按钮。

## 后端 API 契约（前端消费，不修改）

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET  | `/api/topics/new?subject=<可选>` | 获取新课题，返回 `{ id, question, background }` |
| POST | `/api/submissions` | 提交 5 步研究，body `{ topic_id, guess, evidence, contradiction, revision, conclusion }`，返回 `{ submission_id }` |
| GET  | `/api/submissions/{id}/evaluation` | 获取五维评定 + 三层表述 + 差异说明 |

## 三个视图

1. **课题视图（TopicView）**：展示课题问题与背景，「开始研究」进入流程。
2. **研究流程（ResearchFlow）**：5 步引导（原始猜想 / 收集证据 / 遇到矛盾 / 修正理解 / 临时结论），
   顶部 stepper 指示进度，每次只显示一步，支持上一步 / 下一步切换并保留输入，第 5 步「提交研究」。
3. **结果视图（ResultsView）**：分模块展示五维评定、三层表述、差异说明，并提供「换一个课题」重置流程。

## 目录结构

```
frontend/
├─ index.html
├─ package.json
├─ vite.config.js
├─ .gitignore
├─ README.md
└─ src/
   ├─ main.jsx
   ├─ App.jsx          # 视图状态机
   ├─ api.js           # 三个接口的 fetch 封装
   ├─ styles.css       # 深色衬线主题
   └─ components/
      ├─ TopicView.jsx
      ├─ ResearchFlow.jsx
      └─ ResultsView.jsx
```
