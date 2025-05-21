"""Cache utility for the MCP service."""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Simple in-memory cache
_CACHE: Dict[str, Dict[str, Any]] = {}


def timed_lru_cache(
    maxsize: int = 128, 
    typed: bool = False, 
    ttl: int = 300
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """LRU cache with time-to-live (TTL) functionality.
    
    Args:
        maxsize: Maximum size of the cache
        typed: Whether different argument types should be cached separately
        ttl: Time-to-live in seconds (default: 5 minutes)
    
    Returns:
        Decorated function with caching
    """
    
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        """Decorate the function with TTL cache."""
        # Create a cache for the function
        cache_key = f"{func.__module__}.{func.__qualname__}"
        if cache_key not in _CACHE:
            _CACHE[cache_key] = {}
        
        # We'll use functools.lru_cache for the actual caching
        lru_cache = functools.lru_cache(maxsize=maxsize, typed=typed)
        cached_func = lru_cache(func)
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            """Wrapper function that adds TTL to the cached items."""
            # Generate a key for the current arguments
            arg_key = str(args) + str(kwargs)
            
            # Check if the item exists in our TTL tracking
            now = time.time()
            item_cache = _CACHE[cache_key]
            
            if arg_key in item_cache:
                timestamp, _ = item_cache[arg_key]
                if now - timestamp > ttl:
                    # TTL expired, remove from cache and LRU cache
                    del item_cache[arg_key]
                    cached_func.cache_clear()
                    logger.debug(f"Cache expired for {cache_key}({arg_key})")
            
            # Call the LRU-cached function
            result = cached_func(*args, **kwargs)
            
            # Update our TTL tracking
            if arg_key not in item_cache:
                item_cache[arg_key] = (now, result)
            
            return result
        
        # Add cache utility methods to the wrapper function
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = cached_func.cache_clear
        
        # Define a custom method to clear specific keys
        def clear_key(*args: Any, **kwargs: Any) -> None:
            """Clear a specific key from the cache."""
            arg_key = str(args) + str(kwargs)
            if arg_key in _CACHE[cache_key]:
                del _CACHE[cache_key][arg_key]
                # We need to clear the entire LRU cache because we can't
                # selectively clear keys from it
                cached_func.cache_clear()
        
        wrapper.clear_key = clear_key
        
        return wrapper
    
    return decorator
