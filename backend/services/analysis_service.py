import sys
import os
import asyncio
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import yfinance as yf
import logging
import requests
from crewai import Agent, Task, Crew, Process, LLM

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from core.src.analysis import QuantitativeAnalyst
from core.src.visuals import Visualizer, PDFGenerator
from core.sentiment_agent.crew import KPI_FHI_Crew
from core.sentiment_agent.ingestion import fetch_company_data
from services.chroma_service import ChromaService
from services.embedding_service import EmbeddingService
from services.sentiment_history_service import sentiment_history
from config import settings
from core.api_manager import api_manager

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Complete analysis pipeline integrating all predict_report features:
    - Prophet forecasting
    - FinBERT sentiment analysis
    - Financial Health Index (FHI)
    - Investment recommendation engine
    - PDF report generation via Multi-Agent CrewAI
    """
    
    def __init__(self):
        self.analyst = QuantitativeAnalyst()
        self.visualizer = Visualizer()
        self.pdf_generator = PDFGenerator()
        self.api_manager = api_manager
        
        # Initialize LLM for the report writer
        # Set verbose=False to avoid flooding the terminal with CrewAI failure boxes on quota issues
        self.llm = LLM(
            model=f"gemini/{settings.LLM_MODEL}",
            verbose=False,
            temperature=settings.LLM_TEMPERATURE,
            api_key=self.api_manager.get_key()
        )
    
    async def run_full_pipeline(
        self,
        ticker: str,
        user_id: str,
        include_forecast: bool = True,
        include_sentiment: bool = True,
        include_recommendation: bool = True,
        document_ids: Optional[List[str]] = None,
        forecast_days: int = 30,
        custom_questions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete equity research pipeline.
        
        Returns:
            Dictionary with all analysis results
        """
        result = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "stock_info": None,
            "forecast": None,
            "sentiment": None,
            "fhi": None,
            "recommendation": None,
            "report_path": None,
            "chart_url": None
        }
        
        try:
            # 1. Fetch stock data
            logger.info(f"Fetching stock data for {ticker}")
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="2y")
            
            result["stock_info"] = {
                "name": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency", "USD")
            }
            
            # 2. Run Prophet forecast
            if include_forecast and not hist.empty:
                logger.info(f"Running Prophet forecast for {forecast_days} days")
                df = self.analyst.calculate_technicals(hist)
                target_price, trend, forecast_df, model = self.analyst.predict_future_price(df, days_ahead=forecast_days)
                
                result["forecast"] = {
                    "target_price": round(target_price, 2),
                    "trend": trend,
                    "days": forecast_days,
                    "current_price": float(hist['Close'].iloc[-1])
                }
                
                # Generate chart
                if forecast_df is not None and not forecast_df.empty:
                    # Serialize forecast data for interactive UI
                    forecast_points = []
                    for _, row in forecast_df.iterrows():
                        forecast_points.append({
                            "date": row['ds'].strftime('%Y-%m-%d'),
                            "yhat": round(row['yhat'], 2),
                            "yhat_lower": round(row['yhat_lower'], 2),
                            "yhat_upper": round(row['yhat_upper'], 2)
                        })
                    
                    result["forecast"]["points"] = forecast_points

                    currency = "INR" if ticker.endswith((".NS", ".BO")) else "USD"
                    # Generate a unique chart filename to avoid caching issues
                    chart_filename = f"{ticker}_{forecast_days}d_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                    chart_path = os.path.join("output", chart_filename)
                    
                    self.visualizer.generate_charts(df, ticker, forecast_df, currency, custom_path=chart_path)
                    
                    if os.path.exists(chart_path):
                        result["chart_path"] = chart_path
                        result["chart_url"] = f"/charts/{chart_filename}"
            
            # 3. Run Sentiment + FHI + Recommendation
            if include_sentiment or include_recommendation:
                logger.info("Running sentiment and FHI analysis")
                try:
                    # Fetch company data for sentiment analysis
                    payload = fetch_company_data(ticker)
                    
                    # Run the full crew pipeline
                    sentiment_crew = KPI_FHI_Crew(verbose=True)
                    crew_results = sentiment_crew.run(payload)
                    
                    analysis = crew_results.get('analysis', {})
                    rec = crew_results.get('recommendation', {})
                    reasoning = rec.get('reasoning', {})
                    
                    if include_sentiment:
                        compound = analysis.get('sentiment', {}).get('compound', 0)
                        fhi_score = analysis.get('fhi', {}).get('score', 0)
                        fhi_grade = analysis.get('fhi', {}).get('grade') or self._calculate_fhi_grade(fhi_score)
                        
                        result["sentiment"] = {
                            "compound": compound,
                            "label": "Positive" if compound > 0 else "Negative"
                        }
                        
                        result["fhi"] = {
                            "score": round(fhi_score, 2) if isinstance(fhi_score, (int, float)) else fhi_score,
                            "grade": fhi_grade
                        }
                        
                        # Save to sentiment history for trend tracking
                        sentiment_history.save_sentiment(ticker, {
                            "compound": compound,
                            "label": result["sentiment"]["label"],
                            "fhi_score": fhi_score,
                            "fhi_grade": fhi_grade
                        })
                    
                    if include_recommendation:
                        result["recommendation"] = {
                            "rating": rec.get('rating', 'HOLD'),
                            "confidence": rec.get('confidence', 0),
                            "final_score": rec.get('final_score', 0),
                            "risk_level": rec.get('risk_level') or reasoning.get('risk_level', 'Unknown'),
                            "reasoning": reasoning.get('analysis', '')
                        }
                    
                    # Store full results for PDF generation
                    result["_crew_results"] = crew_results
                    
                except Exception as e:
                    logger.error(f"Sentiment/FHI analysis failed: {e}")
                    result["sentiment"] = {"error": str(e)}
            
            # 4. Generate Professional Report Body via CrewAI
            logger.info("Generating report body via CrewAI")
            doc_context = ""
            if document_ids:
                doc_context = await self._get_rag_context(user_id, ticker, document_ids)
            
            report_body = await self._generate_crew_report_body(result, doc_context, custom_questions)
            
            # 4b. Fetch YouTube videos for the ticker
            logger.info(f"Fetching YouTube videos for {ticker}")
            videos = await self._fetch_youtube_videos(ticker, limit=7)
            result["videos"] = videos
            
            # Append YouTube links to report body
            if videos:
                video_links_section = "\n\n## Related Videos\n"
                for vid in videos:
                    video_links_section += f"- [{vid['title']}]({vid['link']}) by {vid['channel']}\n"
                report_body += video_links_section
            
            result["report_body"] = report_body
            
            # 5. Generate PDF report
            if result.get("_crew_results") or result.get("report_body"):
                logger.info("Generating PDF report file")
                try:
                    report_path = self.pdf_generator.create_crew_pdf(
                        result.get("report_body", ""),
                        ticker,
                        sentiment_data=result.get("_crew_results"),
                        chart_path=result.get("chart_path")
                    )
                    
                    # Move to user's reports folder
                    user_reports_dir = f"./reports/{user_id}"
                    os.makedirs(user_reports_dir, exist_ok=True)
                    
                    import shutil
                    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                    base_filename = f"{ticker}_{timestamp_str}"
                    final_pdf_path = os.path.join(user_reports_dir, f"{base_filename}.pdf")
                    final_json_path = os.path.join(user_reports_dir, f"{base_filename}.json")
                    
                    shutil.move(report_path, final_pdf_path)
                    
                    # Save JSON result
                    # Remove non-serializable objects before saving
                    json_result = result.copy()
                    json_result.pop("_crew_results", None)
                    with open(final_json_path, 'w') as f:
                        json.dump(json_result, f, indent=2, default=str)
                    
                    result["report_path"] = final_pdf_path
                    
                    # 6. Auto-upload report to knowledge base for RAG
                    logger.info("Uploading report to knowledge base for RAG")
                    try:
                        chroma = ChromaService(user_id)
                        embedder = EmbeddingService()
                        report_doc_id = f"report_{base_filename}"
                        
                        # Build comprehensive report text for embedding (use result dict for safety)
                        r_rec = result.get("recommendation") or {}
                        r_fhi = result.get("fhi") or {}
                        r_sent = result.get("sentiment") or {}
                        r_fc = result.get("forecast") or {}
                        
                        report_content = f"""
STOCK RESEARCH REPORT - {ticker}
Generated: {timestamp_str}

RATING: {r_rec.get('rating', 'N/A')}
RISK LEVEL: {r_rec.get('risk_level', 'N/A')}
CONFIDENCE: {r_rec.get('confidence', 0):.0%}

FINANCIAL HEALTH INDEX: {r_fhi.get('score', 'N/A')}/100 (Grade: {r_fhi.get('grade', 'N/A')})
SENTIMENT SCORE: {r_sent.get('compound', 0) if isinstance(r_sent.get('compound'), (int, float)) else 0:.2f} ({r_sent.get('label', 'Neutral')})
FORECAST TREND: {r_fc.get('trend', 'N/A')} (Target: ${r_fc.get('target_price', 'N/A')})

ANALYSIS BODY:
{report_body}
"""
                        chunks_created = await chroma.ingest_report_text(
                            report_text=report_content,
                            document_id=report_doc_id,
                            filename=f"{ticker} Research Report ({timestamp_str})",
                            ticker=ticker,
                            report_type="research_report",
                            embedding_service=embedder,
                            extra_metadata={
                                "rating": r_rec.get('rating'),
                                "risk_level": r_rec.get('risk_level'),
                                "fhi_score": r_fhi.get('score'),
                                "sentiment": r_sent.get('compound'),
                                "forecast_trend": r_fc.get('trend')
                            }
                        )
                        logger.info(f"Report uploaded to knowledge base: {chunks_created} chunks")
                    except Exception as e:
                        logger.warning(f"Failed to upload report to knowledge base: {e}")
                        # Non-fatal error, report still generated successfully
                        
                except Exception as e:
                    logger.error(f"Report/JSON generation failed: {e}")
            
            # Clean up internal data
            result.pop("_crew_results", None)
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline error for {ticker}: {e}")
            result["error"] = str(e)
            return result
    
    async def _get_rag_context(self, user_id: str, ticker: str, document_ids: List[str]) -> str:
        """Retrieve relevant context from uploaded documents."""
        try:
            chroma = ChromaService(user_id)
            embedder = EmbeddingService()
            
            # Fetch most relevant chunks from ALL selected documents at once
            search_query = f"{ticker} financial performance metrics and strategic outlook"
            results = await chroma.search(
                query=search_query,
                top_k=10,
                embedding_service=embedder,
                document_ids=document_ids
            )
            
            if not results:
                return "No relevant document context found for this analysis."
            
            context = "\n\n".join([f"[Source: {r['source']}]\n{r['content']}" for r in results])
            return context
        except Exception as e:
            logger.error(f"Failed to get RAG context: {e}")
            return ""

    async def _generate_crew_report_body(self, result: Dict[str, Any], doc_context: str = "", custom_questions: Optional[str] = None) -> str:
        """Generate a professional report using CrewAI agents."""
        ticker = result["ticker"]
        fhi = result.get("fhi") or {}
        sent = result.get("sentiment") or {}
        rec = result.get("recommendation") or {}
        fc = result.get("forecast") or {}
        
        # Build document section for prompt
        doc_section = ""
        if doc_context:
            doc_section = f"""
            **UPLOADED DOCUMENT CONTEXT:**
            The following excerpts are from uploaded financial documents. Use this information to enhance your analysis:
            
            {doc_context[:10000]}
            """
            
        # Retry logic for CrewAI report generation
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # ------------------------------------------------------------------
                # RECREATE AGENTS & CREW INSIDE RETRY LOOP (Ensures provider/key rotation)
                # ------------------------------------------------------------------
                logger.info(f"CrewAI attempt {attempt + 1}/{max_retries}")
                
                # Force update LLM with current key/provider settings
                active_provider = self.api_manager.get_active_provider()
                current_key = self.api_manager.get_key()
                
                # Determine model based on provider
                if active_provider == "google":
                    llm_model_path = f"gemini/{settings.LLM_MODEL}"
                else:
                    llm_model_path = settings.GROQ_MODEL
                    
                logger.info(f"Setting up Analysis LLM: Provider={active_provider}, Model={llm_model_path}")
                
                self.llm = LLM(
                    model=llm_model_path,
                    verbose=True,
                    temperature=settings.LLM_TEMPERATURE,
                    api_key=current_key
                )
                
                # Define agents with fresh LLM instance
                researcher = Agent(
                    role='Lead Quantitative & Market Strategist',
                    goal=f'Conduct a deep-dive technical and fundamental analysis for {ticker}, looking beyond the surface metrics.',
                    backstory="""You are a high-stakes quantitative analyst at a top-tier hedge fund. 
                    You excel at connecting the dots between sentiment, financial health (FHI), and raw document context.""",
                    verbose=True,
                    llm=self.llm
                )
                
                writer = Agent(
                    role='Principal Equity Research Analyst',
                    goal='Synthesize complex analytical data into a high-density, professional investment brief.',
                    backstory="""You are a veteran Wall Street research director. You have no patience for fluff.""",
                    verbose=True,
                    llm=self.llm
                )
                
                # Define tasks
                task_research = Task(
                    description=f"Conduct exhaustive research for {ticker} using FHI: {fhi.get('score')}, Sentiment: {sent.get('compound')}. {doc_section}",
                    agent=researcher,
                    expected_output="High-density summary of investigative findings."
                )
                
                # Define report instructions
                # Build custom questions section outside f-string to avoid backslash issues
                custom_questions_section = ""
                if custom_questions:
                    custom_questions_section = "USER CUSTOM QUESTIONS (Address these specifically in the report):\n" + custom_questions
                
                report_instruction = f"""
                ACTUALLY WRITE a High-Density Professional Equity Research Report for {ticker}.
                
                CRITICAL: YOU MUST USE THE EXACT SECTION TITLES BELOW TO TRIGGER INTERACTIVE UI MODULES.
                
                STRUCTURE AND FORMATTING RULES:
                - Use standard Markdown headers (e.g. ## Section Title).
                - Do not use "Title:" format. Just ## Title.
                - Write directly. No filler.
                
                MANDATORY SECTIONS:
                
                1. ## Executive Summary
                   - Provide a high-level overview.
                   - Include a brief SWOT analysis based on the data.
                
                2. ## Key Performance Indicators (Technical Outlook)
                   - CRITICAL: You MUST provide 3-5 technical metrics with percentage confidence or values.
                   - Format: **Metric Name**: Value% (e.g., **Bullish Momentum**: 85%, **RSI Health**: 60%)
                   - This section drives the Radar Chart.
                   
                3. ## Risk Signals & Strengths (Financial Health)
                   - Analyze the FHI Score ({fhi.get('score', 'N/A')}) and Sentiment ({sent.get('compound', 0):.2f}).
                   - List distinct bullet points for Risks and Strengths.
                   - This section drives the Signals Module.
                   
                4. ## Strategic Actions (Investment Case)
                   - Synthesize the final verdict for the **{rec.get('rating', 'HOLD')}** rating.
                   - Provide 3 clear, actionable steps for the investor (e.g., "Wait for pullback to $150").
                   - This section drives the Actions Stepper.
                
                {f'''5. ## Custom Questions Response
                   - IMPORTANT: The user has asked specific questions that MUST be addressed.
                   - Answer each question clearly and directly based on your analysis.
                   - User Questions: {custom_questions}
                ''' if custom_questions else ''}
                
                MANDATORY DATA TO INTEGRATE:
                - Ticker: {ticker}
                - FHI Score: {fhi.get('score', 'N/A')}/100
                - Sentiment Score: {sent.get('compound', 0):.2f}
                - Investment Rating: {rec.get('rating', 'HOLD')}
                - Forecast Trend: {fc.get('trend', 'N/A')}
                
                OUTPUT FORMAT:
                Wrap the entire report in ---REPORT_START--- and ---REPORT_END---.
                """

                task_write = Task(
                    description=report_instruction,
                    agent=writer,
                    expected_output="Final research report wrapped in ---REPORT_START--- and ---REPORT_END---."
                )
                
                crew = Crew(
                    agents=[researcher, writer],
                    tasks=[task_research, task_write],
                    verbose=True,
                    process=Process.sequential
                )

                # Run crew
                loop = asyncio.get_event_loop()
                crew_result = await loop.run_in_executor(None, crew.kickoff)
                
                full_text = str(crew_result)
                return self.clean_llm_output(full_text)
                
            except Exception as e:
                logger.error(f"CrewAI attempt {attempt + 1} failed: {e}")
                if "429" in str(e) or "quota" in str(e).lower() or "limit" in str(e).lower():
                    logger.warning("🔄 Quota/Limit reached in Analysis loop. Triggering Multi-Provider Rotation.")
                    rotation_data = self.api_manager.rotate_key()
                    logger.info(f"Rotation successful. New destination: {rotation_data.get('provider')} ({rotation_data.get('model')})")
                    
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.info(f"Retrying in {wait_time} seconds with new provider...")
                        await asyncio.sleep(wait_time)
                        continue
                
                # If it's not a retryable error or we're out of retries
                if attempt == max_retries - 1:
                    logger.error("All CrewAI retries failed. Falling back to basic report.")
                    return self._build_report_text(result)
        
        return self._build_report_text(result) # Final fallback

    @staticmethod
    def clean_llm_output(text: str) -> str:
        """Extract report content between delimiters and cleanup artifacts."""
        pattern = r"---REPORT_START---(.*?)---REPORT_END---"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        
        # Remove common AI artifacts
        text = re.sub(r'(?i)^(I must|Drafting|Plan:|Thought:|Mandatory Data:|Structure:).*', '', text, flags=re.MULTILINE)
        text = re.sub(r'(?i)^\*?\s*Disclaimer:.*', '', text, flags=re.MULTILINE)
        
        return text.strip()

    def _calculate_fhi_grade(self, score: float) -> str:
        """Calculate letter grade from FHI score."""
        if score is None or score == 0:
            return "N/A"
        try:
            score = float(score)
            if score >= 80: return "A"
            if score >= 70: return "B"
            if score >= 60: return "C"
            if score >= 50: return "D"
            if score >= 40: return "E"
            return "F"
        except:
            return "N/A"
    
    def _build_report_text(self, result: Dict[str, Any]) -> str:
        """Build a detailed markdown report text as a fallback when LLM is unavailable."""
        sections = []
        ticker = result.get('ticker', 'N/A')
        
        sections.append(f"# Executive Research Report: {ticker}\n")
        sections.append(f"Generated via High-Fidelity Quantitative Engine on {result.get('timestamp', '')[:10]}\n")
        
        if result.get("recommendation"):
            rec = result["recommendation"]
            sections.append(f"\n## 🎯 Investment Recommendation: {rec.get('rating', 'N/A')}")
            sections.append(f"- **Confidence Score**: {rec.get('confidence', 0) * 100:.0f}%")
            sections.append(f"- **Risk Level**: {rec.get('risk_level', 'Moderate')}")
            
            if rec.get("reasoning"):
                sections.append(f"\n### 📝 Strategic Rationale")
                sections.append(rec["reasoning"])
        
        sections.append(f"\n## 📊 Market Vitals")
        if result.get("stock_info"):
            si = result["stock_info"]
            sections.append(f"- **Company**: {si.get('name', ticker)}")
            sections.append(f"- **Sector**: {si.get('sector', 'N/A')}")
            sections.append(f"- **Current Price**: {si.get('currency', '$')}{si.get('current_price', 'N/A')}")

        if result.get("fhi"):
            fhi = result["fhi"]
            sections.append(f"\n## 🛡️ Financial Health & Sentiment")
            sections.append(f"- **FHI Score**: {fhi.get('score', 'N/A')}/100 (Grade: {fhi.get('grade', 'N/A')})")
            
            if result.get("sentiment"):
                sent = result["sentiment"]
                sections.append(f"- **Sentiment Sentiment Score**: {sent.get('compound', 0):.2f} ({sent.get('label', 'Neutral')})")
                sections.append(f"- **Tone Analysis**: Management exhibits a predominantly {sent.get('label', 'neutral').lower()} outlook on recent performance.")
        
        if result.get("forecast"):
            fc = result["forecast"]
            sections.append(f"\n## 📈 Performance Outlook")
            sections.append(f"- **{fc.get('days', 30)}-Day Trajectory**: {fc.get('trend', 'N/A')}")
            sections.append(f"- **Algorithmic Target**: {result.get('stock_info', {}).get('currency', '$')}{fc.get('target_price', 0):.2f}")
            sections.append(f"- **Trend Analysis**: Quantitative modeling indicates a {fc.get('trend', 'neutral').lower()} price action over the next quarter.")
        
        sections.append(f"\n\n---")
        sections.append(f"*Note: This report was generated using core quantitative analytics as the AI-augmented drafting service is currently experiencing high volume.*")
        
        return "\n".join(sections)
    
    async def run_sentiment_only(self, ticker: str) -> Dict[str, Any]:
        """Run sentiment analysis only."""
        return await self.run_full_pipeline(
            ticker=ticker,
            user_id="temp",
            include_forecast=False,
            include_sentiment=True,
            include_recommendation=False
        )
    
    async def run_forecast_only(self, ticker: str) -> Dict[str, Any]:
        """Run Prophet forecast only."""
        return await self.run_full_pipeline(
            ticker=ticker,
            user_id="temp",
            include_forecast=True,
            include_sentiment=False,
            include_recommendation=False
        )
    
    async def run_recommendation_only(self, ticker: str) -> Dict[str, Any]:
        """Run recommendation engine only."""
        return await self.run_full_pipeline(
            ticker=ticker,
            user_id="temp",
            include_forecast=False,
            include_sentiment=True,
            include_recommendation=True
        )
    
    async def _fetch_youtube_videos(self, ticker: str, limit: int = 4) -> List[Dict[str, Any]]:
        """Fetch YouTube videos for a ticker using direct scraping."""
        try:
            search_query = f"{ticker} stock analysis"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            url = f"https://www.youtube.com/results?search_query={search_query}"
            response = requests.get(url, headers=headers, timeout=10)
            
            videos = []
            
            # Extract ytInitialData
            match = re.search(r'var ytInitialData = ({.*?});', response.text)
            if match:
                data = json.loads(match.group(1))
                
                try:
                    contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
                    
                    for item in contents:
                        if 'videoRenderer' in item:
                            video = item['videoRenderer']
                            
                            video_id = video.get('videoId')
                            title = video.get('title', {}).get('runs', [{}])[0].get('text', 'No Title')
                            channel = video.get('ownerText', {}).get('runs', [{}])[0].get('text', 'Unknown Channel')
                            link = f"https://www.youtube.com/watch?v={video_id}"
                            
                            thumbs = video.get('thumbnail', {}).get('thumbnails', [])
                            thumbnail = thumbs[-1]['url'] if thumbs else ""
                            
                            videos.append({
                                "title": title,
                                "link": link,
                                "channel": channel,
                                "thumbnail": thumbnail
                            })
                            
                            if len(videos) >= limit:
                                break
                except Exception as parse_err:
                    logger.warning(f"Failed to parse YouTube JSON: {parse_err}")
                    
            return videos
            
        except Exception as e:
            logger.error(f"Error fetching YouTube videos for {ticker}: {e}")
            return []
