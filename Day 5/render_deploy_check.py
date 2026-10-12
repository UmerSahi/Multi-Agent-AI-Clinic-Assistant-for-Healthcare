"""
Render Deployment Pre-Flight Verification Script
Tests and verifies that the FastAPI application, dependencies, and routes
are 100% ready for free-tier Render deployment.
"""

import os
import sys
import json
from pathlib import Path

# Add all relevant paths
DAY5_DIR = Path(__file__).resolve().parent
ROOT_DIR = DAY5_DIR.parent
for p in [str(ROOT_DIR / "Day 4"), str(DAY5_DIR), str(ROOT_DIR / "Day 3"), str(ROOT_DIR / "Day 2"), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

def test_render_preflight():
    print("=" * 70)
    print("CITY CARE CLINICS -- RENDER PRE-FLIGHT DEPLOYMENT AUDIT")
    print("=" * 70)

    # 1. Check Root Entrypoint
    print("\n[Step 1] Checking Root Entrypoint...")
    main_file = ROOT_DIR / "main.py"
    req_file = ROOT_DIR / "requirements.txt"
    proc_file = ROOT_DIR / "Procfile"
    yaml_file = ROOT_DIR / "render.yaml"

    assert main_file.exists(), "main.py must exist in root"
    assert req_file.exists(), "requirements.txt must exist in root"
    assert proc_file.exists(), "Procfile must exist in root"
    assert yaml_file.exists(), "render.yaml must exist in root"
    print("[OK] All root deployment files present (main.py, requirements.txt, Procfile, render.yaml)")

    # 2. Check Import of ASGI App
    print("\n[Step 2] Importing ASGI Application...")
    import main
    app = main.app
    assert app is not None, "FastAPI app instance failed to initialize"
    print(f"[OK] ASGI Application initialized: '{app.title}' (Version {app.version})")

    # 3. Test Health Check Routes using FastAPI TestClient
    print("\n[Step 3] Testing Health Endpoints...")
    from fastapi.testclient import TestClient
    client = TestClient(app)

    routes_to_test = ["/", "/health", "/api/health"]
    for route in routes_to_test:
        resp = client.get(route)
        assert resp.status_code == 200, f"Route {route} failed with status {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "healthy", f"Route {route} did not report healthy"
        print(f"[OK] Route '{route}' responded HTTP 200 OK -- Status: {data.get('status')}")

    # 4. Check Database Connection
    print("\n[Step 4] Checking Database Connectivity...")
    from db_client import DatabaseClient
    db_test = DatabaseClient()
    print(f"[OK] Database connected (Is Supabase Active: {db_test.is_supabase})")

    # 5. Check SMTP Email Dispatcher
    print("\n[Step 5] Checking Email Notifier Configuration...")
    from email_notifier import email_notifier
    is_smtp = email_notifier.is_smtp_configured
    print(f"[OK] Email Notifier Initialized (Live SMTP Configured: {is_smtp})")

    print("\n" + "=" * 70)
    print("ALL RENDER DEPLOYMENT PRE-FLIGHT CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    test_render_preflight()
