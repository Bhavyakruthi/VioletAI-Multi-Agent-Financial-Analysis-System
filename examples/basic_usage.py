"""
Example Usage of RAG Evidence Agent
===================================
Demonstrates how to use the CrewAI-based RAG system for financial document analysis.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in rag_agent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Also try loading from current directory
load_dotenv()

from rag_agent import RAGEvidenceCrew
from rag_agent.config import RAGConfig, EmbeddingConfig


def main():
    """Main example demonstrating RAG Evidence Agent usage."""
    
    # ========================================================================
    # 1. Initialize the RAG Evidence Crew
    # ========================================================================
    print("=" * 60)
    print("Initializing RAG Evidence Crew...")
    print("=" * 60)
    
    # Create configuration (optional - uses defaults otherwise)
    config = RAGConfig(
        embedding=EmbeddingConfig(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
        ),
        index_dir=Path("data/indices"),
    )
    
    # Initialize the crew
    crew = RAGEvidenceCrew(config=config, verbose=True)
    
    # ========================================================================
    # 2. Ingest Sample Documents
    # ========================================================================
    print("\n" + "=" * 60)
    print("Ingesting sample financial documents...")
    print("=" * 60)
    
    # Sample 10-K excerpt (you would use actual filing content)
    sample_10k = """
    ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS
    
    Overview
    
    We are a global technology company focused on artificial intelligence and cloud computing. 
    Our revenue for fiscal year 2024 was $50.2 billion, representing a 25% increase from the 
    prior year. This growth was primarily driven by strong demand for our cloud services and 
    AI products.
    
    Key Financial Highlights:
    - Total Revenue: $50.2 billion (up 25% YoY)
    - Gross Margin: 65.3% (up from 62.1%)
    - Operating Income: $15.8 billion (up 35% YoY)
    - Net Income: $12.4 billion (up 40% YoY)
    - Free Cash Flow: $18.2 billion
    
    Our AI segment showed exceptional performance with revenue of $15.5 billion, a 75% 
    increase year-over-year. We continue to invest heavily in R&D, with spending of 
    $8.5 billion in fiscal 2024.
    
    Risk Factors
    
    Our business faces several key risks including:
    - Intense competition in the AI and cloud markets
    - Regulatory uncertainty around AI technologies
    - Supply chain constraints for advanced semiconductors
    - Currency fluctuations impacting international revenue
    
    We believe our strong cash position of $25 billion provides adequate flexibility 
    to navigate these challenges.
    """
    
    doc_id_1 = crew.ingest_document(
        content=sample_10k,
        source="10-K_FY2024_SAMPLE.pdf",
        doc_type="10-K",
        company_ticker="TECH",
        company_name="Sample Technology Corp",
        filing_date="2024-03-15",
        fiscal_period="FY 2024",
    )
    print(f"Ingested 10-K document: {doc_id_1}")
    
    # Sample earnings call transcript
    sample_earnings_call = """
    EARNINGS CALL TRANSCRIPT - Q4 FY2024
    Sample Technology Corp (TECH)
    
    Operator: Good morning and welcome to Sample Technology Corp's Fourth Quarter 
    Fiscal Year 2024 Earnings Call.
    
    CEO John Smith: Thank you, and good morning everyone. I'm extremely pleased to 
    report another outstanding quarter. Our team delivered exceptional results, with 
    revenue exceeding our guidance by 5%. 
    
    We're seeing tremendous momentum in our AI business. Customer adoption has been 
    stronger than anticipated, and our pipeline continues to grow robustly. We're 
    confident in our ability to maintain this growth trajectory.
    
    CFO Jane Doe: Looking at the numbers, Q4 revenue was $14.2 billion, up 28% 
    year-over-year. Gross margin expanded to 66.5%, driven by favorable product mix 
    and operational efficiencies.
    
    Operating expenses were well controlled at $5.8 billion, resulting in an operating 
    margin of 25.6%. Diluted EPS was $2.85, beating consensus estimates by $0.15.
    
    For Q1 FY2025, we expect revenue of $14.8 to $15.2 billion, representing 22-25% 
    year-over-year growth. We remain optimistic about the full year outlook.
    
    Analyst Question: Can you comment on competitive dynamics in the AI market?
    
    CEO John Smith: We're seeing rational competition. While there are many players, 
    we believe our integrated platform and strong customer relationships differentiate 
    us. We're not complacent, but we're confident in our competitive position.
    
    Analyst Question: What about the regulatory environment?
    
    CEO John Smith: It's an evolving situation. We're actively engaging with 
    regulators globally and support thoughtful AI governance. While there may be 
    some uncertainty, we don't expect material impact on our business model.
    """
    
    doc_id_2 = crew.ingest_document(
        content=sample_earnings_call,
        source="earnings_call_Q4_FY2024.txt",
        doc_type="earnings_call",
        company_ticker="TECH",
        company_name="Sample Technology Corp",
        filing_date="2024-01-25",
        fiscal_period="Q4 FY2024",
    )
    print(f"Ingested earnings call: {doc_id_2}")
    
    # Save the index
    crew.save_index()
    print("Saved vector store index")
    
    # ========================================================================
    # 3. Ask Questions (Evidence-Backed Q&A)
    # ========================================================================
    print("\n" + "=" * 60)
    print("Asking questions with evidence-backed responses...")
    print("=" * 60)
    
    # Note: This requires a Gemini API key for the LLM
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        import time
        
        # Question 1: Financial performance
        result = crew.ask(
            question="What was TECH's revenue growth and what drove it?",
            company_ticker="TECH"
        )
        print("\n📊 Question: What was TECH's revenue growth and what drove it?")
        print("-" * 40)
        print(result["response"])
        
        # Add delay between questions to avoid rate limiting on free tier
        print("\n⏳ Waiting 5 seconds to avoid rate limiting...")
        time.sleep(5)
        
        # Question 2: Risk factors
        result = crew.ask(
            question="What are the main risk factors for TECH?",
            company_ticker="TECH"
        )
        print("\n⚠️ Question: What are the main risk factors for TECH?")
        print("-" * 40)
        print(result["response"])
    else:
        print("\n⚠️ GOOGLE_API_KEY not set. Skipping LLM-based Q&A.")
        print("Get your free API key at: https://aistudio.google.com/app/apikey")
        print("Set the GOOGLE_API_KEY environment variable to enable full agent functionality.")
    
    # ========================================================================
    # 4. Direct Evidence Search (No LLM Required)
    # ========================================================================
    print("\n" + "=" * 60)
    print("Direct evidence search (no LLM required)...")
    print("=" * 60)
    
    results = crew.search_evidence(
        query="revenue growth AI segment",
        top_k=3,
        company_ticker="TECH"
    )
    
    print(f"\n🔍 Search: 'revenue growth AI segment' - Found {len(results)} results")
    print("-" * 40)
    for i, result in enumerate(results, 1):
        print(f"\nResult {i} (Score: {result['score']:.3f})")
        print(f"Source: {result['metadata'].get('source', 'Unknown')}")
        print(f"Section: {result['metadata'].get('section', 'General')}")
        print(f"Content: {result['content'][:200]}...")
    
    # ========================================================================
    # 5. KPI Extraction
    # ========================================================================
    print("\n" + "=" * 60)
    print("KPI Extraction...")
    print("=" * 60)
    
    if api_key:
        kpi_result = crew.extract_kpis(
            company_ticker="TECH",
            kpis=["revenue", "gross_margin", "operating_income", "free_cash_flow"],
            time_period="FY 2024"
        )
        print("\n📈 Extracted KPIs for TECH (FY 2024):")
        print("-" * 40)
        print(kpi_result["results"])
    else:
        print("⚠️ GOOGLE_API_KEY not set. Skipping KPI extraction.")
    
    # ========================================================================
    # 6. Sentiment Analysis
    # ========================================================================
    print("\n" + "=" * 60)
    print("Sentiment Analysis...")
    print("=" * 60)
    
    if api_key:
        sentiment_result = crew.analyze_sentiment(
            company_ticker="TECH",
            topic="AI business growth"
        )
        print("\n🎭 Sentiment Analysis for TECH on 'AI business growth':")
        print("-" * 40)
        print(sentiment_result["sentiment_analysis"])
    else:
        print("⚠️ GOOGLE_API_KEY not set. Skipping sentiment analysis.")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
