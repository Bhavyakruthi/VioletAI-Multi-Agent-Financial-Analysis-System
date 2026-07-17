"""
RAG Evidence Agent Module
=========================
A CrewAI-based Retrieval-Augmented Generation system for financial document analysis.
Provides evidence-backed insights with proper citations from company filings.
"""

from .crew import RAGEvidenceCrew
from .agents import RAGAgents
from .tasks import RAGTasks

__version__ = "1.0.0"
__all__ = ["RAGEvidenceCrew", "RAGAgents", "RAGTasks"]
