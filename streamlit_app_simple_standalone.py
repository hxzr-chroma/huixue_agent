"""
AI 学习助手 - Streamlit独立版本
纯Streamlit实现，无需后端依赖
可直接运行: streamlit run streamlit_app_simple_standalone.py
"""

import streamlit as st
import os
from datetime import date
import json
import sqlite3
import hashlib
from collections import defaultdict

# ============================================================================
# 页面配置
# ============================================================================

st.set_page_config(
    page_title="AI 学习助手",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "study_assistant.db"

NAV_ITEMS: list[tuple[str, str]] = [
    ("🏠 首页总览", "首页总览"),
    ("✨ 学习计划生成", "学习计划生成"),
    ("📋 当前学习计划", "当前学习计划"),
    ("📌 布置任务", "布置任务"),
    ("📈 学习进度反馈", "学习进度反馈"),
]

# ============================================================================
# 本地数据库操作
# ============================================================================

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, 
                  password TEXT NOT NULL, email TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 计划表
    c.execute('''CREATE TABLE IF NOT EXISTS plans
                 (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, plan_name TEXT NOT NULL,
                  description TEXT, start_date TEXT, status TEXT DEFAULT 'active',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # 任务表
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, plan_id INTEGER NOT NULL, task_name TEXT NOT NULL,
                  task_description TEXT, day INTEGER DEFAULT 1, estimated_hours REAL DEFAULT 2.0,
                  status TEXT DEFAULT 'pending', priority TEXT DEFAULT 'normal',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(plan_id) REFERENCES plans(id))''')
    
    # 进度表
    c.execute('''CREATE TABLE IF NOT EXISTS progress
                 (id INTEGER PRIMARY KEY, plan_id INTEGER NOT NULL, study_date TEXT NOT NULL,
                  completion_ratio INTEGER, completed_tasks TEXT, note TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(plan_id) REFERENCES plans(id))''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, email: str, password: str) -> dict:
    """注册用户"""
    if len(username) < 3:
        return {"error": "用户名至少3个字符"}
    if len(password) < 6:
        return {"error": "密码至少6个字符"}
    
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, hash_password(password)))
        conn.commit()
        return {"success": True, "message": "注册成功"}
    except sqlite3.IntegrityError:
        return {"error": "用户名已存在"}
    finally:
        conn.close()

def verify_user(username: str, password: str) -> dict:
    """验证用户"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[1] == hash_password(password):
        return {"success": True, "user_id": result[0]}
    return {"success": False, "error": "用户名或密码错误"}

# ============================================================================
# 计划和任务管理
# ============================================================================

def create_plan(user_id: int, plan_name: str, description: str, start_date: str) -> bool:
    """创建计划"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO plans (user_id, plan_name, description, start_date) VALUES (?, ?, ?, ?)",
                  (user_id, plan_name, description, start_date))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def get_user_plans(user_id: int) -> list:
    """获取用户的所有计划"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, plan_name, description, start_date, status FROM plans WHERE user_id=? ORDER BY id DESC", (user_id,))
    plans = c.fetchall()
    conn.close()
    return plans

def add_task(plan_id: int, task_name: str, task_description: str, day: int, estimated_hours: float, priority: str) -> bool:
    """添加任务"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO tasks (plan_id, task_name, task_description, day, estimated_hours, priority)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                  (plan_id, task_name, task_description, day, estimated_hours, priority))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def get_tasks(plan_id: int) -> list:
    """获取计划的所有任务"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, task_name, task_description, day, estimated_hours, status, priority FROM tasks WHERE plan_id=? ORDER BY day ASC, priority DESC",
              (plan_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def update_task_status(task_id: int, status: str) -> bool:
    """更新任务状态"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def delete_task(task_id: int) -> bool:
    """删除任务"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

# ============================================================================
# 会话状态初始化
# ============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "current_plan_id" not in st.session_state:
    st.session_state.current_plan_id = None

# ============================================================================
# UI 函数
# ============================================================================

def inject_styles():
    """注入CSS样式"""
    st.markdown(
        """
        <style>
            .main .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
                max-width: 920px;
            }
            .stApp {
                background: #f6f7f9;
            }
            [data-testid="stSidebar"] {
                background: #ffffff;
                border-right: 1px solid #e8eaed;
            }
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .page-header {
                display: flex;
                align-items: flex-start;
                gap: 0.75rem;
                margin-bottom: 1.25rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #e8eaed;
            }
            .page-icon {
                font-size: 2rem;
            }
            .page-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #1a1a1a;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def page_header(title: str, subtitle: str = "", icon: str = "✨"):
    """页面标题"""
    st.markdown(f"""
    <div class="page-header">
        <span class="page-icon">{icon}</span>
        <div>
            <h1 class="page-title">{title}</h1>
            <p style="color: #666; margin: 0.5rem 0 0 0;">{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_auth_page():
    """显示登录/注册页面"""
    col1, col2, col3 = st.columns([1, 2.5, 1])
    
    with col2:
        st.markdown("# 🎓 AI 学习助手")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📝 登录", "✏️ 注册"])
        
        with tab1:
            st.subheader("用户登录")
            username = st.text_input("用户名", key="login_username")
            password = st.text_input("密码", type="password", key="login_password")
            
            if st.button("🔓 登录", use_container_width=True, key="login_btn"):
                if username and password:
                    result = verify_user(username, password)
                    if result["success"]:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_id = result["user_id"]
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error(result["error"])
                else:
                    st.warning("请输入用户名和密码")
        
        with tab2:
            st.subheader("用户注册")
            reg_username = st.text_input("用户名 (至少3个字符)", key="reg_username")
            reg_email = st.text_input("邮箱", key="reg_email")
            reg_password = st.text_input("密码 (至少6个字符)", type="password", key="reg_password")
            reg_password_confirm = st.text_input("确认密码", type="password", key="reg_password_confirm")
            
            if st.button("✅ 注册", use_container_width=True, key="register_btn"):
                if reg_password != reg_password_confirm:
                    st.error("两次密码不一致")
                else:
                    result = register_user(reg_username, reg_email, reg_password)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("注册成功！请登录")

# ============================================================================
# 页面渲染函数
# ============================================================================

def render_home():
    """首页"""
    page_header("AI 学习助手", "制定学习计划 → 布置具体任务 → 记录学习进度", "📘")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📚 快速开始")
        st.markdown("""
        1. **创建计划** - 在「✨ 学习计划生成」创建新计划
        2. **布置任务** - 在「📌 布置任务」添加具体的学习任务
        3. **记录进度** - 在「📈 学习进度反馈」记录学习成果
        """)
    
    with col2:
        st.markdown("### 💡 功能说明")
        st.markdown("""
        - ✨ **灵活计划** - 自由制定学习计划
        - 📌 **任务管理** - 优先级、耗时、状态追踪
        - 📊 **进度跟踪** - 完成度记录和备注
        - 🎯 **支持多任务** - 同时管理多个任务
        """)

def render_create_plan():
    """创建计划页面"""
    page_header("学习计划生成", "创建一个新的学习计划", "✨")
    
    user_id = st.session_state.user_id
    
    col1, col2 = st.columns(2)
    with col1:
        plan_name = st.text_input("📅 计划名称", placeholder="例：Python基础30天速成")
        start_date = st.date_input("📌 开始日期", value=date.today())
    
    with col2:
        estimated_days = st.number_input("⏱️ 预计天数", min_value=1, max_value=365, value=14)
        description = st.text_area("📝 计划描述", placeholder="简要描述你的学习目标和内容", height=80)
    
    if st.button("✅ 创建计划", type="primary", use_container_width=True):
        if not plan_name.strip():
            st.error("请输入计划名称")
        else:
            success = create_plan(user_id, plan_name, description, start_date.isoformat())
            if success:
                st.success(f"✅ 计划「{plan_name}」创建成功！")
                st.rerun()
            else:
                st.error("创建失败，请重试")
    
    st.divider()
    st.subheader("📋 我的计划")
    
    plans = get_user_plans(user_id)
    if not plans:
        st.info("暂无计划，创建一个吧！")
    else:
        for plan_id, plan_name, description, start_date, status in plans:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{plan_name}**")
                    st.caption(f"📅 {start_date} | {description[:50]}...")
                with col2:
                    st.caption(f"状态: {status}")
                with col3:
                    if st.button("📌 选择", key=f"select_{plan_id}", use_container_width=True):
                        st.session_state.current_plan_id = plan_id
                        st.rerun()

def render_current_plan():
    """当前计划页面"""
    page_header("当前学习计划", "查看和管理你的学习任务", "📋")
    
    if not st.session_state.current_plan_id:
        st.info("请先在「✨ 学习计划生成」中选择或创建一个计划")
        return
    
    plan_id = st.session_state.current_plan_id
    tasks = get_tasks(plan_id)
    
    st.subheader("✅ 已布置的任务")
    
    if not tasks:
        st.info("暂无任务，去「📌 布置任务」添加吧")
    else:
        # 按Day分组
        tasks_by_day = defaultdict(list)
        for task in tasks:
            tasks_by_day[task[3]].append(task)
        
        for day in sorted(tasks_by_day.keys()):
            with st.expander(f"📅 Day {day} ({len(tasks_by_day[day])}个任务)", expanded=True):
                for task_id, task_name, description, _, estimated_hours, status, priority in tasks_by_day[day]:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        status_emoji = "✅" if status == "completed" else "⏳" if status == "in_progress" else "📌"
                        priority_emoji = "🔴" if priority == "high" else "🟡" if priority == "normal" else "🟢"
                        st.markdown(f"{status_emoji} {priority_emoji} **{task_name}** (~{estimated_hours}h)")
                        if description:
                            st.caption(description)
                    
                    with col2:
                        new_status = st.selectbox("状态", ["pending", "in_progress", "completed"],
                                                index=["pending", "in_progress", "completed"].index(status),
                                                key=f"status_{task_id}", label_visibility="collapsed")
                        if new_status != status:
                            update_task_status(task_id, new_status)
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️", key=f"del_{task_id}", use_container_width=True):
                            delete_task(task_id)
                            st.rerun()

def render_add_tasks():
    """布置任务页面"""
    page_header("布置任务", "为学习计划添加具体任务", "📌")
    
    if not st.session_state.current_plan_id:
        st.info("请先在「✨ 学习计划生成」中选择或创建一个计划")
        return
    
    plan_id = st.session_state.current_plan_id
    
    st.markdown("### 📌 快速添加任务")
    
    col1, col2 = st.columns(2)
    with col1:
        task_day = st.number_input("📅 第几天", min_value=1, max_value=365, value=1)
        task_name = st.text_input("📌 任务名称", placeholder="例：学习Python字典")
    
    with col2:
        estimated_hours = st.number_input("⏱️ 预计耗时 (小时)", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
        priority = st.selectbox("🎯 优先级", ["high", "normal", "low"],
                              format_func=lambda x: {"high": "🔴 高", "normal": "🟡 普通", "low": "🟢 低"}[x])
    
    task_description = st.text_area("📝 任务描述", placeholder="详细描述任务内容")
    
    if st.button("➕ 添加任务", type="primary", use_container_width=True):
        if not task_name.strip():
            st.error("请输入任务名称")
        else:
            success = add_task(plan_id, task_name, task_description, task_day, estimated_hours, priority)
            if success:
                st.success(f"✅ 任务已添加到 Day {task_day}！")
                st.rerun()
            else:
                st.error("添加失败")
    
    st.divider()
    st.subheader("📋 任务预览")
    
    tasks = get_tasks(plan_id)
    if not tasks:
        st.info("暂无任务")
    else:
        tasks_by_day = defaultdict(list)
        for task in tasks:
            tasks_by_day[task[3]].append(task)
        
        for day in sorted(tasks_by_day.keys()):
            st.markdown(f"**Day {day}** ({len(tasks_by_day[day])}个任务)")
            for _, task_name, _, _, estimated_hours, status, priority in tasks_by_day[day]:
                status_icon = "✅" if status == "completed" else "⏳" if status == "in_progress" else "📌"
                priority_icon = "🔴" if priority == "high" else "🟡" if priority == "normal" else "🟢"
                st.caption(f"{status_icon} {priority_icon} {task_name} (~{estimated_hours}h)")

def render_progress():
    """进度反馈页面"""
    page_header("学习进度反馈", "记录你的学习成果", "📈")
    
    col1, col2 = st.columns([1.1, 1])
    with col1:
        record_date = st.date_input("📅 记录日期", value=date.today())
        completion_ratio = st.slider("✅ 完成度 (%)", 0, 100, 60)
        completed_tasks = st.text_area("✔️ 已完成的任务", placeholder="今天学了什么？")
    
    with col2:
        note = st.text_area("💭 备注", placeholder="学习心得、遇到的困难等", height=120)
    
    if st.button("📤 记录进度", type="primary", use_container_width=True):
        st.success("📝 进度已记录！")
        st.info(f"📅 {record_date.isoformat()} - 完成度: {completion_ratio}%")

# ============================================================================
# 主程序
# ============================================================================

def main():
    inject_styles()
    
    # 检查登录状态
    if not st.session_state.logged_in:
        show_auth_page()
        return
    
    # 用户已登录
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        if st.button("👤 退出"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.rerun()
    
    st.divider()
    
    # 侧边栏导航
    st.sidebar.markdown("### 📌 菜单")
    labels = [pair[0] for pair in NAV_ITEMS]
    picked = st.sidebar.radio("页面", labels, label_visibility="collapsed")
    page = dict(NAV_ITEMS)[picked]
    
    st.sidebar.divider()
    st.sidebar.markdown(f"**用户**: {st.session_state.username}")
    
    if st.session_state.current_plan_id:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**当前计划**: #{st.session_state.current_plan_id}")
    
    # 页面路由
    if page == "首页总览":
        render_home()
    elif page == "学习计划生成":
        render_create_plan()
    elif page == "当前学习计划":
        render_current_plan()
    elif page == "布置任务":
        render_add_tasks()
    elif page == "学习进度反馈":
        render_progress()

if __name__ == "__main__":
    main()
