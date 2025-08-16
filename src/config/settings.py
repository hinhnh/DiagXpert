#!/usr/bin/env python3
"""
Configuration settings for DiagXpert
Professional configuration management with environment variables
"""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    vector_db_path: str = str(BASE_DIR / "data" / "vector_db")
    faiss_index_path: str = str(BASE_DIR / "data" / "faiss_index.pkl")
    docs_path: str = str(BASE_DIR / "data" / "docs.pkl")
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)


@dataclass
class OpenAIConfig:
    """OpenAI configuration settings"""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: str = "GPT-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 1000
    
    def __post_init__(self):
        """Load from environment variables"""
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", self.model)
        
    @property
    def is_configured(self) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(self.base_url and self.api_key)


@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI configuration settings"""
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    deployment_name: str = "GPT-4o-mini"
    embedding_deployment: str = "text-embedding-3-small"
    api_version: str = "2024-07-01-preview"
    
    def __post_init__(self):
        """Load from environment variables"""
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME", self.deployment_name)
        self.embedding_deployment = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", self.embedding_deployment)
        
    @property
    def is_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured"""
        return bool(self.endpoint and self.api_key)


@dataclass
class TTSConfig:
    """Text-to-Speech configuration settings"""
    engine: str = "pyttsx3"  # Default engine
    rate: int = 150  # Speech rate
    volume: float = 0.9  # Volume level
    voice_preference: Optional[str] = None  # Preferred voice
    
    def __post_init__(self):
        """Load from environment variables"""
        self.engine = os.getenv("TTS_ENGINE", self.engine)
        self.rate = int(os.getenv("TTS_RATE", self.rate))
        self.volume = float(os.getenv("TTS_VOLUME", self.volume))
        self.voice_preference = os.getenv("TTS_VOICE_PREFERENCE")


@dataclass
class ServerConfig:
    """Server configuration settings"""
    host: str = "0.0.0.0"
    port: int = 5050
    debug: bool = False
    use_reloader: bool = False
    
    def __post_init__(self):
        """Load from environment variables"""
        self.host = os.getenv("SERVER_HOST", self.host)
        self.port = int(os.getenv("SERVER_PORT", self.port))
        self.debug = os.getenv("SERVER_DEBUG", "false").lower() == "true"
        self.use_reloader = os.getenv("SERVER_USE_RELOADER", "false").lower() == "true"


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    
    def __post_init__(self):
        """Load from environment variables"""
        self.level = os.getenv("LOG_LEVEL", self.level)
        self.file_path = os.getenv("LOG_FILE_PATH")
        
        # Ensure log directory exists
        if self.file_path:
            Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    """Main application configuration"""
    name: str = "DiagXpert"
    version: str = "2.0.0"
    description: str = "AI Automotive Diagnostic Assistant with Workshop 4 Features"
    
    # Sub-configurations
    database: DatabaseConfig = None
    openai: OpenAIConfig = None
    azure_openai: AzureOpenAIConfig = None
    tts: TTSConfig = None
    server: ServerConfig = None
    logging: LoggingConfig = None
    
    def __post_init__(self):
        """Initialize sub-configurations"""
        if self.database is None:
            self.database = DatabaseConfig()
        if self.openai is None:
            self.openai = OpenAIConfig()
        if self.azure_openai is None:
            self.azure_openai = AzureOpenAIConfig()
        if self.tts is None:
            self.tts = TTSConfig()
        if self.server is None:
            self.server = ServerConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        
        # Ensure directories exist
        self.database.ensure_directories()
    
    @property
    def has_ai_provider(self) -> bool:
        """Check if any AI provider is configured"""
        return self.openai.is_configured or self.azure_openai.is_configured
    
    def get_ai_config(self):
        """Get the configured AI configuration"""
        if self.azure_openai.is_configured:
            return self.azure_openai
        elif self.openai.is_configured:
            return self.openai
        else:
            return None


# Global configuration instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance"""
    return config


def reload_config():
    """Reload configuration from environment variables"""
    global config
    config = AppConfig()
    return config
