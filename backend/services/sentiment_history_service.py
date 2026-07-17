# Sentiment History Service
# ==========================
# Store and retrieve sentiment scores over time for trend analysis

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Storage directory for sentiment history
HISTORY_DIR = "./data/sentiment_history"


class SentimentHistoryService:
    """
    Store and retrieve sentiment scores over time.
    Uses JSON files per ticker for simple persistence.
    """
    
    def __init__(self):
        os.makedirs(HISTORY_DIR, exist_ok=True)
    
    def _get_file_path(self, ticker: str) -> str:
        """Get the JSON file path for a ticker."""
        return os.path.join(HISTORY_DIR, f"{ticker.upper()}.json")
    
    def save_sentiment(self, ticker: str, sentiment_data: Dict[str, Any]) -> bool:
        """
        Save a sentiment record for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            sentiment_data: Dict containing compound score, label, fhi_score, etc.
        """
        try:
            file_path = self._get_file_path(ticker)
            
            # Load existing data or create new
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            # Create new record
            record = {
                "timestamp": datetime.now().isoformat(),
                "compound": sentiment_data.get("compound", 0),
                "label": sentiment_data.get("label", "Neutral"),
                "fhi_score": sentiment_data.get("fhi_score"),
                "fhi_grade": sentiment_data.get("fhi_grade"),
            }
            
            history.append(record)
            
            # Keep only last 90 days (approx 90 records max)
            history = history[-90:]
            
            with open(file_path, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.info(f"Saved sentiment record for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save sentiment for {ticker}: {e}")
            return False
    
    def get_history(self, ticker: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get sentiment history for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to retrieve (max 90)
        
        Returns:
            List of sentiment records ordered by timestamp
        """
        try:
            file_path = self._get_file_path(ticker)
            
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, 'r') as f:
                history = json.load(f)
            
            # Return last N records
            return history[-days:]
            
        except Exception as e:
            logger.error(f"Failed to get sentiment history for {ticker}: {e}")
            return []
    
    def get_trend(self, ticker: str) -> Optional[str]:
        """
        Calculate the sentiment trend direction.
        
        Returns: "IMPROVING", "DECLINING", or "STABLE"
        """
        history = self.get_history(ticker, days=7)
        
        if len(history) < 2:
            return None
        
        first_half = history[:len(history)//2]
        second_half = history[len(history)//2:]
        
        avg_first = sum(r.get("compound", 0) for r in first_half) / len(first_half)
        avg_second = sum(r.get("compound", 0) for r in second_half) / len(second_half)
        
        diff = avg_second - avg_first
        
        if diff > 0.1:
            return "IMPROVING"
        elif diff < -0.1:
            return "DECLINING"
        else:
            return "STABLE"


# Singleton instance
sentiment_history = SentimentHistoryService()
