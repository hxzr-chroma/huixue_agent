# Railway 后端项目配置指南

> 这个配置文件用于 **soothing-beauty (后端项目)**，前端项目自动使用 railway.json

## 后端项目启动命令（soothing-beauty）

在 Railway 的 soothing-beauty 项目中，设置以下配置：

### 在 Railway UI 中手动设置：

**步骤：**
1. 打开 soothing-beauty 项目
2. 点击 **Settings** 或 **Deploy** 标签
3. 找到 **Custom Start Command**
4. 填入：
   ```
   python backend_server.py
   ```
5. 点 **Save**
6. 点 **Redeploy** 或 **Deploy Latest**

### 预期日志输出：

```
Starting Uvicorn server on http://0.0.0.0:8000
Application startup complete
```

## 前端项目配置（keen-adventure）

前端项目自动从 `railway.json` 读取配置，使用 Streamlit 启动：

```
startCommand: streamlit run streamlit_app.py
Port: 8501
```

## 验证部署

✅ **后端** (soothing-beauty)
- URL: https://xxx-backend.railway.app (获取此 URL)
- Port: 8000 (内部)
- Status: Online

✅ **前端** (keen-adventure)  
- URL: https://xxx-frontend.railway.app
- Port: 8501 (内部)
- Status: Online

## 前端连接后端

在 keen-adventure 项目的 **Variables** 中设置：

| 变量名 | 值 |
|------|-----|
| API_BASE_URL | https://xxx-backend.railway.app |

然后重新部署前端。

## 如果前端无法连接后端

1. **检查后端是否在线** - 访问 https://xxx-backend.railway.app/api/auth/me
2. **检查 API_BASE_URL** - 确保没有多余的 `/` 
3. **检查网络日志** - 在前端浏览器的开发者工具查看请求

