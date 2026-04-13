@echo off
REM Huixue Agent 2.0 - Development Start Script for Windows

echo Loading environment variables...
for /f "tokens=*" %%A in (.env) do (
    if not "%%A"=="" (
        if not "%%A:~0,1%"=="#" (
            set %%A
        )
    )
)

echo Starting FastAPI backend on http://localhost:8000...
start "FastAPI Backend" python -m uvicorn backend_server:app --host 0.0.0.0 --port 8000 --reload

timeout /t 2 /nobreak

echo Starting Streamlit frontend on http://localhost:8501...
streamlit run streamlit_app_new.py --logger.level=info

echo.
echo Press Ctrl+C to stop all services
