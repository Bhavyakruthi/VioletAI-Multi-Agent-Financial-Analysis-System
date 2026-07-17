# 🤖 AI Agents Overview

This document provides a comprehensive breakdown of the **multi-agent system** powering VioletAI. Our architecture uses specialized agents for distinct tasks (Research, Writing, Math, Compliance) to ensure high accuracy and reduce hallucinations.

---

## 🧠 Group 1: Core Research & Reporting Crew
*Orchestrated in `analysis_service.py` using CrewAI.*

These agents run when a user clicks **"Run Full Analysis"**. They simulate a Wall Street equity research team.

### 1. Lead Quantitative & Market Strategist
*   **Role**: The "Thinker" who connects the dots.
*   **Goal**: Conduct a deep-dive technical and fundamental analysis.
*   **Workflow**:
    *   Takes raw data: FHI Score (Math), Sentiment Score (FinBERT), and Prophet Forecast.
    *   Identifies correlations (e.g., "Sentiment is dropping despite rising prices -> Divergence risk").
    *   Passes structured notes to the Analyst.

### 2. Principal Equity Research Analyst
*   **Role**: The "Writer" who crafts the narrative.
*   **Goal**: Synthesize complex data into a high-density, professional investment brief.
*   **Workflow**:
    *   Receives the Strategist's notes.
    *   Writes the "Executive Summary", "Risks", and "Strategic Actions" sections.
    *   **Constraint**: specific formatting rules (Markdown) to ensure the UI renders charts and modules correctly.

---

## 🔍 Group 2: RAG & Document Intelligence
*Defined in `agents.py`. These power the **Chat** and **Document Search** features.*

### 3. Financial Evidence Retrieval Specialist
*   **Role**: The "Scout".
*   **Goal**: Find precise evidence in SEC filings (10-Ks, 10-Qs).
*   **Capability**: Uses vector search (ChromaDB) to locate paragraphs relevant to a user's query (e.g., "What are the supply chain risks?").

### 4. Senior Financial Analyst (RAG)
*   **Role**: The "Interpreter".
*   **Goal**: Analyze the evidence found by the 'Scout'.
*   **Capability**: Can read a financial table or a risk disclosure and explain *why* it matters, identifying red flags in management commentary.

### 5. Citation & Compliance Specialist
*   **Role**: The "Auditor".
*   **Goal**: Ensure no hallucination.
*   **Action**: Verifies that every claim in the final answer has a citation pointing to a specific document source `[Source: 2023 Annual Report, Page 45]`.

### 6. Management Sentiment Analyst
*   **Role**: The "Psychologist".
*   **Goal**: Detect hidden signals in text.
*   **Technique**: Analyzes "hedging" language (words like *may, could, possibly, unforeseen*) to determine if management is confident or hiding bad news.

### 7. Document Q&A Specialist
*   **Role**: The "Front-Facing Exec".
*   **Goal**: Interface with the user.
*   **Action**: Takes the synthesized answer and formats it into a helpful, conversational response.

### 8. Financial Query Analyst
*   **Role**: The "Translator".
*   **Goal**: optimize search queries.
*   **Action**: Converts a user's vague question ("Is this company good?") into specific semantic search queries ("Revenue growth trends", "Debt maturity profile", "Competitive risks").

### 9. Document Summarization Expert
*   **Role**: The "Compressor".
*   **Goal**: creating executive summaries.
*   **Action**: Compress lengthy 100-page PDFs into concise bullet points without losing critical numerical details.

---

## 🛠️ Group 3: Specialized / Hybrid Agents
*These combine AI with deterministic code for maximum precision.*

### 10. KPI & Sentiment Agent (`kpi_sentiment_agent.py`)
*   **Type**: Deterministic + AI Hybrid.
*   **Task**: Financial Health Calculation.
*   **Workflow**:
    1.  **Code**: Python functions calculate exact ratios (ROE, Debt-to-Equity).
    2.  **AI**: FinBERT calculates a sentiment score (-1 to +1).
    3.  **Synthesis**: Combines these into the **FHI (Financial Health Index)** score (0-100).

### 11. Recommendation Engine (`recommendation_engine.py`)
*   **Type**: Small Language Model (SLM).
*   **Model**: `google/flan-t5-small` (Running locally/CPU).
*   **Task**: Explain the Rating.
*   **Workflow**:
    *   Takes the numeric scores (KPI, Sentiment, Risk).
    *   Generates the text: *"We implement a BUY rating because strong cash flow offsets the negative news sentiment."*
    *   **Why optimized?** Uses a small, fast model instead of a giant LLM to generate this short explanation quickly.
