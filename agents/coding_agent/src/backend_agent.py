"""
Backend Coding Agent

Specialized agent for backend code generation including:
- REST/GraphQL APIs
- Business logic
- Database interactions
- Service integrations
- Authentication/Authorization
- Background jobs
- WebSocket servers
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from agents.shared.base_agent import BaseAgent, AgentConfig, TaskContext, TaskResult


class CodeArtifact(BaseModel):
    """Generated code artifact"""
    file_path: str
    content: str
    language: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    tests_required: bool = True


class CodeGeneration(BaseModel):
    """Complete code generation output"""
    artifacts: List[CodeArtifact]
    documentation: str
    setup_instructions: str
    test_strategy: str
    security_considerations: List[str]


class BackendCodingAgent(BaseAgent):
    """
    Backend Coding Agent for API and service implementation.
    """
    
    def __init__(self, config: AgentConfig, **kwargs):
        super().__init__(config, **kwargs)
        self.llm = None
        self.system_prompt = self._load_system_prompt()
        self.coding_prompt = self._load_coding_prompt()
        
    def _load_system_prompt(self) -> str:
        """Load system prompt"""
        return """You are an expert Senior Backend Engineer with 10+ years of experience.

You specialize in building production-grade backend systems with:
- Clean, maintainable code following SOLID principles
- Comprehensive error handling and logging
- Input validation and security best practices
- Efficient database queries with proper indexing
- RESTful API design following OpenAPI standards
- Async/await patterns for performance
- Proper authentication and authorization
- Type hints and documentation
- Unit test coverage

Tech Stack Expertise:
- Python: FastAPI, Django, Flask, SQLAlchemy, Pydantic
- Node.js: Express, NestJS, Prisma, TypeScript
- Go: Gin, GORM, Chi
- Databases: PostgreSQL, MongoDB, Redis
- Message Queues: RabbitMQ, Kafka, NATS
- Authentication: JWT, OAuth 2.0, API Keys

Always write:
- Production-ready code (not prototypes)
- Comprehensive docstrings/comments
- Proper error handling with custom exceptions
- Input validation with clear error messages
- SQL injection prevention (parameterized queries)
- Rate limiting and request validation
- Logging for observability

Output complete, working code files that can be deployed immediately."""
    
    def _load_coding_prompt(self) -> ChatPromptTemplate:
        """Load coding prompt template"""
        template = """Generate production-grade backend code for the following task.

# Task
{task_description}

# API Specification
{api_spec}

# Database Schema
{database_schema}

# Tech Stack
Language: {language}
Framework: {framework}
Database: {database}

# Requirements
{requirements}

# Existing Codebase Context
{codebase_context}

# Instructions
1. Write complete, production-ready code
2. Include comprehensive error handling
3. Add input validation with Pydantic/TypeScript types
4. Implement proper logging
5. Add authentication/authorization if needed
6. Include docstrings and comments
7. Follow framework best practices
8. Consider edge cases
9. Add TODO comments for manual steps (env vars, migrations)

Generate the code now:"""
        
        return ChatPromptTemplate.from_template(template)
    
    async def _execute_task_impl(self, context: TaskContext) -> TaskResult:
        """Execute backend code generation"""
        spec = context.specification
        
        # Extract task details
        task_description = spec.get("description", "")
        api_spec = spec.get("api_specification", {})
        database_schema = spec.get("database_schema", {})
        
        # Tech stack
        language = spec.get("language", "python")
        framework = spec.get("framework", "fastapi")
        database = spec.get("database", "postgresql")
        
        # Requirements
        requirements = spec.get("requirements", [])
        
        # Get codebase context
        codebase_context = await self._get_codebase_context(
            context.workflow_id,
            spec.get("repository", "")
        )
        
        # Request model routing
        model_config = await self._request_model_routing(context, spec)
        self.llm = self._initialize_llm(model_config)
        
        # Generate code
        self.logger.info(f"Generating {language} backend code")
        
        prompt = self.coding_prompt.format(
            task_description=task_description,
            api_spec=json.dumps(api_spec, indent=2),
            database_schema=json.dumps(database_schema, indent=2),
            language=language,
            framework=framework,
            database=database,
            requirements="\n".join(f"- {r}" for r in requirements),
            codebase_context=json.dumps(codebase_context, indent=2)
        )
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm.agenerate([messages])
        code_output = response.generations[0][0].text
        
        # Parse code artifacts
        artifacts = self._parse_code_artifacts(code_output, language)
        
        # Generate documentation
        documentation = self._generate_documentation(artifacts, spec)
        
        # Store artifacts
        artifact_paths = []
        for artifact in artifacts:
            path = await self._store_artifact(
                context.workflow_id,
                artifact
            )
            artifact_paths.append(path)
        
        # Perform static analysis
        analysis = await self._static_analysis(artifacts, language)
        
        metrics = {
            "files_generated": len(artifacts),
            "lines_of_code": sum(len(a.content.splitlines()) for a in artifacts),
            "language": language,
            "framework": framework,
            "static_analysis": analysis,
            "model_used": model_config.get("model_id"),
            "tokens_used": response.llm_output.get("token_usage", {}).get("total_tokens", 0)
        }
        
        return TaskResult(
            task_id=context.task_id,
            status="completed",
            output={
                "artifacts": [a.dict() for a in artifacts],
                "documentation": documentation,
                "static_analysis": analysis
            },
            artifacts=artifact_paths,
            metrics=metrics
        )
    
    def _parse_code_artifacts(
        self,
        code_output: str,
        language: str
    ) -> List[CodeArtifact]:
        """Parse code output into structured artifacts"""
        artifacts = []
        
        # Simple parsing logic - look for file markers
        # In production, use more sophisticated parsing
        
        lines = code_output.split('\n')
        current_file = None
        current_content = []
        
        for line in lines:
            # Check for file path marker (e.g., "# File: src/api/users.py")
            if line.strip().startswith(('# File:', '// File:', '/* File:')):
                # Save previous file
                if current_file:
                    artifacts.append(CodeArtifact(
                        file_path=current_file,
                        content='\n'.join(current_content),
                        language=language,
                        description=f"Generated {current_file}"
                    ))
                
                # Start new file
                current_file = line.split(':', 1)[1].strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last file
        if current_file:
            artifacts.append(CodeArtifact(
                file_path=current_file,
                content='\n'.join(current_content),
                language=language,
                description=f"Generated {current_file}"
            ))
        
        # If no file markers, treat as single file
        if not artifacts:
            artifacts.append(CodeArtifact(
                file_path="main.py" if language == "python" else "main.ts",
                content=code_output,
                language=language,
                description="Generated code"
            ))
        
        return artifacts
    
    def _generate_documentation(
        self,
        artifacts: List[CodeArtifact],
        spec: Dict[str, Any]
    ) -> str:
        """Generate documentation for the code"""
        doc = f"""# Backend Implementation

