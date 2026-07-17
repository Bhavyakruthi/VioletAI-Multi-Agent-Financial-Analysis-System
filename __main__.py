"""
RAG Evidence Agent - Main Entry Point
=====================================
Command-line interface for the RAG Evidence Agent system.
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Main entry point for the RAG Evidence Agent CLI."""
    parser = argparse.ArgumentParser(
        description="RAG Evidence Agent - Financial Document Analysis with CrewAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a document
  python -m rag_agent ingest --file report.pdf --type 10-K --ticker AAPL

  # Ask a question
  python -m rag_agent ask "What was Apple's revenue growth?"

  # Search for evidence
  python -m rag_agent search "AI segment revenue" --ticker AAPL --top-k 5

  # Extract KPIs
  python -m rag_agent kpis --ticker AAPL --metrics revenue,net_income,eps

  # Analyze sentiment
  python -m rag_agent sentiment --ticker AAPL --topic "supply chain"

  # Run the example
  python -m rag_agent example
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a financial document")
    ingest_parser.add_argument("--file", "-f", required=True, help="Path to the document file")
    ingest_parser.add_argument("--type", "-t", required=True, 
                               choices=["10-K", "10-Q", "8-K", "earnings_call", "press_release"],
                               help="Type of document")
    ingest_parser.add_argument("--ticker", required=True, help="Company ticker symbol")
    ingest_parser.add_argument("--company-name", help="Full company name")
    ingest_parser.add_argument("--filing-date", help="Filing date (YYYY-MM-DD)")
    ingest_parser.add_argument("--fiscal-period", help="Fiscal period (e.g., 'Q3 2024', 'FY 2023')")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question about financial documents")
    ask_parser.add_argument("question", help="The question to ask")
    ask_parser.add_argument("--ticker", help="Filter by company ticker")
    ask_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for evidence in documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--ticker", help="Filter by company ticker")
    search_parser.add_argument("--doc-type", help="Filter by document type")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    
    # KPIs command
    kpis_parser = subparsers.add_parser("kpis", help="Extract KPIs for a company")
    kpis_parser.add_argument("--ticker", required=True, help="Company ticker symbol")
    kpis_parser.add_argument("--metrics", required=True, help="Comma-separated list of KPIs")
    kpis_parser.add_argument("--period", help="Fiscal period to focus on")
    
    # Sentiment command
    sentiment_parser = subparsers.add_parser("sentiment", help="Analyze management sentiment")
    sentiment_parser.add_argument("--ticker", required=True, help="Company ticker symbol")
    sentiment_parser.add_argument("--topic", help="Specific topic to analyze")
    
    # Example command
    example_parser = subparsers.add_parser("example", help="Run the example script")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Import here to avoid slow startup for help
    from rag_agent import RAGEvidenceCrew
    from rag_agent.config import RAGConfig
    
    # Initialize crew
    config = RAGConfig(index_dir=Path("data/indices"))
    
    if args.command == "example":
        # Run the example script
        from rag_agent.examples.basic_usage import main as run_example
        run_example()
        return
    
    crew = RAGEvidenceCrew(config=config, verbose=getattr(args, 'verbose', False))
    
    if args.command == "ingest":
        # Ingest a document
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        
        doc_id = crew.ingest_file(
            file_path=file_path,
            doc_type=args.type,
            company_ticker=args.ticker,
            company_name=args.company_name,
            filing_date=args.filing_date,
            fiscal_period=args.fiscal_period,
        )
        crew.save_index()
        print(f"✅ Ingested document: {doc_id}")
    
    elif args.command == "ask":
        # Ask a question
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set")
            print("Get your free API key at: https://aistudio.google.com/app/apikey")
            sys.exit(1)
        
        result = crew.ask(
            question=args.question,
            company_ticker=args.ticker,
        )
        print("\n📊 Answer:")
        print("-" * 40)
        print(result["response"])
    
    elif args.command == "search":
        # Search for evidence
        results = crew.search_evidence(
            query=args.query,
            top_k=args.top_k,
            company_ticker=args.ticker,
            doc_type=args.doc_type,
        )
        
        print(f"\n🔍 Found {len(results)} results:")
        print("-" * 40)
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] Score: {result['score']:.3f}")
            print(f"    Source: {result['metadata'].get('source', 'Unknown')}")
            print(f"    Section: {result['metadata'].get('section', 'General')}")
            print(f"    Content: {result['content'][:150]}...")
    
    elif args.command == "kpis":
        # Extract KPIs
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set")
            print("Get your free API key at: https://aistudio.google.com/app/apikey")
            sys.exit(1)
        
        metrics = [m.strip() for m in args.metrics.split(",")]
        result = crew.extract_kpis(
            company_ticker=args.ticker,
            kpis=metrics,
            time_period=args.period,
        )
        print("\n📈 Extracted KPIs:")
        print("-" * 40)
        print(result["results"])
    
    elif args.command == "sentiment":
        # Analyze sentiment
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set")
            print("Get your free API key at: https://aistudio.google.com/app/apikey")
            sys.exit(1)
        
        result = crew.analyze_sentiment(
            company_ticker=args.ticker,
            topic=args.topic,
        )
        print("\n🎭 Sentiment Analysis:")
        print("-" * 40)
        print(result["sentiment_analysis"])


if __name__ == "__main__":
    main()
