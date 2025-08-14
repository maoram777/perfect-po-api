import boto3
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import math

logger = logging.getLogger(__name__)

class SQSEnrichmentService:
    """Service for sending product enrichment requests to SQS."""
    
    def __init__(self, queue_url: str, region: str = 'us-east-1', batch_size: int = 20):
        self.sqs = boto3.client('sqs', region_name=region)
        self.queue_url = queue_url
        self.batch_size = batch_size
        
    def send_enrichment_batches(
        self, 
        catalog_id: str, 
        user_id: str, 
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send products to SQS in batches for enrichment."""
        try:
            total_products = len(products)
            total_batches = math.ceil(total_products / self.batch_size)
            
            logger.info(f"Sending {total_products} products to SQS in {total_batches} batches")
            
            batch_results = []
            
            for batch_num in range(total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, total_products)
                batch_products = products[start_idx:end_idx]
                
                # Create SQS message
                message_body = {
                    "catalog_id": catalog_id,
                    "user_id": user_id,
                    "products": batch_products,
                    "batch_number": batch_num + 1,
                    "total_batches": total_batches,
                    "total_products": total_products,
                    "sent_at": datetime.utcnow().isoformat()
                }
                
                # Send message to SQS
                response = self.sqs.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(message_body),
                    MessageAttributes={
                        'catalog_id': {
                            'StringValue': catalog_id,
                            'DataType': 'String'
                        },
                        'user_id': {
                            'StringValue': user_id,
                            'DataType': 'String'
                        },
                        'batch_number': {
                            'StringValue': str(batch_num + 1),
                            'DataType': 'Number'
                        },
                        'total_batches': {
                            'StringValue': str(total_batches),
                            'DataType': 'Number'
                        }
                    }
                )
                
                batch_results.append({
                    "batch_number": batch_num + 1,
                    "products_count": len(batch_products),
                    "message_id": response['MessageId'],
                    "status": "sent"
                })
                
                logger.info(f"Sent batch {batch_num + 1}/{total_batches} with {len(batch_products)} products")
            
            return {
                "status": "success",
                "total_products": total_products,
                "total_batches": total_batches,
                "batch_size": self.batch_size,
                "batches": batch_results,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send enrichment batches: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sent_at": datetime.utcnow().isoformat()
            }
    
    def get_queue_attributes(self) -> Dict[str, Any]:
        """Get SQS queue attributes."""
        try:
            response = self.sqs.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=['All']
            )
            return response['Attributes']
        except Exception as e:
            logger.error(f"Failed to get queue attributes: {e}")
            return {}
    
    def purge_queue(self) -> bool:
        """Purge all messages from the queue."""
        try:
            self.sqs.purge_queue(QueueUrl=self.queue_url)
            logger.info("Queue purged successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to purge queue: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789012/product-enrichment-queue"
    
    # Initialize service
    sqs_service = SQSEnrichmentService(
        queue_url=QUEUE_URL,
        region='us-east-1',
        batch_size=20
    )
    
    # Example products data
    example_products = [
        {"_id": "product1", "name": "Wireless Headphones", "sku": "WH001"},
        {"_id": "product2", "name": "Smartphone Case", "sku": "SC001"},
        # ... more products
    ]
    
    # Send enrichment batches
    result = sqs_service.send_enrichment_batches(
        catalog_id="catalog123",
        user_id="user456",
        products=example_products
    )
    
    print(f"Enrichment batches sent: {result}")
