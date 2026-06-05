import app.core.paths  # Configures Python path for importing existing modules
import os
import re
import uuid
import shutil
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db.models import Job, JobEvent, Report, ReportItem
from app.services.profile_service import ProfileService
from app.services.qdrant_service import QdrantService

# Import functions from existing modules
from utils import (
    read_docx_paragraphs,
    is_malayalam,
    translate_ml_to_en,
    extract_district_tag,
    build_daily_report,
    build_less_priority_report,
    DISTRICT_CODES,
    SOCIAL_MEDIA_KEYWORDS,
)
from intel_tool import (
    _classify_and_summarize_item,
    _sync_profiles_from_texts,
    _resolve_ollama_model,
)

class ConsolidationService:
    def __init__(self):
        self.profile_service = ProfileService()
        self.qdrant = QdrantService()

    async def update_job(
        self,
        db: AsyncSession,
        job_id: str,
        status: str,
        progress: int,
        current_step: str,
        warning: str = None,
        result: Dict[str, Any] = None,
        error_message: str = None
    ):
        """Update job details in DB and append to job events for SSE stream."""
        # Query job
        res = await db.execute(select(Job).filter(Job.id == job_id))
        job = res.scalars().first()
        if not job:
            return
            
        job.status = status
        job.progress = progress
        job.current_step = current_step
        
        if result:
            job.result = result
        if error_message:
            job.error_message = error_message
            
        if warning:
            warnings_list = list(job.warnings or [])
            warnings_list.append(warning)
            job.warnings = warnings_list
            job.warning_count = len(warnings_list)
            
        if status in ["completed", "failed", "cancelled"]:
            job.completed_at = datetime.utcnow()
            
        # Create job event
        event = JobEvent(
            job_id=job_id,
            status=status,
            progress=progress,
            message=current_step
        )
        db.add(event)
        await db.commit()

    async def run_consolidation(self, job_id: str, date_str: str, source_files_dir: str):
        """Execute the full consolidation pipeline asynchronously."""
        from app.db.session import AsyncSessionLocal
        db = AsyncSessionLocal()
        try:
            # 1. Update status to Running
            await self.update_job(
                db, job_id,
                status="running",
                progress=15,
                current_step="Initializing consolidation job workspace"
            )
            
            # Use Ollama if reachable
            use_ollama = False
            summary_model = ""
            try:
                import requests
                resp = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=3)
                if resp.status_code == 200:
                    use_ollama = True
                    summary_model = _resolve_ollama_model(settings.OLLAMA_MODEL, settings.OLLAMA_URL)
            except Exception:
                pass
                
            # Locate all .docx files in folder
            all_files = []
            if os.path.exists(source_files_dir) and os.path.isdir(source_files_dir):
                for fname in sorted(os.listdir(source_files_dir)):
                    if fname.lower().endswith(".docx"):
                        all_files.append(os.path.join(source_files_dir, fname))
                        
            if not all_files:
                await self.update_job(
                    db, job_id,
                    status="failed",
                    progress=100,
                    current_step="Failed: No source .docx files found",
                    error_message="No .docx files found in consolidation directory."
                )
                return

            total_files = len(all_files)
            
            # Setup categories lists
            event_paragraphs = []
            event_raw_texts = []
            forecast_paragraphs = []
            forecast_raw_texts = []
            social_media_items = []
            social_media_raw_texts = []
            not_needed_paragraphs = []
            not_needed_raw_texts = []
            
            failed_files = []
            batch_engines = []

            # 2. Process each file
            for idx, fpath in enumerate(all_files):
                fname = os.path.basename(fpath)
                
                # Check for Malayalam translation
                step_desc = f"Processing file {idx + 1}/{total_files} ({fname})"
                progress_val = 15 + int(50 * idx / total_files)
                
                await self.update_job(
                    db, job_id,
                    status="translating" if idx % 2 == 0 else "summarizing",
                    progress=progress_val,
                    current_step=step_desc
                )
                
                # Default category logic matching CLI fallback rules
                lower_fname = fname.lower().replace(" ", "")
                default_category = "event"
                if any(kw in lower_fname for kw in SOCIAL_MEDIA_KEYWORDS):
                    default_category = "social_media"
                else:
                    base_no_ext = os.path.splitext(fname)[0].strip().upper()
                    if base_no_ext in DISTRICT_CODES or re.match(r"^[Ff]\d", base_no_ext):
                        default_category = "forecast"
                    elif base_no_ext.isupper() and len(base_no_ext) > 3:
                        default_category = "forecast"
                        
                try:
                    # Split or extract details from docx
                    from docx import Document
                    doc = Document(fpath)
                    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                    text_full = "\n".join(paragraphs)
                    
                    # Splitting logic
                    base_no_ext = os.path.splitext(fname)[0].strip().upper()
                    is_alert_file = (
                        base_no_ext in DISTRICT_CODES or 
                        re.match(r"^[Ff]\d", base_no_ext) or
                        "alert" in fname.lower() or
                        "report 1" in text_full.lower()
                    )
                    
                    items = []
                    if is_alert_file:
                        # Split forecast items
                        parts = re.split(r"\bReport\s+\d+\b", text_full, flags=re.IGNORECASE)
                        if len(parts) > 1:
                            for part in parts[1:]:
                                clean = part.strip()
                                clean = re.sub(r"^(?:Detailed\s+)?Description:\s*", "", clean, flags=re.IGNORECASE)
                                clean = re.sub(r"^വിശദീകരണം:\s*", "", clean, flags=re.IGNORECASE)
                                if clean:
                                    items.append(clean)
                        else:
                            numbered = re.split(r"\n\s*\d+[).]\s*", text_full)
                            if len(numbered) > 1:
                                for part in numbered[1:]:
                                    clean = part.strip()
                                    if clean and len(clean) > 15:
                                        items.append(clean)
                            else:
                                if text_full.strip():
                                    items.append(text_full.strip())
                    else:
                        from utils import extract_details_from_docx_paragraphs
                        details = extract_details_from_docx_paragraphs(paragraphs)
                        if details.strip():
                            items = [details.strip()]
                            
                    # Loop over extracted items
                    for item in items:
                        # Translate ML -> EN
                        if is_malayalam(item):
                            item_en = translate_ml_to_en(item, use_ollama=use_ollama, ollama_url=settings.OLLAMA_URL, batch_engines=batch_engines)
                        else:
                            item_en = item
                            
                        # Classify and summarize
                        if summary_model:
                            category, summary = _classify_and_summarize_item(
                                item_en,
                                model=summary_model,
                                ollama_url=settings.OLLAMA_URL,
                                default_category=default_category
                            )
                        else:
                            category = default_category
                            item_en_upper = item_en.upper()
                            if "/RSU/" in item_en_upper:
                                category = "social_media"
                            elif "/CC/" in item_en_upper:
                                category = "forecast"
                            elif "/EC/" in item_en_upper:
                                category = "event"
                            elif "/NN/" in item_en_upper or "/NOT_NEEDED/" in item_en_upper:
                                category = "not_needed"
                            summary = item_en
                            
                        # District Tag
                        tag = extract_district_tag(summary)
                        if not tag:
                            # Infer from filename
                            base = os.path.splitext(fname)[0].upper()
                            for code in DISTRICT_CODES:
                                if code in base:
                                    tag = f"({code})"
                                    break
                        if tag and not summary.endswith(tag):
                            summary = f"{summary} {tag}"
                            
                        # Add to list
                        if category == "social_media":
                            social_media_items.append(summary)
                            social_media_raw_texts.append(item_en)
                        elif category == "forecast":
                            forecast_paragraphs.append(summary)
                            forecast_raw_texts.append(item_en)
                        elif category == "not_needed":
                            not_needed_paragraphs.append(summary)
                            not_needed_raw_texts.append(item_en)
                        else:
                            event_paragraphs.append(summary)
                            event_raw_texts.append(item_en)
                            
                except Exception as e:
                    failed_files.append({"section": "Consolidation Pipeline", "filename": fname})
                    await self.update_job(
                        db, job_id,
                        status="running",
                        progress=progress_val,
                        current_step=f"Warning: Failed to process {fname}: {e}",
                        warning=f"File process error in {fname}: {str(e)}"
                    )

            # 3. Create Report in SQL DB
            await self.update_job(
                db, job_id,
                status="profile_sync",
                progress=65,
                current_step="Writing consolidated report records to PostgreSQL"
            )
            
            ref_number = f"KPIP/{datetime.now().year}/{date_str.replace('.', '/')}"
            report = Report(
                id=str(uuid.uuid4()),
                report_date=date_str,
                ref_number=ref_number,
                event_count=len(event_paragraphs),
                forecast_count=len(forecast_paragraphs),
                social_media_count=len(social_media_items),
                not_needed_count=len(not_needed_paragraphs),
                job_id=job_id
            )
            db.add(report)
            await db.flush()
            
            # Write Report Items
            all_items = []
            sort_counter = 0
            for idx, text in enumerate(event_paragraphs):
                item = ReportItem(
                    id=str(uuid.uuid4()), report_id=report.id, category="event",
                    sort_order=sort_counter, raw_text=event_raw_texts[idx],
                    translated_text=text, summary_text=text
                )
                db.add(item)
                all_items.append(item)
                sort_counter += 1
                
            for idx, text in enumerate(forecast_paragraphs):
                item = ReportItem(
                    id=str(uuid.uuid4()), report_id=report.id, category="forecast",
                    sort_order=sort_counter, raw_text=forecast_raw_texts[idx],
                    translated_text=text, summary_text=text
                )
                db.add(item)
                all_items.append(item)
                sort_counter += 1
                
            for idx, text in enumerate(social_media_items):
                item = ReportItem(
                    id=str(uuid.uuid4()), report_id=report.id, category="social_media",
                    sort_order=sort_counter, raw_text=social_media_raw_texts[idx],
                    translated_text=text, summary_text=text
                )
                db.add(item)
                all_items.append(item)
                sort_counter += 1
                
            for idx, text in enumerate(not_needed_paragraphs):
                item = ReportItem(
                    id=str(uuid.uuid4()), report_id=report.id, category="not_needed",
                    sort_order=sort_counter, raw_text=not_needed_raw_texts[idx],
                    translated_text=text, summary_text=text
                )
                db.add(item)
                all_items.append(item)
                sort_counter += 1
                
            await db.commit()

            # 4. Sync Profiles in filesystem + Neo4j Graph
            await self.update_job(
                db, job_id,
                status="neo4j_sync",
                progress=75,
                current_step="Extracting suspect names, GNN disambiguation, and updating Neo4j Relationships Graph"
            )
            
            all_raw_texts = event_raw_texts + forecast_raw_texts + social_media_raw_texts
            # Run the CLI _sync_profiles_from_texts which updates PP_DIR files and Neo4j
            _sync_profiles_from_texts(all_raw_texts, date_str, use_ollama)
            
            # 5. Sync Profiles from filesystem to SQL DB + Qdrant Index
            await self.update_job(
                db, job_id,
                status="qdrant_indexing",
                progress=85,
                current_step="Synchronizing suspect profiles dossier tables and indexing semantic search collections"
            )
            
            await self.profile_service.sync_all_profiles_to_db(db)
            
            # Index Report Items in Qdrant
            for item in all_items:
                summary_text = item.summary_text or item.translated_text or ""
                self.qdrant.upsert_item(
                    collection="report_items",
                    point_id=item.id,
                    text=summary_text,
                    payload={
                        "report_id": report.id,
                        "report_item_id": item.id,
                        "report_date": date_str,
                        "category": item.category
                    }
                )

            # 6. Build Consolidated DOCX Files on Disk
            await self.update_job(
                db, job_id,
                status="docx_ready",
                progress=95,
                current_step="Building consolidated Daily IS Report and Less Priority Report files on disk"
            )
            
            DAILY_REPORT_DIR = os.path.join(os.path.dirname(settings.PP_DIR), "DAILY IS REPORT")
            os.makedirs(DAILY_REPORT_DIR, exist_ok=True)
            output_path = os.path.join(DAILY_REPORT_DIR, f"IS Daily report {date_str}.docx")
            
            build_daily_report(
                report_date=date_str,
                events=event_paragraphs,
                forecasts=forecast_paragraphs,
                social_media=social_media_items,
                output_path=output_path,
                failed_files=failed_files
            )
            
            if not_needed_paragraphs:
                LESS_PRIORITY_REPORT_DIR = os.path.join(os.path.dirname(settings.PP_DIR), "Daily less priority report")
                os.makedirs(LESS_PRIORITY_REPORT_DIR, exist_ok=True)
                less_priority_path = os.path.join(LESS_PRIORITY_REPORT_DIR, f"Daily less priority report {date_str}.docx")
                build_less_priority_report(
                    report_date=date_str,
                    items=not_needed_paragraphs,
                    output_path=less_priority_path
                )
                
            # 7. Complete the job
            result_summary = {
                "report_id": report.id,
                "event_count": len(event_paragraphs),
                "forecast_count": len(forecast_paragraphs),
                "social_media_count": len(social_media_items),
                "not_needed_count": len(not_needed_paragraphs),
                "failed_files": failed_files
            }
            await self.update_job(
                db, job_id,
                status="completed",
                progress=100,
                current_step="Consolidation pipeline completed successfully",
                result=result_summary
            )
            await db.close()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                await self.update_job(
                    db, job_id,
                    status="failed",
                    progress=100,
                    current_step=f"Failed: {str(e)}",
                    error_message=f"Pipeline error: {str(e)}"
                )
            finally:
                await db.close()
