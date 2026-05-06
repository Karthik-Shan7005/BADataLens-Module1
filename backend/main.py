from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from db import engine, Base
import models.db_models  # ensure all models are registered before create_all
from routers import projects, query

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DataLens API", version="1.0.0", description="AI-powered survey insights platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(query.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "DataLens API"}
