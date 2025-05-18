import hashlib
import secrets
import time
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from utils.core.logger import logger

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
access_codes_table = dynamodb.Table('playlab-access-code')

class AccessCodeManager:
    def __init__(self):
        self.expiry_minutes = 15  # Access codes expire after 15 minutes
        self.max_attempts = 3     # Maximum number of verification attempts
        
    def generate_access_code(self, email: str) -> str:
        """Generate a secure access code and store it in DynamoDB"""
        # Generate a random 6-character code
        access_code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
        
        # Create a hash of the access code
        hashed_code = hashlib.sha256(access_code.encode()).hexdigest()
        
        # Store in DynamoDB with expiration
        try:
            access_codes_table.put_item(
                Item={
                    'email': email,
                    'hashed_code': hashed_code,
                    'attempts': 0,
                    'created_at': int(time.time()),
                    'expires_at': int((datetime.now() + timedelta(minutes=self.expiry_minutes)).timestamp())
                }
            )
            return access_code
        except ClientError as e:
            logger.error(f"Error storing access code: {e}")
            raise
            
    def verify_access_code(self, email: str, code: str) -> bool:
        """Verify an access code"""
        try:
            # Get the stored access code data
            response = access_codes_table.get_item(
                Key={'email': email}
            )
            
            if 'Item' not in response:
                return False
                
            item = response['Item']
            
            # Check if code has expired
            if int(time.time()) > item['expires_at']:
                self._cleanup_access_code(email)
                return False
                
            # Check if too many attempts
            if item['attempts'] >= self.max_attempts:
                self._cleanup_access_code(email)
                return False
                
            # Verify the code
            hashed_code = hashlib.sha256(code.encode()).hexdigest()
            if hashed_code == item['hashed_code']:
                self._cleanup_access_code(email)
                return True
                
            # Increment attempts
            access_codes_table.update_item(
                Key={'email': email},
                UpdateExpression='SET attempts = attempts + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            
            return False
            
        except ClientError as e:
            logger.error(f"Error verifying access code: {e}")
            return False
            
    def _cleanup_access_code(self, email: str):
        """Remove an access code after use or expiration"""
        try:
            access_codes_table.delete_item(
                Key={'email': email}
            )
        except ClientError as e:
            logger.error(f"Error cleaning up access code: {e}") 