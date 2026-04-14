"""
AI 学习助手 - Streamlit版本（本地化 - 无需后端分离）
直接部署在Streamlit Cloud
"""

import streamlit as st
import os
from datetime import date
import json
import sqlite3
import hashlib
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from services.study_planner_service import StudyPlannerService
from services.schedule import calendar_date_for_plan_day, parse_iso_date
from utils.goal_validation import (
    FIELD_LABELS_ZH,
    goal_missing_fields_for_submission,
    merge_goal_supplements,
    validate_parsed_goal,
)

# ============================================================================
# 常量配置
# ============================================================================

GOAL_CLARIFY_CREATE = "goal_clarify_create"
GOAL_CLARIFY_RECREATE = "goal_clarify_recreate"

# 任务分类常量
TASK_CATEGORIES = {
    "all": {"name": "全部任务", "icon": "📋"},
    "theory": {"name": "理论学习", "icon": "📚"},
    "practice": {"name": "实践练习", "icon": "💻"},
    "review": {"name": "复习巩固", "icon": "🔄"},
    "test": {"name": "测试评估", "icon": "🎯"},
    "project": {"name": "项目实战", "icon": "🚀"},
}

NAV_ITEMS: list[tuple[str, str]] = [
    ("🏠 首页总览", "首页总览"),
    ("✨ 学习计划生成", "学习计划生成"),
    ("📋 当前学习计划", "当前学习计划"),
    ("📌 布置任务", "布置任务"),
    ("📈 学习进度反馈", "学习进度反馈"),
    ("📝 学习检测", "学习检测"),
    ("🔄 动态调整", "动态调整"),
]

