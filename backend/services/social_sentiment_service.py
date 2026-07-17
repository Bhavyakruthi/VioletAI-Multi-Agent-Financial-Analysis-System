# Social Sentiment Service
# ==========================
# Scrape and analyze Reddit sentiment for stocks

import requests
import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SocialSentimentService:
    """
    Fetch and analyze social media sentiment for stocks.
    Uses Reddit's public JSON API (no authentication required).
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        }
        
        # Subreddits relevant for stock analysis
        self.subreddits = ["wallstreetbets", "stocks", "investing", "stockmarket"]
    
    def _fetch_reddit_posts(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch Reddit posts mentioning a ticker."""
        all_posts = []
        
        for subreddit in self.subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    "q": ticker,
                    "restrict_sr": 1,
                    "sort": "new",
                    "limit": limit,
                    "t": "week"
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    
                    for child in children:
                        post_data = child.get("data", {})
                        all_posts.append({
                            "title": post_data.get("title", ""),
                            "text": post_data.get("selftext", "")[:500],  # Limit text length
                            "score": post_data.get("score", 0),
                            "num_comments": post_data.get("num_comments", 0),
                            "subreddit": subreddit,
                            "created": datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat(),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch from r/{subreddit}: {e}")
                continue
        
        # Sort by score (most upvoted first)
        all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_posts[:limit]
    
    def _simple_sentiment_score(self, text: str) -> float:
        """
        Simple keyword-based sentiment scorer.
        Returns -1 to +1 score based on bullish/bearish keywords.
        """
        text_lower = text.lower()
        
        bullish_words = [
            "buy", "long", "bullish", "moon", "rocket", "calls", "up", 
            "green", "breakout", "strong", "undervalued", "hold", "diamond",
            "gain", "profit", "winner", "rally", "surge"
        ]
        
        bearish_words = [
            "sell", "short", "bearish", "crash", "puts", "down", "red",
            "dump", "weak", "overvalued", "avoid", "paper", "loss",
            "losing", "loser", "drop", "plunge", "tank"
        ]
        
        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0
        
        return (bullish_count - bearish_count) / total
    
    def get_social_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Get aggregated social sentiment for a stock.
        
        Returns:
            Dict with sentiment score, label, mention count, and sample posts
        """
        try:
            posts = self._fetch_reddit_posts(ticker.upper(), limit=20)
            
            if not posts:
                return {
                    "ticker": ticker.upper(),
                    "platform": "reddit",
                    "mention_count": 0,
                    "sentiment_score": 0,
                    "sentiment_label": "Neutral",
                    "posts": []
                }
            
            # Calculate aggregate sentiment
            total_score = 0
            weighted_total = 0
            
            for post in posts:
                text = f"{post.get('title', '')} {post.get('text', '')}"
                sentiment = self._simple_sentiment_score(text)
                weight = max(1, post.get("score", 1) / 100)  # Weight by upvotes
                
                total_score += sentiment * weight
                weighted_total += weight
            
            avg_sentiment = total_score / weighted_total if weighted_total > 0 else 0
            
            # Determine label
            if avg_sentiment > 0.2:
                label = "Bullish"
            elif avg_sentiment < -0.2:
                label = "Bearish"
            else:
                label = "Mixed"
            
            return {
                "ticker": ticker.upper(),
                "platform": "reddit",
                "mention_count": len(posts),
                "sentiment_score": round(avg_sentiment, 2),
                "sentiment_label": label,
                "posts": posts[:5]  # Return top 5 posts
            }
            
        except Exception as e:
            logger.error(f"Error getting social sentiment for {ticker}: {e}")
            return {
                "ticker": ticker.upper(),
                "platform": "reddit",
                "mention_count": 0,
                "sentiment_score": 0,
                "sentiment_label": "Unknown",
                "error": str(e),
                "posts": []
            }


# Singleton instance
social_sentiment = SocialSentimentService()
