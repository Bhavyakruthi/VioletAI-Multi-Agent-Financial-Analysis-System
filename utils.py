"""
Utility functions for the RAG Evidence Agent system.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Text Processing Utilities
# ============================================================================

def clean_financial_text(text: str) -> str:
    """
    Clean and normalize financial document text.
    
    Args:
        text: Raw text to clean
    
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    
    # Normalize dashes and quotes
    text = text.replace('–', '-').replace('—', '-')
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Clean currency formatting
    text = re.sub(r'\$\s+', '$', text)
    
    # Remove common footer/header patterns
    text = re.sub(r'(?i)confidential\s*-\s*not for distribution', '', text)
    
    return text.strip()


def extract_numbers(text: str) -> List[Dict[str, Any]]:
    """
    Extract numerical values from text with their context.
    
    Args:
        text: Text to extract numbers from
    
    Returns:
        List of dictionaries with number value and context
    """
    numbers = []
    
    # Pattern for currency values
    currency_pattern = r'\$\s*([0-9,]+(?:\.[0-9]+)?)\s*(million|billion|thousand|M|B|K)?'
    for match in re.finditer(currency_pattern, text, re.IGNORECASE):
        value = float(match.group(1).replace(',', ''))
        multiplier = match.group(2)
        
        if multiplier:
            multiplier = multiplier.lower()
            if multiplier in ['billion', 'b']:
                value *= 1_000_000_000
            elif multiplier in ['million', 'm']:
                value *= 1_000_000
            elif multiplier in ['thousand', 'k']:
                value *= 1_000
        
        # Get context (surrounding text)
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end]
        
        numbers.append({
            'value': value,
            'original': match.group(0),
            'type': 'currency',
            'context': context.strip(),
        })
    
    # Pattern for percentages
    percent_pattern = r'([0-9]+(?:\.[0-9]+)?)\s*%'
    for match in re.finditer(percent_pattern, text):
        value = float(match.group(1))
        
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end]
        
        numbers.append({
            'value': value,
            'original': match.group(0),
            'type': 'percentage',
            'context': context.strip(),
        })
    
    return numbers


def detect_financial_section(text: str) -> str:
    """
    Detect the type of financial section from text content.
    
    Args:
        text: Section text
    
    Returns:
        Section type identifier
    """
    text_lower = text.lower()[:500]  # Check first 500 chars
    
    section_indicators = {
        'income_statement': ['statement of operations', 'income statement', 'net revenues', 'cost of revenue'],
        'balance_sheet': ['balance sheet', 'total assets', 'total liabilities', 'stockholders equity'],
        'cash_flow': ['cash flow', 'operating activities', 'investing activities', 'financing activities'],
        'md&a': ['management discussion', 'md&a', 'results of operations'],
        'risk_factors': ['risk factors', 'item 1a'],
        'notes': ['notes to financial statements', 'note 1', 'summary of significant'],
        'earnings_call': ['earnings call', 'conference call', 'operator:', 'good morning', 'good afternoon'],
    }
    
    for section, indicators in section_indicators.items():
        if any(indicator in text_lower for indicator in indicators):
            return section
    
    return 'general'


# ============================================================================
# Citation Utilities
# ============================================================================

def format_citation(
    company_ticker: str,
    doc_type: str,
    filing_date: str,
    section: Optional[str] = None,
    format_type: str = 'inline',
) -> str:
    """
    Format a citation for a financial document.
    
    Args:
        company_ticker: Company ticker symbol
        doc_type: Document type
        filing_date: Filing date
        section: Optional section name
        format_type: Citation format (inline, footnote, full)
    
    Returns:
        Formatted citation string
    """
    if format_type == 'inline':
        return f"[{company_ticker} {doc_type}, {filing_date}]"
    elif format_type == 'footnote':
        section_text = f", Section: {section}" if section else ""
        return f"{company_ticker}. {doc_type}. {filing_date}{section_text}"
    else:  # full
        section_text = f" in section '{section}'" if section else ""
        return f"{company_ticker}. ({filing_date}). {doc_type}{section_text}. SEC Filing."


