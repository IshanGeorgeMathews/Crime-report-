import app.core.paths  # Configures Python path for importing existing modules
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from app.config import settings

# Propagate pydantic config settings to os.environ for non-pydantic modules (like translation.py)
os.environ["DISABLE_INDIC_TRANS"] = getattr(settings, "DISABLE_INDIC_TRANS", "0")
os.environ["TRANSLATION_MODEL_PATH"] = getattr(settings, "TRANSLATION_MODEL_PATH", "")

from app.db.session import engine, Base, AsyncSessionLocal
from app.db.models import User
from app.core import security
from app.api.routes import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def on_startup():
    """App startup lifecycle hook: Creates tables and seeds default user accounts."""
    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("[DB Initialization] SQL tables created successfully.")
        
    # Seed default user accounts if empty
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        if not users:
            print("[DB Initialization] Seeding default user registry...")
            
            # 1. Admin
            admin_user = User(
                username="admin",
                password_hash=security.get_password_hash("admin"),
                full_name="System Administrator",
                role="admin",
                district="PKD",
                is_active=True
            )
            db.add(admin_user)
            
            # 2. Supervisor
            supervisor_user = User(
                username="supervisor",
                password_hash=security.get_password_hash("supervisor"),
                full_name="CI Suresh Kumar",
                role="supervisor",
                district="PKD",
                is_active=True
            )
            db.add(supervisor_user)
            
            # 3. Analyst
            analyst_user = User(
                username="analyst",
                password_hash=security.get_password_hash("analyst"),
                full_name="SI Pradeep Kumar",
                role="analyst",
                district="PKD",
                is_active=True
            )
            db.add(analyst_user)
            
            # 4. Viewer
            viewer_user = User(
                username="viewer",
                password_hash=security.get_password_hash("viewer"),
                full_name="Officer Jacob Varghese",
                role="viewer",
                district="PKD",
                is_active=True
            )
            db.add(viewer_user)
            
            await db.commit()
            print("[DB Initialization] Default users seeded successfully.")
        else:
            print("[DB Initialization] Users registry already populated. Seed skipped.")
            
    # Warmup Qdrant collection setup
    try:
        from app.services.qdrant_service import QdrantService
        qs = QdrantService()
        qs._init_qdrant()
    except Exception as e:
        print(f"[DB Initialization] Qdrant auto-initialization skipped: {e}")
        
    print("[Main Application] FastAPI Server startup sequence finished.")
