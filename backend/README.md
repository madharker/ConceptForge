# ConceptForge 概念锻造器 · 后端

研究式学习平台的后端 harness + skills，编排「课题生成 → 5 步研究收集 → AI 过程评定 → 主流语境对齐」完整闭环，并以 REST/JSON 对外暴露。

技术栈：Python 3 + FastAPI + uvicorn + OpenAI 兼容 LLM 客户端。

## 目录结构

```
backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, 挂载路由
│   ├── harness.py         # 编排器 Harness（按序调度 skills）
│   ├── llm_client.py      # OpenAI 兼容客户端 + mock 回退
│   ├── schemas.py         # pydantic 请求/响应模型
│   ├── store.py           # 内存存储（topics / submissions）
│   ├── skills/
│   │   ├── topic_skill.py     # 课题生成
│   │   ├── collect_skill.py   # 5 步研究收集（校验/归一化）
│   │   ├── evaluate_skill.py  # AI 过程评定（五维）
│   │   └── align_skill.py     # 主流语境对齐（三层 + 差异）
│   └── routers/
│       ├── topics.py          # 课题相关端点
│       └── submissions.py     # 提交/评定端点 + skills 独立端点
├── requirements.txt
├── run.sh                 # 启动脚本 (uvicorn 0.0.0.0:8000)
└── README.md
```

## 安装与运行

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

或直接用启动脚本：

```bash
cd backend
bash run.sh        # 监听 0.0.0.0:8000
```

启动后访问：
- 健康检查：GET http://localhost:8000/api/health
- 交互式文档：http://localhost:8000/docs

## 环境变量

| 变量 | 说明 | 默认 |
| --- | --- | --- |
| `CF_LLM_BASE_URL` | OpenAI 兼容 API 的 base url（如 `https://api.openai.com/v1`） | 无（mock 模式不需要） |
| `CF_LLM_API_KEY` | API key。**为空/未设置时自动启用 mock 回退**，整套流程无需 key 即可跑通 | 空 |
| `CF_LLM_MODEL` | 模型名 | `gpt-4o-mini` |

### Mock 回退机制（重要）

当 `CF_LLM_API_KEY` 未设置或为空时，所有 LLM skill 自动降级为**确定性 mock**，返回结构正确、内容合理的 JSON（以「熵」为例）。这样在本地 / 开发 / E2E 测试环境下，无需任何 API key 即可跑通「课题 → 5 步 → 评定 → 对齐」完整闭环。

设置 `CF_LLM_API_KEY` 后即切换为真实 LLM 调用（OpenAI 兼容接口）。

## API 端点

### 业务流程接口
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查，返回 `{"status":"ok"}` |
| GET | `/api/topics/new?subject=<可选>` | 生成新课题，返回 `{id, question, background}` |
| POST | `/api/submissions` | 提交 5 步研究，同步触发评定+对齐，返回 `{submission_id}` |
| GET | `/api/submissions/{id}/evaluation` | 获取课题+5步+五维评定+三层对齐的完整结果（404 若不存在） |

### Skills 独立可调用接口
| 方法 | 路径 | body |
| --- | --- | --- |
| POST | `/api/skills/topic` | `{subject?}` |
| POST | `/api/skills/collect` | `{guess, evidence, contradiction, revision, conclusion}` |
| POST | `/api/skills/evaluate` | `{topic, submission}` |
| POST | `/api/skills/align` | `{topic, submission, evaluation?}` |

### POST /api/submissions body 示例
```json
{
  "topic_id": "topic-entropy-demo",
  "guess": "...",
  "evidence": "...",
  "contradiction": "...",
  "revision": "...",
  "conclusion": "..."
}
```
