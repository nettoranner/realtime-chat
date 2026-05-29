# Real-Time Multi-Room Chat Application

A modern, high-performance real-time chat application featuring a robust asynchronous backend, a component-driven frontend, and containerized state management. 
Designed with security and scalability best practices, this project showcases modern Python and TypeScript development.


## 🚀 Key Features

- **Real-Time Bidirectional Communication:** Bidirectional messaging powered by FastAPI WebSockets.
- **Dynamic Rooms:** Users can create custom rooms dynamically or join any room using its unique ID.
- **State Persistence:** Messages are persisted asynchronously in PostgreSQL, with history automatically loaded upon entering a room.
- **Database Seeding:** Automatically seeds default channels (`General`, `Random`, `Support`) and manages PostgreSQL sequence states on startup.
- **Secure Authentication:** JWT authentication leveraging **HttpOnly, SameSite=Lax Cookies**, rendering the application immune to Cross-Site Scripting (XSS) token-theft.
- **Vite Development Proxy:** A seamless local proxy routing `/api` and `/ws` to prevent Cross-Origin Resource Sharing (CORS) complications during development.
- **Modern Database Migrations:** Schema changes managed declaratively using Alembic with an asynchronous database driver.


## 🛠️ Tech Stack

### Backend
- **FastAPI** (High-performance Python web framework)
- **SQLAlchemy 2.0** (Asynchronous ORM mapping using `asyncpg`)
- **Alembic** (Database migration tool)
- **PyJWT** (Modern JSON Web Token encoding and validation)
- **Bcrypt** (Secure password hashing)
- **Uvicorn** (ASGI server implementation)
- **UV** (Blazing-fast Rust-based Python package resolver)

### Frontend
- **React 18** (Vite template with TypeScript)
- **Material UI (MUI v6)** (Modern design components with slot-based API)
- **React Router Dom** (Single Page Application routing)
- **Axios** (HTTP client with global credential configurations)

### DevOps & Infrastructure
- **Docker & Docker Compose** (Containerized PostgreSQL deployment)


## 📂 Project Architecture

```text
chat-project/
├── backend/
│   ├── src/                      # Source code
│   │   ├── auth.py               # Password hashing & JWT generation
│   │   ├── config.py             # Pydantic environment configuration
│   │   ├── crud.py               # Asynchronous database queries & seed scripts
│   │   ├── database.py           # Engine setup and AsyncSession generators
│   │   ├── main.py               # REST API and WebSocket connection manager
│   │   ├── models.py             # SQLAlchemy 2.0 declarative database models
│   │   ├── schemas.py            # Pydantic data validation schemas
│   │   └── websocket_manager.py  # Connection mapping and broadcasting logic
│   ├── migrations/               # Alembic database migrations history
│   ├── .env                      # Local environment secrets
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx          # Chat area & WebSocket handler
│   │   │   ├── Login.tsx         # Sign in interface
│   │   │   └── Register.tsx      # Registration interface
│   │   ├── api.ts                # Axios configuration with Vite Proxy base URL
│   │   ├── App.tsx               # Main routing and route guard setup
│   │   └── main.tsx
│   └── vite.config.ts            # Vite proxy settings for same-origin dev
├── docker-compose.yml            # Multi-container PostgreSQL state file
└── README.md
```


## ⚙️ Getting Started

### Prerequisites
Make sure you have the following installed on your machine:
- **Docker Desktop** (or Docker Daemon on Linux)
- **Node.js** (24+)
- **Python** (3.14+)
- **UV** (Rust-based package manager)


### Step 1: Initialize Database (PostgreSQL inside Docker)

1. Navigate to the root directory containing the `docker-compose.yml` file.
2. Spin up the PostgreSQL database container in the background:
   ```bash
   docker compose up -d
   ```


### Step 2: Configure & Start Backend (FastAPI)

1. Move to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create a local environment file `.env`:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASS=postgres_secure_password
   DB_NAME=chat_db
   ```
3. Initialize a virtual environment and install dependencies using **`uv`**:
   ```bash
   uv venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate

   uv pip install -r requirements.txt
   ```
4. Run Alembic database migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the ASGI development server:
   ```bash
   uvicorn src.main:app --reload
   ```
   The backend interactive documentation will be available at `http://127.0.0.1:8000/docs`.


### Step 3: Configure & Start Frontend (React + Vite)

1. Open a new terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install Node modules:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:5173`.


## 🛠️ Security Best Practices Implemented

- **XSS Mitigation:** Access tokens (JWT) are served and stored inside `HttpOnly` and `SameSite=Lax` cookies, preventing JavaScript-based access.
- **CSRF Defense:** Lax same-site policies ensure cookies are not sent during cross-site subrequests.
- **Async Database Architecture:** Connection pools and database reads/writes are entirely non-blocking, ensuring WebSockets do not halt during expensive SQL executions.
- **Modern Cryptography:** Passwords are hashed with `bcrypt`, protecting database dumps against reverse brute-force attacks.
