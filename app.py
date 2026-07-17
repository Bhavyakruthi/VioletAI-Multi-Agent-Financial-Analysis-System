# """
# Streamlit Frontend for RAG System
# =================================
# User interface for document upload, Q&A, and summarization.
# """

# import streamlit as st
# import os
# from datetime import datetime
# import logging
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Page configuration
# st.set_page_config(
#     page_title="RAG Document Assistant",
#     page_icon="📚",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # Custom CSS
# st.markdown("""
#     <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: bold;
#         color: #1E88E5;
#         margin-bottom: 1rem;
#     }
#     .sub-header {
#         font-size: 1.2rem;
#         color: #666;
#         margin-bottom: 2rem;
#     }
#     .success-box {
#         padding: 1rem;
#         background-color: #E8F5E9;
#         border-radius: 0.5rem;
#         border-left: 4px solid #4CAF50;
#     }
#     .info-box {
#         padding: 1rem;
#         background-color: #E3F2FD;
#         border-radius: 0.5rem;
#         border-left: 4px solid #2196F3;
#     }
#     .warning-box {
#         padding: 1rem;
#         background-color: #FFF3E0;
#         border-radius: 0.5rem;
#         border-left: 4px solid #FF9800;
#     }
#     </style>
# """, unsafe_allow_html=True)


# def initialize_session_state():
#     """Initialize session state variables."""
#     if "rag_crew" not in st.session_state:
#         st.session_state.rag_crew = None
#     if "documents_loaded" not in st.session_state:
#         st.session_state.documents_loaded = False
#     if "chat_history" not in st.session_state:
#         st.session_state.chat_history = []
#     if "summary" not in st.session_state:
#         st.session_state.summary = None
#     if "api_key_set" not in st.session_state:
#         st.session_state.api_key_set = False


# def initialize_rag_crew(api_key: str = None):
#     """Initialize the RAG crew with the API key."""
#     try:
#         from rag_crew import RAGCrew
#         st.session_state.rag_crew = RAGCrew(
#             google_api_key=api_key,
#             verbose=False,
#         )
#         st.session_state.api_key_set = True
#         return True
#     except Exception as e:
#         st.error(f"Error initializing RAG system: {str(e)}")
#         logger.exception("Error initializing RAG system")
#         return False


# def main():
#     """Main application function."""
#     initialize_session_state()
    
#     # Header
#     st.markdown('<p class="main-header">📚 RAG Document Assistant</p>', unsafe_allow_html=True)
#     st.markdown('<p class="sub-header">Upload documents, get summaries, and ask questions (Powered by Google Gemini)</p>', unsafe_allow_html=True)
    
#     # Sidebar
#     with st.sidebar:
#         st.header("⚙️ Configuration")
        
#         # Check for existing API key in environment
#         env_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
#         # API Key input
#         api_key = st.text_input(
#             "Google API Key (Gemini)",
#             type="password",
#             help="Enter your Google API key or leave empty to use .env file",
#             value="",
#             placeholder="Leave empty to use .env file" if env_api_key else "Enter API key",
#         )
        
#         # Use env key if input is empty
#         effective_api_key = api_key if api_key else env_api_key
        
#         if env_api_key and not api_key:
#             st.info("🔑 Using API key from .env file")
        
#         # Show current model
#         current_model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
#         st.caption(f"Model: {current_model}")
        
#         if effective_api_key and not st.session_state.api_key_set:
#             if st.button("Initialize System", type="primary"):
#                 with st.spinner("Initializing RAG system..."):
#                     if initialize_rag_crew(effective_api_key):
#                         st.success("✅ System initialized!")
#                         st.rerun()
#         elif not effective_api_key:
#             st.warning("⚠️ No API key found. Add to .env or enter above.")
        
#         if st.session_state.api_key_set:
#             st.success("✅ System Ready")
        
#         st.divider()
        
#         # Document upload section
#         st.header("📁 Document Upload")
        
#         uploaded_files = st.file_uploader(
#             "Upload Documents",
#             type=["pdf", "txt", "docx", "doc"],
#             accept_multiple_files=True,
#             help="Supported formats: PDF, TXT, DOCX",
#         )
        
#         if uploaded_files and st.session_state.rag_crew:
#             if st.button("Process Documents", type="primary"):
#                 with st.spinner("Processing documents..."):
#                     try:
#                         num_docs = st.session_state.rag_crew.add_documents(uploaded_files)
#                         st.session_state.documents_loaded = True
#                         st.success(f"✅ Processed {num_docs} document pages!")
#                     except Exception as e:
#                         st.error(f"Error processing documents: {str(e)}")
        
#         # Show loaded documents
#         if st.session_state.documents_loaded and st.session_state.rag_crew:
#             st.divider()
#             st.subheader("📋 Loaded Documents")
#             doc_list = st.session_state.rag_crew.get_document_list()
#             for doc in doc_list:
#                 st.write(f"• {doc}")
            
