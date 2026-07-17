# 🎤 VioletAI Presentation Guide

This document is your cheat sheet for presenting **VioletAI**. It contains deep dives into the technology, explanations of *how* features are implemented, and a script you can adapt for your demo.

---

## 🛠️ Part 1: The Tech Stack (The "How It's Built")

**"We used a modern, scalable architecture designed for real-time financial intelligence."**

### 1. Frontend: **React + Vite**
*   **Why?** Instant reactivity. Financial dashboards need to be fast. Vite provides next-gen tooling for rapid development.
*   **Key Libraries:**
    *   `ApexCharts`: For the interactive stock price and technical indicator charts.
    *   `Framer Motion`: For smooth UI transitions (making it feel "premium").
    *   `Axios`: For handling API requests to our backend.

### 2. Backend: **FastAPI (Python)**
*   **Why?** High performance. FastAPI is one of the fastest Python frameworks, essential for handling multiple AI agent streams and stock data simultaneously. It handles asynchronous tasks (like scraping Reddit while calculating forecasts) efficiently.

### 3. AI Orchestration: **CrewAI**
*   **Why?** Single LLM calls aren't enough for complex reports. We need *agents*.
*   **Implementation:** We define distinct roles ("Quantitative Strategist", "Equity Research Analyst") that talk to each other to produce a cohesive report, mimicking a real Wall Street firm.

### 4. Intelligence Layer: **Google Gemini & FinBERT**
*   **Google Gemini (2.0 Flash):** The brain behind our agents. Chosen for its large context window and reasoning capabilities.
*   **FinBERT:** A BERT model fine-tuned specifically for financial text. We use it to score news and Reddit posts because generic sentiment models often misinterpret market jargon.

### 5. Memory & Search: **ChromaDB (RAG)**
*   **Why?** Large Context. We can't feed 100 pages of annual reports into an LLM prompt.
*   **How:** We "embed" documents into vectors and store them in ChromaDB. When you ask a question, we semantically search for the most relevant chunks and feed only those to the AI.

### 6. Forecasting: **Facebook Prophet**
*   **Why?** Optimized for time-series data with seasonality. It handles missing data well and is robust to shifts in trend, making it reliable for stock price visualization.

---

## ⚙️ Part 2: Implementation Deep Dives (The "How It Works")

### 🔄 The RAG Pipeline (Retrieval-Augmented Generation)
**"How does it answer questions from PDFs?"**
1.  **Upload:** User uploads a PDF/DOCX.
2.  **Chunking:** `document_processor.py` splits text into manageably sized pieces (~500 chars).
3.  **Embedding:** `vector_store.py` uses an embedding model to turn text into number lists (vectors).
4.  **Storage:** Vectors are saved in `ChromaDB`.
5.  **Retrieval:** When a user asks a question, we convert the question to a vector and find the nearest neighbors in the database.
6.  **Generation:** The context + question is sent to Gemini to generate the final answer.

### 🤖 The Agent Workflow
**"How is the report written?"**
1.  **User Input:** Ticker (e.g., "AAPL") + Goals.
2.  **Agent 1 (Strategist):** Looks at the quantitative data (Prophet forecast, Financial Health Index, moving averages). It identifies *what* looks good or bad.
3.  **Agent 2 (Analyst):** Takes the Strategist's notes + RAG evidence (news/reports) and writes the narrative. It structures the text into "Executive Summary", "Risks", etc.
4.  **Output:** A Markdown string is returned and rendered on the frontend.

### 🐦 Social Sentiment Analysis
**"How do we know what the market 'feels'?"**
1.  **Scraping:** `social_sentiment_service.py` hits Reddit APIs (r/wallstreetbets, r/stocks).
2.  **Filtering:** We search specifically for the Ticker symbols.
3.  **Scoring:** Each post title is passed through FinBERT.
    *   "AAPL moons" -> Positive (Score: 0.9)
    *   "Puts on AAPL" -> Negative (Score: -0.8)
4.  **Aggregation:** We compute a weighted average to give a final "Bullish" or "Bearish" signal.

---

## 🗣️ Part 3: Presentation Script

*(Use this as a guide for what to say during your demo)*

### **Introduction (1 Minute)**
> "Good morning/afternoon. Today I'm presenting **VioletAI**, an institutional-grade equity research assistant designed to democratize financial intelligence.
>
> **The Problem:** In today's market, data is everywhere, but *insight* is scarce. Retail investors struggle to analyze annual reports, understand market sentiment, and predict trends simultaneously.
>
> **The Solution:** VioletAI combines quantitative rigor (math) with qualitative reasoning (AI agents) to act as your personal investment analyst team."

### **Technical Architecture (1-2 Minutes)**
*(Show the Tech Stack Slide or GitHub Readme)*
> "We built this using a cutting-edge stack tailored for AI:
> *   **React & Vite** for a responsive frontend.
> *   **FastAPI** for high-performance backend processing.
> *   And crucially, **CrewAI** to orchestrate a team of autonomous agents.
> *   We also use **RAG (Retrieval-Augmented Generation)** with **ChromaDB** to let the AI 'read' and remember thousands of pages of PDF documents."

### **The Demo (3-4 Minutes)**
*(Walk through the app live)*

**1. Dashboard & Basics**
> "Let's look at Apple (AAPL). Immediately, you see real-time price data and our **Facebook Prophet** forecast model projecting the next 30 days."

**2. Financial Health**
> "Here is our custom **Financial Health Index**. We calculate this by aggregating liquidity, solvency, and profitability ratios into a single 'Grade'. AAPL gets an 'A' here because of its strong cash flow."

**3. Social Sentiment**
> "Markets are driven by psychology. Here, our system has scraped Reddit communities like r/wallstreetbets. Using **FinBERT**, we analyzed the tone of discussions, showing us that retail sentiment is currently [Bullish/Bearish]."

**4. The Core: AI Agent Report**
> "This is the highlight. I'll ask the system to generate a full investment report.
> *[Click Analyze]*
> Behind the scenes, two AI agents are working. The **Strategist** looks at the charts, while the **Analyst** reads the news. They collaborate to write this Executive Summary and SWOT analysis specifically for me."

**5. RAG / Chat**
> "Finally, I have Apple's 10-K report uploaded here. I can simply ask: *'What are the risk factors regarding supply chain?'*
> The system retrieves the exact page from the PDF and summarizes it for me, saving me hours of reading."

### **Conclusion (1 Minute)**
> "In summary, VioletAI isn't just a dashboard—it's a reasoning engine. It automates the tedious parts of research allowing investors to focus on decision making. Thank you, and I'm happy to answer any questions."

---

## ❓ Preparation for Q&A

**Q: How accurate is the forecasting?**
*A: We use Facebook Prophet, which is excellent at capturing seasonality (recurring trends), but like all stock models, it cannot predict black swan events. It's a tool for trend analysis, not crystal-ball prediction.*

**Q: Why use Agents instead of just ChatGPT?**
*A: A single prompt often hallucinates or misses details when doing complex math + writing. By splitting tasks (One agent does math, one writes), we get much higher accuracy and structure.*

**Q: How does the RAG system handle privacy?**
*A: Documents are processed locally into vectors. We don't train the model on user data; we just retrieve relevant chunks for the specific session.*
