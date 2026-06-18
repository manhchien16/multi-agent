"""
Orchestrator Main Service

This is the main orchestration service that:
- Manages workflow lifecycle
- Coordinates agent execution
- Handles state management
- Integrates with Temporal.io
- Exposes REST API
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Request/Response Models
class CreateWorkflowRequest(BaseModel):
    """Request to create a new workflow"""
    tenant_id: str
    title: str
    description: str
    prd_content: Optional[str] = None
    prd_url: Optional[str] = None
    repository: Optional[str] = None
    tech_stack: dict = Field(default_factory=dict)
    constraints: dict = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    """Workflow response"""
    workflow_id: str
    tenant_id: str
    title: str
    status: str
    created_at: str
    updated_at: str
    current_stage: str
    progress_percent: int
    estimated_completion: Optional[str] = None


class TaskResponse(BaseModel):
    """Task response"""
    task_id: str
    workflow_id: str
    agent_type: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    output: Optional[dict] = None


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Multi-Agent Orchestrator")
    
    # Initialize services
    await initialize_services()
    
    logger.info("Orchestrator started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Orchestrator")
    await cleanup_services()


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Orchestrator",
    description="Orchestration service for AI software engineering agents",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory storage (replace with database in production)
workflows = {}
tasks = {}


async def initialize_services():
    """Initialize all services"""
    # Initialize Temporal client
    # Initialize database connection
    # Initialize event bus (NATS)
    # Initialize agent clients
    logger.info("Services initialized")


async def cleanup_services():
    """Cleanup services on shutdown"""
    logger.info("Services cleaned up")


# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "version": "2.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/v1/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: CreateWorkflowRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new workflow.
    
    This initiates the full agent pipeline:
    1. Specification Agent: PRD → Technical Spec
    2. Planner Agent: Spec → Task Graph
    3. Coding Agents: Execute tasks
    4. Review Agent: Code review
    5. Test Agent: Generate and run tests
    6. Approval Agent: Human approval for deployment
    """
    import uuid
    
    workflow_id = str(uuid.uuid4())
    
    # Create workflow record
    workflow = {
        "workflow_id": workflow_id,
        "tenant_id": request.tenant_id,
        "title": request.title,
        "description": request.description,
        "status": "created",
        "current_stage": "specification",
        "progress_percent": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "prd_content": request.prd_content,
        "prd_url": request.prd_url,
        "repository": request.repository,
        "tech_stack": request.tech_stack,
        "constraints": request.constraints
    }
    
    workflows[workflow_id] = workflow
    
    # Start workflow execution in background
    background_tasks.add_task(execute_workflow, workflow_id)
    
    logger.info(f"Created workflow {workflow_id}")
    
    return WorkflowResponse(
        workflow_id=workflow_id,
        tenant_id=workflow["tenant_id"],
        title=workflow["title"],
        status=workflow["status"],
        created_at=workflow["created_at"],
        updated_at=workflow["updated_at"],
        current_stage=workflow["current_stage"],
        progress_percent=workflow["progress_percent"]
    )


