from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, notion, graph

app = FastAPI(
    title="Notion Relation View API",
    description="API for visualizing Notion page relations",
    version="0.0.1",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(notion.router)
app.include_router(graph.router)


@app.get("/")
async def root():
    return {"message": "Notion Relation View API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