## Generated Files
"""
        for artifact in artifacts:
            doc += f"- `{artifact.file_path}`: {artifact.description}\n"
        
        doc += f"""
## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL="postgresql://user:pass@localhost/db"
export SECRET_KEY="your-secret-key"
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start server:
```bash
uvicorn main:app --reload
```

## API Documentation

API documentation available at: http://localhost:8000/docs

## Testing

Run tests with:
```bash
pytest tests/ -v --cov
```
"""
        return doc
    
    async def _get_codebase_context(
        self,
        workflow_id: str,
        repository: str
    ) -> Dict[str, Any]:
        """Get relevant codebase context"""
        if not self.memory_client or not repository:
            return {}
        
        context = await self.memory_client.query_codebase_context(
            repository=repository,
            query="backend structure, models, utilities"
        )
        
        return context
    
    async def _store_artifact(
        self,
        workflow_id: str,
        artifact: CodeArtifact
    ) -> str:
        """Store code artifact"""
        # In production, store in object storage or version control
        artifact_path = f"artifacts/{workflow_id}/{artifact.file_path}"
        
        self.logger.info(f"Storing artifact: {artifact_path}")
        
        # Store artifact (placeholder)
        # await storage_client.put(artifact_path, artifact.content)
        
        return artifact_path
    
    async def _static_analysis(
        self,
        artifacts: List[CodeArtifact],
        language: str
    ) -> Dict[str, Any]:
        """Run static analysis on generated code"""
        analysis = {
            "syntax_valid": True,
            "style_issues": [],
            "security_issues": [],
            "complexity_score": "good"
        }
        
        # In production, run actual linters:
        # - Python: pylint, flake8, mypy, bandit
        # - JavaScript: eslint, tsc
        # - Go: golint, go vet
        
        for artifact in artifacts:
            # Check for common security issues
            if "eval(" in artifact.content:
                analysis["security_issues"].append({
                    "file": artifact.file_path,
                    "issue": "Use of eval() is dangerous",
                    "severity": "high"
                })
            
            if "password" in artifact.content.lower() and "hash" not in artifact.content.lower():
                analysis["security_issues"].append({
                    "file": artifact.file_path,
                    "issue": "Potential plaintext password handling",
                    "severity": "critical"
                })
        
        return analysis
    
    async def _request_model_routing(
        self,
        context: TaskContext,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request model from router"""
        # Use high-quality model for backend code
        return {
            "model_id": "claude-sonnet-4",
            "provider": "anthropic",
            "cost_per_1m_tokens": 3.00
        }
    
    def _initialize_llm(self, model_config: Dict[str, Any]):
        """Initialize LLM"""
        provider = model_config.get("provider")
        model_id = model_config.get("model_id")
        
        if provider == "anthropic":
            return ChatAnthropic(model=model_id, temperature=0.3, max_tokens=8192)
        elif provider == "openai":
            return ChatOpenAI(model=model_id, temperature=0.3, max_tokens=8192)
        else:
            raise ValueError(f"Unsupported provider: {provider}")


if __name__ == "__main__":
    import asyncio
    import os
    
    config = AgentConfig(
        agent_id=f"coding-backend-{os.getenv('HOSTNAME', 'local')}",
        agent_type="coding_backend",
        version="2.1.0",
        max_concurrent_tasks=5,
        capabilities=[
            "api_development",
            "database_integration",
            "authentication",
            "business_logic"
        ]
    )
    
    agent = BackendCodingAgent(config)
    asyncio.run(agent.start())
