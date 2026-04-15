import logging 
from datetime import datetime

def setup_logger():
    """
    logger setup - root
    """
    log_filename = datetime.now().strftime('log_%m_%d_%Y.log')

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()  
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()      
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
