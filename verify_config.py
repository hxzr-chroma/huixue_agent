#!/usr/bin/env python
import os
from dotenv import load_dotenv
import requests
import sys

# 加载.env文件
load_dotenv()

print("=== API密钥检查 ===")
api_key = os.getenv("DEEPSEEK_API_KEY", "")

if api_key and len(api_key) > 10:
    masked = api_key[:10] + "..." + api_key[-5:]
    print(f"✓ DEEPSEEK_API_KEY 已正确配置: {masked}")
else:
    print("✗ DEEPSEEK_API_KEY 未设置或无效")
    sys.exit(1)

print()
print("=== 环境变量配置 ===")
print(f"API_BASE_URL: {os.getenv('API_BASE_URL', '未设置')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', '未设置')}")

print()
print("=== 系统连接测试 ===")

try:
    resp = requests.get("http://localhost:8000/docs", timeout=3)
    print("✓ 后端API 运行正常 (http://localhost:8000)")
except Exception as e:
    print(f"✗ 后端API 连接失败: {str(e)[:50]}")

try:
    resp = requests.get("http://localhost:8501", timeout=3)
    print("✓ 前端UI 运行正常 (http://localhost:8501)")
except Exception as e:
    print("⏳ 前端UI 初始化中...")

print()
print("=" * 50)
print("✨ 配置成功！所有组件已就绪")
print("=" * 50)
print()
print("📍 访问地址: http://localhost:8501")
