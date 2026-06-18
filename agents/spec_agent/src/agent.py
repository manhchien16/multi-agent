"""
Specification Agent

This agent is responsible for converting product requirements into actionable
technical specifications that can be used by other agents in the workflow.

Capabilities:
- Parse PRDs, design documents, API specs
- Generate user stories with acceptance criteria
- Design database schemas
- Define API contracts
- Create architecture proposals
- Identify technical risks and dependencies
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.shared.base_agent import BaseAgent, AgentConfig, TaskContext, TaskResult


# Output models for structured generation
class UserStory(BaseModel):
    """User story model"""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str = Field(..., pattern="^(critical|high|medium|low)$")
    estimated_points: int = Field(..., ge=1, le=21)
    dependencies: List[str] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    """Database schema model"""
    table_name: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)


class APIEndpoint(BaseModel):
    """API endpoint specification"""
    path: str
    method: str = Field(..., pattern="^(GET|POST|PUT|PATCH|DELETE)$")
    description: str
    request_body: Optional[Dict[str, Any]] = None
    response: Dict[str, Any]
    authentication_required: bool = True
    rate_limit: Optional[str] = None


class TechnicalSpecification(BaseModel):
    """Complete technical specification"""
    title: str
    overview: str
    user_stories: List[UserStory]
    database_schemas: List[DatabaseSchema]
    api_endpoints: List[APIEndpoint]
    architecture_decisions: List[Dict[str, str]]
    technical_risks: List[Dict[str, str]]
    dependencies: List[str]
    non_functional_requirements: Dict[str, Any]


class SpecAgent(BaseAgent):
    """
    Specification Agent for converting requirements into technical specs.
    """
    
    def __init__(self, config: AgentConfig, **kwargs):
        super().__init__(config, **kwargs)
        
        # Initialize LLM client (will be selected by model router)
        self.llm = None
        
        # Load prompt templates
        self.system_prompt = self._load_system_prompt()
        self.spec_generation_prompt = self._load_spec_generation_prompt()
        
    def _load_system_prompt(self) -> str:
        """Load system prompt for the agent"""
        return """You are an expert Technical Architect and Product Engineer.

Your role is to analyze product requirements and create comprehensive technical specifications 
that can be used by engineering teams to build high-quality software.

You excel at:
- Breaking down complex requirements into clear, actionable user stories
- Designing scalable database schemas
- Defining clean, RESTful API contracts
- Identifying technical risks and dependencies
- Making sound architectural decisions
- Considering non-functional requirements (performance, security, scalability)

Always produce specifications that are:
- Comprehensive and detailed
- Technically accurate
- Implementable by software engineers
- Aligned with industry best practices
- Considerate of edge cases and error scenarios

Output your specifications in well-structured JSON format following the provided schema."""
    
    def _load_spec_generation_prompt(self) -> ChatPromptTemplate:
        """Load prompt template for specification generation"""
        template = """Given the following product requirements, generate a comprehensive technical specification.

# Product Requirements
{prd_content}

# Additional Context
Repository: {repository}
Existing Architecture: {existing_architecture}
Technology Stack: {tech_stack}
Constraints: {constraints}

# Instructions
1. Analyze the requirements thoroughly
2. Break down into user stories with clear acceptance criteria
3. Design database schema if data storage is needed
4. Define API endpoints with request/response formats
5. Document architectural decisions with rationale
6. Identify technical risks and mitigation strategies
7. List all dependencies and prerequisites
8. Specify non-functional requirements

{format_instructions}

