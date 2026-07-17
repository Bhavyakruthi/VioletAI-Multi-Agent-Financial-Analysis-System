"""
RAG Evidence Crew
=================
Main CrewAI Crew orchestration for the RAG Evidence Agent system.
Combines agents and tasks to provide evidence-backed financial insights.
"""

from crewai import Crew, Process, LLM
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
import os

from .agents import RAGAgents
from .tasks import RAGTasks
from .tools import create_rag_tools
from .vector_store import VectorStoreManager, EmbeddingService
from .document_processor import FinancialDocumentProcessor, Document, DocumentLoader
from .config import get_config, RAGConfig

logger = logging.getLogger(__name__)


def get_gemini_llm(config: RAGConfig) -> LLM:
    """
    Create a Gemini LLM instance for CrewAI.
    
    Args:
        config: RAG configuration with LLM settings
    
    Returns:
        Configured LLM instance
    """
    api_key = config.llm.api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "Gemini API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
        )
    
    return LLM(
        model=config.llm.model,
        temperature=config.llm.temperature,
        api_key=api_key,
        max_tokens=config.llm.max_tokens,
        timeout=60,  # Increase timeout for free tier
        max_retries=3,  # Retry on failures
    )


class RAGEvidenceCrew:
    """
    Main orchestration class for the RAG Evidence Agent system.
    
    This crew provides:
    - Evidence-backed financial Q&A
    - KPI extraction with citations
    - Sentiment analysis from earnings calls
    - Professional research synthesis
    """
    
    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        llm: Optional[Any] = None,
        verbose: bool = True,
    ):
        """
        Initialize the RAG Evidence Crew.
        
        Args:
            config: RAG configuration (uses defaults if not provided)
            llm: Language model to use (defaults to Gemini)
            verbose: Whether to enable verbose logging
        """
        self.config = config or get_config()
        self.verbose = verbose
        
        # Initialize LLM (use provided or create Gemini instance)
        if llm is not None:
            self.llm = llm
        else:
            try:
                self.llm = get_gemini_llm(self.config)
                logger.info(f"Initialized Gemini LLM: {self.config.llm.model}")
            except ValueError as e:
                logger.warning(f"Could not initialize Gemini LLM: {e}")
                self.llm = None
        
        # Initialize components
        self._init_vector_store()
        self._init_document_processor()
        self._init_tools()
        self._init_agents()
    
    def _init_vector_store(self):
        """Initialize the vector store manager."""
        self.vector_store_manager = VectorStoreManager(
            base_path=self.config.index_dir,
            embedding_model=self.config.embedding.model_name,
        )
        logger.info(f"Initialized vector store at {self.config.index_dir}")
    
    def _init_document_processor(self):
        """Initialize the document processor."""
        self.document_processor = FinancialDocumentProcessor(
            chunk_size=self.config.chunking.chunk_size,
            chunk_overlap=self.config.chunking.chunk_overlap,
            min_chunk_size=self.config.chunking.min_chunk_size,
        )
        logger.info("Initialized document processor")
    
    def _init_tools(self):
        """Initialize CrewAI tools."""
        self.tools = create_rag_tools(
            self.vector_store_manager,
            store_name="financial_docs"
        )
        logger.info(f"Initialized {len(self.tools)} RAG tools")
    
    def _init_agents(self):
        """Initialize CrewAI agents."""
        self.agents_factory = RAGAgents(
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
        )
        logger.info("Initialized RAG agents factory")
    
    # ========================================================================
    # Document Management
    # ========================================================================
    
    def ingest_document(
        self,
        content: str,
        source: str,
        doc_type: str,
        company_ticker: Optional[str] = None,
        company_name: Optional[str] = None,
        filing_date: Optional[str] = None,
        fiscal_period: Optional[str] = None,
        **metadata
    ) -> str:
        """
        Ingest a financial document into the vector store.
        
        Args:
            content: Document text content
            source: Source identifier (filename, URL, etc.)
            doc_type: Type of document (10-K, 10-Q, earnings_call, etc.)
            company_ticker: Company ticker symbol
            company_name: Full company name
            filing_date: Date of filing/publication
            fiscal_period: Fiscal period covered
            **metadata: Additional metadata
        
        Returns:
            Document ID
        """
        # Create document
        document = DocumentLoader.load_from_text(
            text=content,
            source=source,
            doc_type=doc_type,
            company_ticker=company_ticker,
            company_name=company_name,
            filing_date=filing_date,
            fiscal_period=fiscal_period,
            **metadata
        )
        
        # Process document into chunks
        processed_doc = self.document_processor.process_document(document)
        
        # Add chunks to vector store
        self.vector_store_manager.add_document_chunks(
            store_name="financial_docs",
            chunks=processed_doc.chunks,
        )
        
        logger.info(f"Ingested document {processed_doc.doc_id} with {len(processed_doc.chunks)} chunks")
        return processed_doc.doc_id
    
    def ingest_file(
        self,
        file_path: Path,
        doc_type: str,
        **metadata
    ) -> str:
        """
        Ingest a document from a file.
        
        Args:
            file_path: Path to the document file
            doc_type: Type of document
            **metadata: Additional metadata
        
        Returns:
            Document ID
        """
        document = DocumentLoader.load_from_file(file_path, doc_type, **metadata)
        processed_doc = self.document_processor.process_document(document)
        
        self.vector_store_manager.add_document_chunks(
            store_name="financial_docs",
            chunks=processed_doc.chunks,
        )
        
        logger.info(f"Ingested file {file_path} with {len(processed_doc.chunks)} chunks")
        return processed_doc.doc_id
    
    def save_index(self):
        """Save the vector store to disk."""
        self.vector_store_manager.save_all()
        logger.info("Saved vector store to disk")
    
    # ========================================================================
    # Query Methods
    # ========================================================================
    
    def ask(
        self,
        question: str,
        company_ticker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ask a question and get an evidence-backed response.
        
        Args:
            question: The question to answer
            company_ticker: Optional company to focus on
        
        Returns:
            Dictionary with response, evidence, and citations
        """
        # Create agents
        query_agent = self.agents_factory.query_processor_agent()
        retrieval_agent = self.agents_factory.evidence_retrieval_agent()
        analyst_agent = self.agents_factory.financial_analyst_agent()
        synthesizer_agent = self.agents_factory.response_synthesizer_agent()
        
        # Create tasks
        query_task = RAGTasks.query_analysis_task(query_agent, question)
        
        search_task = RAGTasks.evidence_search_task(
            retrieval_agent,
            query=question,
            company_ticker=company_ticker,
        )
        
        analysis_task = RAGTasks.financial_analysis_task(
            analyst_agent,
            topic=question,
            evidence="{{search_task.output}}",
            analysis_type="general",
        )
        
        synthesis_task = RAGTasks.response_synthesis_task(
            synthesizer_agent,
            question=question,
            evidence="{{search_task.output}}",
            analysis="{{analysis_task.output}}",
            citations="Evidence citations from search",
        )
        
        # Create and run crew
        crew = Crew(
            agents=[query_agent, retrieval_agent, analyst_agent, synthesizer_agent],
            tasks=[query_task, search_task, analysis_task, synthesis_task],
            process=Process.sequential,
            verbose=self.verbose,
        )
        
        result = crew.kickoff()
        
        return {
            "question": question,
            "response": str(result),
            "company": company_ticker,
        }
    
    def extract_kpis(
        self,
        company_ticker: str,
        kpis: List[str],
        time_period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract specific KPIs for a company.
        
        Args:
            company_ticker: Company ticker symbol
            kpis: List of KPIs to extract
            time_period: Optional time period focus
        
        Returns:
            Dictionary with extracted KPIs and sources
        """
        # Create agents
        retrieval_agent = self.agents_factory.evidence_retrieval_agent()
        analyst_agent = self.agents_factory.financial_analyst_agent()
        
        # Create tasks
        kpi_task = RAGTasks.kpi_extraction_task(
            retrieval_agent,
            company_ticker=company_ticker,
            kpis=kpis,
            time_period=time_period,
        )
        
        # Create and run crew
        crew = Crew(
            agents=[retrieval_agent, analyst_agent],
            tasks=[kpi_task],
            process=Process.sequential,
            verbose=self.verbose,
        )
        
        result = crew.kickoff()
        
        return {
            "company": company_ticker,
            "kpis": kpis,
            "time_period": time_period,
            "results": str(result),
        }
    
    def analyze_sentiment(
        self,
        company_ticker: str,
        topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze management sentiment for a company.
        
        Args:
            company_ticker: Company ticker symbol
            topic: Optional specific topic to focus on
        
        Returns:
            Dictionary with sentiment analysis results
        """
        # Create agents
        retrieval_agent = self.agents_factory.evidence_retrieval_agent()
        sentiment_agent = self.agents_factory.sentiment_analyst_agent()
        
        # Create tasks
        sentiment_task = RAGTasks.sentiment_analysis_task(
            sentiment_agent,
            company_ticker=company_ticker,
            topic=topic,
        )
        
        # Create and run crew
        crew = Crew(
            agents=[retrieval_agent, sentiment_agent],
            tasks=[sentiment_task],
            process=Process.sequential,
            verbose=self.verbose,
        )
        
        result = crew.kickoff()
        
        return {
            "company": company_ticker,
            "topic": topic,
            "sentiment_analysis": str(result),
        }
    
    def search_evidence(
        self,
        query: str,
        top_k: int = 5,
        company_ticker: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for evidence without full agent workflow.
        
        Args:
            query: Search query
            top_k: Number of results
            company_ticker: Optional company filter
            doc_type: Optional document type filter
        
        Returns:
            List of search results with metadata
        """
        filter_metadata = {}
        if company_ticker:
            filter_metadata["company_ticker"] = company_ticker.upper()
        if doc_type:
            filter_metadata["doc_type"] = doc_type
        
        results = self.vector_store_manager.search(
            store_name="financial_docs",
            query=query,
            top_k=top_k,
            filter_metadata=filter_metadata if filter_metadata else None,
        )
        
        return [result.to_dict() for result in results]
    
    # ========================================================================
    # Crew Factory Methods
    # ========================================================================
    
    def create_qa_crew(self) -> Crew:
        """Create a crew for general Q&A."""
        agents = [
            self.agents_factory.query_processor_agent(),
            self.agents_factory.evidence_retrieval_agent(),
            self.agents_factory.financial_analyst_agent(),
            self.agents_factory.citation_specialist_agent(),
            self.agents_factory.response_synthesizer_agent(),
        ]
        
        return Crew(
            agents=agents,
            tasks=[],  # Tasks added dynamically
            process=Process.sequential,
            verbose=self.verbose,
        )
    
    def create_analysis_crew(self) -> Crew:
        """Create a crew for financial analysis."""
        agents = [
            self.agents_factory.evidence_retrieval_agent(),
            self.agents_factory.financial_analyst_agent(),
            self.agents_factory.sentiment_analyst_agent(),
            self.agents_factory.response_synthesizer_agent(),
        ]
        
        return Crew(
            agents=agents,
            tasks=[],  # Tasks added dynamically
            process=Process.sequential,
            verbose=self.verbose,
        )
    
    def create_research_crew(self) -> Crew:
        """Create a crew for comprehensive research."""
        agents_dict = self.agents_factory.get_all_agents()
        
        return Crew(
            agents=list(agents_dict.values()),
            tasks=[],  # Tasks added dynamically
            process=Process.hierarchical,
            manager_agent=agents_dict["financial_analyst"],
            verbose=self.verbose,
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def create_rag_crew(
    index_path: Optional[Path] = None,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    llm: Optional[Any] = None,
    verbose: bool = True,
) -> RAGEvidenceCrew:
    """
    Create a RAG Evidence Crew with custom settings.
    
    Args:
        index_path: Path for vector store indices
        embedding_model: Embedding model to use
        llm: Language model to use
        verbose: Whether to enable verbose logging
    
    Returns:
        Configured RAGEvidenceCrew instance
    """
    from .config import RAGConfig, EmbeddingConfig
    
    config = RAGConfig(
        embedding=EmbeddingConfig(model_name=embedding_model),
        index_dir=index_path or Path("data/indices"),
    )
    
    return RAGEvidenceCrew(config=config, llm=llm, verbose=verbose)
