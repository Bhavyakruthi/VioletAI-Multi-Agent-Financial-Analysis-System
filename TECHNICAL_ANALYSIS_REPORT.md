# 📘 Comprehensive Technical Analysis Report

This document provides an exhaustive breakdown of the **VioletAI** codebase, detailing every implemented feature, the technology used, and the specific logic behind it.

---

## 🏗️ 1. High-Level Architecture

The system follows a **Microservice-like Monolithic** architecture:
*   **Frontend**: React (Vite) + Tailwind CSS (via index.css) + Framer Motion.
*   **Backend**: FastAPI (Python) serving REST endpoints.
*   **Orchestration**: CrewAI for multi-agent logic.
*   **Data/Memory**: ChromaDB (Vector Search) + Supabase (Auth/User Data).
*   **Intelligence**: Google Gemini (LLM) + FinBERT (Sentiment) + Prophet (Forecasting).

---

## 🖥️ 2. Frontend Implementation (`/frontend`)

### **Key Tech Stack**
*   **Build Tool**: Vite (`npm run dev` for instant HMR).
*   **State Management**: React `useState` / `useEffect` (local state) + custom `api.js` hooks.
*   **Visualizations**: `react-apexcharts` (Calculated candlesticks, line charts).
*   **Animations**: `framer-motion` (Smooth entry/exit of cards, e.g., in `SocialSentiment.jsx`).
*   **Icons**: `lucide-react` (Lightweight, consistent SVG icons).

### **Core Components Analysis**
1.  **`SocialSentiment.jsx`**:
    *   **Logic**: Fetches data concurrently from Reddit, StockTwits, and Twitter endpoints using `Promise.all`.
    *   **UI**: Implements a "Smart Tab" system that defaults to the platform with the most mentions. Uses a glassmorphism design (`glass-card` class).
    *   **Visuals**: Color-coded badges (Green/Red/Amber) dynamically set based on `sentiment_label`.

2.  **`PriceChart.jsx` / `ForecastChart.jsx`**:
    *   **Logic**: Receives raw time-series data. `ForecastChart` renders the `yhat` (prediction) line along with `yhat_lower` and `yhat_upper` (confidence intervals) as a shaded area.
    *   **Library**: **ApexCharts** is used here for its performance with large datasets (candlesticks).

3.  **`Analysis.jsx`**:
    *   **Flow**: Handles the "Run Analysis" button state. It polls the backend or waits for the long-running async request to complete. It conditionally renders the "Report" section only when the JSON response contains `report_body`.

---

## ⚙️ 3. Backend Services (`/backend/services`)
This is where the heavy lifting happens.

### **A. Analysis Service** (`analysis_service.py`)
The **Brain** of the operation.
*   **Orchestration**: It acts as a facade, calling `yfinance`, `Prophet`, `CrewAI`, and `PDFGenerator`.
*   **LLM Handling**:
    *   **Provider Rotation**: Implements a retry loop (3 attempts). If Google Gemini hits a quota limit (429), it triggers `api_manager.rotate_key()` to switch to a backup key or provider (Groq).
    *   **Fallback**: If LLM fails completely, it calls `_build_report_text()` to generate a deterministic "safe mode" report using template strings.
*   **RAG Integration**: It automatically "ingests" the generated PDF report back into ChromaDB so the AI "remembers" its own past analysis.

### **B. Social Sentiment Service** (`social_sentiment_service.py`)
*   **Logic**:
    *   Does **NOT** use the official Reddit API (which requires OAuth). Instead, it hits the public JSON endpoints (`https://www.reddit.com/r/{subreddit}/search.json`).
    *   **Scoring**: Uses a deterministic keyword dictionary (`bullish_words` vs `bearish_words`) to calculate a weighted average score based on post upvotes.
    *   **Key Insight**: It prioritizes posts from `wallstreetbets`, `stocks`, and `investing`.

### **C. StockTwits Service** (`stocktwits_service.py`)
*   **Logic**:
    *   Hits `api.stocktwits.com/api/2/streams/symbol/{TICKER}.json`.
    *   **Hybrid Scoring**: It first checks if the user explicitly tagged their post as "Bullish" or "Bearish" (metadata). If not, it falls back to the customized keyword analysis.

### **D. Scheduler Service** (`scheduler_service.py`)
*   **Library**: **APScheduler**.
*   **Function**: Runs background tasks (likely for periodic data fetching or cache cleanup) without blocking the main FastAPI thread.

### **E. Utility Services (Email, YouTube, Twitter, Recommendation)**

#### **1. Email Integration** (`email_service.py`)
*   **Implementation**: A classic SMTP client wrapper using python’s built-in `smtplib`.
*   **Template**: It constructs a simple HTML body (`format_report_html`) that embeds the analysis summary, creating a clean branding wrapper around the raw text.