def create_reference_list(citations: List[Dict[str, Any]]) -> str:
    """
    Create a formatted reference list from citations.
    
    Args:
        citations: List of citation dictionaries
    
    Returns:
        Formatted reference list as string
    """
    if not citations:
        return ""
    
    # Remove duplicates
    seen = set()
    unique_citations = []
    for c in citations:
        key = (c.get('company_ticker'), c.get('doc_type'), c.get('filing_date'))
        if key not in seen:
            seen.add(key)
            unique_citations.append(c)
    
    # Sort by company and date
    unique_citations.sort(key=lambda x: (x.get('company_ticker', ''), x.get('filing_date', '')))
    
    # Format reference list
    references = ["## References\n"]
    for i, c in enumerate(unique_citations, 1):
        ref = format_citation(
            company_ticker=c.get('company_ticker', 'Unknown'),
            doc_type=c.get('doc_type', 'Filing'),
            filing_date=c.get('filing_date', 'Unknown Date'),
            section=c.get('section'),
            format_type='full',
        )
        references.append(f"[{i}] {ref}")
    
    return "\n".join(references)


# ============================================================================
# Validation Utilities
# ============================================================================

def validate_ticker(ticker: str) -> bool:
    """
    Validate a stock ticker symbol.
    
    Args:
        ticker: Ticker symbol to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not ticker:
        return False
    
    # Basic validation: 1-5 uppercase letters
    pattern = r'^[A-Z]{1,5}$'
    return bool(re.match(pattern, ticker.upper()))


def validate_fiscal_period(period: str) -> bool:
    """
    Validate a fiscal period string.
    
    Args:
        period: Fiscal period (e.g., 'Q1 2024', 'FY 2023')
    
    Returns:
        True if valid, False otherwise
    """
    if not period:
        return False
    
    # Patterns: Q1-Q4 YYYY, FY YYYY, H1-H2 YYYY
    patterns = [
        r'^Q[1-4]\s*20[0-9]{2}$',
        r'^FY\s*20[0-9]{2}$',
        r'^H[1-2]\s*20[0-9]{2}$',
        r'^20[0-9]{2}$',
    ]
    
    return any(re.match(p, period.upper()) for p in patterns)


# ============================================================================
# Logging Utilities
# ============================================================================

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> None:
    """
    Set up logging for the RAG system.
    
    Args:
        level: Logging level
        log_file: Optional log file path
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
    )


# ============================================================================
# Financial Metrics Utilities
# ============================================================================

FINANCIAL_METRICS = {
    'revenue': ['revenue', 'net sales', 'total sales', 'net revenue', 'total revenue'],
    'gross_profit': ['gross profit', 'gross margin'],
    'operating_income': ['operating income', 'operating profit', 'income from operations'],
    'net_income': ['net income', 'net earnings', 'net profit'],
    'ebitda': ['ebitda', 'earnings before interest'],
    'eps': ['earnings per share', 'eps', 'diluted eps'],
    'total_assets': ['total assets'],
    'total_liabilities': ['total liabilities'],
    'stockholders_equity': ['stockholders equity', 'shareholders equity', 'total equity'],
    'cash': ['cash and cash equivalents', 'total cash'],
    'debt': ['total debt', 'long-term debt', 'total borrowings'],
    'free_cash_flow': ['free cash flow', 'fcf'],
    'operating_cash_flow': ['cash from operations', 'operating cash flow'],
}


def identify_metric_type(text: str) -> Optional[str]:
    """
    Identify the type of financial metric mentioned in text.
    
    Args:
        text: Text to analyze
    
    Returns:
        Metric type identifier or None
    """
    text_lower = text.lower()
    
    for metric_type, keywords in FINANCIAL_METRICS.items():
        if any(kw in text_lower for kw in keywords):
            return metric_type
    
    return None


def parse_fiscal_period(period_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse a fiscal period string into components.
    
    Args:
        period_str: Fiscal period string
    
    Returns:
        Dictionary with year, quarter, and type or None if invalid
    """
    if not period_str:
        return None
    
    period_str = period_str.upper().strip()
    
    # Q1-Q4 YYYY
    match = re.match(r'^Q([1-4])\s*(\d{4})$', period_str)
    if match:
        return {
            'year': int(match.group(2)),
            'quarter': int(match.group(1)),
            'type': 'quarterly',
        }
    
    # FY YYYY
    match = re.match(r'^FY\s*(\d{4})$', period_str)
    if match:
        return {
            'year': int(match.group(1)),
            'quarter': None,
            'type': 'annual',
        }
    
    # YYYY
    match = re.match(r'^(\d{4})$', period_str)
    if match:
        return {
            'year': int(match.group(1)),
            'quarter': None,
            'type': 'annual',
        }
    
    return None