#             if st.button("Clear All Documents", type="secondary"):
#                 st.session_state.rag_crew.clear_documents()
#                 st.session_state.documents_loaded = False
#                 st.session_state.summary = None
#                 st.session_state.chat_history = []
#                 st.rerun()
    
#     # Main content area
#     if not st.session_state.api_key_set:
#         st.markdown("""
#         <div class="warning-box">
#             <h3>⚠️ Initialize System Required</h3>
#             <p>Click "Initialize System" in the sidebar to get started. 
#             Your API key is loaded from the .env file.</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         st.markdown("""
#         ### Quick Start:
#         1. Make sure your `.env` file has `GOOGLE_API_KEY` set
#         2. Click **Initialize System** in the sidebar
#         3. Upload your documents (PDF, TXT, DOCX)
#         4. Ask questions or generate summaries!
#         """)
#         return
    
#     if not st.session_state.documents_loaded:
#         st.markdown("""
#         <div class="info-box">
#             <h3>📤 Upload Documents</h3>
#             <p>Upload PDF, TXT, or DOCX files using the sidebar to begin analysis.</p>
#         </div>
#         """, unsafe_allow_html=True)
#         return
    
#     # Create tabs for different functionalities
#     tab1, tab2, tab3 = st.tabs(["💬 Ask Questions", "📝 Document Summary", "📊 Analysis"])
    
#     # Tab 1: Q&A
#     with tab1:
#         st.header("Ask Questions About Your Documents")
        
#         # Chat interface
#         question = st.text_input(
#             "Enter your question:",
#             placeholder="What are the main findings in the documents?",
#             key="question_input",
#         )
        
#         col1, col2 = st.columns([1, 5])
#         with col1:
#             ask_button = st.button("Ask", type="primary", use_container_width=True)
#         with col2:
#             clear_chat = st.button("Clear Chat", type="secondary")
        
#         if clear_chat:
#             st.session_state.chat_history = []
#             st.rerun()
        
#         if ask_button and question:
#             with st.spinner("Searching documents and generating answer..."):
#                 try:
#                     answer = st.session_state.rag_crew.answer_question(question)
#                     st.session_state.chat_history.append({
#                         "question": question,
#                         "answer": answer,
#                         "timestamp": datetime.now().strftime("%H:%M:%S"),
#                     })
#                 except Exception as e:
#                     st.error(f"Error: {str(e)}")
        
#         # Display chat history
#         if st.session_state.chat_history:
#             st.divider()
#             for i, chat in enumerate(reversed(st.session_state.chat_history)):
#                 with st.container():
#                     st.markdown(f"**🙋 Question** ({chat['timestamp']})")
#                     st.write(chat["question"])
#                     st.markdown("**🤖 Answer**")
#                     st.write(chat["answer"])
#                     st.divider()
    
#     # Tab 2: Summary
#     with tab2:
#         st.header("Document Summary")
        
#         col1, col2 = st.columns([1, 4])
#         with col1:
#             generate_summary = st.button("Generate Summary", type="primary", use_container_width=True)
        
#         if generate_summary:
#             with st.spinner("Generating comprehensive summary... This may take a moment."):
#                 try:
#                     summary = st.session_state.rag_crew.summarize_documents()
#                     st.session_state.summary = summary
#                 except Exception as e:
#                     st.error(f"Error generating summary: {str(e)}")
        
#         if st.session_state.summary:
#             st.markdown(st.session_state.summary)
            
#             st.divider()
            
#             # Download button
#             summary_bytes = st.session_state.summary.encode("utf-8")
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
#             st.download_button(
#                 label="📥 Download Summary as TXT",
#                 data=summary_bytes,
#                 file_name=f"document_summary_{timestamp}.txt",
#                 mime="text/plain",
#             )
    
#     # Tab 3: Analysis
#     with tab3:
#         st.header("Document Analysis")
        
#         analysis_type = st.selectbox(
#             "Select Analysis Type",
#             options=["general", "financial", "sentiment"],
#             format_func=lambda x: {
#                 "general": "📋 General Analysis",
#                 "financial": "💰 Financial Analysis",
#                 "sentiment": "😊 Sentiment Analysis",
#             }.get(x, x),
#         )
        
#         if st.button("Run Analysis", type="primary"):
#             with st.spinner(f"Running {analysis_type} analysis..."):
#                 try:
#                     analysis = st.session_state.rag_crew.analyze_documents(analysis_type)
#                     st.markdown(analysis)
                    
#                     # Download option
#                     st.divider()
#                     analysis_bytes = analysis.encode("utf-8")
#                     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
#                     st.download_button(
#                         label="📥 Download Analysis as TXT",
#                         data=analysis_bytes,
#                         file_name=f"{analysis_type}_analysis_{timestamp}.txt",
#                         mime="text/plain",
#                     )
#                 except Exception as e:
#                     st.error(f"Error running analysis: {str(e)}")
    
#     # Footer
#     st.divider()
#     st.markdown(
#         """
#         <div style="text-align: center; color: #888; font-size: 0.9rem;">
#             RAG Document Assistant | Powered by CrewAI & Google Gemini
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# if __name__ == "__main__":
#     main()
