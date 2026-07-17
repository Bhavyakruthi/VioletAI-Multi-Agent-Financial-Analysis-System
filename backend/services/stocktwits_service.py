# StockTwits Service
# ==========================
# Fetch and analyze StockTwits sentiment for stocks

import requests
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class StockTwitsService:
    """
    Fetch and analyze StockTwits stream for stocks.
    Uses StockTwits public API.
    """
    
    def __init__(self):
        self.base_url = "https://api.stocktwits.com/api/2/streams/symbol"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://stocktwits.com/",
            "Origin": "https://stocktwits.com",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
    
    def _fetch_stocktwits_messages(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch messages from StockTwits for a ticker."""
        try:
            url = f"{self.base_url}/{ticker.upper()}.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                processed_messages = []
                for msg in messages:
                    # StockTwits often provides a sentiment field
                    sentiment_data = msg.get("entities", {}).get("sentiment", {})
                    st_sentiment = sentiment_data.get("basic") if sentiment_data else None
                    
                    processed_messages.append({
                        "id": msg.get("id"),
                        "text": msg.get("body", ""),
                        "user": msg.get("user", {}).get("username", "Anonymous"),
                        "created": msg.get("created_at"),
                        "st_sentiment": st_sentiment, # 'Bullish' or 'Bearish'
                        "url": f"https://stocktwits.com/message/{msg.get('id')}"
                    })
                return processed_messages[:limit]
            else:
                logger.warning(f"StockTwits API returned {response.status_code} for {ticker}")
                return []
        except Exception as e:
            logger.error(f"Error fetching StockTwits for {ticker}: {e}")
            return []

    def _simple_sentiment_score(self, text: str, st_sentiment: str = None) -> float:
        """
        Keyword-based sentiment scorer, augmented by StockTwits' own sentiment label if available.
        """
        # If StockTwits already provides sentiment, use it
        if st_sentiment == "Bullish":
            return 0.8
        elif st_sentiment == "Bearish":
            return -0.8
            
        text_lower = text.lower()
        bullish_words = ["buy", "long", "bullish", "moon", "calls", "up", "green", "strong"]
        bearish_words = ["sell", "short", "bearish", "crash", "puts", "down", "red", "weak"]
        
        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0
        
        return (bullish_count - bearish_count) / total

    def get_stocktwits_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Get aggregated StockTwits sentiment for a stock.
        """
        try:
            messages = self._fetch_stocktwits_messages(ticker.upper())
            
            if not messages:
                return {
                    "ticker": ticker.upper(),
                    "platform": "stocktwits",
                    "mention_count": 0,
                    "sentiment_score": 0,
                    "sentiment_label": "Neutral",
                    "messages": []
                }
            
            total_score = 0
            for msg in messages:
                total_score += self._simple_sentiment_score(msg["text"], msg["st_sentiment"])
            
            avg_sentiment = total_score / len(messages) if messages else 0
            
            if avg_sentiment > 0.2:
                label = "Bullish"
            elif avg_sentiment < -0.2:
                label = "Bearish"
            else:
                label = "Mixed"
                
            return {
                "ticker": ticker.upper(),
                "platform": "stocktwits",
                "mention_count": len(messages),
                "sentiment_score": round(avg_sentiment, 2),
                "sentiment_label": label,
                "messages": messages[:10]
            }
        except Exception as e:
            logger.error(f"Error processing StockTwits for {ticker}: {e}")
            return {"error": str(e)}

# Singleton instance
stocktwits_service = StockTwitsService()
