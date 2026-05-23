import logging
import os
from pathlib import Path

def setup_logging(debug=False):
    log_dir = Path.home() / ".emata"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "emata.log"
    
    level = logging.DEBUG if debug else logging.INFO
    
    # Configure logging to file
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8")
        ]
    )
    
    # Create a console logger for critical errors if needed, 
    # but we usually handle that via rich in emata.py
    
    logger = logging.getLogger("emata")
    if debug:
        logger.debug("Debug logging enabled.")
    
    return logger
