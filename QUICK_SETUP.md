# 🚀 快速开始 - AI 学习助手

有两个版本可选择使用：

## 版本 1: 独立版本 ⭐ 推荐

**文件**: `streamlit_app_simple_standalone.py`

**特点**:
- ✅ 零依赖（仅需 streamlit）
- ✅ 开箱即用
- ✅ 完全独立，无需后端
- ✅ 推荐首选

### 运行步骤

```bash
# 1. 安装依赖
pip install streamlit

# 2. 运行应用
streamlit run streamlit_app_simple_standalone.py

# 3. 浏览器自动打开
# http://localhost:8501
```

### 功能

- 📝 **用户系统** - 注册/登录
- ✨ **创建计划** - 自由制定学习计划
- 📌 **布置任务** - 添加具体学习任务
  - 支持优先级（高/普通/低）
  - 支持耗时设置
  - 支持任务描述
- 📋 **任务管理** - 按天分类显示
  - 更新任务状态（待办→进行中→完成）
  - 删除任务
- 📊 **进度跟踪** - 记录学习成果

---

## 版本 2: 完整版

**文件**: `streamlit_app_updated.py`

**特点**:
- 需要 DeepSeek API
- 需要 LangGraph 等依赖
- 更多高级功能（AI生成计划等）

### 运行步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置API密钥
export DEEPSEEK_API_KEY="你的API密钥"

# 3. 运行应用
streamlit run streamlit_app_updated.py
```

---

## 📱 使用示例

### 第一步：注册账户

1. 打开应用
2. 点击「✏️ 注册」标签
3. 输入用户名（≥3字符）、邮箱、密码（≥6字符）
4. 点击「✅ 注册」

### 第二步：登录

1. 点击「📝 登录」标签
2. 输入账号密码
3. 点击「🔓 登录」

### 第三步：创建计划

1. 左侧菜单选择「✨ 学习计划生成」
2. 填写计划信息：
   - 计划名称（如：Python基础30天）
   - 开始日期
   - 预计天数
   - 计划描述
3. 点击「✅ 创建计划」
4. 从列表中「📌 选择」你的计划

### 第四步：布置任务

1. 左侧菜单选择「📌 布置任务"
2. 添加任务：
   - 第几天（Day 1, Day 2...）
   - 任务名称（如：学习Python字典）
   - 预计耗时（0.5-8小时）
   - 优先级（高/普通/低）
   - 任务描述
3. 点击「➕ 添加任务」

### 第五步：查看任务

1. 左侧菜单选择「📋 当前学习计划"
2. 按Day查看所有任务
3. 可以：
   - 更新任务状态
   - 删除任务

### 第六步：记录进度

1. 左侧菜单选择「📈 学习进度反馈"
2. 填写学习成果：
   - 记录日期
   - 完成度百分比
   - 已完成任务
   - 学习备注
3. 点击「📤 记录进度」

---

## 📊 数据存储

应用使用 SQLite 本地数据库存储数据：

```
study_assistant.db  ← 所有数据都在这里
```

包含以下数据表：
- `users` - 用户账户
- `plans` - 学习计划
- `tasks` - 学习任务
- `progress` - 学习进度

---

## 🔧 故障排除

### 问题：无法访问 localhost:8501

**解决**:
```bash
# 重启应用
streamlit run streamlit_app_simple_standalone.py --logger.level=debug
```

### 问题：ModuleNotFoundError

**解决**:
```bash
# 重新安装依赖
pip install --upgrade streamlit
```

### 问题：数据库错误

**解决**:
```bash
# 删除旧数据库，重新初始化
rm study_assistant.db
# 重启应用
streamlit run streamlit_app_simple_standalone.py
```

---

## 💡 提示

- 首次使用需要注册账户
- 每个用户可以创建多个计划
- 每个计划可以添加多个任务
- 任务支持按优先级自动排序
- 所有数据本地存储，不上传云端

---

## 📝 文件说明

| 文件 | 说明 |
|------|------|
| `streamlit_app_simple_standalone.py` | ⭐ 独立版本（推荐） |
| `streamlit_app_updated.py` | 完整版本（需要API） |
| `streamlit_app.py` | 备份版本 |

---

## 🎯 后续功能计划

- [ ] 云同步功能
- [ ] 手机版本
- [ ] AI智能建议
- [ ] 数据导出
- [ ] 团队协作

---

**有问题？**在 GitHub Issues 中提出！🙋
