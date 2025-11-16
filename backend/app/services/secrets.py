"""
AWS Secrets Manager utilities for retrieving API keys.

Provides thread-safe caching with TTL to minimize Secrets Manager API calls.
"""
import boto3
import threading
import time
import logging
from typing import Optional, Tuple
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Global cache: {secret_name: (value, expiry_timestamp)}
_secret_cache: dict[str, Tuple[str, float]] = {}
_cache_lock = threading.Lock()
TTL_SECONDS = 3600  # 1 hour


def get_secret(secret_name: str) -> str:
    """
    Retrieve a secret from AWS Secrets Manager with caching.
    
    Secrets are cached globally with a TTL of 1 hour to minimize API calls.
    Thread-safe implementation using locks.
    
    Args:
        secret_name: Name or ARN of the secret in Secrets Manager
                     (e.g., "pipeline/openrouter-api-key")
    
    Returns:
        Secret value as string
    
    Raises:
        ValueError: If secret cannot be retrieved and no cached value exists
        Exception: If Secrets Manager operation fails
    
    Example:
        >>> api_key = get_secret("pipeline/openrouter-api-key")
    """
    global _secret_cache
    
    # Check cache first
    with _cache_lock:
        if secret_name in _secret_cache:
            value, expiry = _secret_cache[secret_name]
            if time.time() < expiry:
                logger.debug(f"Secret '{secret_name}' retrieved from cache")
                return value
            else:
                # Expired, remove from cache
                del _secret_cache[secret_name]
                logger.debug(f"Secret '{secret_name}' cache expired, refreshing")
    
    # Cache miss or expired, fetch from Secrets Manager
    try:
        logger.info(f"Fetching secret '{secret_name}' from AWS Secrets Manager")
        client = boto3.client('secretsmanager')
        
        response = client.get_secret_value(SecretId=secret_name)
        secret_value = response['SecretString']
        
        # Update cache
        expiry = time.time() + TTL_SECONDS
        with _cache_lock:
            _secret_cache[secret_name] = (secret_value, expiry)
        
        logger.info(f"Secret '{secret_name}' cached successfully")
        return secret_value
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        
        logger.error(f"Failed to retrieve secret '{secret_name}': {error_code} - {error_msg}")
        
        # Check if we have a stale cached value (use it as fallback)
        with _cache_lock:
            if secret_name in _secret_cache:
                value, _ = _secret_cache[secret_name]
                logger.warning(f"Using stale cached value for '{secret_name}' due to Secrets Manager error")
                return value
        
        raise ValueError(f"Failed to retrieve secret '{secret_name}': {error_msg}")
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving secret '{secret_name}': {e}")
        
        # Check if we have a stale cached value (use it as fallback)
        with _cache_lock:
            if secret_name in _secret_cache:
                value, _ = _secret_cache[secret_name]
                logger.warning(f"Using stale cached value for '{secret_name}' due to unexpected error")
                return value
        
        raise Exception(f"Unexpected error retrieving secret '{secret_name}': {e}")


def clear_cache(secret_name: Optional[str] = None) -> None:
    """
    Clear the secret cache.
    
    Args:
        secret_name: If provided, clear only this secret. Otherwise, clear all.
    """
    global _secret_cache
    
    with _cache_lock:
        if secret_name:
            if secret_name in _secret_cache:
                del _secret_cache[secret_name]
                logger.debug(f"Cleared cache for secret '{secret_name}'")
        else:
            _secret_cache.clear()
            logger.debug("Cleared all secret caches")

