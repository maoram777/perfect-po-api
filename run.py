#!/usr/bin/env python3
"""
Startup script for Perfect PO API
"""
import os
import uvicorn
from app.config import settings

if __name__ == "__main__":
    # Use debug log level when DEBUG=true so app debug logs (catalog/enrichment) are visible
    log_level = "debug" if os.environ.get("DEBUG", "").lower() in ("true", "1") else "info"
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=int(settings.api_port),
        reload=False,  # Disable reload in production/containerized environments
        log_level=log_level,
        access_log=True
    )








