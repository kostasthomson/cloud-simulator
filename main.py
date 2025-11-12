"""
FastAPI application for smart task allocation.
Provides REST API endpoint for C++ simulator to request allocation decisions.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from models.schemas import AllocationRequest, AllocationDecision, HealthCheckResponse
from services.allocator import TaskAllocator
from config.settings import settings
from utils.logger import setup_logging
from utils.allocation_logger import AllocationLogger

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global allocator instance
allocator: TaskAllocator = None
allocation_logger: AllocationLogger = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global allocator, allocation_logger

    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Model type: {settings.model_type}")

    # Initialize allocator
    allocator = TaskAllocator()
    logger.info("Task allocator initialized")
    logger.info("Task allocator and allocation logger initialized")

    yield

    # Shutdown
    logger.info("Shutting down application")
    stats = allocator.get_statistics()
    logger.info(f"Final statistics: {stats}")

    allocation_logger.save_to_file()
    logger.info("Allocation decisions saved to file")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Smart task allocation service for cloud simulation using ML/DL techniques",
    lifespan=lifespan
)

# Configure CORS
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint - health check."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        model_type=settings.model_type
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        model_type=settings.model_type
    )


@app.post("/allocate_task", response_model=AllocationDecision)
async def allocate_task(request: AllocationRequest) -> AllocationDecision:
    """
    Main allocation endpoint.

    Receives current system state and task requirements from C++ simulator,
    returns allocation decision (cell and server selection).

    Args:
        request: AllocationRequest containing cells status and task requirements

    Returns:
        AllocationDecision with selected placement or rejection

    Raises:
        HTTPException: If request processing fails
    """
    try:
        logger.info(
            f"Received allocation request for task {request.task.task_id} "
            f"at timestamp {request.timestamp}"
        )

        # Validate request
        if not request.cells:
            raise HTTPException(
                status_code=400,
                detail="Request must contain at least one cell"
            )

        # Get allocation decision
        decision = allocator.allocate_task(request)

        allocation_logger.log_decision(request, decision)

        logger.info(
            f"Decision for task {request.task.task_id}: "
            f"{'SUCCESS' if decision.success else 'REJECTED'}"
        )

        return decision

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing allocation request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/statistics")
async def get_statistics():
    """
    Get allocation statistics.

    Returns current statistics about allocation decisions.
    """
    try:
        stats = allocator.get_statistics()
        log_summary = allocation_logger.get_summary()

        return {
            "status": "success",
            "statistics": stats,
            "logged_decisions": log_summary
        }
    except Exception as e:
        logger.error(f"Error retrieving statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset_statistics")
async def reset_statistics():
    """Reset allocation statistics."""
    try:
        global allocator
        allocator = TaskAllocator()
        logger.info("Statistics reset")
        return {"status": "success", "message": "Statistics reset"}
    except Exception as e:
        logger.error(f"Error resetting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save_logs")
async def save_logs():
    """Manually trigger saving of allocation logs to file."""
    try:
        allocation_logger.save_to_file()
        summary = allocation_logger.get_summary()
        return {
            "status": "success",
            "message": "Allocation logs saved successfully",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error saving logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset_statistics")
async def reset_statistics():
    """Reset allocation statistics."""
    try:
        global allocator, allocation_logger
        allocator = TaskAllocator()
        allocation_logger = AllocationLogger()  # ✅ ADD THIS LINE
        logger.info("Statistics and logs reset")
        return {"status": "success", "message": "Statistics and logs reset"}
    except Exception as e:
        logger.error(f"Error resetting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Enable auto-reload during development
        log_level=settings.log_level.lower()
    )
