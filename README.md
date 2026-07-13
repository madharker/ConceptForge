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

## 快速开始

前后端分离架构，需分别启动后端与前端。

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

启动后：
- 健康检查：GET http://localhost:8000/api/health
- 交互式文档：http://localhost:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

生产构建：

```bash
npm run build    # 产物输出到 dist/
npm run preview  # 本地预览构建产物
```

### 配置后端地址

前端默认请求 `http://localhost:8000`。如需改后端地址，在 `frontend/` 下创建 `.env.local`：

```bash
VITE_API_BASE=http://localhost:8000
```

### 接入 LLM

后端无 API key 时自动走 **mock 模式**，返回结构正确的 demo 数据（以「熵」为例），无需任何 key 即可跑通完整闭环。

接入真实 LLM 通过环境变量配置（OpenAI 兼容）：

| 变量 | 说明 | 默认 |
| --- | --- | --- |
| `CF_LLM_BASE_URL` | API base url（如 `https://api.deepseek.com/v1`） | 无（mock 模式） |
| `CF_LLM_API_KEY` | API key。**为空时自动启用 mock 回退** | 空 |
| `CF_LLM_MODEL` | 模型名 | `gpt-4o-mini` |

**支持的 LLM 服务**：
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
│       └── llm_client.py # OpenAI 兼容客户端 + mock 回退
├── frontend/             # Vite + React 前端
│   └── src/
│       ├── components/   # TopicView / ResearchFlow / ResultsView
│       ├── api.js        # 接口 fetch 封装
│       └── styles.css    # 深色衬线主题
├── deploy/               # 部署脚本
└── static-mvp/           # 落地页静态原型
```

## API 端点

### 业务流程接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查，返回 `{"status":"ok"}` |
| GET | `/api/topics/new?subject=<可选>` | 生成新课题，返回 `{id, question, background}` |
| POST | `/api/submissions` | 提交 5 步研究，同步触发评定+对齐，返回 `{submission_id}` |
| GET | `/api/submissions/{id}/evaluation` | 获取课题+5步+五维评定+三层对齐的完整结果 |

### Skills 独立可调用接口

| 方法 | 路径 | body |
| --- | --- | --- |
| POST | `/api/skills/topic` | `{subject?}` |
| POST | `/api/skills/collect` | `{guess, evidence, contradiction, revision, conclusion}` |
| POST | `/api/skills/evaluate` | `{topic, submission}` |
| POST | `/api/skills/align` | `{topic, submission, evaluation?}` |

## 部署

### 后端

```bash
cd backend
bash run.sh        # 监听 0.0.0.0:8000
```

推荐用云服务器 + Nginx 反代，或直接部署到 Vercel/Railway 等平台。详见 [deploy/README.md](deploy/README.md)。

### 前端

构建产物 `dist/` 可托管到任意静态站点（Vercel / Netlify / Cloudflare Pages / 自建 Nginx）。注意配置 CORS 或同源反代。

## 技术栈

- **后端**：Python 3.10+ / FastAPI / uvicorn / OpenAI SDK（兼容接口）
- **前端**：Vite + React（JavaScript）/ 纯 CSS 深色衬线主题

## Vibe Coding 声明

本项目代码由 AI 辅助生成（vibe coding），但**所有代码均经过人工审计**：

- 架构设计、技术选型、关键逻辑由人工决策
- 每个模块提交前均经人工阅读与校验
- 后端 API 契约、前端交互流程均经实际运行验证
- 安全相关（API key 处理、CORS）经人工审查

AI 负责把意图翻译成代码，人负责保证代码是对的。

## License

MIT
