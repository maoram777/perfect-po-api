import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()


def parse_env_file():
    """Parse ENV_FILE_DEV environment variable if it exists (for ECS single secret approach)."""
    # Only run this in ECS/production environments, not locally
    if os.environ.get('ENV_FILE_DEV') and not os.path.exists('.env'):
        print(f"🔍 Found ENV_FILE_DEV: {os.environ.get('ENV_FILE_DEV')[:100]}...")  # Debug log
        # Parse the ENV_FILE_DEV content (key=value format)
        for line in os.environ.get('ENV_FILE_DEV', '').strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Set the environment variable if it's not already set
                if key and value and key not in os.environ:
                    os.environ[key] = value
                    print(f"✅ Set {key}={value[:20]}...")  # Debug log
                elif key and value:
                    print(f"⚠️  {key} already set, skipping")  # Debug log
    else:
        if os.path.exists('.env'):
            print("📁 Local development: Using .env file")  # Debug log
        else:
            print("❌ No ENV_FILE_DEV or .env file found")  # Debug log


# Parse ENV_FILE_DEV at module import time (only in ECS)
parse_env_file()

# Debug: Show what environment variables we have
print(f"🔍 Environment variables after parsing:")
print(f"   MONGODB_URL: {os.environ.get('MONGODB_URL', 'NOT SET')}")
print(f"   JWT_SECRET_KEY: {os.environ.get('JWT_SECRET_KEY', 'NOT SET')[:10] if os.environ.get('JWT_SECRET_KEY') else 'NOT SET'}...")


class Settings:
    # Database Configuration
    mongodb_url: str = os.environ.get("MONGODB_URL")  # No fallback - must be set
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.environ.get("AWS_REGION", "us-east-1")
    s3_bucket_name: str = os.environ.get("S3_BUCKET_NAME", "perfect-po-catalogs")
    sqs_queue_url: Optional[str] = os.environ.get("SQS_QUEUE_URL")
    
    # JWT Configuration
    jwt_secret_key: str = os.environ.get("JWT_SECRET_KEY")  # No fallback - must be set
    jwt_algorithm: str = os.environ.get("JWT_ALGORITHM", "HS256")
    jwt_expiration_minutes: int = int(os.environ.get("JWT_EXPIRATION_MINUTES", "10080"))  # 1 week (7 days * 24 hours * 60 minutes)
    
    # API Configuration
    api_host: str = os.environ.get("API_HOST", "0.0.0.0")
    api_port: int = int(os.environ.get("API_PORT", "8000"))
    debug: bool = os.environ.get("DEBUG", "True").lower() == "true"
    
    # External APIs
    amazon_api_key: Optional[str] = os.environ.get("AMAZON_API_KEY")
    amazon_api_secret: Optional[str] = os.environ.get("AMAZON_API_SECRET")
    keepa_api_key: Optional[str] = os.environ.get("KEEPA_API_KEY")  # No fallback - must be set


settings = Settings()
