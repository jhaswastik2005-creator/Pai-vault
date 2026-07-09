import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "User"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, default="PITCHER") # PITCHER, FETCHER, ADMIN
    kycStatus = Column(String, default="PENDING") # PENDING, VERIFIED, REJECTED
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    startups = relationship("Startup", back_populates="owner", cascade="all, delete-orphan")
    investorProfile = relationship("InvestorProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    creditLedger = relationship("CreditLedger", back_populates="user", cascade="all, delete-orphan")
    participations = relationship("MessageThreadParticipant", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="sender", cascade="all, delete-orphan")

class Startup(Base):
    __tablename__ = "Startup"

    id = Column(String, primary_key=True, default=generate_uuid)
    ownerId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    sector = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    description = Column(String, nullable=False)
    fundingTarget = Column(String, nullable=False)
    treatmentPlan = Column(String, nullable=False)
    isPublic = Column(Boolean, default=True)
    timestampedAt = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="startups")
    ideaVaultEntries = relationship("IdeaVaultEntry", back_populates="startup", cascade="all, delete-orphan")
    aiInsights = relationship("AIInsight", back_populates="startup", cascade="all, delete-orphan")
    watchlistedBy = relationship("Watchlist", back_populates="startup", cascade="all, delete-orphan")
    portfolioedBy = relationship("Portfolio", back_populates="startup", cascade="all, delete-orphan")
    messageThreads = relationship("MessageThread", back_populates="startup")

class InvestorProfile(Base):
    __tablename__ = "InvestorProfile"

    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    thesis = Column(String, nullable=True)
    checkSizeMin = Column(Float, nullable=True)
    checkSizeMax = Column(Float, nullable=True)
    sectors = Column(String, default="") # Comma-separated sectors

    # Relationships
    user = relationship("User", back_populates="investorProfile")
    deals = relationship("Deal", back_populates="investor", cascade="all, delete-orphan")
    watchlist = relationship("Watchlist", back_populates="investor", cascade="all, delete-orphan")
    portfolio = relationship("Portfolio", back_populates="investor", cascade="all, delete-orphan")

class IdeaVaultEntry(Base):
    __tablename__ = "IdeaVaultEntry"

    id = Column(String, primary_key=True, default=generate_uuid)
    startupId = Column(String, ForeignKey("Startup.id", ondelete="CASCADE"), nullable=False)
    contentHash = Column(String, nullable=False)
    documentUrl = Column(String, default="")
    protectedAt = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    startup = relationship("Startup", back_populates="ideaVaultEntries")

class Deal(Base):
    __tablename__ = "Deal"

    id = Column(String, primary_key=True, default=generate_uuid)
    startupId = Column(String, ForeignKey("Startup.id", ondelete="CASCADE"), nullable=False)
    investorId = Column(String, ForeignKey("InvestorProfile.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String, default="DISCOVERY") # DISCOVERY, UNDER_REVIEW, LOI, CLOSED
    amount = Column(Float, nullable=True)
    status = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    startup = relationship("Startup")
    investor = relationship("InvestorProfile", back_populates="deals")
    messageThreads = relationship("MessageThread", back_populates="deal")

class MessageThread(Base):
    __tablename__ = "MessageThread"

    id = Column(String, primary_key=True, default=generate_uuid)
    startupId = Column(String, ForeignKey("Startup.id", ondelete="SET NULL"), nullable=True)
    dealId = Column(String, ForeignKey("Deal.id", ondelete="SET NULL"), nullable=True)
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    startup = relationship("Startup", back_populates="messageThreads")
    deal = relationship("Deal", back_populates="messageThreads")
    participants = relationship("MessageThreadParticipant", back_populates="thread", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")

class MessageThreadParticipant(Base):
    __tablename__ = "MessageThreadParticipant"

    id = Column(String, primary_key=True, default=generate_uuid)
    threadId = Column(String, ForeignKey("MessageThread.id", ondelete="CASCADE"), nullable=False)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("threadId", "userId", name="uq_thread_user"),
    )

    # Relationships
    thread = relationship("MessageThread", back_populates="participants")
    user = relationship("User", back_populates="participations")

class Message(Base):
    __tablename__ = "Message"

    id = Column(String, primary_key=True, default=generate_uuid)
    threadId = Column(String, ForeignKey("MessageThread.id", ondelete="CASCADE"), nullable=False)
    senderId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    thread = relationship("MessageThread", back_populates="messages")
    sender = relationship("User", back_populates="messages")

class AIInsight(Base):
    __tablename__ = "AIInsight"

    id = Column(String, primary_key=True, default=generate_uuid)
    startupId = Column(String, ForeignKey("Startup.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False) # e.g. PITCH_SCORE
    payload = Column(JSON, nullable=False)
    generatedAt = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    startup = relationship("Startup", back_populates="aiInsights")

class Subscription(Base):
    __tablename__ = "Subscription"

    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    tier = Column(String, default="FREE") # FREE, PRO, STARTUP
    stripeCustomerId = Column(String, nullable=True)
    stripeSubscriptionId = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

class CreditLedger(Base):
    __tablename__ = "CreditLedger"

    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    delta = Column(Integer, nullable=False) # positive for top-up, negative for usage
    reason = Column(String, nullable=False)
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="creditLedger")

class Watchlist(Base):
    __tablename__ = "Watchlist"

    id = Column(String, primary_key=True, default=generate_uuid)
    investorId = Column(String, ForeignKey("InvestorProfile.id", ondelete="CASCADE"), nullable=False)
    startupId = Column(String, ForeignKey("Startup.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("investorId", "startupId", name="uq_watchlist_investor_startup"),
    )

    # Relationships
    investor = relationship("InvestorProfile", back_populates="watchlist")
    startup = relationship("Startup", back_populates="watchlistedBy")

class Portfolio(Base):
    __tablename__ = "Portfolio"

    id = Column(String, primary_key=True, default=generate_uuid)
    investorId = Column(String, ForeignKey("InvestorProfile.id", ondelete="CASCADE"), nullable=False)
    startupId = Column(String, ForeignKey("Startup.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("investorId", "startupId", name="uq_portfolio_investor_startup"),
    )

    # Relationships
    investor = relationship("InvestorProfile", back_populates="portfolio")
    startup = relationship("Startup", back_populates="portfolioedBy")

class Document(Base):
    __tablename__ = "Document"

    id = Column(String, primary_key=True, default=generate_uuid)
    startupId = Column(String, ForeignKey("Startup.id", ondelete="CASCADE"), nullable=True)
    uploaderId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    type = Column(String, nullable=False) # PitchDeck, FinancialModel, etc.
    uploadedAt = Column(DateTime, default=datetime.datetime.utcnow)

class AdminAction(Base):
    __tablename__ = "AdminAction"

    id = Column(String, primary_key=True, default=generate_uuid)
    adminId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)
    targetId = Column(String, nullable=True)
    targetType = Column(String, nullable=True)
    details = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)
