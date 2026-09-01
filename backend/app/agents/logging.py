"""
Structured logging for agent operations.
"""
from loguru import logger
from typing import Dict, Any, Optional
from datetime import datetime
import json


class AgentLogger:
    """Structured logger for agent operations."""
    
    def __init__(self, agent_id: str, agent_role: str):
        self.agent_id = agent_id
        self.agent_role = agent_role
    
    def log_task_start(self, task_id: str, task_type: str, input_data: Dict[str, Any]) -> None:
        """Log task start."""
        logger.bind(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            task_id=task_id,
            task_type=task_type,
            event="task_start"
        ).info(
            f"Task started: {task_type}",
            extra={
                "input_data": self._sanitize_data(input_data),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_task_complete(self, task_id: str, task_type: str, output_data: Dict[str, Any], execution_time: float) -> None:
        """Log task completion."""
        logger.bind(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            task_id=task_id,
            task_type=task_type,
            event="task_complete",
            execution_time=execution_time
        ).info(
            f"Task completed: {task_type}",
            extra={
                "output_data": self._sanitize_data(output_data),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_task_error(self, task_id: str, task_type: str, error: str, error_code: Optional[str] = None) -> None:
        """Log task error."""
        logger.bind(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            task_id=task_id,
            task_type=task_type,
            event="task_error",
            error_code=error_code
        ).error(
            f"Task failed: {task_type}",
            extra={
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_task_retry(self, task_id: str, task_type: str, retry_count: int, max_retries: int) -> None:
        """Log task retry."""
        logger.bind(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            task_id=task_id,
            task_type=task_type,
            event="task_retry",
            retry_count=retry_count,
            max_retries=max_retries
        ).warning(
            f"Task retry {retry_count}/{max_retries}: {task_type}",
            extra={"timestamp": datetime.utcnow().isoformat()}
        )
    
    def log_message_sent(self, message_id: str, receiver: str, message_type: str) -> None:
        """Log message sent."""
        logger.bind(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            message_id=message_id,
            receiver=receiver,
            message_type=message_type,
            event="message_sent"
        ).info(
            f"Message sent: {message_type} to {receiver}",
            extra={"timestamp": datetime.utcnow().isoformat()}
        )
    
    def log_message_received(self, message_id: str, sender: str, message_type: str) -> None:
        """Log message received."""
        logger.bind(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            message_id=message_id,
            sender=sender,
            message_type=message_type,
            event="message_received"
        ).info(
            f"Message received: {message_type} from {sender}",
            extra={"timestamp": datetime.utcnow().isoformat()}
        )
    
    def log_agent_state(self, state: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log agent state change."""
        logger.bind(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            event="agent_state_change",
            state=state
        ).info(
            f"Agent state changed: {state}",
            extra={
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_metric(self, metric_name: str, metric_value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Log custom metric."""
        logger.bind(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            event="metric",
            metric_name=metric_name,
            metric_value=metric_value,
            labels=labels or {}
        ).info(
            f"Metric: {metric_name}={metric_value}",
            extra={"timestamp": datetime.utcnow().isoformat()}
        )
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from logs."""
        sensitive_keys = ["password", "token", "api_key", "secret", "credential"]
        sanitized = data.copy()
        
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "***REDACTED***"
        
        return sanitized


class ExecutionLogger:
    """Logger for execution plan tracking."""
    
    def __init__(self, execution_plan_id: str):
        self.execution_plan_id = execution_plan_id
    
    def log_plan_created(self, user_request: str, task_count: int) -> None:
        """Log execution plan creation."""
        logger.bind(
            execution_plan_id=self.execution_plan_id,
            event="plan_created",
            task_count=task_count
        ).info(
            f"Execution plan created with {task_count} tasks",
            extra={
                "user_request": user_request,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_plan_started(self) -> None:
        """Log execution plan start."""
        logger.bind(
            execution_plan_id=self.execution_plan_id,
            event="plan_started"
        ).info(
            "Execution plan started",
            extra={"timestamp": datetime.utcnow().isoformat()}
        )
    
    def log_plan_completed(self, total_time: float, success_count: int, failure_count: int) -> None:
        """Log execution plan completion."""
        logger.bind(
            execution_plan_id=self.execution_plan_id,
            event="plan_completed",
            total_time=total_time,
            success_count=success_count,
            failure_count=failure_count
        ).info(
            f"Execution plan completed in {total_time}s: {success_count} success, {failure_count} failed",
            extra={"timestamp": datetime.utcnow().isoformat()}
        )
    
    def log_plan_failed(self, error: str) -> None:
        """Log execution plan failure."""
        logger.bind(
            execution_plan_id=self.execution_plan_id,
            event="plan_failed"
        ).error(
            f"Execution plan failed: {error}",
            extra={
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_plan_cancelled(self) -> None:
        """Log execution plan cancellation."""
        logger.bind(
            execution_plan_id=self.execution_plan_id,
            event="plan_cancelled"
        ).warning(
            "Execution plan cancelled",
            extra={"timestamp": datetime.utcnow().isoformat()}
        )


def get_agent_logger(agent_id: str, agent_role: str) -> AgentLogger:
    """Get an agent logger instance."""
    return AgentLogger(agent_id, agent_role)


def get_execution_logger(execution_plan_id: str) -> ExecutionLogger:
    """Get an execution logger instance."""
    return ExecutionLogger(execution_plan_id)