#### **2. YouTube Scraper** (in `analysis_service.py`)
*   **Why Custom?** The official YouTube API has strict quota limits.
*   **Technique**: It performs a "Direct HTML Scraping" attack.
    *   It requests the YouTube search results page.
    *   Uses Regex to extract the specialized JSON blob `var ytInitialData = {...}` embedded in the page source.
    *   Parses this JSON to find video IDs, titles, and thumbnails without hitting any API limits.

#### **3. Twitter/X Sentiment** (`twitter_sentiment_service.py`)
*   **Mock Simulation**: Accessing X data is currently expensive (Enterprise API).
*   **Implementation**: This service currently implements a **Simulation Layer**. It generates realistic looking "Mock Tweets" (e.g., from user "TraderJoe") to demonstrate the UI capabilities without incurring API costs.
*   **Fallback**: It includes a keyword-based sentiment scorer (`_simple_sentiment_score`) ready to be hooked into a real scraper like Nitter.

#### **4. The Recommendation Engine** (`backend/core/recommendation/recommendation_engine.py`)
This is a **Hybrid Systems** implementation, combining Rule-Based Logic with Small-Language Models (SLMs).
*   **Logic (The "Score")**:
    *   It calculates a composite `final_score` (0-100) combining three factors:
        1.  **KPI Score**: Weighted average of financial ratios.
        2.  **Sentiment Score**: From FinBERT.
        3.  **Risk Penalty**: Deducts points if Debt-to-Equity > 1.0 or Sentiment < 0.2.
*   **Logic (The "Reasoning")**:
    *   It uses **Google Flan-T5-Small** (a local transformer model) to generate the text explanation.
    *   It constructs a prompt with the numeric scores and asks Flan-T5 to "Rewrite this as a short investment rationale."
*   **Why Flan-T5?** It's small enough to run on CPU without a GPU, making the recommendation engine highly portable.

---

## 🤖 4. AI & Agents Core (`/backend/core`)

### **A. CrewAI Agents** (`agents.py` & `rag_crew.py`)
We use a **Role-Based** agent architecture.
1.  **Evidence Retrieval Specialist**: "Scout" agent. Uses tools to find data in PDFs.
2.  **Financial Analyst**: "Thinker" agent. Interprets the data found by the scout.
3.  **Citation Specialist**: "Compliance" agent. Ensures every claim has a `[Source: Page X]` reference.
4.  **Writer**: Synthesizes everything into the final Markdown report.

### **B. KPI & Sentiment Agent** (`kpi_sentiment_agent.py`)
A specialized **Deterministic Agent**.
*   **Why?** LLMs are bad at precise math (calculating Ratios).
*   **How**: It takes raw financial statements -> runs python functions (`compute_kpis`) to get exact numbers (ROE, Debt-to-Equity) -> then feeds those numbers to the LLM for qualitative interpretation.
*   **Tone Analysis**: It analyzes the "hedging" language (words like "maybe", "possibly", "unforeseen") in earnings transcripts to flag management uncertainty.

---

## 📚 5. Key Libraries & Why They Were Used

| Library | Category | Usage |
| :--- | :--- | :--- |
| **CrewAI** | AI Orchestration | Managing the workflow between multiple agents (Researcher -> Writer). |
| **Facebook Prophet** | Data Science | Time-series forecasting. Chosen for its ability to handle seasonality (holidays, weekends) better than standard linear regression. |
| **yfinance** | Data Source | Scraping Yahoo Finance data for free (Price, Market Cap, Sector). |
| **ChromaDB** | Vector DB | Local vector storage for RAG. It stores the "embeddings" of your PDFs. |
| **Sentence-Transformers** | ML | Converts text into vectors (numbers) for ChromaDB. |
| **FastAPI** | Backend Framework | Chosen for its async capabilities (essential for handling multiple LLM streams). |
| **Framer Motion** | Frontend | Physics-based animations for the React UI. |
| **APScheduler** | Utilities | Python job scheduling (Cron-like behavior inside the app). |
| **Pydantic** | Validation | Data validation for all API requests/responses (ensures type safety). |

---

## 💡 6. Special Implementation Details to Highlight

1.  **The "Safety Net" Report**: The system is designed to **never fail silently**. If the advanced AI crashes, the code seamlessly degrades to a "Quant-Only" report mode (`_build_report_text`), ensuring the user always gets *something* valuable.
2.  **Self-Feeding Memory**: The unique feature where the *generated report* itself becomes part of the knowledge base. This means if you analyze AAPL today, and ask about it next week, the AI remembers its previous analysis.
3.  **Multi-Model Fallback**: The `api_manager` allows the system to switch between Google Gemini and Groq (Llama 3) dynamically if one provider goes down or limits are reached.
