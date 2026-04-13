#!/usr/bin/env python
import sys
import inspect

print("=== Python环境诊断 ===")
print(f"Python版本: {sys.version}")
print()

try:
    import openai
    print(f"OpenAI库版本: {openai.__version__}")
except ImportError:
    print("OpenAI库未安装")
    sys.exit(1)

print()
print("=== 测试OpenAI Client初始化 ===")

from openai import OpenAI

# 尝试查看Client支持的参数
sig = inspect.signature(OpenAI.__init__)
print("OpenAI.__init__ 参数列表:")
for param_name in list(sig.parameters.keys())[1:]:  # 跳过self
    param = sig.parameters[param_name]
    print(f"  - {param_name}")

print()
print("=== 尝试初始化 ===")

# 测试1：最小配置
print("测试1: 最小配置 (仅api_key)")
try:
    client = OpenAI(api_key="test-key-123")
    print("✓ 成功")
except Exception as e:
    print(f"✗ 失败: {type(e).__name__}: {str(e)[:100]}")

print()

# 测试2：带base_url
print("测试2: api_key + base_url")
try:
    client = OpenAI(api_key="test-key-123", base_url="https://api.deepseek.com")
    print("✓ 成功")
except Exception as e:
    print(f"✗ 失败: {type(e).__name__}: {str(e)[:100]}")

print()

# 测试3：带timeout (v1.0+)
print("测试3: api_key + base_url + timeout")
try:
    client = OpenAI(api_key="test-key-123", base_url="https://api.deepseek.com", timeout=60)
    print("✓ 成功")
except TypeError as e:
    if "timeout" in str(e):
        print(f"✗ timeout参数不支持: {str(e)[:100]}")
    else:
        print(f"✗ TypeError: {str(e)[:100]}")
except Exception as e:
    print(f"✗ {type(e).__name__}: {str(e)[:100]}")

print()

# 测试4：检查http_client参数
print("测试4: http_client参数")
try:
    from httpx import Timeout
    client = OpenAI(
        api_key="test-key-123",
        base_url="https://api.deepseek.com",
        timeout=Timeout(60.0)
    )
    print("✓ 使用Timeout对象成功")
except Exception as e:
    print(f"✗ 失败: {type(e).__name__}")
