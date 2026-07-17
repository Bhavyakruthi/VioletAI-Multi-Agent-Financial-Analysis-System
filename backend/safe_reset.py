from services.chroma_service import ChromaService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def perform_safe_reset():
    """
    Triggers a safe reset of the knowledge base via ChromaService.
    This works even if the backend is running because it uses the API
    rather than trying to delete locked files.
    """
    # When SKIP_SUPABASE=True, the system uses this demo ID
    user_id = "00000000-0000-0000-0000-000000000000"
    
    logger.info(f"Starting safe reset for user: {user_id}")
    try:
        chroma = ChromaService(user_id)
        success = chroma.reset_knowledge_base()
        if success:
            logger.info("✅ Knowledge base reset successfully!")
            logger.info("You can now upload documents with your new embedding provider.")
        else:
            logger.error("❌ Failed to reset knowledge base.")
    except Exception as e:
        logger.error(f"Error during reset: {e}")

if __name__ == "__main__":
    perform_safe_reset()
