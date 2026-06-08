import app.core.paths  # Configures Python path for importing existing modules
import os
import re
import uuid
import shutil
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sse_starlette.sse import EventSourceResponse
import asyncio

from app.config import settings
from app.db.session import get_db
from app.db.models import User, Job, JobEvent, Report, ReportItem, Profile, ProfileCase, ProfileRelation, ProfileActivity
from app.core import security
from app.dependencies import get_current_user, require_analyst, require_supervisor, require_admin, require_viewer
from app.schemas import (
    UserLogin, UserResponse, TokenResponse, ChangePassword,
    UserCreate, UserUpdate, UserListItem,
    JobResponse, ReportResponse, ReportDetailResponse, ReportItemResponse,
    ProfileResponse, ProfileDetailResponse, SearchRequest, SearchResultResponse,
    GraphQueryResponse, GraphNodeResponse, GraphEdgeResponse, GnnRecommendationResponse,
    ApiResponse
)
from app.services.consolidation_service import ConsolidationService
from app.services.profile_service import ProfileService
from app.services.graph_service import GraphService
from app.services.qdrant_service import QdrantService
from app.services.ner_service import NERService

router = APIRouter()
consolidation_service = ConsolidationService()
profile_service = ProfileService()
graph_service = GraphService()
qdrant_service = QdrantService()
ner_service = NERService()

# --- Auth Endpoints ---

@router.post("/auth/login")
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """User login endpoint returning JWT token and user details."""
    result = await db.execute(select(User).filter(User.username == login_data.username))
    user = result.scalars().first()
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    access_token = security.create_access_token(
        subject=user.id,
        role=user.role,
        district=user.district
    )
    
    user_res = UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        district=user.district
    )
    return {"success": True, "data": {"user": user_res, "token": access_token}}

@router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Fetch current authenticated user profile."""
    user_res = UserResponse(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
        district=current_user.district
    )
    return {"success": True, "data": user_res}

@router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint (no-op in stateless JWT, audited)."""
    return {"success": True, "message": "Successfully logged out"}

