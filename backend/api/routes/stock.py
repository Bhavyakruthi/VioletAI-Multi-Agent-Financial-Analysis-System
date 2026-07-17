# Stock Routes
# =============
# Stock data fetching endpoints using yfinance

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import yfinance as yf
import logging
from youtubesearchpython import VideosSearch

from api.dependencies import get_current_user
from services.sentiment_history_service import sentiment_history
from services.social_sentiment_service import social_sentiment
from services.stocktwits_service import stocktwits_service
from services.twitter_sentiment_service import twitter_sentiment

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class StockInfo(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None


class StockPrice(BaseModel):
    ticker: str
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    volume: Optional[int] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    risk_score: Optional[float] = None  # Added for risk assessment (0-100)


class HistoricalData(BaseModel):
    ticker: str
    period: str
    data: List[Dict[str, Any]]


class NewsItem(BaseModel):
    title: str
    link: str
    publisher: Optional[str] = None
    published: Optional[str] = None


class VideoItem(BaseModel):
    title: str
    link: str
    thumbnail: str
    channel: str
    published: str
    description: str  # Truncated description as summary



class MarketIndex(BaseModel):
    symbol: str
    value: str
    change: str
    up: bool


# ============================================================================
# Routes
# ============================================================================

@router.get("/market/indices", response_model=List[MarketIndex])
async def get_market_indices(
    current_user: dict = Depends(get_current_user)
):
    """
    Get real-time market indices (S&P 500, NASDAQ, BTC, GOLD).
    """
    indices_map = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "BTC-USD": "BTC",
        "GC=F": "GOLD"
    }
    
    try:
        tickers = list(indices_map.keys())
        # Fetch data in batch (although yfinance might do sequential internal calls for info)
        # Using Ticker/Tickers
        results = []
        
        for symbol, name in indices_map.items():
            try:
                ticker = yf.Ticker(symbol)
                fast_info = getattr(ticker, 'fast_info', None)
                
                if fast_info is not None:
                    price = getattr(fast_info, 'last_price', None)
                    prev_close = getattr(fast_info, 'previous_close', None)
                else:
                    price = None
                    prev_close = None
                
                # Fallback to history if fast_info fails
                if price is None or prev_close is None:
                    hist = ticker.history(period="2d")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                        prev_close = hist['Close'].iloc[0] if len(hist) > 1 else price
                
                if price is not None and prev_close is not None:
                    change_amount = price - prev_close
                    change_pct = (change_amount / prev_close) * 100 if prev_close != 0 else 0
                    
                    # Format
                    formatted_value = f"{price:,.2f}"
                    formatted_change = f"{abs(change_pct):.1f}%"
                    is_up = change_amount >= 0
                    
                    # Add sign
                    sign = "+" if is_up else "-"
                    formatted_change = f"{sign}{formatted_change}"
                    
                    results.append(MarketIndex(
                        symbol=name,
                        value=formatted_value,
                        change=formatted_change,
                        up=is_up
                    ))
                else:
                    raise ValueError("Could not retrieve price data")
                    
            except Exception as e:
                logger.error(f"Error fetching index {symbol}: {e}")
                
        return results
        
    except Exception as e:
        logger.error(f"Error fetching market indices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@router.get("/{ticker}", response_model=StockPrice)

async def get_stock_data(
    ticker: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get current stock price and basic metrics.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        
        change = None
        change_percent = None
        if current_price and previous_close:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
        
        # Calculate Risk Score (0-100)
        # Calculate Risk Score (0-100)
        # Weighted Mult-Factor Model:
        # 1. Market Risk (Beta): 40%
        # 2. Financial Leverge (Debt/Equity): 30%
        # 3. Price Volatility (52w High/Low Spread): 30%
        
        risk_score = 50.0 # Baseline
        
        # 1. Beta Impact (1.0 is neutral)
        beta = info.get("beta")
        if beta:
            # Beta > 1 increases risk, < 1 decreases
            # e.g., Beta 1.5 -> +12.5 points
            beta_impact = (beta - 1.0) * 25
            risk_score += beta_impact
            
        # 2. Debt/Equity Impact
        de_ratio = info.get("debtToEquity")
        if de_ratio:
            # D/E is usually returned as %, so 100 is 1.0 ratio
            # Ratio > 150% is getting risky
            if de_ratio > 200:
                risk_score += 15
            elif de_ratio > 100:
                risk_score += 10
            elif de_ratio < 50:
                risk_score -= 5
                
        # 3. Volatility Impact (52 Week Spread)
        high52 = info.get("fiftyTwoWeekHigh")
        low52 = info.get("fiftyTwoWeekLow")
        if high52 and low52 and low52 > 0:
            volatility = ((high52 - low52) / low52) * 100
            # >50% spread is volatile for large caps, normal for growth
            if volatility > 100: # Very volatile
                risk_score += 20
            elif volatility > 50:
                risk_score += 10
            elif volatility < 20: # Stable
                risk_score -= 10
                
        # Clamp score 0-100
        risk_score = min(max(risk_score, 10), 99)
        
        return StockPrice(
            ticker=ticker,
            current_price=current_price,
            previous_close=previous_close,
            open=info.get("open") or info.get("regularMarketOpen"),
            day_high=info.get("dayHigh") or info.get("regularMarketDayHigh"),
            day_low=info.get("dayLow") or info.get("regularMarketDayLow"),
            volume=info.get("volume") or info.get("regularMarketVolume"),
            change=round(change, 2) if change else None,
            change_percent=round(change_percent, 2) if change_percent else None,
            risk_score=round(risk_score, 1)
        )
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {ticker}: {e}")
        raise HTTPException(status_code=404, detail=f"Could not fetch data for ticker: {ticker}")


@router.get("/{ticker}/info", response_model=StockInfo)
async def get_stock_info(
    ticker: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed company information.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return StockInfo(
            ticker=ticker,
            name=info.get("longName") or info.get("shortName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=info.get("marketCap"),
            currency=info.get("currency"),
            exchange=info.get("exchange")
        )
        
    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {e}")
        raise HTTPException(status_code=404, detail=f"Could not fetch info for ticker: {ticker}")


@router.get("/{ticker}/history", response_model=HistoricalData)
async def get_stock_history(
    ticker: str,
    period: str = Query(default="1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get historical price data.
    """
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Use one of: {valid_periods}")
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        data = []
        for index, row in hist.iterrows():
            data.append({
                "date": index.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"])
            })
        
        return HistoricalData(
            ticker=ticker,
            period=period,
            data=data
        )
        
    except Exception as e:
        logger.error(f"Error fetching history for {ticker}: {e}")
        raise HTTPException(status_code=404, detail=f"Could not fetch history for ticker: {ticker}")


@router.get("/{ticker}/news", response_model=List[NewsItem])
async def get_stock_news(
    ticker: str,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent news for a stock.
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news[:limit] if stock.news else []
        
        return [
            NewsItem(
                title=item.get("title", ""),
                link=item.get("link", ""),
                publisher=item.get("publisher"),
                published=datetime.fromtimestamp(item.get("providerPublishTime", 0)).isoformat()
                if item.get("providerPublishTime") else None
            )
            for item in news
        ]
        
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        raise HTTPException(status_code=404, detail=f"Could not fetch news for ticker: {ticker}")



@router.get("/{ticker}/videos", response_model=List[VideoItem])
async def get_stock_videos(
    ticker: str,
    limit: int = Query(default=4, ge=1, le=10),
    current_user: dict = Depends(get_current_user)
):
    """
    Get relevant YouTube videos for a stock using direct scraping (bypass broken library).
    """
    try:
        search_query = f"{ticker} stock analysis"
        
        # Custom extraction logic using requests + regex to avoid library issues
        import requests
        import re
        import json
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        url = f"https://www.youtube.com/results?search_query={search_query}"
        response = requests.get(url, headers=headers)
        
        video_items = []
        
        # Extract ytInitialData
        match = re.search(r'var ytInitialData = ({.*?});', response.text)
        if match:
            data = json.loads(match.group(1))
            
            # Navigate deep JSON structure to find videos
            try:
                contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
                
                for item in contents:
                    if 'videoRenderer' in item:
                        video = item['videoRenderer']
                        
                        # Extract basic info
                        video_id = video.get('videoId')
                        title = video.get('title', {}).get('runs', [{}])[0].get('text', 'No Title')
                        
                        # Extract generic description
                        desc_runs = video.get('detailedMetadataSnippets', [{}])[0].get('snippetText', {}).get('runs', [])
                        description = "".join([r.get('text', '') for r in desc_runs])
                        
                        if not description:
                             description = "".join([r.get('text', '') for r in video.get('descriptionSnippet', {}).get('runs', [])])
                        
                        # Extract channel name
                        channel = video.get('ownerText', {}).get('runs', [{}])[0].get('text', 'Unknown Channel')
                        
                        # Extract published time
                        published = video.get('publishedTimeText', {}).get('simpleText', 'Recently')
                        
                        # Construct link
                        link = f"https://www.youtube.com/watch?v={video_id}"
                        
                        # Extract thumbnail (highest res available)
                        thumbs = video.get('thumbnail', {}).get('thumbnails', [])
                        thumbnail = thumbs[-1]['url'] if thumbs else ""

                        video_items.append(
                            VideoItem(
                                title=title,
                                link=link,
                                thumbnail=thumbnail,
                                channel=channel,
                                published=published,
                                description=description[:150] + "..." if len(description) > 150 else (description or "Watch for analysis.")
                            )
                        )
                        
                        if len(video_items) >= limit:
                            break
            except Exception as parse_err:
                logger.warning(f"Failed to parse YouTube JSON structure: {parse_err}")
                
        if not video_items:
             logger.warning(f"No videos found for {ticker} via scraper.")
             
        return video_items
        
    except Exception as e:
        logger.error(f"Error fetching videos for {ticker}: {e}")
        # Return empty list instead of erroring out UI
        return []


@router.get("/{ticker}/sentiment-history")
async def get_sentiment_history(
    ticker: str,
    days: int = Query(default=30, ge=7, le=90),
    current_user: dict = Depends(get_current_user)
):
    """
    Get historical sentiment scores for a stock over time.
    Used for trend visualization.
    """
    try:
        history = sentiment_history.get_history(ticker.upper(), days=days)
        trend = sentiment_history.get_trend(ticker.upper())
        
        return {
            "ticker": ticker.upper(),
            "days": days,
            "trend": trend,
            "data": history
        }
    except Exception as e:
        logger.error(f"Error fetching sentiment history for {ticker}: {e}")
        return {"ticker": ticker.upper(), "days": days, "trend": None, "data": []}


@router.get("/{ticker}/social-sentiment")
async def get_social_sentiment(
    ticker: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get social media sentiment for a stock.
    Analyzes Reddit posts from r/wallstreetbets, r/stocks, etc.
    """
    try:
        result = social_sentiment.get_social_sentiment(ticker.upper())
        return result
    except Exception as e:
        logger.error(f"Error fetching social sentiment for {ticker}: {e}")
        return {
            "ticker": ticker.upper(),
            "platform": "reddit",
            "mention_count": 0,
            "sentiment_score": 0,
            "sentiment_label": "Unknown",
            "error": str(e),
            "posts": []
        }

@router.get("/{ticker}/stocktwits")
async def get_stocktwits_sentiment(
    ticker: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get StockTwits sentiment for a stock.
    """
    try:
        result = stocktwits_service.get_stocktwits_sentiment(ticker.upper())
        return result
    except Exception as e:
        logger.error(f"Error fetching StockTwits for {ticker}: {e}")
        return {
            "ticker": ticker.upper(),
            "platform": "stocktwits",
            "mention_count": 0,
            "sentiment_score": 0,
            "sentiment_label": "Unknown",
            "error": str(e),
            "messages": []
        }

@router.get("/{ticker}/twitter-sentiment")
async def get_twitter_sentiment(
    ticker: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get Twitter/X sentiment for a stock.
    """
    try:
        result = twitter_sentiment.get_twitter_sentiment(ticker.upper())
        return result
    except Exception as e:
        logger.error(f"Error fetching Twitter for {ticker}: {e}")
        return {
            "ticker": ticker.upper(),
            "platform": "twitter",
            "mention_count": 0,
            "sentiment_score": 0,
            "sentiment_label": "Unknown",
            "error": str(e),
            "posts": []
        }


@router.get("/market/news", response_model=List[NewsItem])
async def get_market_news(
    limit: int = Query(default=20, ge=5, le=100)
):
    """
    Get market news headlines.
    Returns sample financial news for demonstration.
    """
    # Sample financial news headlines
    headlines = [
        ("Tech Stocks Rally as AI Investments Surge", "https://finance.yahoo.com", "Yahoo Finance"),
        ("Federal Reserve Signals Potential Rate Cuts", "https://www.cnbc.com", "CNBC"),
        ("Oil Prices Rise on Supply Concerns", "https://www.reuters.com", "Reuters"),
        ("Major Tech Earnings Beat Expectations", "https://www.bloomberg.com", "Bloomberg"),
        ("Market Volatility Increases Amid Trade Tensions", "https://www.wsj.com", "Wall Street Journal"),
        ("S&P 500 Reaches New Record High", "https://www.marketwatch.com", "MarketWatch"),
        ("Gold Prices Surge as Dollar Weakens", "https://www.kitco.com", "Kitco News"),
        ("Cryptocurrency Market Shows Strong Recovery", "https://www.coindesk.com", "CoinDesk"),
        ("Housing Market Cools as Rates Rise", "https://www.zillow.com", "Zillow"),
        ("Jobless Claims Fall to Lowest Level This Year", "https://www.bls.gov", "Bureau of Labor Statistics"),
    ]
    
    news_items = []
    for title, link, publisher in headlines[:limit]:
        news_items.append(NewsItem(
            title=title,
            link=link,
            publisher=publisher,
            published=datetime.now().isoformat()
        ))
    
    logger.info(f"Returning {len(news_items)} sample news items")
    return news_items


async def get_market_news_fallback(limit: int) -> List[NewsItem]:
    """
    Fallback method using yfinance if NewsAPI fails.
    """
    try:
        # Fetch news from major market tickers
        tickers = ["^GSPC", "^DJI", "^IXIC", "AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        all_news = []
        seen_links = set()
        
        for ticker_symbol in tickers:
            try:
                ticker = yf.Ticker(ticker_symbol)
                if ticker.news:
                    for item in ticker.news[:3]:  # Get top 3 from each
                        link = item.get("link", "")
                        if link and link not in seen_links:
                            seen_links.add(link)
                            all_news.append(NewsItem(
                                title=item.get("title", ""),
                                link=link,
                                publisher=item.get("publisher"),
                                published=datetime.fromtimestamp(item.get("providerPublishTime", 0)).isoformat()
                                if item.get("providerPublishTime") else None
                            ))
                            if len(all_news) >= limit:
                                break
            except Exception as e:
                logger.warning(f"Failed to fetch news for {ticker_symbol}: {e}")
                continue
            
            if len(all_news) >= limit:
                break
        
        # Sort by published date
        all_news.sort(key=lambda x: x.published if x.published else "", reverse=True)
        
        return all_news[:limit]
    except Exception as e:
        logger.error(f"Fallback news fetch failed: {e}")
        raise


