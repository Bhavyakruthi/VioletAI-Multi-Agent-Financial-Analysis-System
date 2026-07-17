# Scheduler Service
# =================
# Manage recurring stock analysis tasks

import os
import json
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

SCHEDULES_FILE = "./data/schedules.json"

class SchedulerService:
    """
    Manage recurring stock analysis and reporting tasks.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone="UTC"
        )
        self.analysis_service = AnalysisService()
        self._ensure_data_dir()
        self.schedules = self._load_schedules()
        
    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(SCHEDULES_FILE), exist_ok=True)
        if not os.path.exists(SCHEDULES_FILE):
            with open(SCHEDULES_FILE, 'w') as f:
                json.dump([], f)

    def _load_schedules(self) -> List[Dict[str, Any]]:
        try:
            with open(SCHEDULES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load schedules: {e}")
            return []

    def _save_schedules(self):
        try:
            with open(SCHEDULES_FILE, 'w') as f:
                json.dump(self.schedules, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save schedules: {e}")

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started.")
            # Restore jobs from persistence
            self._restore_jobs()

    def _restore_jobs(self):
        for schedule in self.schedules:
            self._add_to_apscheduler(schedule)

    def _add_to_apscheduler(self, schedule: Dict[str, Any]):
        job_id = schedule["id"]
        ticker = schedule["ticker"]
        interval = schedule["interval"] # 'daily', 'weekly', 'hourly'
        user_id = schedule["user_id"]
        
        trigger_args = {}
        if interval == 'daily':
            trigger_args = {'trigger': 'cron', 'hour': 9} # 9 AM UTC
        elif interval == 'weekly':
            trigger_args = {'trigger': 'cron', 'day_of_week': 'mon', 'hour': 9}
        elif interval == 'hourly':
            trigger_args = {'trigger': 'interval', 'hours': 1}
        
        self.scheduler.add_job(
            self._run_scheduled_task,
            id=job_id,
            args=[ticker, user_id, schedule],
            replace_existing=True,
            **trigger_args
        )

    async def _run_scheduled_task(self, ticker: str, user_id: str, schedule: Dict[str, Any]):
        logger.info(f"Running scheduled task for {ticker} (User: {user_id})")
        try:
            # Run the full pipeline
            result = await self.analysis_service.run_full_pipeline(
                ticker=ticker,
                user_id=user_id,
                include_forecast=True,
                include_sentiment=True,
                include_recommendation=True
            )
            
            # Update last run time
            schedule["last_run"] = datetime.now().isoformat()
            schedule["last_status"] = "Success"
            self._save_schedules()
            
            logger.info(f"Scheduled task for {ticker} completed successfully.")
        except Exception as e:
            logger.error(f"Scheduled task for {ticker} failed: {e}")
            schedule["last_run"] = datetime.now().isoformat()
            schedule["last_status"] = f"Failed: {str(e)}"
            self._save_schedules()

    def add_schedule(self, ticker: str, interval: str, user_id: str) -> Dict[str, Any]:
        import uuid
        job_id = str(uuid.uuid4())
        
        new_schedule = {
            "id": job_id,
            "ticker": ticker.upper(),
            "interval": interval,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "last_status": "Pending"
        }
        
        self.schedules.append(new_schedule)
        self._save_schedules()
        self._add_to_apscheduler(new_schedule)
        
        return new_schedule

    def remove_schedule(self, job_id: str):
        self.schedules = [s for s in self.schedules if s["id"] != job_id]
        self._save_schedules()
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def get_user_schedules(self, user_id: str) -> List[Dict[str, Any]]:
        return [s for s in self.schedules if s["user_id"] == user_id]

# Singleton instance
scheduler_service = SchedulerService()
