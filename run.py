#!/usr/bin/env python3
"""
Startup script for Perfect PO API
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=int(settings.api_port),
        reload=False,  # Disable reload in production/containerized environments
        log_level="info",
        access_log=True
    )