st.set_page_config(
    page_title="AI 学习助手",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DB_PATH = "study_assistant.db"

# ============================================================================
# 本地数据库操作
# ============================================================================

def init_user_db():
    """初始化用户表"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, 
                  password TEXT, email TEXT)''')
    
    # 初始化任务分类表
    c.execute('''CREATE TABLE IF NOT EXISTS task_categories
                 (id INTEGER PRIMARY KEY, plan_id TEXT, category_id TEXT, 
                  category_name TEXT, icon TEXT, color TEXT, description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 初始化任务表
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, plan_id TEXT, category_id TEXT,
                  task_name TEXT, task_description TEXT, day INTEGER,
                  estimated_hours REAL, status TEXT DEFAULT 'pending',
                  priority TEXT DEFAULT 'normal', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username: str, password: str) -> bool:
    """验证用户"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return result[0] == hash_password(password)
    return False

def register_user(username: str, email: str, password: str) -> dict:
    """注册用户"""
    if len(username) < 3:
        return {"error": "用户名至少3个字符"}
    if len(password) < 6:
        return {"error": "密码至少6个字符"}
    
    init_user_db()
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

# ============================================================================
# 任务分类管理函数
# ============================================================================

def get_all_tasks(plan_id: str) -> list:
    """获取计划的所有任务"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE plan_id=? ORDER BY day ASC, id ASC", (plan_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def add_task(plan_id: str, task_name: str, task_description: str, day: int,
             estimated_hours: float, priority: str = "normal") -> bool:
    """添加任务"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO tasks
                    (plan_id, category_id, task_name, task_description, day, estimated_hours, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (plan_id, "custom", task_name, task_description, day, estimated_hours, priority))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def delete_task(task_id: int) -> bool:
    """删除任务"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def update_task_status(task_id: int, status: str) -> bool:
    """更新任务状态"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def get_task_categories(plan_id: str) -> list:
    """获取计划的所有任务分类"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM task_categories WHERE plan_id=?", (plan_id,))
    categories = c.fetchall()
    conn.close()
    return categories

def create_task_category(plan_id: str, category_id: str, category_name: str, 
                        icon: str, color: str = "#3498db", description: str = "") -> bool:
    """创建任务分类"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO task_categories 
                    (plan_id, category_id, category_name, icon, color, description)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                  (plan_id, category_id, category_name, icon, color, description))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def get_tasks_by_category(plan_id: str, category_id: str) -> list:
    """获取某分类下的所有任务"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE plan_id=? AND category_id=?", 
              (plan_id, category_id))
    tasks = c.fetchall()
    conn.close()
    return tasks

def add_task_to_category(plan_id: str, category_id: str, task_name: str,
                        task_description: str, day: int, estimated_hours: float,
                        priority: str = "normal") -> bool:
    """向分类中添加任务"""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO tasks
                    (plan_id, category_id, task_name, task_description, day, estimated_hours, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (plan_id, category_id, task_name, task_description, day, estimated_hours, priority))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

# ============================================================================
# 会话状态初始化
# ============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"
if "latest_generated_evaluation" not in st.session_state:
    st.session_state.latest_generated_evaluation = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "all"

# ============================================================================
# 服务初始化
# ============================================================================

api_key_warning = None
if not API_KEY or API_KEY.strip() == "":
    api_key_warning = "⚠️ **DEEPSEEK_API_KEY 未设置**\n\n请在Streamlit Cloud中设置环境变量"
    service = None
else:
    try:
        service = StudyPlannerService(api_key=API_KEY)
    except Exception as e:
        api_key_warning = f"⚠️ 服务初始化失败: {str(e)[:100]}"
        service = None

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
            .hx-page-head {
                display: flex;
                align-items: flex-start;
                gap: 0.75rem;
                margin-bottom: 1.25rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #e8eaed;
            }
            .hx-page-icon {
                font-size: 1.75rem;
                line-height: 1.2;
            }
            .hx-page-title {
                font-size: 1.35rem;
                font-weight: 600;
                color: #1a1a1a;
                margin: 0;
                letter-spacing: -0.02em;
            }
            .hx-subtitle {
                font-size: 0.9rem;
                color: #5f6368;
                margin: 0.35rem 0 0 0;
                line-height: 1.5;
            }
            .category-card {
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
                background: #f8f9fa;
                border-left: 4px solid #3498db;
                cursor: pointer;
                transition: all 0.2s;
            }
            .category-card:hover {
                background: #e8f4f8;
                border-left-color: #2980b9;
            }
            .task-item {
                padding: 0.75rem;
                border-radius: 6px;
                margin: 0.5rem 0;
                background: #ffffff;
                border: 1px solid #e8eaed;
            }
            .task-completed {
                opacity: 0.6;
                text-decoration: line-through;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def page_header(title: str, subtitle: str | None = None, icon: str = "✨"):
    """页面标题"""
    sub = f'<p class="hx-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="hx-page-head">
            <span class="hx-page-icon">{icon}</span>
            <div>
                <h1 class="hx-page-title">{title}</h1>
                {sub}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def show_auth_page():
    """显示登录/注册页面"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🎓 AI 学习助手")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📝 登录", "✏️ 注册"])
        
        with tab1:
            st.subheader("用户登录")
            username = st.text_input("用户名", key="login_username")
            password = st.text_input("密码", type="password", key="login_password")
            
            if st.button("🔓 登录", use_container_width=True):
                if username and password:
                    if verify_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
                else:
                    st.warning("请输入用户名和密码")
        
        with tab2:
            st.subheader("用户注册")
            reg_username = st.text_input("用户名 (至少3个字符)", key="reg_username")
            reg_email = st.text_input("邮箱", key="reg_email")
            reg_password = st.text_input("密码 (至少6个字符)", type="password", key="reg_password")
            reg_password_confirm = st.text_input("确认密码", type="password", key="reg_password_confirm")
            
            if st.button("✅ 注册", use_container_width=True):
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

def render_home(current_plan):
    """首页"""
    page_header("AI 学习助手", "定计划 → 打卡 → 小测 → 按需调整", "📘")
    
    if current_plan:
        st.success("🌟 已有计划！")
        if service:
            try:
                snap = service.get_schedule_snapshot(current_plan["id"])
                if snap and snap.get("needs_attention"):
                    st.warning("🗓 有几天没打卡，记得补录进度！")
            except:
                pass
    else:
        st.info("👋 还没有计划，去左侧「✨ 学习计划生成」创建一个吧")

def render_create_plan():
    """生成计划页面"""
    page_header("学习计划生成", "描述您的学习目标，系统自动为您制定计划", "✨")
    
    if not service:
        st.error("⚠️ 服务未初始化，无法生成计划")
        return
    
    plan_start = st.date_input("📅 计划第1天", value=date.today())
    user_input = st.text_area(
        "🎯 学习目标（自然语言）",
        height=140,
        placeholder="例：两周复习操作系统，每天3小时，重点进程与内存"
    )
    
    if st.button("🚀 生成并保存学习计划", type="primary", use_container_width=True):
        if not user_input.strip():
            st.warning("请输入学习目标")
        else:
            with st.spinner("正在生成计划..."):
                try:
                    parsed = service.parse_user_goal(user_input.strip())
                    missing = service.goal_missing_fields(parsed, user_input.strip())
                    
                    if not missing:
                        plan = service.create_plan(
                            user_input.strip(),
                            plan_start_date=plan_start.isoformat(),
                            parsed_goal=parsed
                        )
                        if plan:
                            st.success("🎉 计划已生成！")
                            st.json(plan)
                        else:
                            st.error("计划生成失败")
                    else:
                        st.warning(f"缺少信息：{', '.join(missing)}")
                except Exception as e:
                    st.error(f"错误：{str(e)}")

