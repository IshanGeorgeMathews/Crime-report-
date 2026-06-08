from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- Auth Schemas ---
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    fullName: str = Field(..., alias="full_name")
    role: str
    district: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class TokenResponse(BaseModel):
    user: UserResponse
    token: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    fullName: str = Field(..., alias="full_name")
    role: str  # 'admin', 'supervisor', 'analyst', 'viewer'
    district: Optional[str] = None

    class Config:
        populate_by_name = True

class UserUpdate(BaseModel):
    fullName: Optional[str] = Field(None, alias="full_name")
    role: Optional[str] = None
    district: Optional[str] = None
    isActive: Optional[bool] = Field(None, alias="is_active")

    class Config:
        populate_by_name = True

class UserListItem(BaseModel):
    id: str
    username: str
    fullName: str = Field(..., alias="full_name")
    role: str
    district: Optional[str] = None
    isActive: bool = Field(..., alias="is_active")
    lastLoginAt: Optional[datetime] = Field(None, alias="last_login_at")
    createdAt: datetime = Field(..., alias="created_at")

    class Config:
        populate_by_name = True
        from_attributes = True

# --- Job Schemas ---
class JobEventResponse(BaseModel):
    id: int
    job_id: str
    status: str
    progress: int
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: str
    jobType: str = Field(..., alias="job_type")
    status: str
    progress: int
    currentStep: Optional[str] = Field(None, alias="current_step")
    warningCount: int = Field(0, alias="warning_count")
    warnings: Optional[List[str]] = None
    result: Optional[Dict[str, Any]] = None
    createdBy: Optional[str] = Field(None, alias="created_by")
    createdAt: datetime = Field(..., alias="created_at")

    class Config:
        populate_by_name = True
        from_attributes = True

# --- Report Schemas ---
class ReportResponse(BaseModel):
    id: str
    reportDate: str = Field(..., alias="report_date")
    refNumber: str = Field(..., alias="ref_number")
    eventCount: int = Field(0, alias="event_count")
    forecastCount: int = Field(0, alias="forecast_count")
    socialMediaCount: int = Field(0, alias="social_media_count")
    notNeededCount: int = Field(0, alias="not_needed_count")
    createdBy: Optional[str] = Field(None, alias="created_by")
    createdAt: datetime = Field(..., alias="created_at")

    class Config:
        populate_by_name = True
        from_attributes = True

class ReportItemResponse(BaseModel):
    id: str
    reportId: str = Field(..., alias="report_id")
    category: str
    rawText: str = Field(..., alias="raw_text")
    translatedText: Optional[str] = Field(None, alias="translated_text")
    summaryText: Optional[str] = Field(None, alias="summary_text")
    sourceFilename: Optional[str] = Field(None, alias="source_filename")
    districtTag: Optional[str] = Field(None, alias="district_tag")
    translationEngine: Optional[str] = Field(None, alias="translation_engine")

    class Config:
        populate_by_name = True
        from_attributes = True

class ReportDetailResponse(ReportResponse):
    items: List[ReportItemResponse]

    class Config:
        populate_by_name = True
        from_attributes = True

# --- Profile Schemas ---
class ProfileRelationResponse(BaseModel):
    id: str
    name: str
    relationType: str = Field(..., alias="relation_type")
    address: Optional[str] = None
    mobile: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class ProfileCaseResponse(BaseModel):
    id: str
    firNumber: str = Field(..., alias="fir_number")
    underSections: Optional[str] = Field(None, alias="under_sections")
    policeStation: Optional[str] = Field(None, alias="police_station")
    caseBrief: Optional[str] = Field(None, alias="case_brief")
    caseStatus: str = Field("Under Investigation", alias="case_status")
    coAccused: Optional[str] = Field(None, alias="co_accused")

    class Config:
        populate_by_name = True
        from_attributes = True

class ProfileActivityResponse(BaseModel):
    id: str
    activityName: str = Field(..., alias="activity_name")
    activityDesc: Optional[str] = Field(None, alias="activity_desc")
    activityDate: Optional[str] = Field(None, alias="activity_date")

    class Config:
        populate_by_name = True
        from_attributes = True

class ProfileResponse(BaseModel):
    id: str
    ppId: Optional[str] = Field(None, alias="pp_id")
    name: str
    parentage: Optional[str] = None
    address: Optional[str] = None
    policeStation: Optional[str] = Field(None, alias="police_station")
    activityType: Optional[str] = Field(None, alias="activity_type")
    reviewStatus: str = Field("pending", alias="review_status")
    updatedAt: datetime = Field(..., alias="updated_at")

    class Config:
        populate_by_name = True
        from_attributes = True

class ProfileDetailResponse(ProfileResponse):
    dob: Optional[str] = None
    placeOfBirth: Optional[str] = Field(None, alias="place_of_birth")
    qualification: Optional[str] = None
    religion: Optional[str] = None
    identificationMarks: Optional[str] = Field(None, alias="identification_marks")
    mobile: Optional[str] = None
    reasonForInclusion: Optional[str] = Field(None, alias="reason_for_inclusion")
    organizationName: Optional[str] = Field(None, alias="organization_name")
    organizationRemarks: Optional[str] = Field(None, alias="organization_remarks")
    briefHistory: Optional[str] = Field(None, alias="brief_history")
    createdAt: datetime = Field(..., alias="created_at")
    cases: List[ProfileCaseResponse] = []
    relations: List[ProfileRelationResponse] = []
    activities: List[ProfileActivityResponse] = []

    class Config:
        populate_by_name = True
        from_attributes = True

class ProfileUpdate(BaseModel):
    ppId: Optional[str] = None
    name: Optional[str] = None
    parentage: Optional[str] = None
    address: Optional[str] = None
    policeStation: Optional[str] = None
    dob: Optional[str] = None
    placeOfBirth: Optional[str] = None
    qualification: Optional[str] = None
    religion: Optional[str] = None
    identificationMarks: Optional[str] = None
    mobile: Optional[str] = None
    activityType: Optional[str] = None
    reasonForInclusion: Optional[str] = None
    organizationName: Optional[str] = None
    organizationRemarks: Optional[str] = None
    briefHistory: Optional[str] = None
    reviewStatus: Optional[str] = None

# --- Search Schemas ---
class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    district: Optional[str] = None
    limit: Optional[int] = 10

class SearchResultResponse(BaseModel):
    entityType: str = Field(..., alias="entity_type")  # 'profile' or 'report_item'
    title: str
    score: float
    snippet: str
    id: str

    class Config:
        populate_by_name = True
        from_attributes = True

# --- Graph Schemas ---
class GraphNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any]

class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    type: str
    weight: float

class GraphQueryResponse(BaseModel):
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]

class GnnRecommendationResponse(BaseModel):
    name: str
    similarity: float
    hasEdge: bool = Field(..., alias="has_edge")

    class Config:
        populate_by_name = True
        from_attributes = True

# --- API Envelope ---
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
