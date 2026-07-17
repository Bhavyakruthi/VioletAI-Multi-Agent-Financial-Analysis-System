"""
CrewAI Custom Tools for RAG Evidence Agent
==========================================
Custom tools for the CrewAI agents to interact with the vector store
and generate evidence-backed responses with citations.
"""

from typing import Type, List, Dict, Any, Optional, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from crewai.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Input Schemas
# ============================================================================

class VectorSearchInput(BaseModel):
    """Input schema for vector search tool."""
    query: str = Field(..., description="The search query to find relevant financial document passages")
    top_k: int = Field(default=5, description="Number of results to return")
    doc_type: Optional[str] = Field(default=None, description="Filter by document type (10-K, 10-Q, earnings_call)")
    company_ticker: Optional[str] = Field(default=None, description="Filter by company ticker symbol")


class DocumentContextInput(BaseModel):
    """Input schema for document context retrieval."""
    chunk_id: str = Field(..., description="The ID of the chunk to get extended context for")
    context_size: int = Field(default=2, description="Number of surrounding chunks to include")


class CitationInput(BaseModel):
    """Input schema for citation generation."""
    chunk_ids: List[str] = Field(..., description="List of chunk IDs to generate citations for")
    format: str = Field(default="inline", description="Citation format: 'inline', 'footnote', or 'endnote'")


class FinancialKPISearchInput(BaseModel):
    """Input schema for KPI-specific search."""
    kpi_name: str = Field(..., description="Name of the KPI to search for (e.g., 'revenue', 'net_income', 'ebitda')")
    company_ticker: str = Field(..., description="Company ticker symbol")
    fiscal_period: Optional[str] = Field(default=None, description="Specific fiscal period (e.g., 'Q3 2024', 'FY 2023')")


class SentimentSearchInput(BaseModel):
    """Input schema for sentiment-related search."""
    topic: str = Field(..., description="Topic to analyze sentiment for")
    company_ticker: str = Field(..., description="Company ticker symbol")
    sentiment_type: str = Field(default="all", description="Type of sentiment: 'positive', 'negative', 'neutral', or 'all'")


# ============================================================================
# Custom Tools
# ============================================================================

class VectorSearchTool(BaseTool):
    """Tool for searching the financial document vector store."""
    
    name: str = "search_financial_documents"
    description: str = """
    Search through financial documents (SEC filings, earnings calls, press releases) 
    to find relevant passages based on a semantic query. Returns the most relevant 
    text chunks with their source information for citation.
    
    Use this tool when you need to:
    - Find evidence for financial claims
    - Look up specific financial metrics or statements
    - Retrieve management commentary on specific topics
    - Find risk factors or forward-looking statements
    """
    args_schema: Type[BaseModel] = VectorSearchInput
    
    vector_store_manager: Any = None
    store_name: str = "financial_docs"
    
    def __init__(self, vector_store_manager, store_name: str = "financial_docs", **kwargs):
        super().__init__(**kwargs)
        self.vector_store_manager = vector_store_manager
        self.store_name = store_name
    
    def _run(
        self,
        query: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        company_ticker: Optional[str] = None,
    ) -> str:
        """Execute the vector search."""
        try:
            # Build filter
            filter_metadata = {}
            if doc_type:
                filter_metadata["doc_type"] = doc_type
            if company_ticker:
                filter_metadata["company_ticker"] = company_ticker.upper()
            
            # Perform search
            results = self.vector_store_manager.search(
                store_name=self.store_name,
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata if filter_metadata else None,
            )
            
            if not results:
                return "No relevant documents found for the query."
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                chunk = result.chunk
                metadata = chunk.metadata
                
                result_text = f"""
**Result {i}** (Relevance: {result.score:.3f})
- Source: {metadata.get('source', 'Unknown')}
- Document Type: {metadata.get('doc_type', 'Unknown')}
- Company: {metadata.get('company_ticker', 'Unknown')} - {metadata.get('company_name', '')}
- Section: {metadata.get('section', 'General')}
- Filing Date: {metadata.get('filing_date', 'Unknown')}
- Chunk ID: {chunk.chunk_id}

Content:
\"\"\"{chunk.content}\"\"\"
"""
                formatted_results.append(result_text)
            
            return "\n---\n".join(formatted_results)
        
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return f"Error performing search: {str(e)}"


