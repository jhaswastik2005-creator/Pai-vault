import os
import random
import datetime
import hashlib
from typing import List
from fastapi import FastAPI, Request, Response, HTTPException, status, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session

# Import our SQLAlchemy models and helper utilities
from models import (
    Base, User, Startup, InvestorProfile, Deal, MessageThread, 
    MessageThreadParticipant, Message, AIInsight, Subscription, CreditLedger, Watchlist, Portfolio
)
from auth_utils import create_token, get_current_user_session, COOKIE_NAME
from ai_coach import analyze_pitch
from mail_utils import send_otp_email

# Initialize DB connection (use absolute path mapping to ensure we target prisma/dev.db)
db_dir = os.path.join(os.getcwd(), "prisma")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "dev.db")
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# In-memory OTP cache storage: { email: { "otp": "code", "expires_at": datetime } }
otp_store = {}

app = FastAPI(title="PAI Platform - Python Backend", version="1.0.0")

# Enable CORS for local cross-origin calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Session Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper to verify active logged-in user
def get_authenticated_user(request: Request, db: Session = Depends(get_db)):
    session = get_current_user_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized session")
    
    user = db.query(User).filter(User.id == session["id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User session invalid")
    return user

# Helper to sum user credits
def calculate_user_credits(db: Session, user_id: str) -> int:
    result = db.query(func.sum(CreditLedger.delta)).filter(CreditLedger.userId == user_id).scalar()
    return int(result) if result is not None else 0


# ── AUTHENTICATION ENDPOINTS ──

@app.post("/api/auth/send-otp")
async def send_otp(request: Request):
    body = await request.json()
    email = body.get("email", "").lower().strip()
    
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email address is required")
    
    # Generate 4-digit code
    otp = f"{random.randint(1000, 9999)}"
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    otp_store[email] = {"otp": otp, "expires_at": expiry}
    
    # Dispatch email
    sent = send_otp_email(email, otp)
    
    # Echo otp in response for dev environment only if SMTP is skipped
    is_dev = os.getenv("NODE_ENV") != "production"
    response_data = {"success": True, "message": "OTP sent successfully"}
    if is_dev and not sent:
        response_data["devOtp"] = otp
        
    return response_data

@app.post("/api/auth/verify-otp")
async def verify_otp(request: Request, response: Response, db: Session = Depends(get_db)):
    body = await request.json()
    email = body.get("email", "").lower().strip()
    otp = body.get("otp", "").strip()
    
    if not email or not otp:
        raise HTTPException(status_code=400, detail="Email and OTP code are required")
    
    # Validate OTP
    record = otp_store.get(email)
    if not record:
        raise HTTPException(status_code=400, detail="OTP not sent or expired")
    
    if datetime.datetime.utcnow() > record["expires_at"]:
        otp_store.pop(email, None)
        raise HTTPException(status_code=400, detail="OTP expired")
        
    if record["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    # Consume OTP
    otp_store.pop(email, None)
    
    # Check if User exists
    user = db.query(User).filter(User.email == email).first()
    is_new = False
    
    if not user:
        is_new = True
        user = User(email=email, role="PITCHER")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create default FREE Subscription
        sub = Subscription(userId=user.id, tier="FREE", status="ACTIVE")
        db.add(sub)
        
        # Feed 50 free credits
        ledger = CreditLedger(userId=user.id, delta=50, reason="Onboarding free credits")
        db.add(ledger)
        db.commit()
    
    # Generate and set session token in HttpOnly cookie
    token = create_token(user.id, user.email, user.role)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False, # Set to True in production
        samesite="lax",
        max_age=60*60*24*7 # 7 days
    )
    
    return {
        "success": True,
        "user": {"id": user.id, "email": user.email, "role": user.role},
        "isNewUser": is_new
    }

@app.post("/api/auth/set-role")
async def set_role(request: Request, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    body = await request.json()
    role = body.get("role", "").upper().strip()
    
    if role not in ["PITCHER", "FETCHER"]:
        raise HTTPException(status_code=400, detail="Invalid role selection")
        
    user.role = role
    db.commit()
    
    # If Fetcher, instantiate Investor Profile if it doesn't exist
    if role == "FETCHER":
        profile = db.query(InvestorProfile).filter(InvestorProfile.userId == user.id).first()
        if not profile:
            profile = InvestorProfile(
                userId=user.id,
                thesis="Early-stage AI/ML and digital solutions",
                checkSizeMin=10000,
                checkSizeMax=250000,
                sectors="AI/ML,FinTech,HealthTech,EdTech,AgriTech"
            )
            db.add(profile)
            db.commit()
            
    # Update token to contain new role
    token = create_token(user.id, user.email, user.role)
    # We must return response to set cookie, but wait, setting it on the Response is cleaner.
    # Instead, we just respond with user object and trust the client session refreshes or updates.
    return {
        "success": True,
        "user": {"id": user.id, "email": user.email, "role": user.role}
    }

@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"success": True, "message": "Session cleared"}

@app.get("/api/auth/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    session = get_current_user_session(request)
    if not session:
        return {"authenticated": False}
        
    user = db.query(User).filter(User.id == session["id"]).first()
    if not user:
        return {"authenticated": False}
        
    credits = calculate_user_credits(db, user.id)
    sub = db.query(Subscription).filter(Subscription.userId == user.id).first()
    sub_tier = sub.tier if sub else "FREE"
    
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "kycStatus": user.kycStatus,
            "credits": credits,
            "subscriptionTier": sub_tier
        }
    }


