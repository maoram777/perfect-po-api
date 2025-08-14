from decouple import config
from typing import Optional


class Settings:
    # Database Configuration
    mongodb_url: str = config("MONGODB_URL", default="mongodb://localhost:27017/perfect_po_db")
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = config("AWS_ACCESS_KEY_ID", default=None)
    aws_secret_access_key: Optional[str] = config("AWS_SECRET_ACCESS_KEY", default=None)
    aws_region: str = config("AWS_REGION", default="us-east-1")
    s3_bucket_name: str = config("S3_BUCKET_NAME", default="perfect-po-catalogs")
    sqs_queue_url: Optional[str] = config("SQS_QUEUE_URL", default=None)
    
    # JWT Configuration
    jwt_secret_key: str = config("JWT_SECRET_KEY", default="your_super_secret_jwt_key_here")
    jwt_algorithm: str = config("JWT_ALGORITHM", default="HS256")
    jwt_expiration_minutes: int = config("JWT_EXPIRATION_MINUTES", default=10080, cast=int)  # 1 week (7 days * 24 hours * 60 minutes)
    
    # API Configuration
    api_host: str = config("API_HOST", default="0.0.0.0")
    api_port: int = config("API_PORT", default=8000, cast=int)
    debug: bool = config("DEBUG", default=True, cast=bool)
    
    # External APIs
    amazon_api_key: Optional[str] = config("AMAZON_API_KEY", default=None)
    amazon_api_secret: Optional[str] = config("AMAZON_API_SECRET", default=None)
    keepa_api_key: Optional[str] = config("KEEPA_API_KEY", default=None)


settings = Settings()
