# should be coming from external configuration
import os


class AppConfig:
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ERROR_MESSAGE_KEY = "message"
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 10 * 60
    RATELIMIT_HEADERS_ENABLED = True
    SECRET_KEY = "super-secret-key"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///test.db")
    # SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://your_name:your_password@localhost:5432/bookmark"
