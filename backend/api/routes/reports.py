# Reports Routes
# ==============
# PDF report generation and management

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import logging

from api.dependencies import get_current_user
from services.email_service import email_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class ReportInfo(BaseModel):
    id: str
    ticker: str
    filename: str
    created_at: str
    file_size_kb: float


class ReportListResponse(BaseModel):
    reports: List[ReportInfo]
    total_count: int


class GenerateReportRequest(BaseModel):
    ticker: str
    include_forecast: bool = True
    include_sentiment: bool = True
    include_recommendation: bool = True

class EmailReportRequest(BaseModel):
    email: str
    report_id: str


# In-memory report tracking (replace with DB in production)
user_reports: dict = {}


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=ReportListResponse)
async def list_reports(
    current_user: dict = Depends(get_current_user)
):
    """
    List all reports for the current user.
    """
    user_id = current_user["id"]
    reports_dir = f"./reports/{user_id}"
    
    reports = []
    
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            if filename.endswith(".pdf"):
                file_path = os.path.join(reports_dir, filename)
                file_stat = os.stat(file_path)
                
                # Extract ticker from filename (format: TICKER_timestamp.pdf)
                parts = filename.replace(".pdf", "").split("_")
                ticker = parts[0] if parts else "Unknown"
                
                reports.append(ReportInfo(
                    id=filename.replace(".pdf", ""),
                    ticker=ticker,
                    filename=filename,
                    created_at=datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    file_size_kb=round(file_stat.st_size / 1024, 2)
                ))
    
    # Sort by creation date (newest first)
    reports.sort(key=lambda x: x.created_at, reverse=True)
    
    return ReportListResponse(
        reports=reports,
        total_count=len(reports)
    )


@router.get("/{report_id}/data")
async def get_report_data(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the JSON data for a specific report to restore analysis state.
    """
    user_id = current_user["id"]
    reports_dir = f"./reports/{user_id}"
    file_path = os.path.join(reports_dir, f"{report_id}.json")
    
    if not os.path.exists(file_path):
        # Fallback for old reports that might not have JSON
        raise HTTPException(status_code=404, detail="Analysis data not found for this report")
        
    try:
        import json
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error reading report data: {e}")
        raise HTTPException(status_code=500, detail="Failed to load report data")


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download a report PDF.
    """
    user_id = current_user["id"]
    reports_dir = f"./reports/{user_id}"
    file_path = os.path.join(reports_dir, f"{report_id}.pdf")
    
    # Also check global output folder
    if not os.path.exists(file_path):
        file_path = f"./output/{report_id}.pdf"
    
    if not os.path.exists(file_path):
        # Try with just the ticker
        file_path = f"./output/{report_id}_Crew_Report.pdf"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=file_path,
        filename=f"{report_id}.pdf",
        media_type="application/pdf"
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a report.
    """
    user_id = current_user["id"]
    reports_dir = f"./reports/{user_id}"
    file_path = os.path.join(reports_dir, f"{report_id}.pdf")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        os.remove(file_path)
        return {"message": "Report deleted successfully", "report_id": report_id}
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_report(
    request: GenerateReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a new PDF report for a ticker.
    """
    from services.analysis_service import AnalysisService
    
    user_id = current_user["id"]
    
    try:
        service = AnalysisService()
        result = await service.run_full_pipeline(
            ticker=request.ticker.upper(),
            user_id=user_id,
            include_forecast=request.include_forecast,
            include_sentiment=request.include_sentiment,
            include_recommendation=request.include_recommendation
        )
        
        if result.get("report_path"):
            report_id = os.path.basename(result["report_path"]).replace(".pdf", "")
            return {
                "status": "success",
                "report_id": report_id,
                "report_path": result["report_path"],
                "ticker": request.ticker.upper()
            }
        else:
            return {
                "status": "completed",
                "message": "Analysis completed but no report generated",
                "result": result
            }
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{report_id}/email")
async def email_report(
    report_id: str,
    request: EmailReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a generated report via email.
    """
    user_id = current_user["id"]
    reports_dir = f"./reports/{user_id}"
    json_path = os.path.join(reports_dir, f"{report_id}.json")
    
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Report data not found")
        
    try:
        import json
        with open(json_path, 'r') as f:
            report_data = json.load(f)
        
        # Prepare data for email service (map keys correctly)
        email_data = {
            "ticker": report_data.get("ticker", "N/A"),
            "analysis": report_data.get("report_body", report_data.get("analysis", "")),
            "date": report_data.get("timestamp", report_data.get("created_at", "N/A"))
        }

        # Format and send
        html_content = email_service.format_report_html(email_data)
        ticker = report_data.get("ticker", "Stock")
        subject = f"Equity Research Report: {ticker}"
        
        success = email_service.send_report(
            to_email=request.email,
            subject=subject,
            content=html_content,
            is_html=True
        )
        
        if success:
            return {"status": "success", "message": f"Report sent to {request.email}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email. Check SMTP configuration.")
            
    except Exception as e:
        logger.error(f"Error emailing report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
