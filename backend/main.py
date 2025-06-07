from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import List, Optional
from datetime import date
import os

os.makedirs("/data", exist_ok=True)

app = FastAPI()

# Database setup
engine = create_engine("sqlite:////data/updates.db")

class PackageUpdate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hostname: str
    os: str
    date: date
    name: str
    old_version: str
    new_version: str

class UpdateIn(SQLModel):
    hostname: str
    os: str
    date: date
    updated_packages: List[dict]

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production!
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/report")
def report_update(update: UpdateIn):
    with Session(engine) as session:
        for pkg in update.updated_packages:
            upd = PackageUpdate(
                hostname=update.hostname,
                os=update.os,
                date=update.date,
                name=pkg["name"],
                old_version=pkg["old_version"],
                new_version=pkg["new_version"]
            )
            session.add(upd)
        session.commit()
    return {"status": "ok"}

@app.get("/hosts")
def list_hosts():
    with Session(engine) as session:
        result = session.exec(select(PackageUpdate.hostname).distinct()).all()
        return {"hosts": result}

@app.get("/history/{hostname}")
def host_history(hostname: str):
    with Session(engine) as session:
        result = session.exec(
            select(PackageUpdate).where(PackageUpdate.hostname == hostname)
        ).all()
        return result

@app.get("/last-updates")
def last_updates():
    with Session(engine) as session:
        hosts = session.exec(select(PackageUpdate.hostname).distinct()).all()
        data = []
        for host in hosts:
            update = session.exec(
                select(PackageUpdate)
                .where(PackageUpdate.hostname == host)
                .order_by(PackageUpdate.date.desc())
            ).first()
            if update:
                data.append({
                    "hostname": host,
                    "os": update.os,
                    "last_update": update.date
                })
        return data
