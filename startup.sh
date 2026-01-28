#!/bin/bash
# Azure App Service Startup Script for FastAPI Backend
# This script is used by Azure App Service (Linux) to start the application

cd backend && python -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}

