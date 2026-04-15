# Huixue Agent 2.0 - 使用指南

## 功能总览

✅ **用户认证系统**
- 分离的登录和注册页面
- JWT Token认证
- 安全的密码存储（bcrypt加密）

✅ **多计划管理**
- 单个用户可创建多个学习计划
- 计划的创建、读取、更新、删除（CRUD）
- 计划激活与归档管理

✅ **任务分类系统**
- 按分类组织任务（基础理论、实践练习、项目应用、总结复习等）
- 优先级设置（高、中、低）
- 任务状态跟踪（未开始、进行中、完成）
- 截止日期设置

✅ **系统测试**
- 数据库初始化
- 认证流程
- 计划CRUD操作
- 任务管理
- DeepSeek API集成（需要版本调整）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
API_BASE_URL=http://localhost:8000
SECRET_KEY=your-secret-key-for-development
DEEPSEEK_API_KEY=sk-d94926f2b2fa4ec3a6e1e8942c20c531
DATABASE_URL=sqlite:///./data/study_assistant.db
```

### 3. 启动后端服务

```bash
python backend_server.py
```

服务将运行在 `http://localhost:8000`

### 4. 启动前端

```bash
streamlit run streamlit_app.py
```

前端将运行在 `http://localhost:8501`

### 5. 测试系统

```bash
python test_integration.py
```

## 系统架构

### 后端 (FastAPI)

端点列表：

**认证**
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

**计划管理**
- `POST /api/plans` - 创建计划
- `GET /api/plans` - 列出用户的所有计划
- `GET /api/plans/{plan_id}` - 获取计划详情
- `PUT /api/plans/{plan_id}` - 更新计划
- `DELETE /api/plans/{plan_id}` - 删除计划
- `POST /api/plans/{plan_id}/activate` - 设置计划为活跃

**任务管理**
- `POST /api/plans/{plan_id}/tasks` - 创建任务
- `PUT /api/plans/{plan_id}/tasks/{task_id}` - 更新任务
- `DELETE /api/plans/{plan_id}/tasks/{task_id}` - 删除任务

### 前端 (Streamlit)

**页面结构**
- 登录页面 - 用户登录入口
- 注册页面 - 新用户注册入口
- 计划列表 - 显示用户的全部计划
- 创建计划 - 新建学习计划
- 计划详情 - 查看计划和任务
- 编辑计划 - 修改计划名称和任务

### 数据库 (SQLite)

**表结构**
- `users` - 用户信息（用户名、邮箱、密码哈希）
- `study_plans` - 学习计划
- `study_tasks` - 任务（包含分类、优先级、状态等）
- `progress_logs` - 学习进度记录
- `plan_adjustments` - 计划调整
- `evaluation_results` - 评估结果

## 使用工作流

1. **注册新用户**
   - 访问前端的注册页面
   - 输入用户名、邮箱、密码
   - 注册成功后自动登录

2. **创建学习计划**
   - 登录后点击"创建新计划"
   - 输入计划信息（名称、目标、时长、每天小时数）
   - 系统自动生成计划（需要DeepSeek API）

3. **管理计划任务**
   - 在计划编辑页面添加、编辑或删除任务
   - 为任务设置分类、优先级和截止日期
   - 任务会按分类和优先级组织显示

4. **查看计划**
   - 在计划详情页面查看任务树形结构
   - 任务按分类展示，便于组织和管理

## 测试结果

系统测试 (test_integration.py) 的结果：

✓ **数据库初始化** - 通过
✓ **用户认证** - 通过  
✓ **计划管理** - 通过
✓ **任务管理** - 通过
⚠ **DeepSeek API** - 需要版本调整

## 文件结构

```
.
├── backend_server.py              # FastAPI后端应用
├── streamlit_app.py               # Streamlit前端应用
├── streamlit_app_backup.py        # 原始前端备份
├── test_integration.py            # 集成测试脚本
├── .env                           # 环境变量配置
├── start_dev.bat                  # Windows启动脚本
├── start_dev.sh                   # Linux启动脚本
├── requirements.txt               # Python依赖
├── storage/
│   └── db.py                      # 数据库初始化和连接
├── services/
│   ├── study_planner_service.py   # 计划服务
│   └── schedule.py                # 日程服务
├── agents/
│   ├── input_parser.py            # 输入解析
│   ├── plan_agent.py              # 计划生成
│   ├── evaluation_agent.py        # 评估代理
│   └── optimization_agent.py      # 优化代理
├── utils/
│   ├── llm.py                     # LLM客户端
│   ├── goal_validation.py         # 目标验证
│   └── json_parser.py             # JSON解析
└── data/
    └── knowledge/                 # 知识库文件
```

## 常见问题

### Q: 如何更改默认端口？

A: 修改 `.env` 文件中的 `API_BASE_URL` 或直接在 `backend_server.py` 中修改监听端口。

### Q: 计划生成失败怎么办？

A: 确保 `DEEPSEEK_API_KEY` 正确配置，或者使用测试中的mock模式。

### Q:多个用户的计划如何隔离？

A: 系统通过JWT Token和user_id自动隔离，每个用户只能访问自己的计划。

## 下一步改进

- [ ] 完整的DeepSeek API集成
- [ ] 学习进度跟踪仪表板
- [ ] 实时协作功能
- [ ] 移动端适配
- [ ] AI智能推荐优化

## 许可证

MIT License
