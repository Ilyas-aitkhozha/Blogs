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

------ | ------ |
| **Business‑grade roles & permissions** | Two built‑in profiles (User / Admin) map to most help‑desk, DevOps and HR scenarios. |
| **Industrial JWT security** | Email & Google OAuth sign‑in, refresh tokens, stateless sessions. |
| **AI Concierge** | Server‑side Gemini chatbot guides users through the API & UI. |
| **Instant availability** | Users flip an `available` switch; APIs expose who can accept work <kbd>in real time</kbd>. |
| **Audit‑ready metadata** | Every ticket stores creator, assignee, timestamps & status history. |
| **Granular workflow** | Admins drive the lifecycle (Open → In Progress → Closed); Users create & assign. |

---

## 🚀 Feature Matrix

| Category | Endpoints / Capability |
| -------- | ---------------------- |
| **Task Core** | `POST /tickets` · `GET /tickets/{id}` · `PATCH /tickets/{id}` |
| **Status Pipeline** | Admin‑only transition: `open → in_progress → closed` |
| **Availability** | `GET /available/users` · `GET /available/admins` |
| **Gemini Chat** | `POST /chat/ask` – context‑aware AI guidance |
| **Auth** | `POST /auth/signup` · `POST /auth/login` · Google OAuth callback |
| **Docs** | Self‑generated Swagger / ReDoc at `/docs` & `/redoc` |

---

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

---

## 🗺️  Roadmap

- [ ] WebSocket live updates for ticket boards
- [ ] Admin analytics dashboard (FastAPI + Vue 3)
- [ ] RBAC groups (Team Lead, Auditor)

---

## ✉️  Contact

**Bauyrzhan Aitkhozha** — Project Manager & Back‑End Engineer  
[LinkedIn](https://www.linkedin.com/in/bauyrzhan-a-b8682b256/) • [Email](mailto:your.email@example.com)

> *I build operational tooling that scales from hobby tiers to enterprise SLAs.*