class DocumentContextTool(BaseTool):
    """Tool for getting extended context around a document chunk."""
    
    name: str = "get_document_context"
    description: str = """
    Get extended context around a specific document chunk. Use this when you need 
    more context around a passage you found through search. Provides surrounding 
    text from the same document.
    """
    args_schema: Type[BaseModel] = DocumentContextInput
    
    vector_store_manager: Any = None
    store_name: str = "financial_docs"
    
    def __init__(self, vector_store_manager, store_name: str = "financial_docs", **kwargs):
        super().__init__(**kwargs)
        self.vector_store_manager = vector_store_manager
        self.store_name = store_name
    
    def _run(self, chunk_id: str, context_size: int = 2) -> str:
        """Get extended context for a chunk."""
        try:
            store = self.vector_store_manager.get_or_create_store(self.store_name)
            
            # Get the target chunk
            target_chunk = store.get_chunk_by_id(chunk_id)
            if not target_chunk:
                return f"Chunk with ID {chunk_id} not found."
            
            # Get document ID and chunk index
            doc_id = target_chunk.metadata.get("doc_id")
            chunk_index = target_chunk.metadata.get("chunk_index", 0)
            
            # Find surrounding chunks from same document
            context_chunks = []
            for idx in range(chunk_index - context_size, chunk_index + context_size + 1):
                search_id = f"{doc_id}_{idx:04d}"
                chunk = store.get_chunk_by_id(search_id)
                if chunk:
                    context_chunks.append(chunk)
            
            # Format context
            context_text = "\n\n[...]\n\n".join([c.content for c in context_chunks])
            
            return f"""
**Extended Context for Chunk {chunk_id}**
Source: {target_chunk.metadata.get('source', 'Unknown')}
Document Type: {target_chunk.metadata.get('doc_type', 'Unknown')}

{context_text}
"""
        
        except Exception as e:
            logger.error(f"Context retrieval error: {e}")
            return f"Error getting context: {str(e)}"


class CitationGeneratorTool(BaseTool):
    """Tool for generating proper citations for document chunks."""
    
    name: str = "generate_citations"
    description: str = """
    Generate proper citations for financial document chunks. Use this to create
    properly formatted references for the evidence you're citing in responses.
    Supports inline citations, footnotes, and endnotes.
    """
    args_schema: Type[BaseModel] = CitationInput
    
    vector_store_manager: Any = None
    store_name: str = "financial_docs"
    
    def __init__(self, vector_store_manager, store_name: str = "financial_docs", **kwargs):
        super().__init__(**kwargs)
        self.vector_store_manager = vector_store_manager
        self.store_name = store_name
    
    def _run(self, chunk_ids: List[str], format: str = "inline") -> str:
        """Generate citations for chunks."""
        try:
            store = self.vector_store_manager.get_or_create_store(self.store_name)
            citations = []
            
            for i, chunk_id in enumerate(chunk_ids, 1):
                chunk = store.get_chunk_by_id(chunk_id)
                if not chunk:
                    continue
                
                metadata = chunk.metadata
                
                # Build citation based on format
                company = metadata.get("company_ticker", "Unknown")
                doc_type = metadata.get("doc_type", "Filing")
                date = metadata.get("filing_date", "Unknown Date")
                section = metadata.get("section", "")
                
                if format == "inline":
                    citation = f"[{company} {doc_type}, {date}]"
                elif format == "footnote":
                    citation = f"^[{i}]: {company}. {doc_type}. {date}. Section: {section}"
                else:  # endnote
                    citation = f"[{i}] {company}. ({date}). {doc_type}. {section}"
                
                citations.append({
                    "chunk_id": chunk_id,
                    "citation": citation,
                    "full_reference": f"{company} - {doc_type} ({date}), Section: {section}"
                })
            
            # Format output
            output = "**Generated Citations:**\n\n"
            for c in citations:
                output += f"- Chunk {c['chunk_id']}: {c['citation']}\n"
                output += f"  Full Reference: {c['full_reference']}\n\n"
            
            return output
        
        except Exception as e:
            logger.error(f"Citation generation error: {e}")
            return f"Error generating citations: {str(e)}"