@router.post("/auth/change-password")
async def change_password(
    payload: ChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change own password (any authenticated user)."""
    if not security.verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    current_user.password_hash = security.get_password_hash(payload.new_password)
    await db.commit()
    return {"success": True, "message": "Password changed successfully"}

# --- Admin User Management Endpoints ---

@router.get("/admin/users")
async def list_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    """List all users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    res_list = []
    for u in users:
        res_list.append(UserListItem(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            role=u.role,
            district=u.district,
            is_active=u.is_active,
            last_login_at=u.last_login_at,
            created_at=u.created_at
        ))
    return {"success": True, "data": res_list}

@router.post("/admin/users")
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new user (admin only)."""
    # Check for duplicate username
    existing = await db.execute(select(User).filter(User.username == payload.username))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' already exists"
        )
    # Validate role
    valid_roles = ["admin", "supervisor", "analyst", "viewer"]
    role = payload.role.lower()
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {payload.role}. Must be one of: {valid_roles}"
        )
    new_user = User(
        username=payload.username,
        password_hash=security.get_password_hash(payload.password),
        full_name=payload.fullName,
        role=role,
        district=payload.district,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    res = UserListItem(
        id=new_user.id,
        username=new_user.username,
        full_name=new_user.full_name,
        role=new_user.role,
        district=new_user.district,
        is_active=new_user.is_active,
        last_login_at=new_user.last_login_at,
        created_at=new_user.created_at
    )
    return {"success": True, "data": res}

@router.put("/admin/users/{user_id}")
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user role/district/active status (admin only)."""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payload.fullName is not None:
        user.full_name = payload.fullName
    if payload.role is not None:
        valid_roles = ["admin", "supervisor", "analyst", "viewer"]
        if payload.role.lower() not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role: {payload.role}")
        user.role = payload.role.lower()
    if payload.district is not None:
        user.district = payload.district
    if payload.isActive is not None:
        user.is_active = payload.isActive

    await db.commit()
    await db.refresh(user)
    res = UserListItem(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        district=user.district,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at
    )
    return {"success": True, "data": res}

@router.delete("/admin/users/{user_id}")
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Deactivate a user (admin only). Does not delete — sets is_active=False."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    return {"success": True, "message": f"User {user.username} deactivated"}

# --- Consolidation Endpoints ---

@router.post("/consolidate/upload")
async def upload_for_consolidation(
    background_tasks: BackgroundTasks,
    date: str = Form(...),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Receive uploaded files and trigger async consolidation processing."""
    # Validate date format (DD.MM.YYYY)
    if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {date}. Must be DD.MM.YYYY"
        )
        
    # Check total & individual file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    for f in files:
        f.file.seek(0, os.SEEK_END)
        size = f.file.tell()
        f.file.seek(0)  # Reset pointer
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {f.filename} exceeds the maximum size limit of 10MB."
            )
        
    job_id = str(uuid.uuid4())
    
    # Create background task directory
    temp_dir = os.path.join(settings.UPLOAD_DIR, "jobs", job_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Write files to disk
    for f in files:
        # Sanitize filename: alphanumeric, space, dot, underscore, dash only
        base_name = os.path.basename(f.filename)
        safe_name = re.sub(r'[^a-zA-Z0-9_.\s-]', '', base_name).strip()
        if not safe_name:
            safe_name = f"uploaded_{uuid.uuid4().hex}.docx"
            
        dest_path = os.path.join(temp_dir, safe_name)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
            
    # Create Job record in SQL
    job = Job(
        id=job_id,
        job_type="consolidation",
        status="received",
        progress=0,
        current_step="Files uploaded successfully",
        created_by=current_user.full_name
    )
    db.add(job)
    await db.commit()
    
    # Trigger background pipeline execution (without request-scoped db session)
    background_tasks.add_task(
        consolidation_service.run_consolidation,
        job_id, date, temp_dir
    )
    
    return {"success": True, "data": {"jobId": job_id}}

# --- Job Tracking Endpoints ---

@router.get("/jobs")
async def list_jobs(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_analyst)):
    """List all recent jobs."""
    result = await db.execute(select(Job).order_by(Job.created_at.desc()).limit(20))
    jobs = result.scalars().all()
    
    res_list = []
    for j in jobs:
        res_list.append(JobResponse(
            id=j.id,
            job_type=j.job_type,
            status=j.status,
            progress=j.progress,
            current_step=j.current_step,
            warning_count=j.warning_count,
            warnings=j.warnings,
            result=j.result,
            created_by=j.created_by,
            created_at=j.created_at
        ))
    return {"success": True, "data": res_list}

@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_analyst)):
    """Fetch status details of a specific job."""
    result = await db.execute(select(Job).filter(Job.id == job_id))
    j = result.scalars().first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
        
    res = JobResponse(
        id=j.id,
        job_type=j.job_type,
        status=j.status,
        progress=j.progress,
        current_step=j.current_step,
        warning_count=j.warning_count,
        warnings=j.warnings,
        result=j.result,
        created_by=j.created_by,
        created_at=j.created_at
    )
    return {"success": True, "data": res}

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_analyst)):
    """Cancel an active job and undo any partial database changes."""
    result = await db.execute(select(Job).filter(Job.id == job_id))
    j = result.scalars().first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    if j.status in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Job is already {j.status} and cannot be cancelled")

    # Derive temp dir path from settings (matches upload route logic)
    temp_dir = os.path.join(settings.UPLOAD_DIR, "jobs", job_id)

    # Request cancellation — background task will detect and roll back
    await consolidation_service.cancel_job(job_id, source_files_dir=temp_dir)

    return {"success": True, "message": f"Job {job_id} cancelled and changes rolled back"}

@router.get("/jobs/{job_id}/events")
async def get_job_events_stream(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Server-Sent Events (SSE) progress stream for active jobs."""
    async def event_generator():
        last_event_id = 0
        while True:
            # Query job and events
            result = await db.execute(select(Job).filter(Job.id == job_id))
            job = result.scalars().first()
            if not job:
                yield {"event": "error", "data": "Job not found"}
                break
                
            res_events = await db.execute(
                select(JobEvent)
                .filter(JobEvent.job_id == job_id, JobEvent.id > last_event_id)
                .order_by(JobEvent.id.asc())
            )
            events = res_events.scalars().all()
            
            for event in events:
                yield {
                    "event": "progress",
                    "data": f'{{"id": "{job.id}", "jobType": "{job.job_type}", "status": "{event.status}", "progress": {event.progress}, "currentStep": "{event.message}", "warningCount": {job.warning_count}}}'
                }
                last_event_id = event.id
                
            if job.status in ["completed", "failed", "cancelled"]:
                # Send a final complete event
                yield {
                    "event": "completed",
                    "data": f'{{"id": "{job.id}", "status": "{job.status}"}}'
                }
                break
                
            await asyncio.sleep(1.0)
            
    return EventSourceResponse(event_generator())

# --- Reports Endpoints ---

@router.get("/reports")
async def list_reports(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_viewer)):
    """List all consolidated reports."""
    result = await db.execute(select(Report).order_by(Report.report_date.desc()))
    reports = result.scalars().all()
    
    res_list = []
    for r in reports:
        res_list.append(ReportResponse(
            id=r.id,
            report_date=r.report_date,
            ref_number=r.ref_number,
            event_count=r.event_count,
            forecast_count=r.forecast_count,
            social_media_count=r.social_media_count,
            not_needed_count=r.not_needed_count,
            created_by="Consolidation Engine",
            created_at=r.created_at
        ))
    return {"success": True, "data": res_list}

@router.get("/reports/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_viewer)):
    """Get full report details, including items."""
    result = await db.execute(select(Report).filter(Report.id == report_id))
    r = result.scalars().first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
        
    res_items = await db.execute(
        select(ReportItem)
        .filter(ReportItem.report_id == report_id)
        .order_by(ReportItem.sort_order.asc())
    )
    items = res_items.scalars().all()
    
    items_res = []
    for item in items:
        items_res.append(ReportItemResponse(
            id=item.id,
            report_id=item.report_id,
            category=item.category,
            raw_text=item.raw_text,
            translated_text=item.translated_text,
            summary_text=item.summary_text,
            source_filename=item.source_filename,
            district_tag=item.district_tag,
            translation_engine=item.translation_engine
        ))
        
    detail = ReportDetailResponse(
        id=r.id,
        report_date=r.report_date,
        ref_number=r.ref_number,
        event_count=r.event_count,
        forecast_count=r.forecast_count,
        social_media_count=r.social_media_count,
        not_needed_count=r.not_needed_count,
        created_by="Consolidation Engine",
        created_at=r.created_at,
        items=items_res
    )
    return {"success": True, "data": detail}

@router.get("/reports/{report_id}/download")
async def download_daily_report(report_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_analyst)):
    """Stream consolidated Daily IS Report .docx file."""
    result = await db.execute(select(Report).filter(Report.id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    DAILY_REPORT_DIR = os.path.join(os.path.dirname(settings.PP_DIR), "DAILY IS REPORT")
    fpath = os.path.join(DAILY_REPORT_DIR, f"IS Daily report {report.report_date}.docx")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Consolidated report file not found on disk")
        
    return FileResponse(
        fpath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"IS_Daily_Report_{report.report_date}.docx"
    )

@router.get("/reports/{report_id}/less-priority/download")
async def download_less_priority_report(report_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_analyst)):
    """Stream consolidated Less Priority Report .docx file."""
    result = await db.execute(select(Report).filter(Report.id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    LESS_PRIORITY_REPORT_DIR = os.path.join(os.path.dirname(settings.PP_DIR), "Daily less priority report")
    fpath = os.path.join(LESS_PRIORITY_REPORT_DIR, f"Daily less priority report {report.report_date}.docx")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Less priority report file not found on disk")
        
    return FileResponse(
        fpath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"Less_Priority_Report_{report.report_date}.docx"
    )

# --- Profiles Endpoints ---

@router.get("/profiles")
async def list_profiles(page: int = 1, limit: int = 10, search: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_viewer)):
    """Fetch suspect profiles registry (paginated and filterable)."""
    res = await profile_service.get_profiles(db, page, limit, search)
    # Map items to ProfileResponse schema
    mapped_items = []
    for p in res["items"]:
        mapped_items.append(ProfileResponse(
            id=p.id,
            pp_id=p.pp_id,
            name=p.name,
            parentage=p.parentage,
            address=p.address,
            police_station=p.police_station,
            activity_type=p.activity_type,
            review_status=p.review_status,
            updated_at=p.updated_at
        ))
    return {
        "success": True,
        "data": {
            "items": mapped_items,
            "total": res["total"],
            "page": res["page"],
            "limit": res["limit"],
            "pages": res["pages"]
        }
    }

@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_viewer)):
    """Fetch detailed suspect profile dossier."""
    res = await profile_service.get_profile_detail(db, profile_id)
    if not res:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"success": True, "data": res}

