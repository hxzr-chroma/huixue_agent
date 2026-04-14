# Railway 部署完成清单

## ✅ 已完成

- [x] 后端项目（soothing-beauty）Custom Start Command = `python backend_server.py`
- [x] railway.json 前端配置正确（Streamlit）

## 🚀 现在要执行的步骤

### 步骤 1：保存后端启动命令
- [ ] 在 soothing-beauty 项目 Settings 中
- [ ] 点右边的 **✓** 按钮保存 `python backend_server.py` 命令

### 步骤 2：重新部署后端
- [ ] 点 **Deployments** 标签
- [ ] 点 **Redeploy** 或 **Deploy Latest** 按钮
- [ ] 等待状态变为 **Online**（绿色）
- [ ] 注意显示的日志应该是：
  ```
  Starting Uvicorn server on http://0.0.0.0:8000
  Application startup complete
  ```

### 步骤 3：获取后端 URL
- [ ] 部署完成后，记下后端项目的 URL，格式如：
  ```
  https://xxx-backend.railway.app
  ```

### 步骤 4：配置前端连接后端
- [ ] 切换到 **keen-adventure** (前端)项目
- [ ] 点 **Variables** 标签
- [ ] 找 **API_BASE_URL** 变量
- [ ] 修改值为后端 URL（第 3 步获得的）
  ```
  API_BASE_URL = https://xxx-backend.railway.app
  ```
- [ ] 点 Save

### 步骤 5：重新部署前端
- [ ] 回到 keen-adventure 项目
- [ ] 点 **Deployments** 标签
- [ ] 点 **Redeploy**
- [ ] 等待状态变为 **Online**

### 步骤 6：验证部署
- [ ] 前端项目获得的 URL：https://xxx-frontend.railway.app
- [ ] 点开链接，应该看到登录页面
- [ ] 测试登录/注册功能
- [ ] 确认后端能正常响应

## 🆘 如果出现问题

### 后端始终显示 streamlit 日志
- 检查是否正确点了 ✓ 保存了命令
- 尝试再次编辑，完全删除，重新输入 `python backend_server.py`

### 前端无法连接后端
- 检查 API_BASE_URL 变量是否正确（不要多余的 `/`）
- 在浏览器开发者工具 (F12) 查看网络请求错误
- 确认后端项目状态是否为 Online

### 登录时显示 API 错误
- 检查后端服务器是否在运行
- 查看 soothing-beauty 项目的 Deploy Logs 找错误信息

## 📚 参考文档

- RAILWAY_SETUP_CN.md - 详细的部署指南
- RAILWAY_BACKEND_CONFIG.md - 后端配置说明
- GitHub: https://github.com/hxzr-chroma/huixue_agent

