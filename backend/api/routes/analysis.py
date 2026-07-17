# Analysis Routes
# ================
# Full analysis pipeline endpoints using integrated predict_report features

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import uuid4
from datetime import datetime
import asyncio
import logging

from api.dependencies import get_current_user
from services.analysis_service import AnalysisService
from services.scheduler_service import scheduler_service

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory job storage (replace with Redis/DB in production)
analysis_jobs: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalysisRequest(BaseModel):
    ticker: str
    include_forecast: bool = True
    include_sentiment: bool = True
    include_recommendation: bool = True
    document_ids: Optional[List[str]] = None  # Include RAG documents
    forecast_days: int = 30  # Default to 30 days
    custom_questions: Optional[str] = None  # Custom questions for report


class AnalysisJobResponse(BaseModel):
    job_id: str
    ticker: str
    status: str
    created_at: str


class AnalysisResult(BaseModel):
    job_id: str
    ticker: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SentimentRequest(BaseModel):
    ticker: str
    text: Optional[str] = None


class ForecastRequest(BaseModel):
    ticker: str
    days: int = 30


class RecommendationRequest(BaseModel):
    ticker: str


class FHIRequest(BaseModel):
    ticker: str


class ScheduleRequest(BaseModel):
    ticker: str
    interval: str  # 'hourly', 'daily', 'weekly'


# ============================================================================
# Background Task Functions
# ============================================================================

async def run_analysis_pipeline(job_id: str, request: AnalysisRequest, user_id: str):
    """Run the full analysis pipeline in the background."""
    try:
        analysis_jobs[job_id]["status"] = "running"
        
        # Initialize analysis service
        service = AnalysisService()
        
        # Run full pipeline
        result = await service.run_full_pipeline(
            ticker=request.ticker.upper(),
            user_id=user_id,
            include_forecast=request.include_forecast,
            include_sentiment=request.include_sentiment,
            include_recommendation=request.include_recommendation,
            document_ids=request.document_ids,
            forecast_days=request.forecast_days,
            custom_questions=request.custom_questions
        )
        
        # Update job status
        analysis_jobs[job_id]["status"] = "completed"
        analysis_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        analysis_jobs[job_id]["result"] = result
        
    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}")
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["error"] = str(e)


# ============================================================================
# Routes
# ============================================================================

@router.post("/start", response_model=AnalysisJobResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a full analysis pipeline for a stock.
    
    Runs Prophet forecast, FinBERT sentiment, FHI calculation,
    and recommendation engine. Returns job_id to track progress.
    """
    job_id = str(uuid4())
    created_at = datetime.now().isoformat()
    
    # Store job info
    analysis_jobs[job_id] = {
        "job_id": job_id,
        "ticker": request.ticker.upper(),
        "status": "pending",
        "created_at": created_at,
        "user_id": current_user["id"],
        "result": None,
        "error": None
    }
    
    # Start background task
    background_tasks.add_task(
        run_analysis_pipeline,
        job_id,
        request,
        current_user["id"]
    )
    
    return AnalysisJobResponse(
        job_id=job_id,
        ticker=request.ticker.upper(),
        status="pending",
        created_at=created_at
    )


@router.get("/schedules")
async def list_analysis_schedules(
    current_user: dict = Depends(get_current_user)
):
    """
    List all automated analysis schedules for the current user.
    """
    return scheduler_service.get_user_schedules(current_user["id"])


@router.get("/{job_id}", response_model=AnalysisResult)
async def get_analysis_result(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status and results of an analysis job.
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    # Verify ownership
    if job.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return AnalysisResult(
        job_id=job["job_id"],
        ticker=job["ticker"],
        status=job["status"],
        created_at=job["created_at"],
        completed_at=job.get("completed_at"),
        result=job.get("result"),
        error=job.get("error")
    )


@router.post("/sentiment")
async def analyze_sentiment(
    request: SentimentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Run FinBERT sentiment analysis only.
    """
    try:
        service = AnalysisService()
        result = await service.run_sentiment_only(request.ticker.upper())
        
        return {
            "ticker": request.ticker.upper(),
            "sentiment": result.get("sentiment"),
            "fhi": result.get("fhi")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast")
async def run_forecast(
    request: ForecastRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Run Prophet forecast only.
    """
    try:
        service = AnalysisService()
        result = await service.run_forecast_only(request.ticker.upper())
        
        return {
            "ticker": request.ticker.upper(),
            "forecast": result.get("forecast"),
            "chart_path": result.get("chart_path")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def get_recommendation(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Get AI investment recommendation (BUY/HOLD/SELL).
    """
    try:
        service = AnalysisService()
        result = await service.run_recommendation_only(request.ticker.upper())
        
        return {
            "ticker": request.ticker.upper(),
            "recommendation": result.get("recommendation"),
            "fhi": result.get("fhi"),
            "sentiment": result.get("sentiment")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fhi")
async def calculate_fhi(
    request: FHIRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate Financial Health Index (FHI) only.
    """
    try:
        service = AnalysisService()
        result = await service.run_sentiment_only(request.ticker.upper())
        
        return {
            "ticker": request.ticker.upper(),
            "fhi": result.get("fhi")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def create_analysis_schedule(
    request: ScheduleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a recurring analysis schedule for a stock.
    """
    if request.interval not in ['hourly', 'daily', 'weekly']:
        raise HTTPException(status_code=400, detail="Invalid interval. Use 'hourly', 'daily', or 'weekly'.")
    
    try:
        schedule = scheduler_service.add_schedule(
            ticker=request.ticker.upper(),
            interval=request.interval,
            user_id=current_user["id"]
        )
        return schedule
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.delete("/schedule/{job_id}")
async def delete_analysis_schedule(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove an automated analysis schedule.
    """
    try:
        scheduler_service.remove_schedule(job_id)
        return {"message": "Schedule removed successfully", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
