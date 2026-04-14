import os
import json
from datetime import datetime, timedelta
from typing import Optional

import jwt
import bcrypt
from fastapi import FastAPI, HTTPException, Depends, status, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from storage.db import get_connection, init_db
from services.study_planner_service import StudyPlannerService

# Initialize database
init_db()

# FastAPI app
app = FastAPI(title="Huixue Agent API", version="2.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


# ============================================================================
# Pydantic Models
# ============================================================================

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    password_confirm: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    raw_input: str
    plan_start_date: Optional[str] = None


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class TaskCreate(BaseModel):
    title: str
    category: Optional[str] = None
    priority: str = "medium"
    deadline: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[str] = None


# ============================================================================
# Utilities
# ============================================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: int, username: str) -> str:
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user_id, "username": username, "exp": expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    return verify_token(parts[1])


# ============================================================================
# Auth Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=TokenResponse)
def register(user: UserRegister):
    """User registration"""
    if user.password != user.password_confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                      (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="User already exists")
        
        # Create user
        password_hash = hash_password(user.password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (user.username, user.email, password_hash)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        token = create_access_token(user_id, user.username)
        
        return TokenResponse(
            access_token=token,
            user_id=user_id,
            username=user.username
        )


@app.post("/api/auth/login", response_model=TokenResponse)
def login(credentials: UserLogin):
    """User login"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?",
                      (credentials.username,))
        row = cursor.fetchone()
        
        if not row or not verify_password(credentials.password, row[2]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_id, username = row[0], row[1]
        token = create_access_token(user_id, username)
        
        return TokenResponse(
            access_token=token,
            user_id=user_id,
            username=username
        )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(id=row[0], username=row[1], email=row[2])


# ============================================================================
# Plan Endpoints
# ============================================================================

@app.post("/api/plans", response_model=dict)
async def create_plan(plan: PlanCreate, current_user: dict = Depends(get_current_user)):
    """Create a study plan"""
    user_id = current_user["user_id"]
    
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    try:
        service = StudyPlannerService(api_key=api_key)
    except Exception as e:
        # If service initialization fails, create a mock plan
        plan_result = {
            "parsed_goal": {},
            "plan_data": {
                "plan_overview": f"学习计划: {plan.name}",
                "note": f"由于API配置问题，这是一个简化的计划。原始输入: {plan.raw_input}"
            }
        }
        plan_rag = None
    else:
        try:
            plan_result, plan_rag = service.create_plan(
                plan.raw_input,
                plan_start_date=plan.plan_start_date
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")
    
    if not plan_result:
        raise HTTPException(status_code=500, detail="Plan generation failed")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO study_plans 
            (user_id, name, raw_input, parsed_goal_json, plan_json, plan_text, plan_start_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                plan.name,
                plan.raw_input,
                json.dumps(plan_result.get("parsed_goal", {})),
                json.dumps(plan_result.get("plan_data", {})),
                str(plan_result.get("plan_data", "")),
                plan.plan_start_date,
                1  # Set as active
            )
        )
        conn.commit()
        plan_id = cursor.lastrowid
        
        return {
            "id": plan_id,
            "name": plan.name,
            "status": "active",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }


@app.get("/api/plans")
async def list_plans(current_user: dict = Depends(get_current_user)):
    """List user's plans"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, status, is_active, created_at, updated_at
            FROM study_plans WHERE user_id = ? ORDER BY updated_at DESC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "status": row[2],
                "is_active": bool(row[3]),
                "created_at": row[4],
                "updated_at": row[5]
            }
            for row in rows
        ]


@app.get("/api/plans/{plan_id}")
async def get_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    """Get plan details"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, raw_input, parsed_goal_json, plan_json, plan_text, 
                   status, is_active, created_at, updated_at
            FROM study_plans WHERE id = ? AND user_id = ?
            """,
            (plan_id, user_id)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Get tasks
        cursor.execute(
            "SELECT id, title, category, priority, status, deadline FROM study_tasks WHERE plan_id = ? ORDER BY order_index",
            (plan_id,)
        )
        tasks = [
            {
                "id": t[0],
                "title": t[1],
                "category": t[2],
                "priority": t[3],
                "status": t[4],
                "deadline": t[5]
            }
            for t in cursor.fetchall()
        ]
        
        return {
            "id": row[0],
            "name": row[1],
            "raw_input": row[2],
            "parsed_goal": json.loads(row[3]) if row[3] else {},
            "plan_data": json.loads(row[4]) if row[4] else {},
            "plan_text": row[5],
            "status": row[6],
            "is_active": bool(row[7]),
            "created_at": row[8],
            "updated_at": row[9],
            "tasks": tasks
        }


