"""
System Integration Test - Huixue Agent 2.0

Tests:
1. Database initialization
2. User authentication (register/login)
3. Plan management (CRUD)
4. Task management
5. DeepSeek API integration
"""

import os
import sys
import json
import requests
from datetime import datetime

# Setup environment
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-d94926f2b2fa4ec3a6e1e8942c20c531")

from storage.db import init_db, get_connection
from services.study_planner_service import StudyPlannerService

API_BASE_URL = "http://localhost:8000"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_print(message: str, status: str = "INFO"):
    colors = {
        "PASS": Colors.GREEN,
        "FAIL": Colors.RED,
        "INFO": Colors.BLUE,
        "WARN": Colors.YELLOW,
    }
    color = colors.get(status, Colors.BLUE)
    print(f"{color}[{status}]{Colors.END} {message}")


def test_db_init():
    """Test 1: Database Initialization"""
    test_print("=" * 60, "INFO")
    test_print("TEST 1: Database Initialization", "INFO")
    test_print("=" * 60, "INFO")
    
    try:
        init_db()
        test_print("✓ Database initialized successfully", "PASS")
        
        # Check tables
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            test_print(f"✓ Tables created: {', '.join(tables)}", "PASS")
        return True
    except Exception as e:
        test_print(f"✗ Database init failed: {e}", "FAIL")
        return False


