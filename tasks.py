"""
CrewAI Tasks for RAG System
===========================
Defines tasks for document summarization and Q&A.
"""

from crewai import Task, Agent
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RAGTasks:
    """Factory class for creating RAG-related tasks."""
    
    @staticmethod
    def summarize_documents_task(
        agent: Agent,
        document_names: Optional[str] = None,
    ) -> Task:
        """
        Create a task for summarizing uploaded documents.
        
        Args:
            agent: The agent to perform the task
            document_names: Optional specific document names
            
        Returns:
            Task object for document summarization
        """
        context = f"Documents to summarize: {document_names}" if document_names else "Summarize all uploaded documents"
        
        return Task(
            description=f"""
            Create a comprehensive summary of the uploaded documents.
            
            {context}
            
            Your summary should include:
            1. **Executive Summary**: A brief overview (2-3 paragraphs) of the main content
            2. **Key Points**: Bullet points of the most important information
            3. **Main Topics**: The primary subjects covered in the documents
            4. **Key Findings/Data**: Any important statistics, figures, or conclusions
            5. **Notable Quotes**: Important statements or passages (with citations)
            
            Use the available tools to:
            1. First, list all available documents
            2. Get the document content
            3. Search for key themes and topics
            
            Ensure your summary is:
            - Accurate and faithful to the source material
            - Well-organized and easy to read
            - Comprehensive but concise
            - Properly cited with source references
            """,
            agent=agent,
            expected_output="""
            A well-structured document summary in the following format:
            
            # Document Summary
            
            ## Executive Summary
            [2-3 paragraph overview]
            
            ## Key Points
            - Point 1
            - Point 2
            - ...
            
            ## Main Topics Covered
            1. Topic 1
            2. Topic 2
            ...
            
            ## Key Findings and Data
            - Finding 1 (Source: document name, page X)
            - Finding 2 (Source: document name, page X)
            
            ## Notable Quotes
            > "Quote 1" - Source
            > "Quote 2" - Source
            
            ## Conclusion
            [Brief concluding remarks]
            """,
        )
    
    @staticmethod
    def answer_question_task(
        agent: Agent,
        question: str,
    ) -> Task:
        """
        Create a task for answering a question from documents.
        
        Args:
            agent: The agent to perform the task
            question: The user's question
            
        Returns:
            Task object for Q&A
        """
        return Task(
            description=f"""
            Answer the following question based on the uploaded documents:
            
            **Question**: {question}
            
            Instructions:
            1. Use the search_documents tool to find relevant information
            2. Analyze the retrieved passages carefully
            3. Formulate a comprehensive answer based ONLY on the document content
            4. If the information is not found in the documents, clearly state that
            5. Always cite your sources (document name and page number when available)
            
            Important:
            - Do NOT make up information
            - If you're unsure, say so
            - Provide context for your answer
            - Quote relevant passages when appropriate
            """,
            agent=agent,
            expected_output="""
            A clear, well-structured answer that:
            1. Directly addresses the question
            2. Provides supporting evidence from the documents
            3. Includes proper citations
            4. Acknowledges any limitations or uncertainties
            
            Format:
            ## Answer
            [Direct answer to the question]
            
            ## Supporting Evidence
            [Relevant quotes and information from documents]
            
            ## Sources
            - Source 1: [document name, page]
            - Source 2: [document name, page]
            """,
        )
    
    @staticmethod
    def analyze_document_task(
        agent: Agent,
        analysis_type: str = "general",
    ) -> Task:
        """
        Create a task for in-depth document analysis.
        
        Args:
            agent: The agent to perform the task
            analysis_type: Type of analysis (general, financial, sentiment)
            
        Returns:
            Task object for document analysis
        """
        analysis_instructions = {
            "general": """
                Perform a general analysis including:
                - Document structure and organization
                - Main themes and arguments
                - Key conclusions and recommendations
            """,
            "financial": """
                Perform a financial analysis including:
                - Key financial metrics and figures
                - Trends and patterns
                - Risk factors identified
                - Forward-looking statements
            """,
            "sentiment": """
                Perform a sentiment analysis including:
                - Overall tone of the documents
                - Positive vs negative language
                - Confidence indicators
                - Areas of concern or optimism
            """,
        }
        
        instructions = analysis_instructions.get(analysis_type, analysis_instructions["general"])
        
        return Task(
            description=f"""
            Perform an in-depth {analysis_type} analysis of the uploaded documents.
            
            {instructions}
            
            Use the available tools to search and retrieve relevant information.
            Support all findings with specific citations from the documents.
            """,
            agent=agent,
            expected_output=f"""
            A comprehensive {analysis_type} analysis report with:
            - Executive summary
            - Detailed findings
            - Supporting evidence with citations
            - Conclusions and recommendations
            """,
        )
