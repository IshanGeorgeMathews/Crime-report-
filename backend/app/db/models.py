import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Date, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin', 'supervisor', 'analyst', 'viewer'
    district = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_date = Column(String(20), unique=True, nullable=False, index=True) # DD.MM.YYYY format
    ref_number = Column(String(50), nullable=False)
    event_count = Column(Integer, default=0, nullable=False)
    forecast_count = Column(Integer, default=0, nullable=False)
    social_media_count = Column(Integer, default=0, nullable=False)
    not_needed_count = Column(Integer, default=0, nullable=False)
    validation_warnings = Column(JSON, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    job_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship("ReportItem", back_populates="report", cascade="all, delete-orphan")

class ReportItem(Base):
    __tablename__ = "report_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False)
    category = Column(String(20), nullable=False)  # 'event', 'forecast', 'social_media', 'not_needed'
    sort_order = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)
    summary_text = Column(Text, nullable=True)
    source_filename = Column(String(255), nullable=True)
    district_tag = Column(String(20), nullable=True)
    translation_engine = Column(String(20), nullable=True)
    llm_model = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="items")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pp_id = Column(String(20), unique=True, nullable=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    parentage = Column(String(150), nullable=True)
    address = Column(Text, nullable=True)
    police_station = Column(String(100), nullable=True)
    dob = Column(String(20), nullable=True)
    place_of_birth = Column(String(100), nullable=True)
    qualification = Column(String(100), nullable=True)
    religion = Column(String(50), nullable=True)
    identification_marks = Column(Text, nullable=True)
    mobile = Column(String(20), nullable=True)
    activity_type = Column(String(100), nullable=True)
    reason_for_inclusion = Column(Text, nullable=True)
    organization_name = Column(String(150), nullable=True)
    organization_remarks = Column(Text, nullable=True)
    brief_history = Column(Text, nullable=True)
    review_status = Column(String(20), default="pending", nullable=False)  # 'approved', 'pending', 'rejected'
    neo4j_node_id = Column(String(100), nullable=True)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    cases = relationship("ProfileCase", back_populates="profile", cascade="all, delete-orphan")
    relations = relationship("ProfileRelation", back_populates="profile", cascade="all, delete-orphan")
    activities = relationship("ProfileActivity", back_populates="profile", cascade="all, delete-orphan")

class ProfileRelation(Base):
    __tablename__ = "profile_relations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    name = Column(String(150), nullable=False)
    relation_type = Column(String(50), nullable=False)  # 'Father', 'Mother', 'Spouse', etc.
    address = Column(Text, nullable=True)
    mobile = Column(String(20), nullable=True)

    profile = relationship("Profile", back_populates="relations")

class ProfileCase(Base):
    __tablename__ = "profile_cases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    fir_number = Column(String(50), nullable=False)
    under_sections = Column(Text, nullable=True)
    police_station = Column(String(100), nullable=True)
    case_brief = Column(Text, nullable=True)
    case_status = Column(String(50), default="Under Investigation", nullable=False)
    co_accused = Column(Text, nullable=True)
    neo4j_case_node_id = Column(String(100), nullable=True)

    profile = relationship("Profile", back_populates="cases")

class ProfileActivity(Base):
    __tablename__ = "profile_activities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    activity_name = Column(String(200), nullable=False)
    activity_desc = Column(Text, nullable=True)
    activity_date = Column(String(20), nullable=True)  # DD.MM.YYYY format
    report_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("Profile", back_populates="activities")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String(50), nullable=False)  # 'consolidation', 'profile_sync', etc.
    status = Column(String(30), default="received", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    current_step = Column(String(200), nullable=True)
    input_params = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    warnings = Column(JSON, nullable=True)
    warning_count = Column(Integer, default=0, nullable=False)
    celery_task_id = Column(String(255), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan")

class JobEvent(Base):
    __tablename__ = "job_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    status = Column(String(30), nullable=False)
    progress = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("Job", back_populates="events")

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class UploadSession(Base):
    __tablename__ = "upload_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    report_date = Column(String(20), nullable=False)
    status = Column(String(20), default="active", nullable=False)  # 'active', 'completed', 'expired', 'failed'
    total_files = Column(Integer, default=0, nullable=False)
    total_bytes = Column(BigInteger, default=0, nullable=False)
    temp_dir = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    files = relationship("UploadedFile", back_populates="session", cascade="all, delete-orphan")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("upload_sessions.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    mime_type = Column(String(100), nullable=True)
    category_hint = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("UploadSession", back_populates="files")

class IngestionSchedule(Base):
    __tablename__ = "ingestion_schedules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    schedule_type = Column(String(50), nullable=False)  # 'folder_watch', 'gnn_retrain', etc.
    cron_expression = Column(String(50), nullable=False)
    source_directory = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