class FinancialKPISearchTool(BaseTool):
    """Tool for searching financial KPI-related content."""
    
    name: str = "search_financial_kpis"
    description: str = """
    Search for specific financial KPI information in documents. Use this to find 
    mentions of revenue, earnings, margins, growth rates, and other key metrics.
    More targeted than general search for financial performance data.
    """
    args_schema: Type[BaseModel] = FinancialKPISearchInput
    
    vector_store_manager: Any = None
    store_name: str = "financial_docs"
    
    # KPI-related keywords for enhanced search
    KPI_KEYWORDS: ClassVar[Dict[str, List[str]]] = {
        "revenue": ["revenue", "net sales", "total sales", "top line", "sales growth"],
        "net_income": ["net income", "net earnings", "net profit", "bottom line", "profit"],
        "ebitda": ["ebitda", "operating income", "operating profit", "earnings before"],
        "gross_margin": ["gross margin", "gross profit", "cost of goods", "cogs"],
        "operating_margin": ["operating margin", "operating expenses", "opex"],
        "eps": ["earnings per share", "eps", "diluted eps", "basic eps"],
        "cash_flow": ["cash flow", "operating cash", "free cash flow", "fcf"],
        "debt": ["debt", "leverage", "borrowings", "credit facility", "loans"],
        "liquidity": ["liquidity", "current ratio", "quick ratio", "working capital"],
    }
    
    def __init__(self, vector_store_manager, store_name: str = "financial_docs", **kwargs):
        super().__init__(**kwargs)
        self.vector_store_manager = vector_store_manager
        self.store_name = store_name
    
    def _run(
        self,
        kpi_name: str,
        company_ticker: str,
        fiscal_period: Optional[str] = None,
    ) -> str:
        """Search for KPI-related content."""
        try:
            # Get relevant keywords for the KPI
            kpi_key = kpi_name.lower().replace(" ", "_")
            keywords = self.KPI_KEYWORDS.get(kpi_key, [kpi_name])
            
            # Build enhanced query
            query = f"{' OR '.join(keywords)} {company_ticker}"
            if fiscal_period:
                query += f" {fiscal_period}"
            
            # Perform search with company filter
            results = self.vector_store_manager.search(
                store_name=self.store_name,
                query=query,
                top_k=10,
                filter_metadata={"company_ticker": company_ticker.upper()},
            )
            
            if not results:
                return f"No KPI information found for {kpi_name} at {company_ticker}"
            
            # Filter results that actually contain KPI keywords
            relevant_results = []
            for result in results:
                content_lower = result.chunk.content.lower()
                if any(kw.lower() in content_lower for kw in keywords):
                    relevant_results.append(result)
            
            if not relevant_results:
                relevant_results = results[:5]  # Fall back to top results
            
            # Format results
            output = f"**KPI Search Results: {kpi_name.upper()} for {company_ticker}**\n\n"
            
            for i, result in enumerate(relevant_results[:5], 1):
                chunk = result.chunk
                metadata = chunk.metadata
                
                output += f"""
**Result {i}** (Relevance: {result.score:.3f})
- Source: {metadata.get('doc_type', 'Unknown')} - {metadata.get('filing_date', 'Unknown')}
- Section: {metadata.get('section', 'General')}
- Chunk ID: {chunk.chunk_id}

> {chunk.content[:500]}{'...' if len(chunk.content) > 500 else ''}

"""
            
            return output
        
        except Exception as e:
            logger.error(f"KPI search error: {e}")
            return f"Error searching for KPI: {str(e)}"


