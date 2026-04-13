"""
Huixue Agent 2.0 - Streamlit Frontend with Authentication & Multi-Plan Management
"""
from __future__ import annotations

import json
import os
from datetime import date

import streamlit as st
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

st.set_page_config(
    page_title="AI 学习助手",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# Session State Initialization
# ============================================================================

if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "current_plan_id" not in st.session_state:
    st.session_state.current_plan_id = None
if "plans" not in st.session_state:
    st.session_state.plans = []


# ============================================================================
# API Utilities
# ============================================================================

def api_call(method: str, endpoint: str, data=None, **kwargs):
    """Make API call with authentication"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, **kwargs)
        elif method.upper() == "POST":
            resp = requests.post(url, json=data, headers=headers, **kwargs)
        elif method.upper() == "PUT":
            resp = requests.put(url, json=data, headers=headers, **kwargs)
        elif method.upper() == "DELETE":
            resp = requests.delete(url, headers=headers, **kwargs)
        else:
            return None, "Invalid method"
        
        if resp.status_code in [200, 201]:
            return resp.json(), None
        else:
            try:
                err = resp.json().get("detail", resp.text)
            except:
                err = resp.text
            return None, err
    except Exception as e:
        return None, str(e)


# ============================================================================
# Auth Pages
# ============================================================================

def page_login():
    """Login page"""
    st.markdown("# 📘 学习助手·登录")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("用户名", key="login_username")
            password = st.text_input("密码", type="password", key="login_password")
            submitted = st.form_submit_button("🔓 登录", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("请输入用户名和密码")
                else:
                    result, err = api_call("POST", "/api/auth/login", {
                        "username": username,
                        "password": password
                    })
                    
                    if result:
                        st.session_state.token = result["access_token"]
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error(f"登录失败: {err}")
        
        st.divider()
        st.markdown(
            """
            <div style="text-align: center;">
                <p style="color: #666;">还没有账号？ <a href="?page=register">立即注册</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )


