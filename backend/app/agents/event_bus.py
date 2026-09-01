"""
Event bus for agent communication using async pub/sub pattern.
"""
from typing import Dict, Callable, Optional, Any
from collections import defaultdict
import asyncio
from loguru import logger
from .base import AgentMessage


class EventBus:
    """Async event bus for agent communication."""
    
    def __init__(self) -> None:
        self._subscribers: Dict[str, Dict[str, Callable]] = defaultdict(dict)
        self._message_queue: Optional[asyncio.Queue] = None
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    async def subscribe(self, agent_id: str, message_type: str, handler: Callable) -> None:
        """Subscribe an agent to a specific message type."""
        self._subscribers[agent_id][message_type] = handler
        logger.info(f"Agent {agent_id} subscribed to {message_type}")
    
    async def unsubscribe(self, agent_id: str, message_type: Optional[str] = None) -> None:
        """Unsubscribe an agent from a message type or all types."""
        if message_type:
            self._subscribers[agent_id].pop(message_type, None)
            logger.info(f"Agent {agent_id} unsubscribed from {message_type}")
        else:
            self._subscribers.pop(agent_id, None)
            logger.info(f"Agent {agent_id} unsubscribed from all messages")
    
    async def publish(self, message: AgentMessage) -> None:
        """Publish a message to the event bus."""
        await self._message_queue.put(message)
        logger.debug(f"Message published: {message.message_type} from {message.sender} to {message.receiver}")
    
    async def start(self) -> None:
        """Start the event bus worker."""
        if self._running:
            return
        
        # Create queue in the current event loop
        self._message_queue = asyncio.Queue()
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus worker."""
        if not self._running:
            return
        
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Clear the queue
        if self._message_queue:
            while not self._message_queue.empty():
                try:
                    self._message_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            self._message_queue = None
        
        logger.info("Event bus stopped")
    
    async def _worker(self) -> None:
        """Worker that processes messages from the queue."""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                await self._deliver_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    
    async def _deliver_message(self, message: AgentMessage) -> None:
        """Deliver a message to the subscribed agent."""
        receiver = message.receiver
        
        if receiver not in self._subscribers:
            logger.warning(f"No subscriber found for agent: {receiver}")
            return
        
        handler = self._subscribers[receiver].get(message.message_type)
        if not handler:
            logger.warning(f"No handler for message type {message.message_type} on agent {receiver}")
            return
        
        try:
            await handler(message)
        except Exception as e:
            logger.error(f"Error handling message {message.message_type} on agent {receiver}: {e}", exc_info=True)
    
    async def publish_and_wait(self, message: AgentMessage, timeout: float = 30.0) -> AgentMessage:
        """Publish a message and wait for a response."""
        response_future: asyncio.Future = asyncio.Future()
        
        async def response_handler(response: AgentMessage) -> None:
            if response.correlation_id == message.id:
                response_future.set_result(response)
        
        # Subscribe to response
        await self.subscribe(message.sender, f"{message.message_type}_response", response_handler)
        
        try:
            # Publish original message
            await self.publish(message)
            
            # Wait for response
            return await asyncio.wait_for(response_future, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response to {message.id}")
            raise
        finally:
            await self.unsubscribe(message.sender, f"{message.message_type}_response")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "subscribers": len(self._subscribers),
            "queue_size": self._message_queue.qsize() if self._message_queue else 0,
            "running": self._running
        }


# Global event bus instance
event_bus = EventBus()