Generate the technical specification now:"""
        
        return ChatPromptTemplate.from_template(template)
    
    async def _execute_task_impl(self, context: TaskContext) -> TaskResult:
        """
        Execute specification generation task.
        
        Args:
            context: Task context containing PRD and requirements
            
        Returns:
            TaskResult with generated specification
        """
        spec = context.specification
        
        # Extract inputs
        prd_content = spec.get("prd_content", "")
        prd_url = spec.get("prd_url")
        repository = spec.get("repository", "")
        
        # Fetch PRD if URL provided
        if prd_url and not prd_content:
            prd_content = await self._fetch_prd(prd_url)
        
        # Get existing architecture context
        existing_architecture = await self._analyze_existing_architecture(repository)
        
        # Extract tech stack and constraints
        tech_stack = spec.get("tech_stack", {})
        constraints = spec.get("constraints", {})
        
        # Request model from router
        model_config = await self._request_model_routing(context, spec)
        
        # Initialize LLM with selected model
        self.llm = self._initialize_llm(model_config)
        
        # Set up output parser
        parser = PydanticOutputParser(pydantic_object=TechnicalSpecification)
        
        # Format prompt
        prompt = self.spec_generation_prompt.format(
            prd_content=prd_content,
            repository=repository,
            existing_architecture=json.dumps(existing_architecture, indent=2),
            tech_stack=json.dumps(tech_stack, indent=2),
            constraints=json.dumps(constraints, indent=2),
            format_instructions=parser.get_format_instructions()
        )
        
        # Generate specification
        self.logger.info("Generating technical specification")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm.agenerate([messages])
        spec_text = response.generations[0][0].text
        
        # Parse output
        try:
            specification = parser.parse(spec_text)
        except Exception as e:
            self.logger.error(f"Failed to parse specification: {str(e)}")
            # Fallback: return raw text
            specification = {"raw": spec_text}
        
        # Generate additional artifacts
        markdown_doc = await self._generate_markdown_documentation(specification)
        architecture_diagram = await self._generate_architecture_diagram(specification)
        
        # Store in memory system
        if self.memory_client:
            await self._store_specification(context, specification)
        
        # Calculate metrics
        metrics = {
            "requirements_count": len(specification.user_stories),
            "api_endpoints_count": len(specification.api_endpoints),
            "database_tables_count": len(specification.database_schemas),
            "risks_identified": len(specification.technical_risks),
            "model_used": model_config.get("model_id"),
            "tokens_used": response.llm_output.get("token_usage", {}).get("total_tokens", 0),
            "cost_usd": self._calculate_cost(
                model_config,
                response.llm_output.get("token_usage", {})
            )
        }
        
        return TaskResult(
            task_id=context.task_id,
            status="completed",
            output={
                "specification": specification.dict(),
                "markdown_documentation": markdown_doc,
                "architecture_diagram_url": architecture_diagram
            },
            artifacts=[
                f"spec-{context.task_id}.json",
                f"spec-{context.task_id}.md",
                f"architecture-{context.task_id}.mmd"
            ],
            metrics=metrics
        )
    
    async def _fetch_prd(self, prd_url: str) -> str:
        """Fetch PRD content from URL"""
        # Implementation would fetch and parse PRD
        # Could support: Markdown files, Google Docs, Notion, Figma, etc.
        self.logger.info(f"Fetching PRD from {prd_url}")
        # Placeholder
        return "PRD content would be fetched here"
    
    async def _analyze_existing_architecture(self, repository: str) -> Dict[str, Any]:
        """Analyze existing codebase architecture"""
        if not repository:
            return {}
        
        # Query memory system for codebase embeddings
        if self.memory_client:
            architecture = await self.memory_client.query_codebase_context(
                repository=repository,
                query="What is the current architecture and tech stack?"
            )
            return architecture
        
        return {}
    
    async def _request_model_routing(
        self,
        context: TaskContext,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request optimal model from model router"""
        # This would call the model router agent
        # For now, return a default configuration
        return {
            "model_id": "claude-opus-4",
            "provider": "anthropic",
            "context_window": 200000,
            "cost_per_1m_tokens": 15.00
        }
    
    def _initialize_llm(self, model_config: Dict[str, Any]):
        """Initialize LLM client with model configuration"""
        provider = model_config.get("provider")
        model_id = model_config.get("model_id")
        
        if provider == "anthropic":
            return ChatAnthropic(
                model=model_id,
                temperature=0.7,
                max_tokens=4096
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=model_id,
                temperature=0.7,
                max_tokens=4096
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _generate_markdown_documentation(
        self,
        specification: TechnicalSpecification
    ) -> str:
        """Generate markdown documentation from specification"""
        # Generate comprehensive markdown document
        md = f"""# {specification.title}

## Overview
{specification.overview}

## User Stories

"""
        for story in specification.user_stories:
            md += f"""### {story.title}

**Priority:** {story.priority}  
**Estimated Points:** {story.estimated_points}

{story.description}

**Acceptance Criteria:**
"""
            for criterion in story.acceptance_criteria:
                md += f"- {criterion}\n"
            md += "\n"
        
        # Add database schema, API endpoints, etc.
        # ...
        
        return md
    
    async def _generate_architecture_diagram(
        self,
        specification: TechnicalSpecification
    ) -> str:
        """Generate architecture diagram (Mermaid format)"""
        # Generate Mermaid diagram
        diagram = """graph TD
    A[Client] --> B[API Gateway]
    B --> C[Backend Service]
    C --> D[Database]
"""
        # Would be more sophisticated based on specification
        return diagram
    
    async def _store_specification(
        self,
        context: TaskContext,
        specification: TechnicalSpecification
    ):
        """Store specification in memory system"""
        if not self.memory_client:
            return
        
        await self.memory_client.store_specification(
            workflow_id=context.workflow_id,
            specification=specification.dict(),
            metadata={
                "task_id": context.task_id,
                "agent_id": self.config.agent_id,
                "created_at": datetime.utcnow().isoformat()
            }
        )
    
    def _calculate_cost(
        self,
        model_config: Dict[str, Any],
        token_usage: Dict[str, int]
    ) -> float:
        """Calculate cost in USD based on token usage"""
        total_tokens = token_usage.get("total_tokens", 0)
        cost_per_1m = model_config.get("cost_per_1m_tokens", 0)
        return (total_tokens / 1_000_000) * cost_per_1m


# Entry point
if __name__ == "__main__":
    import asyncio
    import os
    
    # Initialize agent
    config = AgentConfig(
        agent_id=f"spec-agent-{os.getenv('HOSTNAME', 'local')}",
        agent_type="spec",
        version="2.1.0",
        max_concurrent_tasks=5,
        capabilities=[
            "prd_parsing",
            "spec_generation",
            "schema_design",
            "api_design"
        ]
    )
    
    agent = SpecAgent(config)
    
    # Start agent
    asyncio.run(agent.start())
    
    # Agent would then listen for tasks from orchestrator
    # via event bus or task queue
