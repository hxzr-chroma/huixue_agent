# ✨ API Key 配置完成 - 部署指南

## ✅ 当前状态

- ✅ **本地应用已启动**: http://localhost:8502
- ✅ **API Key 已配置**: `.streamlit/secrets.toml`
- ✅ **秘钥文件受保护**: 已在 `.gitignore` 中

## 🎯 后续步骤

### Step 1️⃣：本地测试（现在进行）

1. 打开浏览器访问 http://localhost:8502
2. 测试以下功能：
   - ✅ 注册新用户
   - ✅ 用刚创建的账户登录
   - ✅ 生成学习计划
   - ✅ 记录学习进度

### Step 2️⃣：部署到 Streamlit Cloud

#### 2.1 确保不提交秘钥文件

```bash
# 验证 secrets.toml 不在 git 追踪中
git status
# 应该看到：working tree clean（秘钥文件已被 .gitignore 忽略）
```

#### 2.2 访问 Streamlit Cloud

1. 打开 https://share.streamlit.io
2. 用 GitHub 账号登录
3. 点击「New app」

#### 2.3 配置应用

在弹窗中选择：
- **Repository**: `hxzr-chroma/huixue_agent`
- **Branch**: `main`
- **Main file path**: `streamlit_app_simple.py`

点击「Deploy」开始自动部署

#### 2.4 配置 API Key（⚠️ 关键步骤）

部署完成后：

1. 打开你的应用 URL
2. 点击右上角 **⋮** (三点菜单)
3. 选择 **Settings**
4. 点击 **Secrets** 标签
5. 粘贴以下内容：

```toml
DEEPSEEK_API_KEY = "sk-d94926f2b2fa4ec3a6e1e8942c20c531"
```

6. 点击 **Save** → 应用自动重启

✨ **完成！** 应用现在在线了

## 🔐 重要提醒

**永远不要：**
```bash
git add .streamlit/secrets.toml
git push  # ❌ 这会暴露你的 API Key！
```

**秘钥文件保护检查清单：**
- ✅ `.streamlit/.gitignore` 包含 `secrets.toml`
- ✅ 本地有 `.streamlit/secrets.toml`（不提交）
- ✅ GitHub 上没有秘钥文件
- ✅ Streamlit Cloud 的 Secrets 配置中有秘钥

## 📱 URL 汇总

| 环境 | URL | 用途 |
|------|-----|------|
| **本地测试** | http://localhost:8502 | 开发和测试 |
| **Streamlit Cloud** | https://huixue-agent-xxxxx.streamlit.app | 公开应用 |

## 🎯 验收标准

部署成功时，应该能够：

- [ ] 访问应用 URL
- [ ] 看到登录/注册页面
- [ ] 创建新用户账户
- [ ] 用新账户登录
- [ ] 生成学习计划（调用 DeepSeek API）
- [ ] 记录学习进度
- [ ] 重新打开页面，数据仍在

## 📞 故障排查

### 问题 1️⃣：API Key 仍未设置警告

**解决**：
- 本地开发：确保 `.streamlit/secrets.toml` 已创建并包含 API Key
- Streamlit Cloud：确保在 Settings → Secrets 中正确配置

### 问题 2️⃣：应用无法连接 DeepSeek API

**检查**：
1. API Key 是否正确？
2. 网络是否正常？
3. API 配额是否用尽？

### 问题 3️⃣：登录后没有反应

**检查**：
1. SQLite 数据库权限
2. 浏览器控制台错误（F12）
3. 应用日志（Streamlit Cloud 中的 Logs 标签）

---

**准备好了吗？开始测试吧！** 🚀

访问 http://localhost:8502 来测试你的应用
