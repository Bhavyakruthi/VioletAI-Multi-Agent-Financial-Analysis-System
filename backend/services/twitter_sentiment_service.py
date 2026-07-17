# Twitter Sentiment Service
# ==========================
# Fetch and analyze Twitter (X) sentiment for stocks
# Uses a search-based approach to avoid high API costs

import requests
import logging
import re
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TwitterSentimentService:
    """
    Fetch and analyze Twitter/X sentiment for stocks.
    Uses public search or guest tokens if possible.
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _fetch_twitter_posts(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent posts from X/Twitter for a ticker.
        NOTE: Direct scraping of X search is restricted.
        In a real app, this would use a 3rd-party search API or a guest-token scraper.
        We will simulate with a fallback or search-engine scraping.
        """
        try:
            # For demonstration, we'll use a mocked response or search-based approach
            # Real implementation would likely use Nitter or a similar proxy
            # or a lightweight search tool.
            
            # Simulated data for prototype
            simulated_posts = [
                {
                    "text": f"Just bought more ${ticker}! The growth potential is insane. 🚀 #stocks",
                    "user": "TraderJoe",
                    "likes": 120,
                    "retweets": 45,
                    "timestamp": datetime.now().isoformat(),
                    "url": "https://x.com/mock/1"
                },
                {
                    "text": f"Watching ${ticker} closely. Support at current levels is strong. Bullish.",
                    "user": "ChartMaster",
                    "likes": 85,
                    "retweets": 12,
                    "timestamp": datetime.now().isoformat(),
                    "url": "https://x.com/mock/2"
                }
            ]
            return simulated_posts[:limit]
        except Exception as e:
            logger.error(f"Error fetching Twitter for {ticker}: {e}")
            return []

    def _simple_sentiment_score(self, text: str) -> float:
        """Simple keyword-based sentiment scorer."""
        text_lower = text.lower()
        bullish_words = ["buy", "long", "bullish", "moon", "calls", "up", "green", "strong", "rocket"]
        bearish_words = ["sell", "short", "bearish", "crash", "puts", "down", "red", "weak", "tank"]
        
        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0
        
        return (bullish_count - bearish_count) / total

    def get_twitter_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Get aggregated Twitter/X sentiment."""
        try:
            posts = self._fetch_twitter_posts(ticker.upper())
            
            if not posts:
                return {
                    "ticker": ticker.upper(),
                    "platform": "twitter",
                    "mention_count": 0,
                    "sentiment_score": 0,
                    "sentiment_label": "Neutral",
                    "posts": []
                }
            
            total_score = 0
            for post in posts:
                total_score += self._simple_sentiment_score(post["text"])
            
            avg_sentiment = total_score / len(posts) if posts else 0
            
            if avg_sentiment > 0.2:
                label = "Bullish"
            elif avg_sentiment < -0.2:
                label = "Bearish"
            else:
                label = "Mixed"
                
            return {
                "ticker": ticker.upper(),
                "platform": "twitter",
                "mention_count": len(posts),
                "sentiment_score": round(avg_sentiment, 2),
                "sentiment_label": label,
                "posts": posts
            }
        except Exception as e:
            logger.error(f"Error processing Twitter for {ticker}: {e}")
            return {"error": str(e)}

# Singleton instance
twitter_sentiment = TwitterSentimentService()
