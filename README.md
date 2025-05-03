<!-- Project Title and Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/Built%20with-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Auth-JWT%20%26%20Google%20OAuth-F44336?style=for-the-badge&logo=jsonwebtokens&logoColor=white"/>
  <img src="https://img.shields.io/badge/AI-Gemini-673AB7?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Deploy-Render.com-4CAF50?style=for-the-badge"/>
</p>

<h1 align="center"> TicketSystem — FastAPI Back‑End</h1>
<p align="center"><em>Production‑ready task engine with real‑time availability, admin workflow control &amp; an AI navigation assistant.</em></p>

---

## Overview

TicketSystem is a FastAPI-based backend that provides a full-featured task and ticketing service. It offers JWT and Google OAuth authentication, role-based permissions (User / Administrator), real-time availability flags and an integrated Gemini chatbot for help within the service.

Business-class roles and permissions - two built-in profiles (User / Administrator) that fit most helpdesk and DevOps workloads.

JWT + Google OAuth security - login via email or Google, access and update tokens, static-free sessions.

AI friend - Gemini server-side chatbot to help users understand the API and UI.

Real-time availability - users toggle the availability flag; endpoints immediately show who can accept work.

Auditable metadata - each ticket tracks creator, recipient, timestamps, and status history. 

Detailed workflow management - administrators move tickets Open → In Progress → Closed; users create and assign tickets.

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

##  Tech Stack

- **Python 3.12 · FastAPI**
- **SQLAlchemy + PostgreSQL**
- **Authlib · PyJWT**
- **Google Gemini API**
- **Render.com CI deploy**

---

## 🚀 Quick Start

1. **Clone repository**  
   ```bash
   git clone https://github.com/Ilyas-aitkhozha/TicketSystem.git
   cd TicketSystem

    Создать файл окружения
    Скопируйте шаблон и заполните свои значения:

cp env.example .env

Run it via Docker Compose

  ```docker-compose up --build -d```

checking how its working 

    Swagger UI: http://localhost:8000/docs

stop containers:

  ```docker-compose down```

> **Prod URL:** <(https://trackzy-gamma.vercel.app/)>

---

##  Security Highlights

- HTTP‑only secure cookies & `Authorization: Bearer` headers
- Passwords hashed with **bcrypt**
- CORS locked to front‑end domain in production