class ManagementSentimentSearchTool(BaseTool):
    """Tool for searching management sentiment and tone in earnings calls."""
    
    name: str = "search_management_sentiment"
    description: str = """
    Search for management sentiment and tone in earnings calls and filings. 
    Use this to find management commentary on specific topics, forward-looking 
    statements, or to gauge management confidence and tone.
    """
    args_schema: Type[BaseModel] = SentimentSearchInput
    
    vector_store_manager: Any = None
    store_name: str = "financial_docs"
    
    # Sentiment indicators
    SENTIMENT_KEYWORDS: ClassVar[Dict[str, List[str]]] = {
        "positive": ["confident", "strong", "growth", "improvement", "exceed", "optimistic", 
                     "robust", "momentum", "outperform", "success", "opportunity"],
        "negative": ["concern", "challenge", "difficult", "decline", "risk", "uncertain",
                     "headwind", "pressure", "weakness", "disappointing", "miss"],
        "hedging": ["may", "might", "could", "potentially", "possible", "uncertain",
                    "expect", "anticipate", "believe", "estimate", "approximately"],
    }
    
    def __init__(self, vector_store_manager, store_name: str = "financial_docs", **kwargs):
        super().__init__(**kwargs)
        self.vector_store_manager = vector_store_manager
        self.store_name = store_name
    
    def _run(
        self,
        topic: str,
        company_ticker: str,
        sentiment_type: str = "all",
    ) -> str:
        """Search for sentiment-related content."""
        try:
            # Build query with sentiment keywords
            query_parts = [topic]
            
            if sentiment_type != "all" and sentiment_type in self.SENTIMENT_KEYWORDS:
                # Add sentiment-specific keywords
                sentiment_keywords = self.SENTIMENT_KEYWORDS[sentiment_type][:5]
                query_parts.extend(sentiment_keywords)
            
            query = " ".join(query_parts)
            
            # Search primarily in earnings calls
            results = self.vector_store_manager.search(
                store_name=self.store_name,
                query=query,
                top_k=10,
                filter_metadata={
                    "company_ticker": company_ticker.upper(),
                },
            )
            
            # Prioritize earnings call content
            earnings_results = [r for r in results if r.chunk.metadata.get("doc_type") == "earnings_call"]
            other_results = [r for r in results if r.chunk.metadata.get("doc_type") != "earnings_call"]
            
            sorted_results = earnings_results + other_results
            
            if not sorted_results:
                return f"No sentiment-related content found for '{topic}' at {company_ticker}"
            
            # Analyze sentiment in results
            output = f"**Management Sentiment Search: '{topic}' for {company_ticker}**\n\n"
            
            for i, result in enumerate(sorted_results[:5], 1):
                chunk = result.chunk
                metadata = chunk.metadata
                content = chunk.content
                
                # Count sentiment indicators
                sentiment_counts = {}
                for sent_type, keywords in self.SENTIMENT_KEYWORDS.items():
                    count = sum(1 for kw in keywords if kw.lower() in content.lower())
                    if count > 0:
                        sentiment_counts[sent_type] = count
                
                sentiment_summary = ", ".join([f"{k}: {v}" for k, v in sentiment_counts.items()]) or "Neutral"
                
                output += f"""
**Result {i}** (Relevance: {result.score:.3f})
- Source: {metadata.get('doc_type', 'Unknown')} - {metadata.get('filing_date', 'Unknown')}
- Sentiment Indicators: {sentiment_summary}
- Chunk ID: {chunk.chunk_id}

> {content[:600]}{'...' if len(content) > 600 else ''}

"""
            
            return output
        
        except Exception as e:
            logger.error(f"Sentiment search error: {e}")
            return f"Error searching for sentiment: {str(e)}"


# ============================================================================
# Tool Factory
# ============================================================================

def create_rag_tools(vector_store_manager, store_name: str = "financial_docs") -> List[BaseTool]:
    """Create all RAG tools with the given vector store manager."""
    return [
        VectorSearchTool(vector_store_manager, store_name),
        DocumentContextTool(vector_store_manager, store_name),
        CitationGeneratorTool(vector_store_manager, store_name),
        FinancialKPISearchTool(vector_store_manager, store_name),
        ManagementSentimentSearchTool(vector_store_manager, store_name),
    ]