def page_register():
    """Register page"""
    st.markdown("# 📘 学习助手·注册")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("register_form"):
            username = st.text_input("用户名（3-50字符）", key="reg_username")
            email = st.text_input("邮箱", key="reg_email")
            password = st.text_input("密码（至少6位）", type="password", key="reg_password")
            password_confirm = st.text_input("确认密码", type="password", key="reg_password_confirm")
            submitted = st.form_submit_button("✅ 注册", use_container_width=True)
            
            if submitted:
                if not username or not email or not password or not password_confirm:
                    st.error("请填写所有字段")
                elif len(username) < 3:
                    st.error("用户名至少3个字符")
                elif len(password) < 6:
                    st.error("密码至少6个字符")
                elif password != password_confirm:
                    st.error("密码不一致")
                else:
                    result, err = api_call("POST", "/api/auth/register", {
                        "username": username,
                        "email": email,
                        "password": password,
                        "password_confirm": password_confirm
                    })
                    
                    if result:
                        st.session_state.token = result["access_token"]
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.success("注册成功，已自动登录！")
                        st.rerun()
                    else:
                        st.error(f"注册失败: {err}")
        
        st.divider()
        st.markdown(
            """
            <div style="text-align: center;">
                <p style="color: #666;">已有账号？ <a href="?page=login">登录</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================================
# Plan Management Pages
# ============================================================================

def page_plans_list():
    """List all plans"""
    st.markdown("# 📚 我的学习计划")
    
    # User info
    col1, col2 = st.columns([1, 10])
    with col1:
        st.markdown(f"👤")
    with col2:
        st.markdown(f"**{st.session_state.username}**")
    
    # Fetch plans
    plans, err = api_call("GET", "/api/plans")
    if err:
        st.error(f"获取计划失败: {err}")
        return
    
    st.session_state.plans = plans or []
    
    # Tabs for active and archived
    tab1, tab2 = st.tabs(["✨ 活跃计划", "📦 归档计划"])
    
    with tab1:
        active_plans = [p for p in st.session_state.plans if p.get("status") == "active"]
        if not active_plans:
            st.info("暂无活跃计划，创建一个开始学习吧")
        else:
            for plan in active_plans:
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.markdown(f"**{plan['name']}**")
                        st.caption(f"创建于 {plan['created_at'][:10]}")
                    with col2:
                        if st.button("📖 查看", key=f"view_{plan['id']}", use_container_width=True):
                            st.session_state.current_plan_id = plan['id']
                            st.session_state.current_page = "plan_detail"
                            st.rerun()
                    with col3:
                        if st.button("✏️ 编辑", key=f"edit_{plan['id']}", use_container_width=True):
                            st.session_state.current_plan_id = plan['id']
                            st.session_state.current_page = "plan_edit"
                            st.rerun()
                    with col4:
                        if st.button("🚀 激活", key=f"activate_{plan['id']}", use_container_width=True):
                            _, err = api_call("POST", f"/api/plans/{plan['id']}/activate", {})
                            if not err:
                                st.success("已激活")
                                st.rerun()
                            else:
                                st.error(f"激活失败: {err}")
    
    with tab2:
        archived_plans = [p for p in st.session_state.plans if p.get("status") != "active"]
        if not archived_plans:
            st.info("暂无归档计划")
        else:
            for plan in archived_plans:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**{plan['name']}**")
                        st.caption(f"创建于 {plan['created_at'][:10]}")
                    with col2:
                        if st.button("📖 查看", key=f"archive_view_{plan['id']}", use_container_width=True):
                            st.session_state.current_plan_id = plan['id']
                            st.session_state.current_page = "plan_detail"
                            st.rerun()
                    with col3:
                        if st.button("🗑️ 删除", key=f"delete_{plan['id']}", use_container_width=True):
                            _, err = api_call("DELETE", f"/api/plans/{plan['id']}", {})
                            if not err:
                                st.success("已删除")
                                st.rerun()
                            else:
                                st.error(f"删除失败: {err}")
    
    st.divider()
    if st.button("➕ 创建新计划", use_container_width=True):
        st.session_state.current_page = "create_plan"
        st.rerun()


def page_create_plan():
    """Create new plan"""
    st.markdown("# ✨ 创建学习计划")
    
    with st.form("create_plan_form"):
        name = st.text_input("计划名称", placeholder="例如：Python进阶学习")
        description = st.text_area("学习目标", placeholder="描述你的学习目标和具体要求")
        
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("计划天数", min_value=1, max_value=365, value=14)
        with col2:
            daily_hours = st.number_input("每天学习时长（小时）", min_value=0.5, max_value=24.0, value=2.0, step=0.5)
        
        submitted = st.form_submit_button("🚀 生成计划", use_container_width=True, type="primary")
    
    if submitted:
        if not name or not description:
            st.error("请填写计划名称和学习目标")
        else:
            input_text = f"{description}，计划{duration}天内完成，每天学习{daily_hours}小时"
            
            with st.spinner("正在生成计划..."):
                result, err = api_call("POST", "/api/plans", {
                    "name": name,
                    "raw_input": input_text,
                    "plan_start_date": None
                })
                
                if result:
                    st.session_state.current_plan_id = result["id"]
                    st.success("计划已创建！")
                    st.rerun()
                else:
                    st.error(f"创建失败: {err}")
    
    if st.button("← 返回计划列表"):
        st.session_state.current_page = "plans_list"
        st.rerun()


def page_plan_detail():
    """View plan details"""
    plan_id = st.session_state.current_plan_id
    if not plan_id:
        st.error("计划ID缺失")
        return
    
    plan, err = api_call("GET", f"/api/plans/{plan_id}")
    if err:
        st.error(f"获取计划失败: {err}")
        return
    
    st.markdown(f"# 📋 {plan['name']}")
    st.caption(f"创建于 {plan['created_at'][:10]}")
    
    tab1, tab2, tab3 = st.tabs(["📊 计划详情", "✅ 任务列表", "🎯 学习进度"])
    
    with tab1:
        st.json(plan.get("plan_data", {}))
    
    with tab2:
        st.markdown("### 任务分类")
        tasks = plan.get("tasks", [])
        
        if not tasks:
            st.info("暂无任务")
        else:
            # Group by category
            categories = {}
            for task in tasks:
                cat = task.get("category") or "无分类"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(task)
            
            for category, cat_tasks in categories.items():
                with st.expander(f"📂 {category} ({len(cat_tasks)}个任务)"):
                    for task in cat_tasks:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.markdown(f"**{task['title']}**")
                            if task.get("deadline"):
                                st.caption(f"截止: {task['deadline']}")
                        with col2:
                            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority"), "⚪")
                            st.markdown(f"{priority_emoji} {task.get('priority', 'N/A')}")
                        with col3:
                            st.markdown(f"**{task.get('status', 'pending')}**")
    
    with tab3:
        st.markdown("### 学习进度")
        st.info("（功能敬请期待）")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ 编辑", use_container_width=True):
            st.session_state.current_page = "plan_edit"
            st.rerun()
    with col2:
        if st.button("← 返回列表", use_container_width=True):
            st.session_state.current_page = "plans_list"
            st.rerun()


def page_plan_edit():
    """Edit plan"""
    plan_id = st.session_state.current_plan_id
    if not plan_id:
        st.error("计划ID缺失")
        return
    
    plan, err = api_call("GET", f"/api/plans/{plan_id}")
    if err:
        st.error(f"获取计划失败: {err}")
        return
    
    st.markdown(f"# ✏️ 编辑计划：{plan['name']}")
    
    with st.form("edit_plan_form"):
        name = st.text_input("计划名称", value=plan.get("name", ""))
        submitted = st.form_submit_button("💾 保存", use_container_width=True, type="primary")
    
    if submitted:
        _, err = api_call("PUT", f"/api/plans/{plan_id}", {"name": name})
        if not err:
            st.success("已保存")
            st.session_state.current_page = "plan_detail"
            st.rerun()
        else:
            st.error(f"保存失败: {err}")
    
    st.divider()
    st.markdown("### 添加任务")
    with st.form("add_task_form"):
        title = st.text_input("任务标题")
        category = st.selectbox("分类", ["基础理论", "实践练习", "项目应用", "总结复习"])
        priority = st.selectbox("优先级", ["low", "medium", "high"], format_func=lambda x: {"low": "低", "medium": "中", "high": "高"}[x])
        submitted = st.form_submit_button("➕ 添加任务", use_container_width=True)
    
    if submitted:
        if not title:
            st.error("请输入任务标题")
        else:
            _, err = api_call("POST", f"/api/plans/{plan_id}/tasks", {
                "title": title,
                "category": category,
                "priority": priority
            })
            if not err:
                st.success("任务已添加")
                st.rerun()
            else:
                st.error(f"添加失败: {err}")
    
    if st.button("← 返回"):
        st.session_state.current_page = "plan_detail"
        st.rerun()


# ============================================================================
# Main App
# ============================================================================

def inject_styles():
    """Inject CSS styles"""
    st.markdown("""
    <style>
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with user menu"""
    if not st.session_state.token:
        return
    
    with st.sidebar:
        st.markdown("### 📘 学习助手")
        st.divider()
        
        if st.button("📚 我的计划", use_container_width=True):
            st.session_state.current_page = "plans_list"
            st.rerun()
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 账户", use_container_width=True):
                st.session_state.current_page = "account"
                st.rerun()
        with col2:
            if st.button("🚪 登出", use_container_width=True):
                st.session_state.token = None
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.current_plan_id = None
                st.rerun()


def main():
    """Main app logic"""
    inject_styles()
    
    # Get page from query params
    page = st.query_params.get("page", ["login"])[0]
    if "current_page" in st.session_state:
        page = st.session_state.current_page
    
    # Auth pages
    if not st.session_state.token:
        if page == "register":
            page_register()
        else:
            page_login()
    else:
        # Protected pages
        render_sidebar()
        
        if page == "plans_list":
            page_plans_list()
        elif page == "create_plan":
            page_create_plan()
        elif page == "plan_detail":
            page_plan_detail()
        elif page == "plan_edit":
            page_plan_edit()
        else:
            page_plans_list()


if __name__ == "__main__":
    main()
