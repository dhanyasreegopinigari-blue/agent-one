# Agent One — Deployment Guide

This guide covers production deployment for the Agent One backend (Docker + Compose + Caddy on Linux) and frontend (Vercel).

---

## 1. Prerequisites (Human Checklist)

| # | Item | Purpose |
|---|---|---|
| **H1** | GitHub repository | Pushing code and triggering Vercel builds |
| **H2** | Vercel account | Hosting the Next.js frontend |
| **H3** | Supabase project | Authentication (Supabase URL, Anon key, JWT secret or JWKS) |
| **H4** | Google Cloud OAuth client | Enabling "Sign in with Google" in Supabase Auth |
| **H5** | Gemini API key | Optional fallback LLM when Ollama is unreachable |
| **H6** | Linux server with Docker & Compose | Hosting Ollama, SearXNG, FastAPI backend, and Caddy (≥ 16 GB RAM recommended, NVIDIA GPU optional) |
| **H7** | Public DNS record | Pointing `api.yourdomain.com` (A record) to the Linux server |

---

## 2. Backend Deployment (Docker Compose)

### 2.1 Server Setup
1. Clone the repository onto your server:
   ```bash
   git clone <repo-url> agent-one && cd agent-one
   ```
2. Configure backend environment:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Set:
   - `ENV=production`
   - `AUTH_DISABLED=false`
   - `SUPABASE_URL=https://<ref>.supabase.co`
   - `SUPABASE_JWT_SECRET=<jwt-secret>` (or leave empty if using JWKS asymmetric verification)
   - `CORS_ORIGINS=https://<your-vercel-domain>`
   - `CORS_ORIGIN_REGEX=^https://agent-one-[a-z0-9-]+\.vercel\.app$`
   - `GEMINI_API_KEY=<gemini-key>`
   - `ALLOW_GEMINI_FALLBACK=true`

3. Configure deployment environment:
   ```bash
   cp deploy/.env.example deploy/.env
   # Edit BACKEND_DOMAIN=api.yourdomain.com
   ```

4. Configure SearXNG secret:
   Generate a 32-byte hex secret (`openssl rand -hex 32`) and paste into `deploy/searxng/settings.yml`.

5. Build and launch containers:
   - **CPU only**:
     ```bash
     cd deploy && docker compose --profile prod up -d --build
     ```
   - **With NVIDIA GPU**:
     ```bash
     cd deploy && docker compose --profile prod -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
     ```

6. Pull required Ollama models:
   ```bash
   bash pull-models.sh
   ```

7. Verify health:
   ```bash
   curl -s https://api.yourdomain.com/health
   # Should return: {"status": "ok", "ollama": {"status": "ok", "available": true}, ...}
   ```

---

## 3. Frontend Deployment (Vercel)

### 3.1 Project Settings
1. Connect your GitHub repository to Vercel.
2. Ensure settings:
   - Framework preset: **Next.js**
   - Root directory: `./`
   - Node.js version: **20.x or 22.x**

### 3.2 Environment Variables
Add the following 3 variables in Vercel project settings (Production and Preview):
- `NEXT_PUBLIC_BACKEND_URL`: `https://api.yourdomain.com` (no trailing slash)
- `NEXT_PUBLIC_SUPABASE_URL`: `https://<ref>.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: `<anon-key>`

### 3.3 Supabase Authentication Settings
In the Supabase Dashboard:
1. **Providers**:
   - Enable **Google** (add Client ID & Secret; set redirect callback in Google Console to `https://<ref>.supabase.co/auth/v1/callback`).
   - Enable **Anonymous sign-ins** (for guest workspace access).
2. **URL Configuration**:
   - **Site URL**: `https://<your-vercel-domain>`
   - **Redirect URLs**:
     - `https://<your-vercel-domain>/dashboard`
     - `https://<your-vercel-domain>/reset-password`
     - `http://localhost:3000/dashboard`
     - `http://localhost:3000/reset-password`
     - Wildcards: `https://*-<team>.vercel.app/**`
