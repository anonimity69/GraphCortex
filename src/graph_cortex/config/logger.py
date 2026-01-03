import os
import logging
from datetime import datetime

# Build absolute path to the Logs directory at the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
LOGS_DIR = os.path.join(PROJECT_ROOT, "Logs")

# Ensure the Logs directory physically exists early
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

def get_retrieval_logger():
    """
    Configures and returns a dedicated logger for Retrieval operations.
    Maintains a physical trail of Lexical vs Semantic Fallback triggers.
    """
    logger = logging.getLogger("RetrievalEngine")
    
    # Only configure if it doesn't already have handlers to prevent duplicate lines
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create a timestamped log file specific to this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(LOGS_DIR, f"retrieval_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Structural logging format for easy analysis
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
    return logger
