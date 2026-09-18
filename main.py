from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from enum import Enum
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from starlette.middleware.sessions import SessionMiddleware

from database import engine, Base, SessionLocal
from models import Fault
from user_models import User


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="University Fault Reporting Event Service",
    description="Cloud-based API for reporting university equipment faults",
    version="1.0.0"
)


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET")
)


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class FaultReport(BaseModel):
    equipment_id: str = Field(min_length=3, max_length=32)
    location: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=5, max_length=500)
    severity: Severity


password_hash = PasswordHash.recommended()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_staff(request: Request):
    role = request.session.get("role")

    if role not in ["technician", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied: technician or admin role required"
        )

    return role


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "University Fault Reporting Event Service"
    }


@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    user = db.query(User).filter(User.username == username).first()

    if user is None or not password_hash.verify(password, user.password):
        return {
            "status": "error",
            "message": "Invalid username or password"
        }

    request.session["username"] = user.username
    request.session["role"] = user.role

    return {
        "status": "success",
        "message": "Login successful",
        "username": user.username,
        "role": user.role
    }


@app.post("/logout")
def logout(request: Request):
    request.session.clear()

    return {
        "status": "success",
        "message": "Logout successful"
    }


@app.post("/faults")
def create_fault(
    fault: FaultReport,
    request: Request,
    db: Session = Depends(get_db)
):
    username = request.session.get("username")

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    if fault.severity == Severity.high:
        priority = "P1"
    elif fault.severity == Severity.medium:
        priority = "P2"
    else:
        priority = "P3"

    new_fault = Fault(
        equipment_id=fault.equipment_id,
        location=fault.location,
        description=fault.description,
        severity=fault.severity.value,
        priority=priority,
        reporter_id=username,
        status="open"
    )

    db.add(new_fault)
    db.commit()
    db.refresh(new_fault)

    return {
        "status": "success",
        "message": "Fault report received",
        "fault_id": new_fault.id,
        "equipment_id": new_fault.equipment_id,
        "location": new_fault.location,
        "description": new_fault.description,
        "severity": new_fault.severity,
        "priority": new_fault.priority,
        "reporter_id": new_fault.reporter_id,
        "fault_status": new_fault.status,
        "created_at": new_fault.created_at
    }


@app.get("/faults")
def get_faults(
    request: Request,
    db: Session = Depends(get_db)
):
    require_staff(request)

    faults = db.query(Fault).all()

    return {
        "status": "success",
        "count": len(faults),
        "faults": [
            {
                "fault_id": fault.id,
                "equipment_id": fault.equipment_id,
                "location": fault.location,
                "description": fault.description,
                "severity": fault.severity,
                "priority": fault.priority,
                "reporter_id": fault.reporter_id,
                "status": fault.status,
                "created_at": fault.created_at
            }
            for fault in faults
        ]
    }


@app.put("/faults/{fault_id}/status")
def update_fault_status(
    fault_id: int,
    status: str,
    request: Request,
    db: Session = Depends(get_db)
):
    require_staff(request)

    fault = db.query(Fault).filter(Fault.id == fault_id).first()

    if fault is None:
        return {
            "status": "error",
            "message": "Fault not found"
        }

    allowed_statuses = ["open", "in_progress", "resolved"]

    if status not in allowed_statuses:
        return {
            "status": "error",
            "message": "Invalid status",
            "allowed_statuses": allowed_statuses
        }

    fault.status = status

    db.commit()
    db.refresh(fault)

    return {
        "status": "success",
        "message": "Fault status updated",
        "fault_id": fault.id,
        "new_status": fault.status
    }


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/dashboard")
def dashboard(request: Request):
    require_staff(request)
    return FileResponse("static/dashboard.html")