def render_current_plan(current_plan):
    """当前计划页面"""
    page_header("当前学习计划", "查看您的学习日程和已布置的任务", "📋")
    
    if not current_plan:
        st.info("还没有计划，请先去「学习计划生成」创建计划")
        return
    
    plan_id = current_plan.get("id", "default")
    plan_data = current_plan.get("plan_data", {})
    
    # 显示计划摘要
    st.subheader("📝 计划摘要")
    st.markdown(plan_data.get("summary", "暂无摘要"))
    
    # 显示系统生成的每日任务
    st.subheader("🗓️ 系统生成的每日任务")
    daily_tasks = plan_data.get("daily_tasks", [])
    if daily_tasks:
        for task in daily_tasks[:5]:
            st.markdown(f"- **Day {task.get('day')}**: {task.get('task')} (~{task.get('estimated_hours')}h)")
    else:
        st.caption("暂无任务")
    
    st.divider()
    
    # 显示已布置的自定义任务
    st.subheader("✅ 已布置的自定义任务")
    custom_tasks = get_all_tasks(plan_id)
    
    if not custom_tasks:
        st.info("还没有布置任务，去「📌 布置任务」添加吧")
    else:
        # 按Day分组显示任务
        from collections import defaultdict
        tasks_by_day = defaultdict(list)
        for task in custom_tasks:
            tasks_by_day[task[5]].append(task)
        
        for day in sorted(tasks_by_day.keys()):
            with st.expander(f"📅 Day {day} ({len(tasks_by_day[day])}个任务)", expanded=True):
                for idx, task in enumerate(tasks_by_day[day]):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        status_emoji = "✅" if task[7] == "completed" else "⏳" if task[7] == "in_progress" else "📌"
                        priority_emoji = "🔴" if task[8] == "high" else "🟡" if task[8] == "normal" else "🟢"
                        
                        st.markdown(f"{status_emoji} {priority_emoji} **{task[2]}** (~{task[6]}h)")
                        if task[3]:
                            st.caption(f"📄 {task[3]}")
                    
                    with col2:
                        current_status = task[7]
                        new_status = st.selectbox(
                            "状态",
                            ["pending", "in_progress", "completed"],
                            index=["pending", "in_progress", "completed"].index(current_status),
                            key=f"task_status_{task[0]}",
                            label_visibility="collapsed"
                        )
                        if new_status != current_status:
                            update_task_status(task[0], new_status)
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️ 删除", key=f"delete_task_{task[0]}", use_container_width=True):
                            delete_task(task[0])
                            st.rerun()

