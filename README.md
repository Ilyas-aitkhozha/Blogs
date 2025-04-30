<!-- Project Title and Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/Built%20with-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Auth-JWT%20%26%20Google%20OAuth-F44336?style=for-the-badge&logo=jsonwebtokens&logoColor=white"/>
  <img src="https://img.shields.io/badge/AI-Gemini-673AB7?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Deploy-Render.com-4CAF50?style=for-the-badge"/>
</p>

<h1 align="center">🎟️ TicketSystem — FastAPI Back‑End</h1>
<p align="center"><em>Production‑ready task engine with real‑time availability, admin workflow control &amp; an AI navigation assistant.</em></p>

---

## ✨ Overview

TicketSystem is a FastAPI‑powered back‑end that delivers a fully featured task‑and‑ticket workflow service.  It offers JWT & Google OAuth authentication, role‑based permissions (User / Admin), real‑time availability flags, and an integrated Gemini chatbot for context‑aware assistance.

Business‑grade roles & permissions – two built‑in profiles (User / Admin) that fit most help‑desk and DevOps cases.

JWT + Google OAuth security – email or Google sign‑in, access & refresh tokens, stateless sessions.

AI concierge – server‑side Gemini chatbot that guides users through the API and UI.

Real‑time availability – users toggle an available flag; endpoints immediately show who can accept work.

Audit‑ready metadata – each ticket tracks creator, assignee, timestamps and status history out of the box.

Granular workflow control – admins move tickets Open → In Progress → Closed; users create and assign

---

### Feature Matrix

| Category | Key Endpoints / Behaviour |
|----------|---------------------------|
| **Tickets** | `POST /tickets` – create • `GET /tickets/{id}` – read • `PATCH /tickets/{id}` – update |
| **Status Flow** | Admin-only: `open` ➜ `in_progress` ➜ `closed` |
| **Availability** | `GET /available/users` • `GET /available/admins` — show who can take new work |
| **Gemini Chat** | `POST /chat/ask` — context-aware AI help inside the UI & API |
| **Auth** | `POST /auth/signup` • `POST /auth/login` (JWT) • Google OAuth callback |
| **Docs** | Auto-generated Swagger `/docs` |

## 🏗️ Tech Stack

- **Python 3.12 · FastAPI**
- **SQLAlchemy + PostgreSQL**
- **Authlib · PyJWT**
- **Google Gemini API**
- **Render.com CI deploy**

---

## 🧩  Quick‑Start (Local)

```bash
# clone & enter
$ git clone https://github.com/Ilyas-aitkhozha/TicketSystem.git
$ cd TicketSystem

# virtualenv
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt

# run dev server
$ uvicorn tickets.main:app --reload --port 8000

# browse docs
$ open http://localhost:8000/docs
```

> **Prod URL:** <https://tickets-backend.onrender.com>

---

## 🔒  Security Highlights

- HTTP‑only secure cookies & `Authorization: Bearer` headers
- Passwords hashed with **bcrypt**
- CORS locked to front‑end domain in production



