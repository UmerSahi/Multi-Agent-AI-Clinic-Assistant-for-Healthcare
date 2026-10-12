# City Care Clinics -- Cloud Deployment Guide and Render Blueprints

## 1. Overview and Architecture

This guide provides instructions for deploying the **City Care Clinics Multi-Agent Healthcare Platform** to **Render** using free-tier resources. The system consists of two primary services:

1. **Backend Web Service (FastAPI and LangGraph)**:
   - Python 3.11 ASGI application serving the multi-agent orchestration engine, REST APIs, medical safety guards, and SMTP email dispatcher.
   - Connected directly to live Supabase PostgreSQL for persistent FHIR records.
2. **Frontend Web Service (Next.js 14 and React)**:
   - Modern patient and physician portal interface communicating with the FastAPI backend.

```
       +--------------------------------------------------------+
       |                     RENDER CLOUD                       |
       |                                                        |
       |   +-----------------------+                            |
       |   | clinic-frontend       | (Next.js Node Web Service) |
       |   | Patient & Staff Portal|                            |
       |   +-----------+-----------+                            |
       |               | (REST / SSE / WebSockets)              |
       |               v                                        |
       |   +-----------------------+                            |
       |   | clinic-backend        | (Python 3.11 FastAPI)      |
       |   | LangGraph Coordinator |                            |
       |   +-------+-------+-------+                            |
       +-----------|-------|------------------------------------+
                   |       |
                   |       +--------------------> [ Google Gmail SMTP ]
                   v                               (Port 587 TLS)
          [ Supabase Cloud ]
          (PostgreSQL Database)
```

---

## 2. Render Free Tier Specifications and Considerations

Render offers generous free tier hosting suitable for portfolio demonstration and testing:

| Resource Dimension | Free Tier Allowance | Clinic Platform Suitability |
| :--- | :--- | :--- |
| **Instance Type** | Free Web Service (0.5 CPU, 512 MB RAM) | Fully sufficient for FastAPI ASGI server |
| **Monthly Hours** | 750 free instance hours per month | Runs continuously 24 hours per day |
| **Bandwidth** | 100 GB outbound bandwidth per month | Sufficient for clinical chat and report handling |
| **Sleep Inactivity** | Spins down after 15 minutes of inactivity | Wakes up automatically on next HTTP request (30-50s) |
| **Custom Domains** | Included with free SSL/TLS certificates | Allows custom clinic domains |

---

## 3. Deployment Files Reference

The repository includes all necessary configuration files ready for deployment:

| File Location | Purpose in Render Build |
| :--- | :--- |
| `main.py` | Root ASGI entrypoint mapping `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| `requirements.txt` | Production pip dependencies pinned for clean installation |
| `render.yaml` | Infrastructure as Code blueprint defining backend and frontend services |
| `Procfile` | Process definition for standard cloud container runners |
| `Day 5/render_deploy_check.py` | Pre-flight audit script to verify all endpoints prior to deployment |

---

## 4. Option 1: Automated Blueprint Deployment (Recommended)

Render Blueprints allow one-click deployment using the included `render.yaml` specification.

### Step 1: Open Render Dashboard
1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** in the top navigation bar and select **Blueprint**.

### Step 2: Connect GitHub Repository
1. Select your GitHub repository: `Multi-Agent-AI-Clinic-Assistant-for-Healthcare`.
2. Render will automatically detect `render.yaml`.
3. Provide a Blueprint name: `city-care-clinics`.

### Step 3: Populate Secret Environment Variables
Render will ask you to supply values for secret variables marked with `sync: false`:
- `GEMINI_API_KEY`: Your Google Gemini API key.
- `SUPABASE_URL`: Your live Supabase URL (e.g. `https://yswtqhoikwqumuoaimub.supabase.co`).
- `SUPABASE_KEY`: Your Supabase publishable anon key.
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role secret key.
- `SMTP_USER`: Your Gmail address (e.g. `umersahi5p@gmail.com`).
- `SMTP_PASSWORD`: Your 16-character Google App Password.
- `SMTP_FROM_EMAIL`: Your clinic sender email.

### Step 4: Apply and Deploy
Click **Apply**. Render will simultaneously provision the Python backend and the Next.js frontend.

---

## 5. Option 2: Manual Web Service Deployment

If you prefer deploying services individually:

### Deploying the Backend (clinic-backend)
1. Click **New +** -> **Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name**: `clinic-backend`
   - **Region**: Oregon (US West) or Frankfurt (EU Central)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (root)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
4. Under **Advanced** -> **Health Check Path**, enter: `/health`
5. Add the Environment Variables listed in Section 6 below.
6. Click **Create Web Service**.

### Deploying the Frontend (clinic-frontend)
1. Click **New +** -> **Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name**: `clinic-frontend`
   - **Region**: Same region as backend
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Runtime**: Node
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run start`
   - **Instance Type**: Free
4. Under **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: Paste your backend Render URL (e.g. `https://clinic-backend.onrender.com`).
5. Click **Create Web Service**.

---

## 6. Environment Variables Checklist

Ensure these variables are added in your Render Service Settings under **Environment**:

| Environment Variable | Recommended Value | Description |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Ensures Python 3.11 runtime environment |
| `DEFAULT_CLINIC_CITY` | `Lahore` | Default primary branch city |
| `DEFAULT_LANGUAGE` | `urdu_lish` | Default patient conversational language |
| `DEBUG` | `false` | Production mode flag |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | High-speed, cost-efficient clinical LLM |
| `GEMINI_API_KEY` | *(Secret)* | Gemini API access key |
| `SUPABASE_URL` | *(Secret)* | Live PostgreSQL Supabase project URL |
| `SUPABASE_KEY` | *(Secret)* | Public anon API key |
| `SUPABASE_SERVICE_ROLE_KEY` | *(Secret)* | Privileged database admin key |
| `SMTP_HOST` | `smtp.gmail.com` | Outgoing email server |
| `SMTP_PORT` | `587` | STARTTLS port |
| `SMTP_USER` | *(Secret)* | Authenticated Gmail address |
| `SMTP_PASSWORD` | *(Secret)* | 16-character Google App Password |
| `SMTP_FROM_EMAIL` | *(Secret)* | Email shown in From address |
| `SMTP_FROM_NAME` | `City Care Clinics` | Branded sender display name |
| `SMTP_USE_TLS` | `true` | Secure TLS handshake flag |

---

## 7. Verification and Health Check Verification

Once deployment finishes, verify the live deployment using these endpoints:

1. **System Health Check**:
   ```
   GET https://your-backend-service.onrender.com/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "system": "City Care Clinics Multi-Agent Orchestration",
     "model": "gemini-3.5-flash-lite",
     "langgraph_ready": true,
     "timestamp": "2026-10-12T12:00:00Z"
   }
   ```

2. **Branch List Verification**:
   ```
   GET https://your-backend-service.onrender.com/api/branches
   ```

3. **Physician Directory**:
   ```
   GET https://your-backend-service.onrender.com/api/practitioners
   ```

---

## 8. Tips for Render Free Tier

1. **Managing Cold Starts**:
   - On the free tier, services spin down after 15 minutes of zero traffic.
   - The first request after a pause takes approximately 30 to 50 seconds to initialize.
   - For demo presentations or defense evaluations, trigger a simple request to `/health` two minutes beforehand to ensure the instance is active and warm.
2. **Database Resilience**:
   - Because Supabase is hosted externally, database records, appointments, and patient profiles persist permanently even when the Render free web service restarts.