# ── STARTUPS & VAULT ENDPOINTS ──

@app.get("/api/startups")
async def get_startups(
    request: Request, 
    sector: str = None, 
    stage: str = None, 
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user)
):
    if user.role == "PITCHER":
        # Pitcher views their own registered startups
        items = db.query(Startup).filter(Startup.ownerId == user.id).all()
        startups_list = []
        for s in items:
            vault = db.query(IdeaVaultEntry).filter(IdeaVaultEntry.startupId == s.id).order_by(IdeaVaultEntry.protectedAt.desc()).first()
            insight = db.query(AIInsight).filter(AIInsight.startupId == s.id, AIInsight.type == "PITCH_SCORE").order_by(AIInsight.generatedAt.desc()).first()
            
            startups_list.append({
                "id": s.id,
                "name": s.name,
                "sector": s.sector,
                "stage": s.stage,
                "description": s.description,
                "fundingTarget": s.fundingTarget,
                "treatmentPlan": s.treatmentPlan,
                "isPublic": s.isPublic,
                "ideaHash": vault.contentHash if vault else None,
                "aiScore": insight.payload if insight else None,
                "isUnlocked": True
            })
        return {"startups": startups_list}
        
    else:
        # Fetcher browsing startups feed
        profile = db.query(InvestorProfile).filter(InvestorProfile.userId == user.id).first()
        if not profile:
            return {"startups": []}
            
        query = db.query(Startup).filter(Startup.isPublic == True)
        if sector and sector != "All sectors":
            query = query.filter(Startup.sector == sector)
        if stage and stage != "All stages":
            query = query.filter(Startup.stage == stage)
            
        items = query.all()
        startups_list = []
        for s in items:
            # Check if this fetcher has unlocked this startup
            has_deal = db.query(Deal).filter(Deal.startupId == s.id, Deal.investorId == profile.id).first()
            is_unlocked = bool(has_deal)
            
            # Check if watchlisted
            is_starred = db.query(Watchlist).filter(Watchlist.investorId == profile.id, Watchlist.startupId == s.id).first()
            
            startups_list.append({
                "id": s.id,
                "name": s.name,
                "sector": s.sector,
                "stage": s.stage,
                "description": s.description,
                "fundingTarget": s.fundingTarget,
                "isUnlocked": is_unlocked,
                "isWatchlisted": bool(is_starred),
                "founderEmail": s.owner.email if is_unlocked else "••••••@paivoult.com",
                "treatmentPlan": s.treatmentPlan if is_unlocked else "🔒 This content is locked. Spend 5 credits to unlock the treatment plan."
            })
        return {"startups": startups_list}

