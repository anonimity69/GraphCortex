import os
import logging
from datetime import datetime
from graph_cortex.config.retrieval import LOG_LEVEL

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
LOGS_DIR = os.path.join(PROJECT_ROOT, "Logs")
os.makedirs(LOGS_DIR, exist_ok=True)


def get_retrieval_logger():
    logger = logging.getLogger("RetrievalEngine")

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    if not logger.handlers:
        logger.setLevel(level)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fh = logging.FileHandler(os.path.join(LOGS_DIR, f"retrieval_{timestamp}.log"))
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(fh)

    return logger
