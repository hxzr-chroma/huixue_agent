# huixue_agent

AI 学习助手：Streamlit 前端 + DeepSeek API + LangGraph 编排 + 本地 BM25 RAG（`data/knowledge/`）。

## 运行

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=你的密钥
streamlit run streamlit_app_simple_standalone.py
```

数据库与知识库在首次运行时会写入 `data/`。

## 核心功能

- 🔐 用户认证系统
- 📋 学习计划管理
- 📌 灵活的任务布置
- ✅ 任务状态追踪（待办→进行中→完成）
- 📊 学习进度记录
- 🎯 优先级系统
- 📅 按日期分组

## 项目结构

```
.
├── streamlit_app_simple_standalone.py  # 独立版本（推荐直接运行）
├── backend_server.py                   # FastAPI后端（可选）
├── main.py                            # 主程序
├── requirements.txt                   # 依赖
├── storage/
│   └── db.py                         # 数据库操作
├── utils/
│   └── llm.py                        # LLM封装
├── agents/
│   └── input_parser.py               # 输入解析
├── graph/
│   └── workflows.py                  # LangGraph工作流
└── data/
    └── study_assistant.db            # SQLite数据库
```