@app.get("/v1/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get workflow details"""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[workflow_id]
    
    return WorkflowResponse(
        workflow_id=workflow["workflow_id"],
        tenant_id=workflow["tenant_id"],
        title=workflow["title"],
        status=workflow["status"],
        created_at=workflow["created_at"],
        updated_at=workflow["updated_at"],
        current_stage=workflow["current_stage"],
        progress_percent=workflow["progress_percent"]
    )


@app.get("/v1/workflows")
async def list_workflows(
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List workflows with optional filtering"""
    filtered_workflows = list(workflows.values())
    
    if tenant_id:
        filtered_workflows = [
            w for w in filtered_workflows
            if w["tenant_id"] == tenant_id
        ]
    
    if status:
        filtered_workflows = [
            w for w in filtered_workflows
            if w["status"] == status
        ]
    
    # Pagination
    total = len(filtered_workflows)
    paginated = filtered_workflows[offset:offset + limit]
    
    return {
        "workflows": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.delete("/v1/workflows/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow"""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[workflow_id]
    workflow["status"] = "cancelled"
    workflow["updated_at"] = datetime.utcnow().isoformat()
    
    logger.info(f"Cancelled workflow {workflow_id}")
    
    return {"message": "Workflow cancelled", "workflow_id": workflow_id}


@app.get("/v1/workflows/{workflow_id}/tasks")
async def get_workflow_tasks(workflow_id: str):
    """Get all tasks for a workflow"""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow_tasks = [
        task for task in tasks.values()
        if task["workflow_id"] == workflow_id
    ]
    
    return {
        "workflow_id": workflow_id,
        "tasks": workflow_tasks,
        "total": len(workflow_tasks)
    }


@app.get("/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task details"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    return TaskResponse(
        task_id=task["task_id"],
        workflow_id=task["workflow_id"],
        agent_type=task["agent_type"],
        status=task["status"],
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
        output=task.get("output")
    )


@app.get("/v1/agents")
async def list_agents():
    """List available agents and their status"""
    # In production, query actual agent registry
    agents = [
        {
            "agent_id": "spec-agent-1",
            "agent_type": "specification",
            "status": "running",
            "version": "2.1.0",
            "current_tasks": 0,
            "max_concurrent_tasks": 5
        },
        {
            "agent_id": "planner-agent-1",
            "agent_type": "planner",
            "status": "running",
            "version": "2.1.0",
            "current_tasks": 0,
            "max_concurrent_tasks": 3
        },
        {
            "agent_id": "model-router-1",
            "agent_type": "model_router",
            "status": "running",
            "version": "2.1.0",
            "current_tasks": 0,
            "max_concurrent_tasks": 20
        },
        {
            "agent_id": "coding-backend-1",
            "agent_type": "coding_backend",
            "status": "running",
            "version": "2.1.0",
            "current_tasks": 0,
            "max_concurrent_tasks": 5
        },
        {
            "agent_id": "review-agent-1",
            "agent_type": "review",
            "status": "running",
            "version": "2.1.0",
            "current_tasks": 0,
            "max_concurrent_tasks": 10
        },
        {
            "agent_id": "test-agent-1",
            "agent_type": "test",
            "status": "running",
            "version": "2.1.0",
            "current_tasks": 0,
            "max_concurrent_tasks": 5
        }
    ]
    
    return {
        "agents": agents,
        "total": len(agents),
        "healthy": len([a for a in agents if a["status"] == "running"])
    }


# Workflow Execution Logic

async def execute_workflow(workflow_id: str):
    """
    Execute complete workflow through agent pipeline.
    
    Pipeline stages:
    1. Specification Generation
    2. Planning
    3. Code Generation
    4. Review
    5. Testing
    6. Approval
    7. Deployment
    """
    import uuid
    
    workflow = workflows[workflow_id]
    
    try:
        logger.info(f"Starting workflow execution: {workflow_id}")
        workflow["status"] = "running"
        
        # Stage 1: Specification Generation
        workflow["current_stage"] = "specification"
        workflow["progress_percent"] = 10
        logger.info(f"[{workflow_id}] Stage 1: Specification Generation")
        
        spec_task = await execute_agent_task(
            workflow_id=workflow_id,
            agent_type="specification",
            specification={
                "prd_content": workflow.get("prd_content"),
                "prd_url": workflow.get("prd_url"),
                "repository": workflow.get("repository"),
                "tech_stack": workflow.get("tech_stack"),
                "constraints": workflow.get("constraints")
            }
        )
        
        if spec_task["status"] != "completed":
            raise Exception("Specification generation failed")
        
        technical_spec = spec_task["output"]["specification"]
        
        # Stage 2: Planning
        workflow["current_stage"] = "planning"
        workflow["progress_percent"] = 30
        logger.info(f"[{workflow_id}] Stage 2: Planning")
        
        plan_task = await execute_agent_task(
            workflow_id=workflow_id,
            agent_type="planner",
            specification={
                "specification": technical_spec,
                "constraints": workflow.get("constraints")
            }
        )
        
        if plan_task["status"] != "completed":
            raise Exception("Planning failed")
        
        execution_plan = plan_task["output"]["execution_plan"]
        
        # Stage 3: Code Generation
        workflow["current_stage"] = "coding"
        workflow["progress_percent"] = 50
        logger.info(f"[{workflow_id}] Stage 3: Code Generation")
        
        # Execute coding tasks (simplified - in production, execute in parallel)
        coding_artifacts = []
        for task in execution_plan["tasks"][:3]:  # Execute first 3 tasks as demo
            code_task = await execute_agent_task(
                workflow_id=workflow_id,
                agent_type="coding_backend",
                specification={
                    "description": task.get("description", ""),
                    "api_specification": technical_spec.get("api_endpoints", []),
                    "database_schema": technical_spec.get("database_schemas", []),
                    "language": workflow.get("tech_stack", {}).get("language", "python"),
                    "framework": workflow.get("tech_stack", {}).get("framework", "fastapi")
                }
            )
            
            if code_task["status"] == "completed":
                coding_artifacts.extend(code_task["output"]["artifacts"])
        
        # Stage 4: Review
        workflow["current_stage"] = "review"
        workflow["progress_percent"] = 70
        logger.info(f"[{workflow_id}] Stage 4: Code Review")
        
        review_task = await execute_agent_task(
            workflow_id=workflow_id,
            agent_type="review",
            specification={
                "code_artifacts": coding_artifacts,
                "language": workflow.get("tech_stack", {}).get("language", "python")
            }
        )
        
        # Stage 5: Testing
        workflow["current_stage"] = "testing"
        workflow["progress_percent"] = 85
        logger.info(f"[{workflow_id}] Stage 5: Testing")
        
        test_task = await execute_agent_task(
            workflow_id=workflow_id,
            agent_type="test",
            specification={
                "code_artifacts": coding_artifacts,
                "language": workflow.get("tech_stack", {}).get("language", "python"),
                "execute_tests": False
            }
        )
        
        # Complete
        workflow["status"] = "completed"
        workflow["current_stage"] = "completed"
        workflow["progress_percent"] = 100
        workflow["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Workflow {workflow_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {str(e)}", exc_info=True)
        workflow["status"] = "failed"
        workflow["error"] = str(e)
        workflow["updated_at"] = datetime.utcnow().isoformat()


async def execute_agent_task(
    workflow_id: str,
    agent_type: str,
    specification: dict
) -> dict:
    """
    Execute a task with the appropriate agent.
    
    In production, this would:
    1. Route through model router for LLM selection
    2. Publish task to event bus
    3. Wait for agent to complete
    4. Return result
    
    For now, simulates execution.
    """
    import uuid
    
    task_id = str(uuid.uuid4())
    
    task = {
        "task_id": task_id,
        "workflow_id": workflow_id,
        "agent_type": agent_type,
        "status": "running",
        "created_at": datetime.utcnow().isoformat(),
        "specification": specification
    }
    
    tasks[task_id] = task
    
    logger.info(f"Executing task {task_id} with {agent_type} agent")
    
    # Simulate agent execution
    await asyncio.sleep(1)
    
    # Simulate successful completion
    task["status"] = "completed"
    task["completed_at"] = datetime.utcnow().isoformat()
    task["output"] = {
        "specification": {"mock": "data"},
        "artifacts": [{"file_path": "mock.py", "content": "# Mock code"}]
    }
    
    logger.info(f"Task {task_id} completed")
    
    return task


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
