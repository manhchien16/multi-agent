"""
Planner Agent

This agent is responsible for converting technical specifications into optimized
execution plans with task graphs, dependency management, and resource allocation.

Capabilities:
- Parse technical specifications
- Generate DAG (Directed Acyclic Graph) of tasks
- Identify task dependencies and parallelization opportunities
- Optimize task ordering for minimal critical path
- Allocate appropriate agent types to each task
- Estimate complexity and resource requirements
- Detect circular dependencies
- Generate execution timeline
"""

import json
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.shared.base_agent import BaseAgent, AgentConfig, TaskContext, TaskResult


class TaskType(str, Enum):
    """Task types"""
    DATABASE_SCHEMA = "database_schema"
    API_IMPLEMENTATION = "api_implementation"
    FRONTEND_COMPONENT = "frontend_component"
    BACKEND_SERVICE = "backend_service"
    INTEGRATION = "integration"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"


class AgentType(str, Enum):
    """Agent types for task execution"""
    CODING_BACKEND = "coding_backend"
    CODING_FRONTEND = "coding_frontend"
    CODING_DEVOPS = "coding_devops"
    CODING_DATABASE = "coding_database"
    REVIEW = "review"
    TEST = "test"
    APPROVAL = "approval"


class Task(BaseModel):
    """Individual task in the execution plan"""
    task_id: str
    task_type: TaskType
    title: str
    description: str
    agent_type: AgentType
    dependencies: List[str] = Field(default_factory=list)
    estimated_duration_minutes: int = Field(..., ge=1, le=480)
    complexity: str = Field(..., pattern="^(low|medium|high|critical)$")
    required_context: List[str] = Field(default_factory=list)
    success_criteria: List[str]
    artifacts_produced: List[str]
    
    # Resource requirements
    model_preference: Optional[str] = None  # e.g., "gpt-4", "claude-opus"
    requires_human_approval: bool = False
    max_retries: int = 3
    timeout_minutes: int = 30


class ExecutionPlan(BaseModel):
    """Complete execution plan with task graph"""
    plan_id: str
    specification_id: str
    tasks: List[Task]
    total_estimated_duration_minutes: int
    critical_path: List[str]
    parallelization_opportunities: List[List[str]]
    resource_requirements: Dict[str, int]
    risk_factors: List[Dict[str, str]]


