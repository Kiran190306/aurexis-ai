"""
Metrics collection for agent operations.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge, Info
import time


class AgentMetrics:
    """Metrics collector for agent operations."""
    
    def __init__(self) -> None:
        # Prometheus metrics
        self.task_executions_total = Counter(
            'agent_task_executions_total',
            'Total number of task executions',
            ['agent_role', 'task_type', 'status']
        )
        
        self.task_execution_duration = Histogram(
            'agent_task_execution_duration_seconds',
            'Task execution duration in seconds',
            ['agent_role', 'task_type']
        )
        
        self.active_tasks = Gauge(
            'agent_active_tasks',
            'Number of currently active tasks',
            ['agent_role']
        )
        
        self.task_retries_total = Counter(
            'agent_task_retries_total',
            'Total number of task retries',
            ['agent_role', 'task_type']
        )
        
        self.message_sent_total = Counter(
            'agent_messages_sent_total',
            'Total number of messages sent',
            ['sender_role', 'receiver_role', 'message_type']
        )
        
        self.message_received_total = Counter(
            'agent_messages_received_total',
            'Total number of messages received',
            ['receiver_role', 'sender_role', 'message_type']
        )
        
        self.quality_score = Gauge(
            'agent_quality_score',
            'Quality score of agent responses',
            ['agent_role']
        )
        
        self.hallucination_count = Counter(
            'agent_hallucinations_total',
            'Total number of detected hallucinations',
            ['agent_role']
        )
        
        # In-memory metrics for aggregation
        self._task_history: Dict[str, list] = defaultdict(list)
        self._agent_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._start_times: Dict[str, float] = {}
    
    def task_started(self, task_id: str, agent_role: str, task_type: str) -> None:
        """Record task start."""
        self._start_times[task_id] = time.time()
        self.active_tasks.labels(agent_role=agent_role).inc()
    
    def task_completed(self, task_id: str, agent_role: str, task_type: str, status: str) -> None:
        """Record task completion."""
        if task_id in self._start_times:
            duration = time.time() - self._start_times[task_id]
            self.task_execution_duration.labels(
                agent_role=agent_role,
                task_type=task_type
            ).observe(duration)
            
            self._task_history[agent_role].append({
                "task_id": task_id,
                "task_type": task_type,
                "status": status,
                "duration": duration,
                "timestamp": datetime.utcnow()
            })
            
            del self._start_times[task_id]
        
        self.task_executions_total.labels(
            agent_role=agent_role,
            task_type=task_type,
            status=status
        ).inc()
        self.active_tasks.labels(agent_role=agent_role).dec()
    
    def task_retried(self, task_id: str, agent_role: str, task_type: str) -> None:
        """Record task retry."""
        self.task_retries_total.labels(
            agent_role=agent_role,
            task_type=task_type
        ).inc()
    
    def message_sent(self, sender_role: str, receiver_role: str, message_type: str) -> None:
        """Record message sent."""
        self.message_sent_total.labels(
            sender_role=sender_role,
            receiver_role=receiver_role,
            message_type=message_type
        ).inc()
    
    def message_received(self, receiver_role: str, sender_role: str, message_type: str) -> None:
        """Record message received."""
        self.message_received_total.labels(
            receiver_role=receiver_role,
            sender_role=sender_role,
            message_type=message_type
        ).inc()
    
    def quality_score_recorded(self, agent_role: str, score: float) -> None:
        """Record quality score."""
        self.quality_score.labels(agent_role=agent_role).set(score)
        self._agent_stats[agent_role]['last_quality_score'] = score
        self._agent_stats[agent_role]['last_quality_update'] = datetime.utcnow()
    
    def hallucination_detected(self, agent_role: str) -> None:
        """Record hallucination detection."""
        self.hallucination_count.labels(agent_role=agent_role).inc()
        self._agent_stats[agent_role]['hallucination_count'] = \
            self._agent_stats[agent_role].get('hallucination_count', 0) + 1
    
    def get_agent_stats(self, agent_role: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated stats for an agent."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        recent_tasks = [
            task for task in self._task_history[agent_role]
            if task['timestamp'] >= cutoff_time
        ]
        
        if not recent_tasks:
            return {
                "agent_role": agent_role,
                "task_count": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "active_tasks": 0
            }
        
        successful_tasks = [t for t in recent_tasks if t['status'] == 'completed']
        total_duration = sum(t['duration'] for t in recent_tasks)
        
        return {
            "agent_role": agent_role,
            "task_count": len(recent_tasks),
            "success_count": len(successful_tasks),
            "success_rate": len(successful_tasks) / len(recent_tasks),
            "avg_duration": total_duration / len(recent_tasks),
            "active_tasks": int(self.active_tasks.labels(agent_role=agent_role)._value.get()),
            "last_quality_score": self._agent_stats[agent_role].get('last_quality_score'),
            "hallucination_count": self._agent_stats[agent_role].get('hallucination_count', 0)
        }
    
    def get_all_stats(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get stats for all agents."""
        agent_roles = ['planner', 'orchestrator', 'research', 'coding', 'memory', 'tool', 'reflection']
        return {
            role: self.get_agent_stats(role, time_window_minutes)
            for role in agent_roles
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)."""
        self.task_executions_total.clear()
        self.task_execution_duration.clear()
        self.active_tasks.clear()
        self.task_retries_total.clear()
        self.message_sent_total.clear()
        self.message_received_total.clear()
        self.quality_score.clear()
        self.hallucination_count.clear()
        self._task_history.clear()
        self._agent_stats.clear()
        self._start_times.clear()


# Global metrics instance
agent_metrics = AgentMetrics()
