"""
Task Status API Endpoints
Endpoints for querying Celery task status and results
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.security import get_current_user_id
from app.worker import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user_id: int = Depends(get_current_user_id)
) -> dict:
    """
    Get the status of a Celery task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status information
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "state": result.state,
            "result": result.result if result.ready() else None,
            "traceback": result.traceback if result.failed() else None,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "failed": result.failed() if result.ready() else None,
        }
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/{task_id}/result")
async def get_task_result(
    task_id: str,
    current_user_id: int = Depends(get_current_user_id)
) -> dict:
    """
    Get the result of a completed Celery task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task result
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        if not result.ready():
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Task not yet completed"
            )
        
        if result.failed():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task failed: {result.traceback}"
            )
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task result: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task result: {str(e)}"
        )


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user_id: int = Depends(get_current_user_id)
) -> dict:
    """
    Cancel a running Celery task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Cancellation result
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        if result.ready():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a completed task"
            )
        
        celery_app.control.revoke(task_id, terminate=True)
        
        logger.info(f"Task {task_id} cancelled by user {current_user_id}")
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.get("/stats")
async def get_worker_stats(
    current_user_id: int = Depends(get_current_user_id)
) -> dict:
    """
    Get Celery worker statistics
    
    Returns:
        Worker statistics
    """
    try:
        inspect = celery_app.control.inspect()
        
        stats = inspect.stats()
        active = inspect.active()
        registered = inspect.registered()
        
        return {
            "workers": stats if stats else {},
            "active_tasks": active if active else {},
            "registered_tasks": registered if registered else {},
            "worker_count": len(stats) if stats else 0,
        }
    except Exception as e:
        logger.error(f"Failed to get worker stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker stats: {str(e)}"
        )
