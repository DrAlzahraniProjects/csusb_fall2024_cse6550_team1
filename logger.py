import logging
import os
from logging.handlers import RotatingFileHandler

class Logger():
    """
    A class to log messages to a file with improved configuration
    """
    def __init__(self, name):
        """
        Initialize the logger

        Args:
            name (str): The name of the logger
        """
        # Disable watchdog logging completely
        logging.getLogger('watchdog').setLevel(logging.ERROR)
        logging.getLogger('watchdog.observers.inotify_buffer').disabled = True
        
        # Create logs directory if it doesn't exist
        log_dir = '/app/logs'
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure the logger
        self.log = logging.getLogger(name)
        
        # Only add handlers if they haven't been added already
        if not self.log.handlers:
            self.log.setLevel(logging.INFO)
            
            # Create rotating file handler with custom filter
            handler = RotatingFileHandler(
                filename=f'{log_dir}/app.log',
                maxBytes=1024 * 1024,  # 1MB
                backupCount=5,
                mode='a'
            )
            # Create and add filter to exclude watchdog messages
            class WatchdogFilter(logging.Filter):
                def filter(self, record):
                    return not record.name.startswith('watchdog')
            
            handler.addFilter(WatchdogFilter())
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # Add handler to logger
            self.log.addHandler(handler)
            
            # Prevent propagation to root logger
            self.log.propagate = False
        
    def info(self, message):
        """
        Log an info message

        Args:
            message (str): The message to log
        """
        self.log.info(message)

    def debug(self, message):
        """
        Log a debug message

        Args:
            message (str): The message to log
        """
        self.log.debug(message)

    def error(self, message):
        """
        Log an error message

        Args:
            message (str): The message to log
        """
        self.log.error(message)