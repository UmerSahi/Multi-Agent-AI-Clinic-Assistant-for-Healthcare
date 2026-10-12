"""
City Care Clinics Multi-Agent Healthcare Platform
Root ASGI Entrypoint for Render and Cloud Deployment.
"""

import os
import sys
from pathlib import Path

# Setup paths for multi-day module resolution
ROOT_DIR = Path(__file__).resolve().parent
for d in ["Day 4", "Day 5", "Day 3", "Day 3/agents", "Day 2", "Day 1", "."]:
    target_path = str(ROOT_DIR / d)
    if target_path not in sys.path:
        sys.path.insert(0, target_path)

# Import the FastAPI application from Day 4 api_server
from api_server import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
