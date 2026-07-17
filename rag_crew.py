"""
RAG Crew Orchestration
======================
Main orchestration for the RAG system using CrewAI.
"""

from crewai import Crew, Process, LLM
from typing import Optional, List
import logging
import os
from dotenv import load_dotenv

from agents import RAGAgents
from document_processor import DocumentProcessor
from rag_tools import create_rag_tools
from tasks import RAGTasks

load_dotenv()

logger = logging.getLogger(__name__)


class RAGCrew:
    """Main class for orchestrating the RAG system."""
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        model: Optional[str] = None,
        verbose: bool = True,
    ):
        """
        Initialize the RAG crew.
        
        Args:
            google_api_key: Google API key (uses env var if not provided)
            model: LLM model to use
            verbose: Enable verbose logging
        """
        # Set API key
        api_key = google_api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        
        # Get model from env or use default
        self.model_name = model or os.getenv("LLM_MODEL", "gemini-2.0-flash")
        self.verbose = verbose
        
        # Initialize LLM for CrewAI
        self.llm = LLM(
            model=f"gemini/{self.model_name}",
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        )
        
        # Initialize document processor
        self.document_processor = DocumentProcessor()
        
        # Initialize tools
        self.tools = create_rag_tools(self.document_processor)
        
        # Initialize agents factory with Gemini LLM
        self.agents_factory = RAGAgents(
            tools=self.tools,
            llm=self.llm,
            verbose=verbose,
        )
        
        # Create agents
        self.summarizer_agent = self.agents_factory.document_summarizer_agent()
        self.qa_agent = self.agents_factory.qa_agent()
        self.analyst_agent = self.agents_factory.financial_analyst_agent()
        
        logger.info(f"RAG Crew initialized with model: {self.model_name}")
    
    def add_documents(self, uploaded_files: List) -> int:
        """
        Add documents to the system.
        
        Args:
            uploaded_files: List of uploaded file objects
            
        Returns:
            Number of documents processed
        """
        return self.document_processor.add_documents(uploaded_files)
    
    def get_document_list(self) -> List[str]:
        """Get list of loaded documents."""
        return self.document_processor.get_document_list()
    
    def summarize_documents(self) -> str:
        """
        Generate a summary of all uploaded documents.
        
        Returns:
            Document summary as string
        """
        if not self.document_processor.documents:
            return "No documents have been uploaded. Please upload documents first."
        
        task = RAGTasks.summarize_documents_task(self.summarizer_agent)
        
        crew = Crew(
            agents=[self.summarizer_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
        )
        
        result = crew.kickoff()
        return str(result)
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question based on uploaded documents.
        
        Args:
            question: User's question
            
        Returns:
            Answer as string
        """
        if not self.document_processor.documents:
            return "No documents have been uploaded. Please upload documents first."
        
        task = RAGTasks.answer_question_task(self.qa_agent, question)
        
        crew = Crew(
            agents=[self.qa_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
        )
        
        result = crew.kickoff()
        return str(result)
    
    def analyze_documents(self, analysis_type: str = "general") -> str:
        """
        Perform in-depth document analysis.
        
        Args:
            analysis_type: Type of analysis (general, financial, sentiment)
            
        Returns:
            Analysis report as string
        """
        if not self.document_processor.documents:
            return "No documents have been uploaded. Please upload documents first."
        
        task = RAGTasks.analyze_document_task(self.analyst_agent, analysis_type)
        
        crew = Crew(
            agents=[self.analyst_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
        )
        
        result = crew.kickoff()
        return str(result)
    
    def clear_documents(self):
        """Clear all loaded documents."""
        self.document_processor.clear()
        logger.info("All documents cleared")
    
    def save_summary_to_file(self, summary: str, filename: str = "summary.txt") -> str:
        """
        Save summary to a text file.
        
        Args:
            summary: Summary text to save
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(summary)
        return filename
