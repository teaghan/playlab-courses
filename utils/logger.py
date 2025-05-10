import logging
import re
import psutil
import os

class AppLogger:
    def __init__(self):
        # Initialize the logger
        self.logger = logging.getLogger('app_logger')
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter with memory usage
        formatter = logging.Formatter('%(message)s')# [Memory: %(memory_usage).2f MB]')
        console_handler.setFormatter(formatter)
        
        # Add memory usage filter
        class MemoryFilter(logging.Filter):
            def filter(self, record):
                process = psutil.Process(os.getpid())
                memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
                record.memory_usage = memory
                return True
                
        #self.logger.addFilter(MemoryFilter())

        # Add handler to logger
        self.logger.addHandler(console_handler)
        
        # Regular expression patterns for filtering
        self.ignore_patterns = [
            r'/_stcore/health',
            r'/_stcore/host-config',
            r'/_stcore/stream',
            r'/static/',
            r'/favicon',
            r'\.woff2',
            r'\.css',
            r'\.js',
            r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3}\sThread\s'  # Thread pattern
        ]
    
    def should_log(self, message):
        message = str(message)
        
        # Skip if message matches any ignore pattern
        if any(re.search(pattern, message) for pattern in self.ignore_patterns):
            return False
            
        # Skip other unwanted messages
        skip_patterns = [
            'HTTP Request:',
            'missing ScriptRunContext',
            'file_cache',
        ]
        
        return not any(pattern in message for pattern in skip_patterns)
    
    def info(self, message):
        if self.should_log(message):
            self.logger.info(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)

# Create a singleton instance
logger = AppLogger()