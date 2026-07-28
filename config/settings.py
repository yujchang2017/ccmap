"""
Application configuration settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    # Security: Default to False for production safety
    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 'yes']
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Embedding settings
    # IMPORTANT: Runtime queries must use the same model that generated the precomputed .npy files.
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "3072"))
    
    # MongoDB settings
    MONGO_URI = os.getenv("MONGO_URI")
    
    # Redis settings (for rate limiting and caching)
    REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL")
    REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    
    # MongoDB connection pool settings for security and performance
    MONGO_MAX_POOL_SIZE = int(os.getenv('MONGO_MAX_POOL_SIZE', '35'))  # Max connections in pool (30 users + buffer)
    MONGO_MIN_POOL_SIZE = int(os.getenv('MONGO_MIN_POOL_SIZE', '5'))   # Min connections in pool (baseline performance)
    MONGO_MAX_IDLE_TIME_MS = int(os.getenv('MONGO_MAX_IDLE_TIME_MS', '30000'))  # 30 seconds
    MONGO_CONNECT_TIMEOUT_MS = int(os.getenv('MONGO_CONNECT_TIMEOUT_MS', '5000'))  # 5 seconds
    MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv('MONGO_SERVER_SELECTION_TIMEOUT_MS', '5000'))  # 5 seconds
    MONGO_SOCKET_TIMEOUT_MS = int(os.getenv('MONGO_SOCKET_TIMEOUT_MS', '10000'))  # 10 seconds
    
    # File paths - use absolute paths relative to project root
    # Find project root (where main.py is located)
    BASE_PATH = str(Path(__file__).parent.parent.resolve())
    DATA_PATH = os.path.join(BASE_PATH, "data")
    STATIC_PATH = os.path.join(BASE_PATH, "static")
    TEMPLATES_PATH = os.path.join(BASE_PATH, "templates")
    SCRIPTS_PATH = os.path.join(BASE_PATH, "scripts")
    LOGS_PATH = os.path.join(BASE_PATH, "logs")
    MAPS_PATH = os.path.join(DATA_PATH, "maps")
    
    # CORS settings (secure by default)
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
    CORS_SUPPORTS_CREDENTIALS = os.getenv('CORS_SUPPORTS_CREDENTIALS', 'False').lower() in ['true', '1', 'yes']
    
    # Embedding file paths
    DESCRIPTION_EMBEDDING_FILE = os.path.join(DATA_PATH, "embeddings", "description_embeddings.npy")
    KEYIDEA_EMBEDDING_FILE = os.path.join(DATA_PATH, "embeddings", "keyidea_embeddings.npy")
    UNIQUE_KEYIDEA_TEXTS_FILE = os.path.join(DATA_PATH, "embeddings", "unique_keyidea_texts.csv")
    # 各領域 cont.csv 的 content 欄位預先運算 embedding（避免每次查詢即時呼叫 API）
    CONTENT_EMBEDDING_FILE = os.path.join(DATA_PATH, "embeddings", "content_embeddings.npy")
    CONTENT_CATALOG_FILE = os.path.join(DATA_PATH, "embeddings", "content_catalog.csv")
    
    # CSV file paths
    GUIDEMETA_CSV = os.path.join(DATA_PATH, "raw", "guidemeta_tw.csv")
    MAP_CSV = os.path.join(DATA_PATH, "maps", "map.csv")

    # 領域內容 CSV 檔案（學習階段/領域/主題/細分內容選單資料來源）
    DOMAIN_CSV_FILES = {
        "國文": os.path.join(DATA_PATH, "raw", "1cn-cont.csv"),
        "英文": os.path.join(DATA_PATH, "raw", "2en-cont.csv"),
        "數學": os.path.join(DATA_PATH, "raw", "3math-cont.csv"),
        "社會": os.path.join(DATA_PATH, "raw", "4social-cont.csv"),
        "自然": os.path.join(DATA_PATH, "raw", "5nature-cont.csv"),
        "藝術": os.path.join(DATA_PATH, "raw", "6art-cont.csv"),
        "健康與體育": os.path.join(DATA_PATH, "raw", "7health-cont.csv"),
        "綜合活動": os.path.join(DATA_PATH, "raw", "8inte-cont.csv"),
        "科技": os.path.join(DATA_PATH, "raw", "9tech-cont.csv"),
        "生活": os.path.join(DATA_PATH, "raw", "10life-cont.csv"),
        "SDG": os.path.join(DATA_PATH, "raw", "SDGtw-cont.csv"),
    }
    
    @classmethod
    def validate(cls) -> bool:
        """驗證必要的配置"""
        if not cls.OPENAI_API_KEY:
            print("⚠ Warning: OPENAI_API_KEY not set")
            return False
        if not cls.MONGO_URI:
            print("⚠ Warning: MONGO_URI not set")
            return False
        
        # Redis 是可選的，但如果要使用速率限制功能，建議設定
        if not cls.REDIS_URL or not cls.REDIS_TOKEN:
            print("ℹ️  Info: Redis not configured - rate limiting will be disabled")
            print("   To enable Redis rate limiting, set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN")
        
        # Validate MongoDB connection pool settings
        if cls.MONGO_MAX_POOL_SIZE < cls.MONGO_MIN_POOL_SIZE:
            print("⚠ Warning: MONGO_MAX_POOL_SIZE should be >= MONGO_MIN_POOL_SIZE")
            return False
        if cls.MONGO_MAX_POOL_SIZE > 100:
            print("⚠ Warning: MONGO_MAX_POOL_SIZE should not exceed 100 for security")
            return False
        if cls.MONGO_MIN_POOL_SIZE < 3:
            print("⚠ Warning: MONGO_MIN_POOL_SIZE should be at least 3 for baseline performance")
            return False
        if cls.MONGO_MAX_POOL_SIZE < 30:
            print("⚠ Warning: MONGO_MAX_POOL_SIZE should be at least 30 for 30 concurrent users")
            return False
        
        return True


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = os.getenv('DEBUG', 'True').lower() in ['true', '1', 'yes']
    CORS_SUPPORTS_CREDENTIALS = True
    
    def __init__(self):
        # CORS settings for development (more permissive)
        self.CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000').split(',')


class ProductionConfig(Config):
    """Production configuration with enhanced security."""
    # Force debug to False in production for security
    DEBUG = False
    # Enhance secret key security for production
    SECRET_KEY = os.getenv('SECRET_KEY')
    CORS_SUPPORTS_CREDENTIALS = False  # Disable credentials for production security
    
    def __init__(self):
        # CORS settings for production (strict security)
        cors_origins_env = os.getenv('CORS_ORIGINS', '')
        self.CORS_ORIGINS = cors_origins_env.split(',') if cors_origins_env else []
    
    def validate(self) -> bool:
        """Enhanced validation for production."""
        if not self.SECRET_KEY:
            print("❌ Error: SECRET_KEY must be set in production")
            return False
        if self.SECRET_KEY == 'your-secret-key-here':
            print("❌ Error: Default SECRET_KEY cannot be used in production")
            return False
        # Check CORS_ORIGINS
        if not self.CORS_ORIGINS:
            print("⚠️ Warning: No CORS_ORIGINS set in production - only same-origin requests allowed")
        return super().validate()


# 簡化配置 - 只有開發和生產環境
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}