@router.put("/profiles/{profile_id}")
async def update_profile(profile_id: str, updates: Dict[str, Any], db: AsyncSession = Depends(get_db), current_user: User = Depends(require_supervisor)):
    """Update suspect profile details."""
    res = await profile_service.update_profile(db, profile_id, updates)
    if not res:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    mapped = ProfileResponse(
        id=res.id,
        pp_id=res.pp_id,
        name=res.name,
        parentage=res.parentage,
        address=res.address,
        police_station=res.police_station,
        activity_type=res.activity_type,
        review_status=res.review_status,
        updated_at=res.updated_at
    )
    return {"success": True, "data": mapped}

@router.get("/profiles/{profile_id}/docx")
async def download_profile_docx(profile_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_analyst)):
    """Download the dossier docx file for a suspect profile."""
    fpath = await profile_service.get_profile_docx_path(profile_id, db)
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="suspect dossier file not found on disk")
        
    return FileResponse(
        fpath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(fpath)
    )

@router.get("/profiles/{profile_id}/generate-uo")
async def generate_uo_note(profile_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_analyst)):
    """Generate and stream Malayalam UO Note .docx file."""
    fpath = await profile_service.generate_uo_note(profile_id, db)
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Failed to generate UO note or profile not found")
        
    return FileResponse(
        fpath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(fpath)
    )