@app.put("/api/plans/{plan_id}", response_model=dict)
async def update_plan(plan_id: int, update: PlanUpdate, current_user: dict = Depends(get_current_user)):
    """Update plan"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM study_plans WHERE id = ? AND user_id = ?", 
                      (plan_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plan not found")
        
        updates = []
        values = []
        
        if update.name is not None:
            updates.append("name = ?")
            values.append(update.name)
        if update.status is not None:
            updates.append("status = ?")
            values.append(update.status)
        if update.is_active is not None:
            # Deactivate other plans
            if update.is_active:
                cursor.execute("UPDATE study_plans SET is_active = 0 WHERE user_id = ?", (user_id,))
            updates.append("is_active = ?")
            values.append(1 if update.is_active else 0)
        
        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(plan_id)
        
        query = f"UPDATE study_plans SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        
        return {"id": plan_id, "message": "Plan updated"}


@app.delete("/api/plans/{plan_id}")
async def delete_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    """Delete plan"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM study_plans WHERE id = ? AND user_id = ?", 
                      (plan_id, user_id))
        conn.commit()
        
        return {"message": "Plan deleted"}


# ============================================================================
# Task Endpoints
# ============================================================================

@app.post("/api/plans/{plan_id}/tasks", response_model=dict)
async def create_task(plan_id: int, task: TaskCreate, current_user: dict = Depends(get_current_user)):
    """Create task"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM study_plans WHERE id = ? AND user_id = ?", 
                      (plan_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plan not found")
        
        cursor.execute(
            """
            INSERT INTO study_tasks (plan_id, title, category, priority, deadline)
            VALUES (?, ?, ?, ?, ?)
            """,
            (plan_id, task.title, task.category, task.priority, task.deadline)
        )
        conn.commit()
        task_id = cursor.lastrowid
        
        return {"id": task_id, "plan_id": plan_id, "message": "Task created"}


@app.put("/api/plans/{plan_id}/tasks/{task_id}", response_model=dict)
async def update_task(plan_id: int, task_id: int, update: TaskUpdate, current_user: dict = Depends(get_current_user)):
    """Update task"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM study_plans WHERE id = ? AND user_id = ?", 
                      (plan_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plan not found")
        
        updates = []
        values = []
        
        if update.title is not None:
            updates.append("title = ?")
            values.append(update.title)
        if update.category is not None:
            updates.append("category = ?")
            values.append(update.category)
        if update.priority is not None:
            updates.append("priority = ?")
            values.append(update.priority)
        if update.status is not None:
            updates.append("status = ?")
            values.append(update.status)
        if update.deadline is not None:
            updates.append("deadline = ?")
            values.append(update.deadline)
        
        if not updates:
            return {"id": task_id, "message": "No updates"}
        
        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.extend([task_id, plan_id])
        
        query = f"UPDATE study_tasks SET {', '.join(updates)} WHERE id = ? AND plan_id = ?"
        cursor.execute(query, values)
        conn.commit()
        
        return {"id": task_id, "message": "Task updated"}


@app.delete("/api/plans/{plan_id}/tasks/{task_id}")
async def delete_task(plan_id: int, task_id: int, current_user: dict = Depends(get_current_user)):
    """Delete task"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM study_plans WHERE id = ? AND user_id = ?", 
                      (plan_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plan not found")
        
        cursor.execute("DELETE FROM study_tasks WHERE id = ? AND plan_id = ?", 
                      (task_id, plan_id))
        conn.commit()
        
        return {"message": "Task deleted"}


@app.post("/api/plans/{plan_id}/activate")
async def activate_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    """Set plan as active"""
    user_id = current_user["user_id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM study_plans WHERE id = ? AND user_id = ?", 
                      (plan_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Deactivate other plans
        cursor.execute("UPDATE study_plans SET is_active = 0 WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE study_plans SET is_active = 1 WHERE id = ?", (plan_id,))
        conn.commit()
        
        return {"message": "Plan activated"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
