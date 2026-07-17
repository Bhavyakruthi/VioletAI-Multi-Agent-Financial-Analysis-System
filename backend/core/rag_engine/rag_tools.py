"""
RAG Tools for CrewAI Agents
===========================
Custom tools for document retrieval, search, and analysis.
These tools enable CrewAI agents to interact with the document vector store.
"""

from typing import Optional, Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


class SearchDocumentsInput(BaseModel):
    """Input schema for document search."""
    query: str = Field(..., description="The search query to find relevant information")
    num_results: int = Field(default=5, description="Number of results to return")


class SearchDocumentsTool(BaseTool):
    """Tool for searching documents in the vector store."""
    
    name: str = "search_documents"
    description: str = """
    Search through uploaded financial documents to find relevant information.
    Use this tool to find specific facts, figures, management commentary, 
    risk factors, or any other information from annual reports, earnings calls,
    or investor presentations. Returns relevant text chunks with source citations.
    
    ALWAYS use this tool when you need to find specific information from uploaded documents.
    """
    args_schema: Type[BaseModel] = SearchDocumentsInput
    document_processor: Optional[object] = None
    
    def _run(self, query: str, num_results: int = 5) -> str:
        """Execute the document search."""
        if self.document_processor is None:
            return "Error: Document processor not initialized. No documents have been uploaded."
        
        try:
            results = self.document_processor.similarity_search(query, k=num_results)
            
            if not results:
                return f"No relevant information found for query: '{query}'"
            
            output = f"Found {len(results)} relevant passages:\n\n"
            
            for i, doc in enumerate(results, 1):
                source = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", "N/A")
                output += f"--- Result {i} ---\n"
                output += f"📄 Source: {source} (Page: {page})\n"
                output += f"Content: {doc.page_content}\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return f"Error searching documents: {str(e)}"


class GetDocumentSummaryInput(BaseModel):
    """Input schema for document summary."""
    document_name: Optional[str] = Field(
        default=None, 
        description="Name of specific document to get content from (optional, leave empty for all)"
    )


class GetDocumentContentTool(BaseTool):
    """Tool for getting document content for analysis."""
    
    name: str = "get_document_content"
    description: str = """
    Get the full content of uploaded documents for comprehensive analysis.
    Use this tool when you need to create a summary or need broader context
    beyond what search_documents provides.
    
    Optionally specify a document_name to get content from a specific file.
    """
    args_schema: Type[BaseModel] = GetDocumentSummaryInput
    document_processor: Optional[object] = None
    
    def _run(self, document_name: Optional[str] = None) -> str:
        """Get document content."""
        if self.document_processor is None:
            return "Error: Document processor not initialized. No documents have been uploaded."
        
        try:
            if document_name:
                # Get content from specific document
                relevant_docs = [
                    doc for doc in self.document_processor.documents
                    if doc.metadata.get("source") == document_name
                ]
                if not relevant_docs:
                    return f"Document '{document_name}' not found."
                content = "\n\n".join([doc.page_content for doc in relevant_docs])
            else:
                # Get all content
                content = self.document_processor.get_all_text()
            
            # Truncate if too long (to avoid context overflow)
            max_length = 30000
            if len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated due to length...]"
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting document content: {e}")
            return f"Error getting document content: {str(e)}"


class ListDocumentsInput(BaseModel):
    """Input schema for listing documents."""
    pass


class ListDocumentsTool(BaseTool):
    """Tool for listing all uploaded documents."""
    
    name: str = "list_documents"
    description: str = """
    List all documents that have been uploaded to the system.
    Use this tool to see what documents are available for analysis
    before searching or retrieving content.
    """
    args_schema: Type[BaseModel] = ListDocumentsInput
    document_processor: Optional[object] = None
    
    def _run(self) -> str:
        """List all documents."""
        if self.document_processor is None:
            return "Error: Document processor not initialized."
        
        try:
            docs = self.document_processor.get_document_list()
            
            if not docs:
                return "No documents have been uploaded yet."
            
            output = f"📚 Uploaded Documents ({len(docs)}):\n\n"
            for doc_name in docs:
                metadata = self.document_processor.document_metadata.get(doc_name, {})
                pages = metadata.get("pages", "N/A")
                size = metadata.get("size", 0)
                size_kb = size / 1024 if size else 0
                output += f"  • {doc_name} ({pages} pages, {size_kb:.1f} KB)\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return f"Error listing documents: {str(e)}"


def create_rag_tools(document_processor) -> List[BaseTool]:
    """
    Create all RAG tools with the document processor.
    
    Args:
        document_processor: DocumentProcessor instance
        
    Returns:
        List of initialized CrewAI tools
    """
    search_tool = SearchDocumentsTool()
    search_tool.document_processor = document_processor
    
    content_tool = GetDocumentContentTool()
    content_tool.document_processor = document_processor
    
    list_tool = ListDocumentsTool()
    list_tool.document_processor = document_processor
    
    return [search_tool, content_tool, list_tool]