@app.post("/api/startups")
async def create_startup(request: Request, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    if user.role != "PITCHER":
        raise HTTPException(status_code=403, detail="Only founders/pitchers can register ideas")
        
    body = await request.json()
    name = body.get("name", "").strip()
    sector = body.get("sector", "").strip()
    stage = body.get("stage", "").strip()
    description = body.get("description", "").strip()
    funding_target = body.get("fundingTarget", "").strip()
    treatment_plan = body.get("treatmentPlan", "").strip()
    
    if not name or not sector or not stage or not description or not funding_target or not treatment_plan:
        raise HTTPException(status_code=400, detail="All fields are required")
        
    # Create Startup
    startup = Startup(
        ownerId=user.id,
        name=name,
        sector=sector,
        stage=stage,
        description=description,
        fundingTarget=funding_target,
        treatmentPlan=treatment_plan,
        isPublic=True, # default to public
        timestampedAt=datetime.datetime.utcnow()
    )
    db.add(startup)
    db.commit()
    db.refresh(startup)
    
    # Generate SHA-256 digital proof
    raw_payload = f"{description}|{treatment_plan}|{startup.id}"
    content_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    
    vault_entry = IdeaVaultEntry(
        startupId=startup.id,
        contentHash=content_hash,
        documentUrl=""
    )
    db.add(vault_entry)
    
    # Run AI evaluation and save insight
    analysis = analyze_pitch(name, sector, stage, description, treatment_plan)
    ai_insight = AIInsight(
        startupId=startup.id,
        type="PITCH_SCORE",
        payload=analysis
    )
    db.add(ai_insight)
    db.commit()
    
    return {
        "success": True,
        "startup": {
            "id": startup.id,
            "name": startup.name,
            "ideaHash": content_hash,
            "aiScore": analysis
        }
    }

@app.get("/api/startups/{startup_id}")
async def get_startup_details(
    startup_id: str, 
    user: User = Depends(get_authenticated_user), 
    db: Session = Depends(get_db)
):
    startup = db.query(Startup).filter(Startup.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
        
    vault = db.query(IdeaVaultEntry).filter(IdeaVaultEntry.startupId == startup.id).order_by(IdeaVaultEntry.protectedAt.desc()).first()
    insight = db.query(AIInsight).filter(AIInsight.startupId == startup.id, AIInsight.type == "PITCH_SCORE").order_by(AIInsight.generatedAt.desc()).first()
    
    if user.role == "PITCHER":
        if startup.ownerId != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        return {
            "success": True,
            "startup": {
                "id": startup.id,
                "name": startup.name,
                "sector": startup.sector,
                "stage": startup.stage,
                "description": startup.description,
                "fundingTarget": startup.fundingTarget,
                "treatmentPlan": startup.treatmentPlan,
                "isPublic": startup.isPublic,
                "isUnlocked": True,
                "ideaHash": vault.contentHash if vault else None,
                "aiScore": insight.payload if insight else None
            }
        }
    else:
        # Fetcher
        profile = db.query(InvestorProfile).filter(InvestorProfile.userId == user.id).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Investor profile missing")
            
        has_deal = db.query(Deal).filter(Deal.startupId == startup.id, Deal.investorId == profile.id).first()
        is_unlocked = bool(has_deal)
        
        is_starred = db.query(Watchlist).filter(Watchlist.investorId == profile.id, Watchlist.startupId == startup.id).first()
        
        return {
            "success": True,
            "startup": {
                "id": startup.id,
                "name": startup.name,
                "sector": startup.sector,
                "stage": startup.stage,
                "description": startup.description,
                "fundingTarget": startup.fundingTarget,
                "isUnlocked": is_unlocked,
                "isWatchlisted": bool(is_starred),
                "founderEmail": startup.owner.email if is_unlocked else "••••••@paivoult.com",
                "treatmentPlan": startup.treatmentPlan if is_unlocked else "🔒 Locked details.",
                "ideaHash": vault.contentHash if is_unlocked and vault else None,
                "aiScore": insight.payload if is_unlocked and insight else None
            }
        }

@app.patch("/api/startups/{startup_id}")
async def update_startup_visibility(
    startup_id: str,
    request: Request,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    if user.role != "PITCHER":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    startup = db.query(Startup).filter(Startup.id == startup_id).first()
    if not startup or startup.ownerId != user.id:
        raise HTTPException(status_code=404, detail="Startup not found")
        
    body = await request.json()
    is_public = body.get("isPublic")
    
    if is_public is not None:
        startup.isPublic = bool(is_public)
        db.commit()
        
    return {"success": True, "isPublic": startup.isPublic}


# ── WATCHLIST & CONTACT UNLOCKS ──

@app.post("/api/startups/watchlist")
async def toggle_watchlist(request: Request, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    if user.role != "FETCHER":
        raise HTTPException(status_code=403, detail="Only investors can watchlist startups")
        
    profile = db.query(InvestorProfile).filter(InvestorProfile.userId == user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Investor profile not found")
        
    body = await request.json()
    startup_id = body.get("startupId")
    
    if not startup_id:
        raise HTTPException(status_code=400, detail="Startup ID is required")
        
    entry = db.query(Watchlist).filter(Watchlist.investorId == profile.id, Watchlist.startupId == startup_id).first()
    
    if entry:
        db.delete(entry)
        db.commit()
        return {"success": True, "watchlisted": False}
    else:
        new_entry = Watchlist(investorId=profile.id, startupId=startup_id)
        db.add(new_entry)
        db.commit()
        return {"success": True, "watchlisted": True}

@app.post("/api/startups/contact")
async def unlock_contact(request: Request, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    if user.role != "FETCHER":
        raise HTTPException(status_code=403, detail="Only investors can contact founders")
        
    profile = db.query(InvestorProfile).filter(InvestorProfile.userId == user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Investor profile not found")
        
    body = await request.json()
    startup_id = body.get("startupId")
    
    if not startup_id:
        raise HTTPException(status_code=400, detail="Startup ID is required")
        
    startup = db.query(Startup).filter(Startup.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
        
    # Check if already unlocked
    deal = db.query(Deal).filter(Deal.startupId == startup.id, Deal.investorId == profile.id).first()
    if deal:
        # Re-fetch thread if active
        thread = db.query(MessageThread).filter(MessageThread.dealId == deal.id).first()
        return {"success": True, "message": "Already unlocked", "threadId": thread.id if thread else None}
        
    # Check credit balance
    balance = calculate_user_credits(db, user.id)
    if balance < 5:
        raise HTTPException(status_code=400, detail="Insufficient credits. Spend 5 credits to unlock.")
        
    # Deduct 5 credits from ledger
    ledger = CreditLedger(userId=user.id, delta=-5, reason=f"Unlocked startup contact for {startup.name}")
    db.add(ledger)
    
    # Create Deal unlock mapping
    new_deal = Deal(startupId=startup.id, investorId=profile.id, stage="DISCOVERY")
    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)
    
    # Create Message Thread
    thread = MessageThread(startupId=startup.id, dealId=new_deal.id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    
    # Add thread participants
    p1 = MessageThreadParticipant(threadId=thread.id, userId=user.id)
    p2 = MessageThreadParticipant(threadId=thread.id, userId=startup.ownerId)
    db.add(p1)
    db.add(p2)
    
    # Send introductory text
    intro = Message(
        threadId=thread.id,
        senderId=user.id,
        content=f"Hello founder! I just unlocked your startup contacts for '{startup.name}'. Let's start discussing due diligence!"
    )
    db.add(intro)
    db.commit()
    
    return {
        "success": True,
        "message": "Founder details unlocked successfully",
        "threadId": thread.id
    }


# ── BILLING & RECHARGES ENDPOINTS ──

@app.post("/api/subscriptions")
async def simulated_checkout(request: Request, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    body = await request.json()
    tier = body.get("tier", "").upper().strip()
    
    if tier not in ["PRO", "STARTUP"]:
        raise HTTPException(status_code=400, detail="Invalid billing tier")
        
    credits_delta = 100 if tier == "PRO" else 200
    
    # Update user Subscription
    sub = db.query(Subscription).filter(Subscription.userId == user.id).first()
    if sub:
        sub.tier = tier
    else:
        sub = Subscription(userId=user.id, tier=tier, status="ACTIVE")
        db.add(sub)
        
    # Credit top-up
    ledger = CreditLedger(userId=user.id, delta=credits_delta, reason=f"Simulated subscription topup: {tier} tier")
    db.add(ledger)
    db.commit()
    
    return {"success": True, "tier": tier, "creditsAdded": credits_delta}


# ── SECURE CHATROOM MESSAGES ENDPOINTS ──

@app.get("/api/messages")
async def get_messages(
    request: Request,
    threadId: str = None,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    if threadId:
        # Get message history in single thread
        # Verify participation
        participant = db.query(MessageThreadParticipant).filter(
            MessageThreadParticipant.threadId == threadId,
            MessageThreadParticipant.userId == user.id
        ).first()
        
        if not participant:
            raise HTTPException(status_code=403, detail="Access denied to conversation")
            
        msgs = db.query(Message).filter(Message.threadId == threadId).order_by(Message.createdAt.asc()).all()
        history = []
        for m in msgs:
            history.append({
                "id": m.id,
                "senderId": m.senderId,
                "content": m.content,
                "createdAt": m.createdAt,
                "sender": {"email": m.sender.email}
            })
        return {"messages": history}
        
    else:
        # Get list of all conversation threads
        participations = db.query(MessageThreadParticipant).filter(MessageThreadParticipant.userId == user.id).all()
        threads_list = []
        
        for p in participations:
            thread = p.thread
            # Find the other participant in this thread
            other = db.query(MessageThreadParticipant).filter(
                MessageThreadParticipant.threadId == thread.id,
                MessageThreadParticipant.userId != user.id
            ).first()
            
            if not other:
                continue
                
            last_msg = db.query(Message).filter(Message.threadId == thread.id).order_by(Message.createdAt.desc()).first()
            startup_name = thread.startup.name if thread.startup else "Unknown pitch"
            
            threads_list.append({
                "id": thread.id,
                "startupName": startup_name,
                "otherUser": {"email": other.user.email},
                "lastMessage": {
                    "content": last_msg.content,
                    "createdAt": last_msg.createdAt
                } if last_msg else None
            })
        return {"threads": threads_list}

@app.post("/api/messages")
async def post_message(request: Request, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    body = await request.json()
    thread_id = body.get("threadId")
    content = body.get("content", "").strip()
    
    if not thread_id or not content:
        raise HTTPException(status_code=400, detail="Thread ID and message body content are required")
        
    participant = db.query(MessageThreadParticipant).filter(
        MessageThreadParticipant.threadId == thread_id,
        MessageThreadParticipant.userId == user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Unauthorized thread participant")
        
    # Write Message
    msg = Message(threadId=thread_id, senderId=user.id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    return {
        "success": True,
        "message": {
            "id": msg.id,
            "senderId": msg.senderId,
            "content": msg.content,
            "createdAt": msg.createdAt,
            "sender": {"email": user.email}
        }
    }


# ── STATIC FRONTEND SPA FALLBACK ──

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    # API paths yield actual 404 JSON
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"error": "Endpoint not found"})
        
    # SPA paths (onboarding, pitcher, fetcher, etc.) yield index.html to allow client router handling
    index_path = os.path.join(os.getcwd(), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>PAI Platform Webpage Loading...</h1>", status_code=404)

# Mount the static files directory on the root
# Note: Mount this at the very bottom so it doesn't intercept API path requests
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Start dev server on port 3002
    uvicorn.run("main:app", host="127.0.0.1", port=3002, reload=True)
