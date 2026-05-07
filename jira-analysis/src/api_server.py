"""FastAPI server for Jira Analysis workflows."""

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.settings import settings, init_settings
from src.workflow_modules.deep_analysis import DeepAnalysisWorkflow
from src.workflow_modules.batch_analysis import BatchAnalysisWorkflow


# Request models
class AnalyzeRequest(BaseModel):
    """Request model for single issue analysis."""
    issue_key: str
    mode: str = "balanced"  # strict/balanced/exploratory
    retrieve_evidence: bool = True


class BatchAnalyzeRequest(BaseModel):
    """Request model for batch analysis."""
    issue_keys: list[str]
    mode: str = "balanced"
    retrieve_evidence: bool = True


# Global workflow instances
deep_analysis_workflow: DeepAnalysisWorkflow | None = None
batch_analysis_workflow: BatchAnalysisWorkflow | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize workflows on startup."""
    import os
    from pathlib import Path

    global deep_analysis_workflow, batch_analysis_workflow

    # Debug: print working directory and paths
    print(f"[API SERVER] Working directory: {os.getcwd()}")
    print(f"[API SERVER] __file__: {__file__}")
    print(f"[API SERVER] Resolved __file__: {Path(__file__).resolve()}")

    # Initialize settings
    init_settings()

    print(f"[API SERVER] index_base_path from settings: {settings.index_base_path}")
    print(f"[API SERVER] Resolved index_base_path: {Path(settings.index_base_path).resolve()}")
    print(f"[API SERVER] Index path exists: {Path(settings.index_base_path).exists()}")

    # Create workflow instances
    deep_analysis_workflow = DeepAnalysisWorkflow(timeout=300)
    batch_analysis_workflow = BatchAnalysisWorkflow(timeout=600)

    yield

    # Cleanup on shutdown
    deep_analysis_workflow = None
    batch_analysis_workflow = None


# Create FastAPI app
app = FastAPI(
    title="Jira Analysis API",
    description="API for deep analysis of Jira issues using LlamaIndex workflows",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "jira-analysis",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze",
            "batch_analyze": "/api/batch-analyze",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "jira-analysis",
        "workflows": {
            "deep_analysis": deep_analysis_workflow is not None,
            "batch_analysis": batch_analysis_workflow is not None,
        }
    }


@app.post("/api/analyze")
async def analyze_issue(request: AnalyzeRequest):
    """Analyze a single Jira issue with streaming response."""
    if deep_analysis_workflow is None:
        raise HTTPException(status_code=503, detail="Workflow not initialized")

    async def event_generator():
        """Generate SSE events from workflow."""
        try:
            # Run the workflow
            handler = deep_analysis_workflow.run(
                issue_key=request.issue_key,
                mode=request.mode,
                retrieve_evidence=request.retrieve_evidence,
            )

            # Stream events
            async for event in handler.stream_events():
                event_data = {
                    "type": event.__class__.__name__,
                    "data": event.dict() if hasattr(event, "dict") else str(event),
                }
                yield f"data: {json.dumps(event_data)}\n\n"

            # Get final result
            result = await handler
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"

        except Exception as e:
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/batch-analyze")
async def batch_analyze_issues(request: BatchAnalyzeRequest):
    """Analyze multiple Jira issues in batch with streaming response."""
    if batch_analysis_workflow is None:
        raise HTTPException(status_code=503, detail="Workflow not initialized")

    async def event_generator():
        """Generate SSE events from batch workflow."""
        try:
            # Run the batch workflow
            handler = batch_analysis_workflow.run(
                issue_keys=request.issue_keys,
                mode=request.mode,
                retrieve_evidence=request.retrieve_evidence,
            )

            # Stream events
            async for event in handler.stream_events():
                event_data = {
                    "type": event.__class__.__name__,
                    "data": event.dict() if hasattr(event, "dict") else str(event),
                }
                yield f"data: {json.dumps(event_data)}\n\n"

            # Get final result
            result = await handler
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"

        except Exception as e:
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api_server:app",
        host="0.0.0.0",
        port=4501,
        reload=True,
    )
