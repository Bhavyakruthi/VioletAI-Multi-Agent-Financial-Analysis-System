"""
CrewAI Agents for RAG Evidence System
=====================================
Defines specialized agents for evidence retrieval, analysis, and citation
in financial document analysis.
"""

from crewai import Agent
from typing import List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RAGAgents:
    """Factory class for creating RAG-specialized CrewAI agents."""
    
    def __init__(
        self,
        tools: List[Any],
        llm: Optional[Any] = None,
        verbose: bool = True,
    ):
        """
        Initialize the RAG agents factory.
        
        Args:
            tools: List of CrewAI tools for the agents to use
            llm: Language model to use (defaults to OpenAI)
            verbose: Whether to enable verbose logging
        """
        self.tools = tools
        self.llm = llm
        self.verbose = verbose
    
    def evidence_retrieval_agent(self) -> Agent:
        """
        Create an agent specialized in retrieving relevant evidence from financial documents.
        
        This agent excels at:
        - Finding relevant passages in SEC filings
        - Locating specific financial data and metrics
        - Identifying management commentary on topics
        """
        return Agent(
            role="Financial Evidence Retrieval Specialist",
            goal="""Find and retrieve the most relevant evidence from financial documents 
            to support analysis and answer questions. Ensure all retrieved information 
            is accurate and properly sourced.""",
            backstory="""You are an expert financial research analyst with 15+ years of 
            experience analyzing SEC filings, earnings call transcripts, and corporate 
            documents. You have a keen eye for finding relevant information quickly and 
            accurately. You understand the structure of 10-K, 10-Q filings, and know 
            exactly where to find specific financial data, risk factors, management 
            discussion, and key metrics. You always cite your sources meticulously.""",
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=False,
            memory=True,
        )
    
    def financial_analyst_agent(self) -> Agent:
        """
        Create an agent specialized in analyzing financial information.
        
        This agent excels at:
        - Interpreting financial statements
        - Analyzing trends and patterns
        - Understanding management tone and sentiment
        """
        return Agent(
            role="Senior Financial Analyst",
            goal="""Analyze financial information retrieved from documents to provide 
            accurate insights, identify trends, and support investment decision-making 
            with evidence-backed analysis.""",
            backstory="""You are a CFA charterholder with extensive experience in 
            equity research at top investment banks. You specialize in fundamental 
            analysis, financial statement interpretation, and management assessment. 
            You understand complex financial metrics, can identify red flags, and 
            provide nuanced analysis of company performance. You always base your 
            analysis on concrete evidence from official filings.""",
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=True,
            memory=True,
        )
    
    def citation_specialist_agent(self) -> Agent:
        """
        Create an agent specialized in proper citation and source attribution.
        
        This agent excels at:
        - Creating proper citations for financial sources
        - Ensuring all claims are backed by evidence
        - Formatting references consistently
        """
        return Agent(
            role="Citation and Compliance Specialist",
            goal="""Ensure all financial analysis and insights are properly cited with 
            accurate source attribution. Verify that claims are supported by evidence 
            and format citations according to professional standards.""",
            backstory="""You are a compliance and documentation specialist with deep 
            experience in financial research standards. You ensure that all research 
            reports meet regulatory requirements for source attribution. You have an 
            exceptional attention to detail and never allow uncited claims to pass. 
            You understand SEC filing conventions and proper citation formats for 
            financial documents.""",
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=False,
            memory=True,
        )
    
    def query_processor_agent(self) -> Agent:
        """
        Create an agent specialized in understanding and processing user queries.
        
        This agent excels at:
        - Understanding user intent
        - Breaking down complex questions
        - Formulating effective search strategies
        """
        return Agent(
            role="Financial Query Analyst",
            goal="""Understand user questions about financial topics and translate them 
            into effective search queries. Break down complex questions into specific, 
            searchable components.""",
            backstory="""You are an expert in financial information retrieval with a 
            background in both finance and information science. You understand how 
            financial professionals think and what information they need. You excel 
            at translating vague or complex questions into precise search queries 
            that yield relevant results. You know the terminology used in SEC filings 
            and financial reports.""",
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=True,
            memory=True,
        )
    
    def response_synthesizer_agent(self) -> Agent:
        """
        Create an agent specialized in synthesizing evidence into coherent responses.
        
        This agent excels at:
        - Combining multiple pieces of evidence
        - Creating clear, professional responses
        - Highlighting key insights and citations
        """
        return Agent(
            role="Research Synthesis Specialist",
            goal="""Synthesize evidence from multiple sources into clear, comprehensive, 
            and professionally formatted responses. Ensure all insights are backed by 
            citations and present information in an easy-to-understand manner.""",
            backstory="""You are an expert financial writer who has authored numerous 
            equity research reports for institutional investors. You excel at taking 
            complex financial information and presenting it clearly. You always 
            maintain a professional tone, highlight key takeaways, and ensure every 
            claim is properly cited. Your reports are known for being thorough yet 
            accessible.""",
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=False,
            memory=True,
        )
    
    def sentiment_analyst_agent(self) -> Agent:
        """
        Create an agent specialized in analyzing management sentiment and tone.
        
        This agent excels at:
        - Detecting management confidence levels
        - Identifying hedging language
        - Analyzing tone changes over time
        """
        return Agent(
            role="Management Sentiment Analyst",
            goal="""Analyze management tone, sentiment, and language patterns in earnings 
            calls and filings. Identify confidence levels, hedging language, and changes 
            in management communication style.""",
            backstory="""You are a specialist in behavioral finance and linguistic 
            analysis of corporate communications. You have developed proprietary 
            methods for detecting management sentiment from their choice of words. 
            You can identify when management is being overly optimistic, hedging their 
            statements, or showing signs of concern. You understand that what management 
            doesn't say is often as important as what they do say.""",
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=False,
            memory=True,
        )
    
    def document_summarizer_agent(self) -> Agent:
        """
        Create an agent specialized in summarizing documents.
        
        This agent excels at:
        - Creating comprehensive document summaries
        - Extracting key points and themes
        - Organizing information hierarchically
        """
        return Agent(
            role="Document Summarization Expert",
            goal="""Create comprehensive, accurate summaries of financial documents. 
            Extract key points, main themes, and critical information while maintaining 
            the essential meaning and context of the original documents.""",
            backstory="""You are a professional document analyst with expertise in 
            condensing complex financial documents into clear, actionable summaries. 
            You have worked with investment firms creating executive summaries of 
            lengthy SEC filings, research reports, and corporate documents. You know 
            how to identify the most important information and present it concisely 
            without losing critical details. Your summaries are known for being 
            comprehensive yet easy to digest.""",
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=False,
            memory=True,
        )
    
    def qa_agent(self) -> Agent:
        """
        Create an agent specialized in answering questions from documents.
        
        This agent excels at:
        - Finding precise answers to specific questions
        - Providing context for answers
        - Citing sources accurately
        """
        return Agent(
            role="Document Q&A Specialist",
            goal="""Answer user questions accurately based on the content of uploaded 
            documents. Provide precise, well-cited answers with relevant context. 
            If the answer is not found in the documents, clearly state that.""",
            backstory="""You are an expert research assistant specializing in 
            extracting precise answers from complex documents. You have extensive 
            experience in legal and financial document review, where accuracy is 
            paramount. You never make up information and always cite the specific 
            section or page where you found the answer. When information is not 
            available in the documents, you clearly communicate this to the user.""",
            tools=self.tools,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=True,
            memory=True,
        )
    
    def get_all_agents(self) -> dict:
        """Return all available agents as a dictionary."""
        return {
            "evidence_retrieval": self.evidence_retrieval_agent(),
            "financial_analyst": self.financial_analyst_agent(),
            "citation_specialist": self.citation_specialist_agent(),
            "query_processor": self.query_processor_agent(),
            "response_synthesizer": self.response_synthesizer_agent(),
            "sentiment_analyst": self.sentiment_analyst_agent(),
            "document_summarizer": self.document_summarizer_agent(),
            "qa_agent": self.qa_agent(),
        }