class PlannerAgent(BaseAgent):
    """
    Planner Agent for generating optimized execution plans.
    """
    
    def __init__(self, config: AgentConfig, **kwargs):
        super().__init__(config, **kwargs)
        self.llm = None
        self.system_prompt = self._load_system_prompt()
        self.planning_prompt = self._load_planning_prompt()
        
    def _load_system_prompt(self) -> str:
        """Load system prompt"""
        return """You are an expert Software Project Manager and Technical Lead.

Your role is to analyze technical specifications and create optimized execution plans
that maximize parallelization while respecting dependencies.

You excel at:
- Breaking down complex features into granular, executable tasks
- Identifying task dependencies and data flow
- Optimizing task ordering to minimize critical path
- Allocating appropriate specialist agents to each task
- Estimating complexity and duration accurately
- Detecting potential bottlenecks and risks
- Balancing speed vs quality tradeoffs

Always produce plans that are:
- Executable: Each task has clear inputs, outputs, and success criteria
- Optimized: Maximum parallelization without violating dependencies
- Realistic: Accurate time and resource estimates
- Safe: Critical tasks require human approval
- Monitorable: Clear milestones and checkpoints

Output in well-structured JSON following the provided schema."""
    
    def _load_planning_prompt(self) -> ChatPromptTemplate:
        """Load planning prompt template"""
        template = """Given the following technical specification, create an optimized execution plan.

# Technical Specification
{specification}

# Constraints
Max Parallel Tasks: {max_parallel_tasks}
Available Agent Types: {available_agents}
Budget Constraints: {budget_constraints}
Timeline: {timeline_constraints}

# Instructions
1. Analyze all user stories and technical requirements
2. Break down into granular, executable tasks (15-120 min each)
3. Identify dependencies between tasks (data flow, order requirements)
4. Assign appropriate agent type to each task
5. Optimize task ordering to minimize critical path
6. Identify parallelization opportunities
7. Flag tasks requiring human approval (deployment, data deletion, etc.)
8. Estimate resource requirements
9. Identify risk factors

# Task Breakdown Strategy
- Database tasks first (schema creates foundation)
- API implementations depend on schemas
- Frontend components depend on APIs
- Integration tasks depend on all components
- Testing tasks depend on implementation
- Documentation can often run in parallel
- Deployment is the final stage

{format_instructions}

Generate the execution plan now:"""
        
        return ChatPromptTemplate.from_template(template)
    
    async def _execute_task_impl(self, context: TaskContext) -> TaskResult:
        """
        Execute plan generation task.
        
        Args:
            context: Task context with specification
            
        Returns:
            TaskResult with execution plan
        """
        spec = context.specification
        
        # Extract specification
        technical_spec = spec.get("specification", {})
        constraints = spec.get("constraints", {})
        
        # Request model routing
        model_config = await self._request_model_routing(context, spec)
        self.llm = self._initialize_llm(model_config)
        
        # Set up parser
        parser = PydanticOutputParser(pydantic_object=ExecutionPlan)
        
        # Format prompt
        prompt = self.planning_prompt.format(
            specification=json.dumps(technical_spec, indent=2),
            max_parallel_tasks=constraints.get("max_parallel_tasks", 10),
            available_agents=json.dumps([
                "coding_backend", "coding_frontend", "coding_devops",
                "coding_database", "review", "test", "approval"
            ]),
            budget_constraints=json.dumps(constraints.get("budget", {})),
            timeline_constraints=constraints.get("timeline", "No strict deadline"),
            format_instructions=parser.get_format_instructions()
        )
        
        # Generate plan
        self.logger.info("Generating execution plan")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm.agenerate([messages])
        plan_text = response.generations[0][0].text
        
        # Parse output
        try:
            execution_plan = parser.parse(plan_text)
        except Exception as e:
            self.logger.error(f"Failed to parse plan: {str(e)}")
            raise ValueError(f"Plan generation failed: {str(e)}")
        
        # Validate plan
        validation_result = self._validate_plan(execution_plan)
        if not validation_result["valid"]:
            self.logger.error(f"Plan validation failed: {validation_result['errors']}")
            raise ValueError(f"Invalid plan: {validation_result['errors']}")
        
        # Optimize plan
        optimized_plan = self._optimize_plan(execution_plan)
        
        # Generate visualizations
        task_graph_diagram = self._generate_task_graph(optimized_plan)
        timeline_diagram = self._generate_timeline(optimized_plan)
        
        # Store in memory
        if self.memory_client:
            await self.memory_client.store_execution_plan(
                workflow_id=context.workflow_id,
                plan=optimized_plan.dict()
            )
        
        # Calculate metrics
        metrics = {
            "total_tasks": len(optimized_plan.tasks),
            "critical_path_length": len(optimized_plan.critical_path),
            "max_parallel_tasks": max(len(p) for p in optimized_plan.parallelization_opportunities),
            "estimated_duration_hours": optimized_plan.total_estimated_duration_minutes / 60,
            "tasks_requiring_approval": sum(
                1 for t in optimized_plan.tasks if t.requires_human_approval
            ),
            "model_used": model_config.get("model_id"),
            "tokens_used": response.llm_output.get("token_usage", {}).get("total_tokens", 0)
        }
        
        return TaskResult(
            task_id=context.task_id,
            status="completed",
            output={
                "execution_plan": optimized_plan.dict(),
                "task_graph": task_graph_diagram,
                "timeline": timeline_diagram,
                "validation": validation_result
            },
            artifacts=[
                f"plan-{context.task_id}.json",
                f"task-graph-{context.task_id}.mmd",
                f"timeline-{context.task_id}.mmd"
            ],
            metrics=metrics
        )
    
    def _validate_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Validate execution plan for correctness"""
        errors = []
        warnings = []
        
        # Build dependency graph
        graph = nx.DiGraph()
        
        for task in plan.tasks:
            graph.add_node(task.task_id)
            for dep in task.dependencies:
                graph.add_edge(dep, task.task_id)
        
        # Check for circular dependencies
        try:
            cycles = list(nx.simple_cycles(graph))
            if cycles:
                errors.append(f"Circular dependencies detected: {cycles}")
        except:
            pass
        
        # Check for invalid dependencies
        task_ids = {t.task_id for t in plan.tasks}
        for task in plan.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task {task.task_id} has invalid dependency: {dep}")
        
        # Check for orphaned tasks
        if not nx.is_weakly_connected(graph):
            warnings.append("Plan contains disconnected task groups")
        
        # Validate critical path
        if not plan.critical_path:
            errors.append("Critical path is empty")
        
        # Check resource allocation
        agent_usage = {}
        for task in plan.tasks:
            agent_type = task.agent_type
            agent_usage[agent_type] = agent_usage.get(agent_type, 0) + 1
        
        # Verify reasonable distribution
        total_tasks = len(plan.tasks)
        if agent_usage.get("approval", 0) > total_tasks * 0.3:
            warnings.append("Too many tasks require approval (>30%)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "graph_metrics": {
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "is_dag": nx.is_directed_acyclic_graph(graph)
            }
        }
    
    def _optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Optimize task ordering and parallelization"""
        # Build dependency graph
        graph = nx.DiGraph()
        task_map = {t.task_id: t for t in plan.tasks}
        
        for task in plan.tasks:
            graph.add_node(
                task.task_id,
                duration=task.estimated_duration_minutes,
                task=task
            )
            for dep in task.dependencies:
                graph.add_edge(dep, task.task_id)
        
        # Find critical path using topological sort and longest path
        critical_path = self._find_critical_path(graph)
        
        # Find parallelization opportunities (tasks at same level in DAG)
        parallel_groups = self._find_parallel_groups(graph)
        
        # Calculate total duration considering parallelization
        total_duration = self._calculate_total_duration(graph, parallel_groups)
        
        # Calculate resource requirements
        resource_requirements = {}
        for task in plan.tasks:
            agent_type = task.agent_type.value
            resource_requirements[agent_type] = resource_requirements.get(agent_type, 0) + 1
        
        # Create optimized plan
        return ExecutionPlan(
            plan_id=plan.plan_id,
            specification_id=plan.specification_id,
            tasks=plan.tasks,
            total_estimated_duration_minutes=total_duration,
            critical_path=critical_path,
            parallelization_opportunities=parallel_groups,
            resource_requirements=resource_requirements,
            risk_factors=plan.risk_factors
        )
    
    def _find_critical_path(self, graph: nx.DiGraph) -> List[str]:
        """Find critical path (longest path) in task graph"""
        try:
            # Use DAG longest path algorithm
            path = nx.dag_longest_path(graph, weight='duration')
            return path
        except:
            # Fallback: topological sort
            return list(nx.topological_sort(graph))
    
    def _find_parallel_groups(self, graph: nx.DiGraph) -> List[List[str]]:
        """Find groups of tasks that can run in parallel"""
        # Generate all topological generations (levels in DAG)
        try:
            generations = list(nx.topological_generations(graph))
            return [list(gen) for gen in generations if len(gen) > 1]
        except:
            return []
    
    def _calculate_total_duration(
        self,
        graph: nx.DiGraph,
        parallel_groups: List[List[str]]
    ) -> int:
        """Calculate total duration considering parallelization"""
        # Simple heuristic: longest path duration
        try:
            longest_path = nx.dag_longest_path_length(graph, weight='duration')
            return int(longest_path)
        except:
            # Fallback: sum all durations
            total = sum(
                data.get('duration', 0)
                for _, data in graph.nodes(data=True)
            )
            return total
    
    def _generate_task_graph(self, plan: ExecutionPlan) -> str:
        """Generate Mermaid task graph diagram"""
        mermaid = "graph TD\n"
        
        for task in plan.tasks:
            label = f"{task.task_id}[{task.title}<br/>{task.estimated_duration_minutes}min]"
            mermaid += f"    {label}\n"
            
            for dep in task.dependencies:
                mermaid += f"    {dep} --> {task.task_id}\n"
        
        # Highlight critical path
        for i in range(len(plan.critical_path) - 1):
            current = plan.critical_path[i]
            next_task = plan.critical_path[i + 1]
            mermaid += f"    style {current} fill:#ff6b6b\n"
        
        return mermaid
    
    def _generate_timeline(self, plan: ExecutionPlan) -> str:
        """Generate Gantt chart timeline"""
        gantt = """gantt
    title Execution Timeline
    dateFormat YYYY-MM-DD HH:mm
    
"""
        start_time = datetime.utcnow()
        
        for task in plan.tasks:
            duration = task.estimated_duration_minutes
            gantt += f"    {task.title} : {task.task_id}, {start_time.isoformat()}, {duration}m\n"
        
        return gantt
    
    async def _request_model_routing(
        self,
        context: TaskContext,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request optimal model from model router"""
        # Medium complexity task - use GPT-4o
        return {
            "model_id": "gpt-4o",
            "provider": "openai",
            "cost_per_1m_tokens": 2.50
        }
    
    def _initialize_llm(self, model_config: Dict[str, Any]):
        """Initialize LLM client"""
        provider = model_config.get("provider")
        model_id = model_config.get("model_id")
        
        if provider == "anthropic":
            return ChatAnthropic(model=model_id, temperature=0.5, max_tokens=4096)
        elif provider == "openai":
            return ChatOpenAI(model=model_id, temperature=0.5, max_tokens=4096)
        else:
            raise ValueError(f"Unsupported provider: {provider}")


if __name__ == "__main__":
    import asyncio
    import os
    
    config = AgentConfig(
        agent_id=f"planner-agent-{os.getenv('HOSTNAME', 'local')}",
        agent_type="planner",
        version="2.1.0",
        max_concurrent_tasks=3,
        capabilities=[
            "task_decomposition",
            "dependency_analysis",
            "graph_optimization",
            "resource_planning"
        ]
    )
    
    agent = PlannerAgent(config)
    asyncio.run(agent.start())