def test_auth():
    """Test 2: User Authentication"""
    test_print("\n" + "=" * 60, "INFO")
    test_print("TEST 2: User Authentication (Register & Login)", "INFO")
    test_print("=" * 60, "INFO")
    
    test_user = {
        "username": "testuser_" + datetime.now().strftime("%H%M%S"),
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123"
    }
    
    try:
        # Register
        test_print("→ Testing registration...", "INFO")
        resp = requests.post(f"{API_BASE_URL}/api/auth/register", json=test_user)
        if resp.status_code == 200:
            reg_result = resp.json()
            token = reg_result.get("access_token")
            user_id = reg_result.get("user_id")
            test_print(f"✓ Registration successful (User ID: {user_id})", "PASS")
        else:
            test_print(f"✗ Registration failed: {resp.text}", "FAIL")
            return False, None, None
        
        # Login
        test_print("→ Testing login...", "INFO")
        resp = requests.post(f"{API_BASE_URL}/api/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        if resp.status_code == 200:
            login_result = resp.json()
            test_print(f"✓ Login successful", "PASS")
            return True, token, user_id
        else:
            test_print(f"✗ Login failed: {resp.text}", "FAIL")
            return False, None, None
    except Exception as e:
        test_print(f"✗ Auth test failed: {e}", "FAIL")
        return False, None, None


def test_plans(token: str):
    """Test 3: Plan Management"""
    test_print("\n" + "=" * 60, "INFO")
    test_print("TEST 3: Plan Management (CRUD)", "INFO")
    test_print("=" * 60, "INFO")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    plan_id = None
    
    try:
        # Create
        test_print("→ Creating plan...", "INFO")
        plan_data = {
            "name": f"Test Plan {datetime.now().strftime('%H:%M:%S')}",
            "raw_input": "Learn Python basics in 7 days, 2 hours per day. Focus on fundamentals and best practices."
        }
        resp = requests.post(f"{API_BASE_URL}/api/plans", json=plan_data, headers=headers)
        if resp.status_code == 200:
            result = resp.json()
            plan_id = result.get("id")
            test_print(f"✓ Plan created (Plan ID: {plan_id})", "PASS")
        else:
            test_print(f"✗ Plan creation failed: {resp.text}", "FAIL")
            return False, None
        
        # Read
        test_print("→ Fetching plan...", "INFO")
        resp = requests.get(f"{API_BASE_URL}/api/plans/{plan_id}", headers=headers)
        if resp.status_code == 200:
            plan = resp.json()
            test_print(f"✓ Plan fetched: {plan.get('name')}", "PASS")
        else:
            test_print(f"✗ Plan fetch failed: {resp.text}", "FAIL")
            return False, None
        
        # Update
        test_print("→ Updating plan...", "INFO")
        resp = requests.put(f"{API_BASE_URL}/api/plans/{plan_id}", 
            json={"name": "Updated Plan Name"}, headers=headers)
        if resp.status_code == 200:
            test_print(f"✓ Plan updated", "PASS")
        else:
            test_print(f"✗ Plan update failed: {resp.text}", "FAIL")
            return False, None
        
        # List
        test_print("→ Listing plans...", "INFO")
        resp = requests.get(f"{API_BASE_URL}/api/plans", headers=headers)
        if resp.status_code == 200:
            plans = resp.json()
            test_print(f"✓ Plans listed: {len(plans)} plan(s)", "PASS")
        else:
            test_print(f"✗ Plans listing failed: {resp.text}", "FAIL")
            return False, None
        
        return True, plan_id
    except Exception as e:
        test_print(f"✗ Plan test failed: {e}", "FAIL")
        return False, None


def test_tasks(token: str, plan_id: int):
    """Test 4: Task Management"""
    test_print("\n" + "=" * 60, "INFO")
    test_print("TEST 4: Task Management", "INFO")
    test_print("=" * 60, "INFO")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        # Create task
        test_print("→ Creating task...", "INFO")
        task_data = {
            "title": "Learn Python Variables",
            "category": "基础理论",
            "priority": "high",
            "deadline": "2025-04-20"
        }
        resp = requests.post(f"{API_BASE_URL}/api/plans/{plan_id}/tasks", 
            json=task_data, headers=headers)
        if resp.status_code == 200:
            result = resp.json()
            task_id = result.get("id")
            test_print(f"✓ Task created (Task ID: {task_id})", "PASS")
        else:
            test_print(f"✗ Task creation failed: {resp.text}", "FAIL")
            return False
        
        # Verify task in plan
        resp = requests.get(f"{API_BASE_URL}/api/plans/{plan_id}", headers=headers)
        if resp.status_code == 200:
            plan = resp.json()
            tasks = plan.get("tasks", [])
            if tasks:
                test_print(f"✓ Task appears in plan (Total: {len(tasks)} task(s))", "PASS")
                # Display task categorization
                for task in tasks:
                    test_print(f"  - {task['title']} [{task.get('category')}] (Priority: {task.get('priority')})", "INFO")
                return True
            else:
                test_print(f"✗ Task not found in plan", "FAIL")
                return False
        else:
            test_print(f"✗ Could not verify task", "FAIL")
            return False
    except Exception as e:
        test_print(f"✗ Task test failed: {e}", "FAIL")
        return False


def test_deepseek():
    """Test 5: DeepSeek API Integration"""
    test_print("\n" + "=" * 60, "INFO")
    test_print("TEST 5: DeepSeek API Integration", "INFO")
    test_print("=" * 60, "INFO")
    
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            test_print("⚠ DeepSeek API key not configured", "WARN")
            return False
        
        service = StudyPlannerService(api_key=api_key)
        
        test_print("→ Testing plan generation with DeepSeek...", "INFO")
        user_input = "我想用3天时间复习计算机网络中的TCP/IP协议，每天4小时"
        
        plan, rag = service.create_plan(user_input)
        
        if plan:
            test_print(f"✓ Plan generated successfully", "PASS")
            test_print(f"  Plan ID: {plan.get('id')}", "INFO")
            test_print(f"  Content preview: {str(plan.get('plan_data', ''))[:100]}...", "INFO")
            
            if rag:
                test_print(f"✓ RAG retrieval successful", "PASS")
                test_print(f"  Content preview: {rag[:80]}...", "INFO")
            else:
                test_print(f"⚠ No RAG content retrieved", "WARN")
            
            return True
        else:
            test_print(f"✗ Plan generation failed", "FAIL")
            return False
    except Exception as e:
        test_print(f"✗ DeepSeek test failed: {e}", "FAIL")
        return False


def check_backend():
    """Check if backend is running"""
    test_print("Checking backend connection...", "INFO")
    try:
        resp = requests.get(f"{API_BASE_URL}/docs", timeout=2)
        test_print("✓ Backend is running", "PASS")
        return True
    except:
        test_print("✗ Backend is not running. Please start: python -m uvicorn backend_server:app --port 8000", "FAIL")
        return False


def main():
    """Run all tests"""
    test_print("\n╔════════════════════════════════════════════════════════════╗", "BLUE")
    test_print("║     Huixue Agent 2.0 - Integration Test Suite           ║", "BLUE")
    test_print("╚════════════════════════════════════════════════════════════╝", "BLUE")
    
    results = {}
    
    # Check backend first
    if not check_backend():
        return
    
    test_print("\n", "INFO")
    
    # Test 1: Database
    results["Database"] = test_db_init()
    
    # Test 2: Auth
    auth_result, token, user_id = test_auth()
    results["Authentication"] = auth_result
    
    if not token:
        test_print("\n✗ Authentication failed, skipping further tests", "FAIL")
        return
    
    # Test 3: Plans
    plans_result, plan_id = test_plans(token)
    results["Plan Management"] = plans_result
    
    if not plan_id:
        test_print("\n⚠ Plan creation failed, skipping task tests", "WARN")
    else:
        # Test 4: Tasks
        results["Task Management"] = test_tasks(token, plan_id)
    
    # Test 5: DeepSeek
    results["DeepSeek API"] = test_deepseek()
    
    # Summary
    test_print("\n" + "=" * 60, "INFO")
    test_print("TEST SUMMARY", "INFO")
    test_print("=" * 60, "INFO")
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        test_print(f"{icon} {test_name}: {status}", status)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    percentage = (passed / total * 100) if total > 0 else 0
    
    test_print(f"\nTotal: {passed}/{total} ({percentage:.0f}%)", "INFO")
    test_print("=" * 60, "INFO")


if __name__ == "__main__":
    main()
