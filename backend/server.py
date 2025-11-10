from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    token: str
    user: dict

class Client(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None

class InvoiceItem(BaseModel):
    description: str
    quantity: float
    rate: float
    amount: float

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    invoice_number: str
    client_id: str
    client_name: str
    client_email: Optional[str] = None
    client_company: Optional[str] = None
    date: str
    due_date: str
    items: List[InvoiceItem]
    subtotal: float
    tax: float
    discount: float
    total: float
    status: str  # draft, sent, paid, overdue
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InvoiceCreate(BaseModel):
    client_id: str
    date: str
    due_date: str
    items: List[InvoiceItem]
    tax: float
    discount: float
    status: str
    notes: Optional[str] = None

class DashboardStats(BaseModel):
    total_revenue: float
    paid_amount: float
    pending_amount: float
    overdue_amount: float
    total_invoices: int
    paid_invoices: int
    pending_invoices: int
    overdue_invoices: int

# Auth routes
@api_router.post("/auth/signup", response_model=AuthResponse)
async def signup(user_data: UserSignup):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_access_token(user_id, user_data.email)
    return AuthResponse(
        token=token,
        user={"id": user_id, "email": user_data.email, "name": user_data.name}
    )

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user["id"], user["email"])
    return AuthResponse(
        token=token,
        user={"id": user["id"], "email": user["email"], "name": user["name"]}
    )

# Client routes
@api_router.post("/clients", response_model=Client)
async def create_client(client_data: ClientCreate, user_id: str = Depends(get_current_user)):
    client = Client(user_id=user_id, **client_data.model_dump())
    doc = client.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.clients.insert_one(doc)
    return client

@api_router.get("/clients", response_model=List[Client])
async def get_clients(user_id: str = Depends(get_current_user)):
    clients = await db.clients.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    for client in clients:
        if isinstance(client['created_at'], str):
            client['created_at'] = datetime.fromisoformat(client['created_at'])
    return clients

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, user_id: str = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id, "user_id": user_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if isinstance(client['created_at'], str):
        client['created_at'] = datetime.fromisoformat(client['created_at'])
    return client

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_data: ClientCreate, user_id: str = Depends(get_current_user)):
    result = await db.clients.update_one(
        {"id": client_id, "user_id": user_id},
        {"$set": client_data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return await get_client(client_id, user_id)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, user_id: str = Depends(get_current_user)):
    result = await db.clients.delete_one({"id": client_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Invoice routes
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate, user_id: str = Depends(get_current_user)):
    # Get client details
    client = await db.clients.find_one({"id": invoice_data.client_id, "user_id": user_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Generate invoice number
    count = await db.invoices.count_documents({"user_id": user_id})
    invoice_number = f"INV-{count + 1:05d}"
    
    # Calculate totals
    subtotal = sum(item.amount for item in invoice_data.items)
    total = subtotal + invoice_data.tax - invoice_data.discount
    
    invoice = Invoice(
        user_id=user_id,
        invoice_number=invoice_number,
        client_name=client["name"],
        client_email=client.get("email"),
        client_company=client.get("company"),
        subtotal=subtotal,
        total=total,
        **invoice_data.model_dump()
    )
    
    doc = invoice.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.invoices.insert_one(doc)
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(user_id: str = Depends(get_current_user)):
    invoices = await db.invoices.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for invoice in invoices:
        if isinstance(invoice['created_at'], str):
            invoice['created_at'] = datetime.fromisoformat(invoice['created_at'])
    return invoices

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str, user_id: str = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id, "user_id": user_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if isinstance(invoice['created_at'], str):
        invoice['created_at'] = datetime.fromisoformat(invoice['created_at'])
    return invoice

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, invoice_data: InvoiceCreate, user_id: str = Depends(get_current_user)):
    # Get client details
    client = await db.clients.find_one({"id": invoice_data.client_id, "user_id": user_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Calculate totals
    subtotal = sum(item.amount for item in invoice_data.items)
    total = subtotal + invoice_data.tax - invoice_data.discount
    
    update_data = invoice_data.model_dump()
    update_data.update({
        "client_name": client["name"],
        "client_email": client.get("email"),
        "client_company": client.get("company"),
        "subtotal": subtotal,
        "total": total
    })
    
    result = await db.invoices.update_one(
        {"id": invoice_id, "user_id": user_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return await get_invoice(invoice_id, user_id)

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, user_id: str = Depends(get_current_user)):
    result = await db.invoices.delete_one({"id": invoice_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": "Invoice deleted successfully"}

# Dashboard routes
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(user_id: str = Depends(get_current_user)):
    invoices = await db.invoices.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    total_revenue = sum(inv['total'] for inv in invoices)
    paid_amount = sum(inv['total'] for inv in invoices if inv['status'] == 'paid')
    pending_amount = sum(inv['total'] for inv in invoices if inv['status'] in ['sent', 'draft'])
    overdue_amount = sum(inv['total'] for inv in invoices if inv['status'] == 'overdue')
    
    return DashboardStats(
        total_revenue=total_revenue,
        paid_amount=paid_amount,
        pending_amount=pending_amount,
        overdue_amount=overdue_amount,
        total_invoices=len(invoices),
        paid_invoices=len([inv for inv in invoices if inv['status'] == 'paid']),
        pending_invoices=len([inv for inv in invoices if inv['status'] in ['sent', 'draft']]),
        overdue_invoices=len([inv for inv in invoices if inv['status'] == 'overdue'])
    )

@api_router.get("/dashboard/chart-data")
async def get_chart_data(user_id: str = Depends(get_current_user)):
    invoices = await db.invoices.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    # Monthly revenue data for line chart
    from collections import defaultdict
    monthly_revenue = defaultdict(float)
    
    for invoice in invoices:
        if invoice['status'] == 'paid':
            # Parse date string
            month_key = invoice['date'][:7]  # YYYY-MM format
            monthly_revenue[month_key] += invoice['total']
    
    # Sort and format for chart
    sorted_months = sorted(monthly_revenue.keys())
    revenue_data = [{
        "month": month,
        "revenue": monthly_revenue[month]
    } for month in sorted_months[-6:]]  # Last 6 months
    
    # Status distribution for pie chart
    status_counts = {
        "paid": len([inv for inv in invoices if inv['status'] == 'paid']),
        "sent": len([inv for inv in invoices if inv['status'] == 'sent']),
        "draft": len([inv for inv in invoices if inv['status'] == 'draft']),
        "overdue": len([inv for inv in invoices if inv['status'] == 'overdue'])
    }
    
    return {
        "revenue_trend": revenue_data,
        "status_distribution": status_counts
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
