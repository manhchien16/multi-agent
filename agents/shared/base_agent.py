"""
Base Agent Implementation

This module provides the foundational BaseAgent class that all agents inherit from.
It handles common functionality like event publishing, observability, policy enforcement,
and lifecycle management.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json
import logging

from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe


@dataclass
class AgentConfig:
    """Agent configuration"""
    agent_id: str
    agent_type: str
    version: str
    max_concurrent_tasks: int = 1
    capabilities: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    """Context for task execution"""
    task_id: str
    workflow_id: str
    tenant_id: str
    specification: Dict[str, Any]
    execution_context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    status: str  # completed, failed
    output: Optional[Dict[str, Any]] = None
    artifacts: List[str] = field(default_factory=list)
    error: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all agents in the platform.
    
    Provides common functionality:
    - Event publishing
    - Observability (Langfuse tracing)
    - Policy enforcement
    - Lifecycle management
    - Error handling and retries
    """
    
    def __init__(
        self,
        config: AgentConfig,
        event_client=None,
        policy_client=None,
        memory_client=None,
        langfuse_client: Optional[Langfuse] = None
    ):
        self.config = config
        self.event_client = event_client
        self.policy_client = policy_client
        self.memory_client = memory_client
        self.langfuse = langfuse_client or Langfuse()
        
        self.logger = logging.getLogger(f"agent.{config.agent_type}")
        self.is_running = False
        self.current_tasks: Dict[str, asyncio.Task] = {}
        
        self.logger.info(
            f"Initialized {config.agent_type} agent",
            extra={
                "agent_id": config.agent_id,
                "version": config.version,
                "capabilities": config.capabilities
            }
        )
    
    async def start(self):
        """Start the agent"""
        self.logger.info(f"Starting agent {self.config.agent_id}")
        self.is_running = True
        
        # Emit agent started event
        await self.emit_event("agent.started", {
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type,
            "version": self.config.agent_version,
            "capabilities": self.config.capabilities
        })
        
        # Start heartbeat task
        asyncio.create_task(self._heartbeat_loop())
        
        self.logger.info(f"Agent {self.config.agent_id} started successfully")
    
    async def stop(self):
        """Stop the agent gracefully"""
        self.logger.info(f"Stopping agent {self.config.agent_id}")
        self.is_running = False
        
        # Wait for current tasks to complete
        if self.current_tasks:
            self.logger.info(f"Waiting for {len(self.current_tasks)} tasks to complete")
            await asyncio.gather(*self.current_tasks.values(), return_exceptions=True)
        
        # Emit agent stopped event
        await self.emit_event("agent.stopped", {
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type
        })
        
        self.logger.info(f"Agent {self.config.agent_id} stopped")
    
    @observe(as_type="generation")
    async def execute_task(self, context: TaskContext) -> TaskResult:
        """
        Execute a task with full observability and error handling.
        
        This method wraps the agent-specific implementation with:
        - Policy enforcement
        - Observability tracing
        - Error handling
        - Event emission
        - Metrics collection
        """
        task_id = context.task_id
        workflow_id = context.workflow_id
        
        # Update langfuse context
        langfuse_context.update_current_trace(
            name=f"{self.config.agent_type}_task_execution",
            metadata={
                "task_id": task_id,
                "workflow_id": workflow_id,
                "agent_id": self.config.agent_id,
                "retry_count": context.retry_count
            }
        )
        
        self.logger.info(
            f"Starting task execution",
            extra={
                "task_id": task_id,
                "workflow_id": workflow_id,
                "agent_id": self.config.agent_id
            }
        )
        
        # Emit task started event
        await self.emit_event("task.started", {
            "task_id": task_id,
            "workflow_id": workflow_id,
            "agent_id": self.config.agent_id,
            "started_at": datetime.utcnow().isoformat()
        })
        
        start_time = datetime.utcnow()
        
        try:
            # Policy check before execution
            if self.policy_client:
                policy_decision = await self.policy_client.check_policy(
                    action="task_execution",
                    context={
                        "agent_id": self.config.agent_id,
                        "agent_type": self.config.agent_type,
                        "task_id": task_id,
                        "workflow_id": workflow_id,
                        "tenant_id": context.tenant_id
                    }
                )
                
                if not policy_decision.get("allow", False):
                    raise PermissionError(
                        f"Policy denied task execution: {policy_decision.get('reason')}"
                    )
            
            # Execute agent-specific logic
            result = await self._execute_task_impl(context)
            
            # Calculate metrics
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result.metrics.update({
                "duration_ms": duration_ms,
                "agent_id": self.config.agent_id,
                "agent_type": self.config.agent_type,
                "retry_count": context.retry_count
            })
            
            # Emit task completed event
            await self.emit_event("task.completed", {
                "task_id": task_id,
                "workflow_id": workflow_id,
                "status": "completed",
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "output": result.output,
                "artifacts": result.artifacts,
                "metrics": result.metrics
            })
            
            self.logger.info(
                f"Task completed successfully",
                extra={
                    "task_id": task_id,
                    "duration_ms": duration_ms
                }
            )
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            error_info = {
                "code": type(e).__name__,
                "message": str(e),
                "recoverable": self._is_recoverable_error(e)
            }
            
            self.logger.error(
                f"Task failed: {str(e)}",
                extra={
                    "task_id": task_id,
                    "error": error_info,
                    "duration_ms": duration_ms
                },
                exc_info=True
            )
            
            # Emit task failed event
            await self.emit_event("task.failed", {
                "task_id": task_id,
                "workflow_id": workflow_id,
                "status": "failed",
                "error": error_info,
                "started_at": start_time.isoformat(),
                "failed_at": end_time.isoformat(),
                "retry_count": context.retry_count,
                "max_retries": context.max_retries,
                "will_retry": (
                    error_info["recoverable"] and
                    context.retry_count < context.max_retries
                )
            })
            
            # Record error in Langfuse
            langfuse_context.update_current_observation(
                level="ERROR",
                status_message=str(e)
            )
            
            return TaskResult(
                task_id=task_id,
                status="failed",
                error=error_info,
                metrics={
                    "duration_ms": duration_ms,
                    "agent_id": self.config.agent_id,
                    "retry_count": context.retry_count
                }
            )
    
    @abstractmethod
    async def _execute_task_impl(self, context: TaskContext) -> TaskResult:
        """
        Agent-specific task execution logic.
        
        This method must be implemented by each agent subclass.
        
        Args:
            context: Task context with specification and execution environment
            
        Returns:
            TaskResult with output, artifacts, and metrics
            
        Raises:
            Any exception indicating task failure
        """
        pass
    
    async def emit_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Emit an event to the event bus.
        
        Args:
            event_type: Type of event (e.g., "task.completed")
            payload: Event payload
        """
        if not self.event_client:
            return
        
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "source": {
                "agent_id": self.config.agent_id,
                "agent_type": self.config.agent_type,
                "instance_id": self.config.configuration.get("instance_id")
            },
            "workflow_id": payload.get("workflow_id"),
            "payload": payload
        }
        
        try:
            await self.event_client.publish(
                subject=f"agents.{self.config.agent_type}.{event_type.split('.')[1]}",
                event=event
            )
        except Exception as e:
            self.logger.error(
                f"Failed to emit event: {str(e)}",
                extra={"event_type": event_type},
                exc_info=True
            )
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat signals"""
        while self.is_running:
            try:
                await self.emit_event("agent.heartbeat", {
                    "agent_id": self.config.agent_id,
                    "status": "running",
                    "current_task_count": len(self.current_tasks),
                    "max_concurrent_tasks": self.config.max_concurrent_tasks
                })
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {str(e)}")
            
            await asyncio.sleep(30)  # Heartbeat every 30 seconds
    
    def _is_recoverable_error(self, error: Exception) -> bool:
        """
        Determine if an error is recoverable (should retry).
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if the error is recoverable, False otherwise
        """
        # Transient errors that should be retried
        recoverable_errors = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
        
        # Errors that should not be retried
        non_recoverable_errors = (
            ValueError,
            TypeError,
            KeyError,
            PermissionError,
        )
        
        if isinstance(error, non_recoverable_errors):
            return False
        
        if isinstance(error, recoverable_errors):
            return True
        
        # Default to recoverable for unknown errors
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.
        
        Returns:
            Dictionary with agent status information
        """
        return {
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type,
            "version": self.config.version,
            "status": "running" if self.is_running else "stopped",
            "current_task_count": len(self.current_tasks),
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "capabilities": self.config.capabilities
        }
