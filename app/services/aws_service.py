import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
from ..config import settings
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AWSService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        
        self.sqs_client = boto3.client(
            'sqs',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
    
    async def upload_file_to_s3(
        self, 
        file_data: bytes, 
        file_name: str, 
        user_id: str,
        catalog_id: str
    ) -> str:
        """Upload catalog file to S3 under user's catalog folder."""
        try:
            # Create S3 key: users/{user_id}/catalogs/{catalog_id}/{file_name}
            s3_key = f"users/{user_id}/catalogs/{catalog_id}/{file_name}"
            
            self.s3_client.put_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType='application/octet-stream'
            )
            
            logger.info(f"File uploaded to S3: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise Exception(f"Failed to upload file to S3: {e}")
    
    async def send_enrichment_message(
        self, 
        catalog_id: str, 
        user_id: str,
        file_path: str,
        line_items: list
    ) -> bool:
        """Send enrichment message to SQS queue."""
        try:
            if not settings.sqs_queue_url:
                logger.warning("SQS queue URL not configured, skipping message")
                return False
            
            message_body = {
                "catalog_id": str(catalog_id),
                "user_id": str(user_id),
                "file_path": file_path,
                "line_items": line_items,
                "timestamp": str(datetime.utcnow())
            }
            
            response = self.sqs_client.send_message(
                QueueUrl=settings.sqs_queue_url,
                MessageBody=json.dumps(message_body)
            )
            
            logger.info(f"Enrichment message sent to SQS: {response['MessageId']}")
            return True
            
        except ClientError as e:
            logger.error(f"Error sending message to SQS: {e}")
            return False
    
    async def get_file_from_s3(self, file_path: str) -> Optional[bytes]:
        """Download file from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=settings.s3_bucket_name,
                Key=file_path
            )
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {e}")
            return None
    
    async def delete_file_from_s3(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=file_path
            )
            logger.info(f"File deleted from S3: {file_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False


# Global instance
aws_service = AWSService()