def render_add_tasks(current_plan):
    """布置任务页面"""
    page_header("布置任务", "为学习计划添加具体的学习任务", "📌")
    
    if not current_plan:
        st.info("还没有计划，请先去「学习计划生成」创建计划")
        return
    
    plan_id = current_plan.get("id", "default")
    plan_data = current_plan.get("plan_data", {})
    
    # 获取计划总天数用作参考
    daily_tasks = plan_data.get("daily_tasks", [])
    max_days = max([t.get("day", 1) for t in daily_tasks], default=1) if daily_tasks else 1
    
    st.markdown("### 📌 快速添加任务")
    
    col1, col2 = st.columns(2)
    with col1:
        task_day = st.number_input("📅 任务所在天数", min_value=1, max_value=max(max_days + 5, 30), value=1)
        task_name = st.text_input("📌 任务名称", placeholder="例：复习操作系统 - 进程管理")
    
    with col2:
        estimated_hours = st.number_input("⏱️ 预计耗时 (小时)", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
        priority = st.selectbox("🎯 优先级", ["high", "normal", "low"], format_func=lambda x: {"high": "⚠️ 高", "normal": "📌 普通", "low": "✅ 低"}[x])
    
    task_description = st.text_area("📝 任务描述", placeholder="详细描述任务内容、要点等", height=100)
    
    if st.button("➕ 添加任务", type="primary", use_container_width=True):
        if not task_name.strip():
            st.error("请输入任务名称")
        else:
            success = add_task(plan_id, task_name, task_description, task_day, estimated_hours, priority)
            if success:
                st.success(f"✅ 任务「{task_name}」已添加到 Day {task_day}！")
                st.rerun()
            else:
                st.error("添加失败，请重试")
    
    st.divider()
    
    # 显示所有已布置任务的快速预览
    st.markdown("### 📋 任务列表预览")
    all_tasks = get_all_tasks(plan_id)
    
    if not all_tasks:
        st.info("暂无任务")
    else:
        # 按优先级分类显示 (高优先级在前)
        priority_order = {"high": 0, "normal": 1, "low": 2}
        sorted_tasks = sorted(all_tasks, key=lambda x: (x[5], -priority_order.get(x[8], 1)))
        
        from collections import defaultdict
        tasks_by_day = defaultdict(list)
        for task in sorted_tasks:
            tasks_by_day[task[5]].append(task)
        
        for day in sorted(tasks_by_day.keys()):
            st.markdown(f"**Day {day}** - {len(tasks_by_day[day])}个任务")
            for task in tasks_by_day[day]:
                status_icon = "✅" if task[7] == "completed" else "⏳" if task[7] == "in_progress" else "📌"
                priority_icon = "🔴" if task[8] == "high" else "🟡" if task[8] == "normal" else "🟢"
                st.caption(f"{status_icon} {priority_icon} {task[2]} - (~{task[6]}h)")

def render_progress(current_plan):
    """进度反馈页面"""
    page_header("学习进度反馈", "记录今日学习情况", "📈")
    
    if not current_plan:
        st.info("请先生成计划")
        return
    
    if not service:
        st.error("服务未初始化")
        return
    
    col1, col2 = st.columns([1.1, 1])
    with col1:
        record_date = st.date_input("📅 进度日期", value=date.today())
        completion_ratio = st.slider("✅ 当日完成度 (%)", 0, 100, 60)
        completed_tasks = st.text_area("✔️ 已完成", placeholder="今天搞定了什么")
    
    with col2:
        note = st.text_area("💭 备注", height=120, placeholder="随手记两句")
    
    if st.button("📤 提交进度", type="primary", use_container_width=True):
        progress_data = {
            "study_date": record_date.isoformat(),
            "completion_ratio": completion_ratio,
            "completed_tasks": completed_tasks,
            "note": note,
        }
        try:
            latest = service.record_progress(current_plan["id"], progress_data)
            if latest:
                st.success("📝 已记下进度！")
            else:
                st.error("记录失败")
        except Exception as e:
            st.error(f"错误：{str(e)}")

def render_evaluation(current_plan):
    """学习检测页面"""
    page_header("学习检测", "先记进度才会出题", "📝")
    
    if not current_plan:
        st.info("请先生成计划")
        return
    
    st.info("请先在「学习进度反馈」中记录进度，系统会自动生成题目")

def render_adjustment(current_plan):
    """动态调整页面"""
    page_header("动态调整", "根据进度重新安排任务", "🔄")
    
    if not current_plan:
        st.info("请先生成计划")
        return
    
    if not service:
        st.error("服务未初始化")
        return
    
    st.info("系统会根据您的学习进度，智能调整后续任务")
    
    if st.button("⚡ 生成调整建议", type="primary", use_container_width=True):
        with st.spinner("分析中..."):
            try:
                result = service.adjust_plan(current_plan["id"])
                if result:
                    st.success("✅ 已重新调整！")
                else:
                    st.warning("暂无调整建议")
            except Exception as e:
                st.error(f"错误：{str(e)}")

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
            st.rerun()
    
    st.divider()
    
    # 显示API KEY警告
    if api_key_warning:
        st.error(api_key_warning)
    
    # 获取当前计划
    current_plan = None
    if service:
        try:
            current_plan = service.get_current_plan()
        except:
            pass
    
    # 侧边栏导航
    st.sidebar.markdown("### 📌 菜单")
    labels = [pair[0] for pair in NAV_ITEMS]
    picked = st.sidebar.radio("页面", labels, label_visibility="collapsed")
    page = dict(NAV_ITEMS)[picked]
    
    st.sidebar.divider()
    st.sidebar.markdown(f"**用户**: {st.session_state.username}")
    
    # 页面路由
    if page == "首页总览":
        render_home(current_plan)
    elif page == "学习计划生成":
        render_create_plan()
    elif page == "当前学习计划":
        render_current_plan(current_plan)
    elif page == "布置任务":
        render_add_tasks(current_plan)
    elif page == "学习进度反馈":
        render_progress(current_plan)
    elif page == "学习检测":
        render_evaluation(current_plan)
    elif page == "动态调整":
        render_adjustment(current_plan)

if __name__ == "__main__":
    main()
