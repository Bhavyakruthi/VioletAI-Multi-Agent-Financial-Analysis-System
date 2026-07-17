# Handle ChromaDB Migration
# Deletes old 768-dim DB to support new 384-dim local embeddings

import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "./chroma_db"

def migrate_db():
    if os.path.exists(DB_PATH):
        logger.info(f"Detected existing ChromaDB at {DB_PATH}.")
        logger.info("Migrating to local embeddings (Dimension shift 768 -> 384 required).")
        try:
            shutil.rmtree(DB_PATH)
            logger.info("Successfully cleared old DB. New local embeddings will be generated on next ingestion.")
        except Exception as e:
            logger.error(f"Failed to clear old DB: {e}")
    else:
        logger.info("No existing ChromaDB found. Ready for fresh local embeddings.")

if __name__ == "__main__":
    migrate_db()
