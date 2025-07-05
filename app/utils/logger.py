import logging
import sys
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure log rotation
log_file = os.path.join(LOG_DIR, "ai_tutor.log")
MAX_BYTES = 10 * 1024 * 1024  # 10MB per file
BACKUP_COUNT = 5  # Keep 5 backup files

logger = logging.getLogger("ai_tutor")
logger.setLevel(logging.INFO)

# Remove all handlers first (avoid duplicate logs)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Console handler with UTF-8 encoding
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# Ensure UTF-8 encoding for the console handler (fix UnicodeEncodeError)
if hasattr(console_handler.stream, 'reconfigure'):
    console_handler.stream.reconfigure(encoding='utf-8')

# File handler with rotation
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=MAX_BYTES,
    backupCount=BACKUP_COUNT,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(console_handler)
logger.addHandler(file_handler)

def log_tool_usage(tool_name: str, input_data: dict, result: any, success: bool):
    """Log tool usage for debugging and monitoring"""
    logger.info(f"Tool Used: {tool_name}")
    logger.info(f"Input: {input_data}")
    logger.info(f"Result: {result}")
    logger.info(f"Success: {success}")

def log_agent_action(agent_name: str, action: str, details: str = ""):
    """Log agent actions"""
    logger.info(f"Agent: {agent_name} | Action: {action} | Details: {details}")

def log_api_call(endpoint: str, method: str, status_code: int = None):
    """Log API calls"""
    log_message = f"API Call: {method} {endpoint}"
    if status_code:
        log_message += f" | Status: {status_code}"
    logger.info(log_message)