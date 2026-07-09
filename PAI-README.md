# PAI — Post-AI Startups Platform (MVP)

> The One-Stop Trust Network to Protect Original Startup Treatment Plans & Align Strategic Capital

---

## Project Structure

```
pai-mvp/
├── frontend/
│   └── index.html          ← Complete single-file frontend
└── backend/
    ├── server.js            ← Express entry point
    ├── .env.example         ← Copy to .env and fill in
    ├── package.json
    ├── models/
    │   ├── User.js          ← User (Pitcher / Fetcher)
    │   ├── Startup.js       ← Startup / Pitch (with IP protection)
    │   └── Message.js       ← Chat messages
    ├── routes/
    │   ├── auth.js          ← Send OTP, verify OTP, set role, T&C
    │   ├── startups.js      ← Register idea, list, browse, contact
    │   ├── subscriptions.js ← Plans, subscribe, status
    │   └── messages.js      ← Conversations, send, thread
    └── middleware/
        └── auth.js          ← JWT protect, requireRole, requireVerified
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/CSS/JS (no framework — single file) |
| Backend | Node.js + Express |
| Database | MongoDB + Mongoose |
| Auth | JWT + OTP via email |
| Email | Nodemailer (Mailtrap for dev, Gmail/SES for prod) |

---

## Setup & Run

### 1. Backend

```bash
cd backend
npm install

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your MongoDB URI, JWT secret, and email credentials

# Run in development (auto-reload)
npm run dev

# Run in production
npm start
```

**Backend runs on:** `http://localhost:5000`

### 2. Frontend

The frontend is a single HTML file. Open it in two ways:

**Option A — Just open the file:**
```bash
open frontend/index.html
# or double-click it in your file explorer
```

**Option B — Serve it (recommended for API calls):**
```bash
# Using Python
cd frontend && python3 -m http.server 3000

# Using Node
npx serve frontend -p 3000
```

**Frontend runs on:** `http://localhost:3002`

---

## Environment Variables (.env)

```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/pai_platform
JWT_SECRET=change_this_to_a_long_random_string
JWT_EXPIRES_IN=7d

# Email — use Mailtrap.io for free dev testing
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your_mailtrap_user
SMTP_PASS=your_mailtrap_pass
EMAIL_FROM=noreply@pai.in

FRONTEND_URL=http://localhost:3000
```

> **Dev mode:** When `NODE_ENV` is not `production`, the OTP is returned directly in the API response AND logged to the terminal — so you don't need a real email setup to test.

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/send-otp` | Send OTP to email |
| POST | `/api/auth/verify-otp` | Verify OTP, get JWT |
| POST | `/api/auth/set-role` | Set pitcher/fetcher |
| POST | `/api/auth/accept-tc` | Accept T&C |
| POST | `/api/auth/login` | Login with email+password |
| GET  | `/api/auth/me` | Get current user |

### Startups
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/startups` | Register idea (FREE, pitcher only) |
| GET  | `/api/startups/mine` | Pitcher's own startups |
| POST | `/api/startups/:id/list` | List publicly (paid) |
| GET  | `/api/startups` | Browse listed startups (fetcher) |
| GET  | `/api/startups/:id` | Single startup detail |
| POST | `/api/startups/:id/contact` | Use 5 credits to contact |
| POST | `/api/startups/:id/watchlist` | Toggle watchlist |
| GET  | `/api/startups/watchlist/mine` | Fetcher's watchlist |

### Subscriptions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/subscriptions/plans` | List all plans |
| POST | `/api/subscriptions/subscribe` | Subscribe to plan |
| GET  | `/api/subscriptions/status` | Current plan & credits |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/messages` | Send a message |
| GET  | `/api/messages/conversations` | All conversations |
| GET  | `/api/messages/:userId` | Thread with a user |

---

## User Flow (matches flowchart)

```
1. Enter email
2. OTP verification
3. Choose role: Pitcher or Fetcher
4. Accept T&C (mandatory compliance)
5a. Pitcher → Register idea FREE → Subscribe to list → Investors find you
5b. Fetcher → Browse FREE → Subscribe for credits → Contact founders (5 credits each)
6. Chat & negotiate
7. Deal closure + legal support
```

---

## Next Steps for Production

- [ ] Add real payment gateway (Razorpay for India)
- [ ] Add WebSockets for real-time chat (Socket.io)
- [ ] Add image/file upload for pitch decks (AWS S3 / Cloudinary)
- [ ] Add AI scoring via OpenAI / Anthropic API
- [ ] Deploy backend to Railway / Render / AWS
- [ ] Deploy frontend to Vercel / Netlify
- [ ] Add admin panel for compliance review
- [ ] Add push notifications

---

*PAI — Proposed by Devansh · © 2026*
