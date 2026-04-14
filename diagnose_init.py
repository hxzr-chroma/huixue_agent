#!/usr/bin/env python
import os
from dotenv import load_dotenv

print("=== 环境变量加载诊断 ===")

# 加载.env文件
load_dotenv()

# 检查所有环境变量
print("环境变量列表:")
for key in ["DEEPSEEK_API_KEY", "API_BASE_URL", "DATABASE_URL", "HTTPX_TIMEOUT", "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    value = os.getenv(key, "未设置")
    if key.endswith("_KEY") and value != "未设置":
        print(f"  {key}: {value[:10]}...{value[-5:]}")
    else:
        print(f"  {key}: {value}")

print()
print("=== 测试OpenAI初始化 ===")

from openai import OpenAI

api_key = os.getenv("DEEPSEEK_API_KEY", "")

if not api_key:
    print("✗ DEEPSEEK_API_KEY未设置")
    exit(1)

print(f"API密钥: {api_key[:10]}...{api_key[-5:]}")

# 直接初始化，捕获详细错误
try:
    print("尝试初始化OpenAI Client...")
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    print("✓ 初始化成功!")
except TypeError as e:
    print(f"✗ TypeError: {str(e)}")
    print()
    print("分析错误原因...")
    
    # 尝试查看是否有环境变量注入
    import sys
    print(f"sys.argv: {sys.argv}")
    
    # 检查是否有代理环境变量
    for proxy_var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
        if proxy_var in os.environ:
            print(f"发现代理环境变量: {proxy_var}={os.environ[proxy_var]}")
    
except Exception as e:
    print(f"✗ {type(e).__name__}: {str(e)}")