# --- Review Endpoints ---

@router.get("/review")
async def get_review_queue(current_user: User = Depends(require_supervisor)):
    """List pending review candidate names (VEG review queue)."""
    items = ner_service.get_review_queue()
    return {"success": True, "data": items}

@router.post("/review/{cand_id}/approve")
async def approve_candidate(cand_id: str, current_user: User = Depends(require_supervisor)):
    """Approve candidate (promotes to production suspect profile)."""
    res = ner_service.approve_candidate(cand_id)
    if not res:
        raise HTTPException(status_code=404, detail="Candidate not found or error approving")
    return {"success": True, "data": {"id": cand_id, "status": "approved"}}

@router.post("/review/{cand_id}/reject")
async def reject_candidate(cand_id: str, current_user: User = Depends(require_supervisor)):
    """Reject candidate (silences name from further profile creation)."""
    res = ner_service.reject_candidate(cand_id)
    if not res:
        raise HTTPException(status_code=404, detail="Candidate not found or error rejecting")
    return {"success": True, "data": {"id": cand_id, "status": "rejected"}}

# --- Graph Endpoints ---

@router.get("/graph/stats")
async def get_graph_stats(current_user: User = Depends(require_viewer)):
    """Fetch graph network nodes and edges stats."""
    stats = graph_service.get_stats()
    return {"success": True, "data": stats}

@router.get("/graph/query")
async def query_subgraph(
    centerNodeId: Optional[str] = None,
    depth: int = 1,
    queryType: str = "node",
    date: Optional[str] = None,
    crimeKeyword: Optional[str] = None,
    current_user: User = Depends(require_viewer)
):
    """Query sub-graph. queryType: 'all' | 'node' | 'date' | 'crime'."""
    res = graph_service.query_subgraph(
        center_node_id=centerNodeId,
        depth=depth,
        query_type=queryType,
        date=date,
        crime_keyword=crimeKeyword,
    )
    return {"success": True, "data": res}

@router.get("/graph/associates/{person_name}")
async def get_predicted_associates(person_name: str, current_user: User = Depends(require_viewer)):
    """Discover hidden associates predicted via GNN Link Prediction GCN model embeddings."""
    res = graph_service.get_associates(person_name, top_n=5)
    return {"success": True, "data": res}

@router.post("/graph/clean")
async def clean_junk_graph_nodes(current_user: User = Depends(require_admin)):
    """Remove nodes with invalid person names (cleans graph and audits)."""
    removed_count = graph_service.clean_junk_nodes()
    return {"success": True, "data": {"removedCount": removed_count}}

# --- Search Endpoints ---

@router.post("/search/semantic")
async def search_semantic(search_req: SearchRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_viewer)):
    """Semantic vector search against indexed collections (report items, suspect profiles)."""
    # Vector query against Qdrant
    res_profiles = qdrant_service.search(collection="profiles", query=search_req.query, limit=5)
    res_items = qdrant_service.search(collection="report_items", query=search_req.query, limit=5)
    
    results = []
    
    # Map profiles
    for hit in res_profiles:
        pid = hit["payload"]["profile_id"]
        res_db = await db.execute(select(Profile).filter(Profile.id == pid))
        profile = res_db.scalars().first()
        if profile:
            results.append(SearchResultResponse(
                entity_type="profile",
                title=f"{profile.name} (PP/{profile.pp_id or 'PENDING'})",
                score=hit["score"],
                snippet=profile.brief_history or f"Suspect profile with activity: {profile.activity_type}",
                id=profile.id
            ))
            
    # Map report items
    for hit in res_items:
        ri_id = hit["payload"]["report_item_id"]
        res_db = await db.execute(select(ReportItem).filter(ReportItem.id == ri_id))
        item = res_db.scalars().first()
        if item:
            results.append(SearchResultResponse(
                entity_type="report_item",
                title=f"Consolidated Report Item ({item.category.title()})",
                score=hit["score"],
                snippet=item.summary_text or item.translated_text or item.raw_text,
                id=item.report_id
            ))
            
    # Sort merged results by vector similarity score
    results.sort(key=lambda x: x.score, reverse=True)
    
    return {"success": True, "data": results[:search_req.limit]}
