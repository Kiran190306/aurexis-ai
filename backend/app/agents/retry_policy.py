"""
Retry policies and timeout handling for agent execution.
"""
from typing import Callable, Optional, Type, Dict, Any
from functools import wraps
from datetime import datetime, timedelta
import asyncio
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)


class RetryConfig:
    """Configuration for retry policies."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on_exceptions: Optional[tuple] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay_seconds = initial_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on_exceptions = retry_on_exceptions or (Exception,)


# Default retry configurations
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay_seconds=1.0,
    max_delay_seconds=30.0,
    exponential_base=2.0,
    jitter=True
)

CRITICAL_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay_seconds=0.5,
    max_delay_seconds=60.0,
    exponential_base=2.0,
    jitter=True
)

QUICK_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    initial_delay_seconds=0.5,
    max_delay_seconds=5.0,
    exponential_base=2.0,
    jitter=True
)


def with_retry(
    config: RetryConfig = DEFAULT_RETRY_CONFIG,
    on_retry: Optional[Callable] = None
) -> Callable:
    """Decorator to add retry logic to async functions."""
    
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(config.max_attempts),
            wait=wait_exponential(
                multiplier=config.initial_delay_seconds,
                max=config.max_delay_seconds,
                exp_base=config.exponential_base
            ),
            retry=retry_if_exception_type(config.retry_on_exceptions),
            before_sleep=before_sleep_log(logger, logger.level) if hasattr(logger, 'level') else None,  # type: ignore[arg-type]
            retry_error_callback=lambda retry_state: logger.warning(
                f"Retry {retry_state.attempt_number}/{config.max_attempts} failed for {func.__name__}"
            )
        )
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if on_retry:
                await on_retry(*args, **kwargs)
            return await func(*args, **kwargs)
        
        return wrapper  # type: ignore[no-any-return]
    return decorator


class TimeoutHandler:
    """Handler for managing timeouts in agent execution."""
    
    def __init__(self, default_timeout_seconds: int = 300):
        self.default_timeout_seconds = default_timeout_seconds
    
    async def execute_with_timeout(
        self,
        coro: Any,
        timeout_seconds: Optional[int] = None,
        on_timeout: Optional[Callable] = None
    ) -> Any:
        """Execute a coroutine with timeout handling."""
        timeout = timeout_seconds or self.default_timeout_seconds
        
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout_seconds} seconds")
            if on_timeout:
                await on_timeout()
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
    
    async def execute_with_deadline(
        self,
        coro: Any,
        deadline: datetime,
        on_timeout: Optional[Callable] = None
    ) -> Any:
        """Execute a coroutine with a specific deadline."""
        now = datetime.utcnow()
        if deadline <= now:
            raise ValueError("Deadline must be in the future")
        
        timeout_seconds = int((deadline - now).total_seconds())
        return await self.execute_with_timeout(coro, timeout_seconds, on_timeout)


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = "closed"  # closed, open, half-open
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute a function with circuit breaker protection."""
        async with self._lock:
            if self._state == "open":
                if self._should_attempt_reset():
                    self._state = "half-open"
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                if self._state == "half-open":
                    self._reset()
                else:
                    self._failure_count = 0
            return result
        except self.expected_exception as e:
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = datetime.utcnow()
                
                if self._failure_count >= self.failure_threshold:
                    self._state = "open"
                    logger.error(f"Circuit breaker opened after {self._failure_count} failures")
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self._last_failure_time is None:
            return True
        
        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout_seconds
    
    def _reset(self) -> None:
        """Reset the circuit breaker."""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = "closed"
        logger.info("Circuit breaker reset to closed state")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None
        }


class AgentExecutionPolicy:
    """Combined execution policy for agents with retry, timeout, and circuit breaker."""
    
    def __init__(
        self,
        retry_config: RetryConfig = DEFAULT_RETRY_CONFIG,
        timeout_seconds: int = 300,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.retry_config = retry_config
        self.timeout_handler = TimeoutHandler(timeout_seconds)
        self.circuit_breaker = circuit_breaker
    
    async def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute a function with all policies applied."""
        if self.circuit_breaker:
            return await self.circuit_breaker.call(
                self._execute_with_retry_timeout,
                func,
                *args,
                **kwargs
            )
        else:
            return await self._execute_with_retry_timeout(func, *args, **kwargs)
    
    @with_retry(DEFAULT_RETRY_CONFIG)
    async def _execute_with_retry_timeout(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute with retry and timeout."""
        return await self.timeout_handler.execute_with_timeout(func(*args, **kwargs))
