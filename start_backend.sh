#!/bin/bash
cd /app
uvicorn backend_server:app --host 0.0.0.0 --port 8000
