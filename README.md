# PAI (Post-AI Startups Platform) — Trust Network & Deal Room

> The One-Stop Trust Network to Protect Original Startup Treatment Plans & Align Strategic Capital.

PAI is a security-first, high-performance platform designed for **Pitchers** (founders) to register, timestamp, and protect their intellectual property (startup ideas and treatment plans) and **Fetchers** (investors) to discover secure deals, evaluate pitches, and initiate direct communication.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3 + FastAPI |
| **Database** | SQLite + SQLAlchemy ORM |
| **Security / Auth** | JWT Session Keys (stored in secure HTTP-Only Cookies) |
| **Email Verification**| Email OTP (SMTP Server with console fallback for local dev) |
| **AI Scoring Engine** | Local heuristic-based business pitch analyzer |
| **Frontend** | Single-Page Application (HTML5 / Vanilla CSS / JavaScript) |

---

## 📂 Project Directory Structure

```
PAIVOULT/
├── static/                 ← Frontend single-page app directory
│   ├── index.html          ← Main dashboard, registration, and chat interface
│   └── style.css           ← Modern dashboard design system
├── prisma/                 ← Database directory
│   └── dev.db              ← Local SQLite database file
├── main.py                 ← FastAPI main entrypoint and API routes
├── models.py               ← SQLAlchemy database models (Users, Startups, Messages, Deals, etc.)
├── auth_utils.py           ← JWT generation, cookie-based session verification
├── ai_coach.py             ← Local business heuristic and AI insights analysis logic
├── mail_utils.py           ← OTP email delivery configuration
├── .env                    ← Environment variables (Database URL, JWT Secret, SMTP info)
├── .gitignore              ← Git ignore configuration
└── README.md               ← Project documentation (this file)
```

---

## 🚀 Getting Started

### 1. Install Dependencies

Ensure you have Python 3.9+ installed, then install the required Python libraries:

```bash
pip install fastapi uvicorn PyJWT sqlalchemy
```

### 2. Configure Environment Variables

Create or edit your `.env` file in the root directory:

```env
DATABASE_URL="file:./prisma/dev.db"
JWT_SECRET="super-secret-key-change-this-in-production"
PORT=3002

# SMTP Email Configuration (Optional - for sending actual OTP emails)
# SMTP_HOST="smtp.gmail.com"
# SMTP_PORT=587
# SMTP_USER="your-email@gmail.com"
# SMTP_PASS="your-app-password"
# SMTP_FROM='"PAI Security" <your-email@gmail.com>'
```

> **Note:** If SMTP variables are missing or left commented out, the platform runs in **Sandbox/Development Mode**—it will print the verification OTP directly to the terminal console so you can copy and paste it into the UI.

### 3. Run the Server

Start the development server:

```bash
python main.py
```

The server will initialize the SQLite database, apply the models schema (if not already initialized), and serve the application on:
- **Web App Dashboard:** [http://127.0.0.1:3002](http://127.0.0.1:3002)
- **Interactive OpenAPI Docs:** [http://127.0.0.1:3002/docs](http://127.0.0.1:3002/docs)

---

## 🔐 Core Workflows

### 1. Secure Authentication (OTP + JWT)
- Enter your email on the landing page.
- Receive a 4-digit OTP via email (or check terminal log if SMTP is not configured).
- Verify the OTP. The server issues a JWT token set as an `HttpOnly` secure cookie (`pai_session`).
- New users are granted 50 free credits automatically.

### 2. Pitcher (Founder) Journey
- **Onboarding:** Set role to **Pitcher** and accept the terms of service.
- **Register Startup:** Submit startup details (Name, Sector, Stage, Funding Target, Description, Treatment Plan).
- **IP Protection (Idea Vault):** Registering a startup generates an `IdeaVaultEntry` with a secure cryptographic SHA-256 content hash of the treatment plan, establishing proof-of-existence.
- **AI Coach Analysis:** Get immediate scores, business taxonomy feedback, gap analysis, and tailored roadmap steps from the built-in analyzer.

### 3. Fetcher (Investor) Journey
- **Onboarding:** Set role to **Fetcher** and fill out the Investor Profile (investment thesis, check size range, target sectors).
- **Browse & Filter:** Search and filter through public startups in the database.
- **Watchlist & Portfolio:** Keep track of interesting startups or log actual investment deals.
- **Secure Communication:** Pitch details remain locked. Investors use **5 credits** to establish contact, which notifies the Pitcher and opens a private chat room.

### 4. Direct Messaging & Deal Management
- An interactive, real-time chat module allows founders and investors to converse safely once contact is established.
- Investors can log deals, update transaction stages (`DISCOVERY`, `UNDER_REVIEW`, `LOI`, `CLOSED`), and track investment parameters directly.

---

*PAI — Secure Post-AI Startup Trust Network & Ecosystem*
