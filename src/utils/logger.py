"""
Professional Logging Utility for DiagXpert
Provides colored console output, file rotation, and performance logging
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
import time

# Fix import issue
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grand_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grand_parent_dir)
sys.path.insert(0, parent_dir)

try:
    from config.settings import LoggingConfig
except ImportError:
    # Fallback for direct execution
    class LoggingConfig:
        def __init__(self):
            self.level = "INFO"
            self.file_path = "logs/diagxpert.log"
            self.max_size = 10 * 1024 * 1024  # 10MB
            self.backup_count = 5
            self.console_format = "%(log_color)s%(levelname)s:%(name)s:%(message)s"
            self.file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to log level
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class DiagXpertLogger:
    """Professional logger for DiagXpert application"""
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        """Initialize the logger"""
        if config is None:
            from config.settings import get_config
            config = get_config().logging
        
        self.config = config
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup the logger with handlers and formatters"""
        # Create logger
        self.logger = logging.getLogger('DiagXpert')
        self.logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler (if configured)
        if self.config.file_path:
            file_handler = self._create_file_handler()
            self.logger.addHandler(file_handler)
        
        # Add console handler
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _create_file_handler(self) -> logging.Handler:
        """Create file handler with rotation"""
        log_path = os.path.abspath(self.config.file_path)
        log_path = os.path.normpath(log_path)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Use RotatingFileHandler for log rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=self.config.max_size,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        
        # Create formatter
        formatter = logging.Formatter(self.config.file_format)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        return file_handler
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance"""
        if name:
            return logging.getLogger(f'DiagXpert.{name}')
        return self.logger
    
    def set_level(self, level: str):
        """Set logging level"""
        level_upper = level.upper()
        if hasattr(logging, level_upper):
            self.logger.setLevel(getattr(logging, level_upper))
            self.config.level = level
            logging.info(f"Logging level set to: {level}")
        else:
            logging.warning(f"Invalid logging level: {level}")
    
    def add_file_handler(self, file_path: str, level: int = logging.DEBUG) -> None:
        """Add additional file handler"""
        try:
            log_path = os.path.abspath(file_path)
            log_path = os.path.normpath(log_path)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            formatter = logging.Formatter(self.config.file_format)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            
            self.logger.addHandler(file_handler)
            logging.info(f"📁 Added file handler: {file_path}")
            
        except Exception as e:
            logging.error(f"❌ Failed to add file handler: {e}")
    
    def log_startup(self, app_name: str, version: str):
        """Log application startup information"""
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 Starting {app_name} v{version}")
        self.logger.info(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"🔧 Log level: {self.config.level}")
        self.logger.info(f"📁 Log file: {self.config.file_path or 'Console only'}")
        self.logger.info("=" * 60)
    
    def log_shutdown(self, app_name: str):
        """Log application shutdown information"""
        self.logger.info("=" * 60)
        self.logger.info(f"🛑 Shutting down {app_name}")
        self.logger.info(f"📅 Shutdown at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)


def setup_logging(config: Optional[LoggingConfig] = None) -> DiagXpertLogger:
    """Setup and return DiagXpert logger"""
    return DiagXpertLogger(config)


def get_logger(name: str = "DiagXpert") -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


# Convenience functions for common logging tasks
def log_function_call(func_name: str, args: Dict[str, Any] = None, kwargs: Dict[str, Any] = None):
    """Decorator helper for logging function calls"""
    logger = get_logger()
    
    if args:
        logger.debug(f"Calling {func_name} with args: {args}")
    if kwargs:
        logger.debug(f"Calling {func_name} with kwargs: {kwargs}")
    
    if not args and not kwargs:
        logger.debug(f"Calling {func_name}")


def log_function_result(func_name: str, result: Any = None, error: Exception = None):
    """Log function result or error"""
    logger = get_logger()
    
    if error:
        logger.error(f"Function {func_name} failed: {error}")
    else:
        logger.debug(f"Function {func_name} completed successfully")
        if result is not None:
            logger.debug(f"Function {func_name} returned: {type(result).__name__}")


def log_performance(func_name: str, execution_time: float):
    """Log function performance"""
    logger = get_logger()
    
    if execution_time > 1.0:
        logger.warning(f"Function {func_name} took {execution_time:.2f}s (slow)")
    elif execution_time > 0.1:
        logger.info(f"Function {func_name} took {execution_time:.2f}s")
    else:
        logger.debug(f"Function {func_name} took {execution_time:.3f}s")


# Performance logging decorator
def log_performance_decorator(func):
    """Decorator to log function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"⚡ {func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper


# Error logging decorator
def log_errors(func):
    """Decorator to log errors in route handlers"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = get_logger()
            logger.error(f"❌ Error in {func.__name__}: {e}")
            logger.exception("Full traceback:")
            return jsonify({"error": str(e)}), 500
    return wrapper
