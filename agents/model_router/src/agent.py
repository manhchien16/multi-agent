"""
Model Router Agent

This agent is responsible for intelligent model selection and routing based on
task characteristics, cost constraints, and quality requirements.

Capabilities:
- Analyze task complexity and requirements
- Select optimal LLM model (balancing cost vs quality)
- Route requests to appropriate model providers
- Track model performance metrics
- Implement fallback strategies
- Optimize for cost efficiency
- Support multi-provider redundancy
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from agents.shared.base_agent import BaseAgent, AgentConfig, TaskContext, TaskResult


class ModelProvider(str, Enum):
    """Supported model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    GOOGLE = "google"


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    TRIVIAL = "trivial"          # Simple formatting, basic transformations
    SIMPLE = "simple"             # Straightforward code, clear requirements
    MODERATE = "moderate"         # Standard features with some complexity
    COMPLEX = "complex"           # Multi-component integration, edge cases
    CRITICAL = "critical"         # Architecture decisions, security-sensitive


@dataclass
class ModelCapability:
    """Model capability profile"""
    model_id: str
    provider: ModelProvider
    context_window: int
    cost_per_1m_input_tokens: float
    cost_per_1m_output_tokens: float
    
    # Capability scores (0-10)
    code_generation: int
    reasoning: int
    instruction_following: int
    context_retention: int
    speed_tokens_per_sec: int
    
    # Constraints
    max_output_tokens: int
    supports_tools: bool
    supports_vision: bool


class ModelConfig(BaseModel):
    """Model configuration for task execution"""
    model_id: str
    provider: str
    reasoning: str  # Why this model was selected
    estimated_cost_usd: float
    fallback_models: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Complete routing decision"""
    primary_model: ModelConfig
    fallback_strategy: List[ModelConfig]
    cost_analysis: Dict[str, float]
    performance_prediction: Dict[str, Any]


class ModelRouterAgent(BaseAgent):
    """
    Model Router Agent for intelligent LLM selection.
    """
    
    def __init__(self, config: AgentConfig, **kwargs):
        super().__init__(config, **kwargs)
        
        # Initialize model registry
        self.model_registry = self._initialize_model_registry()
        
        # Performance tracking
        self.performance_history = {}
        
    def _initialize_model_registry(self) -> Dict[str, ModelCapability]:
        """Initialize registry of available models"""
        return {
            # Premium models - High quality, high cost
            "claude-opus-4": ModelCapability(
                model_id="claude-opus-4",
                provider=ModelProvider.ANTHROPIC,
                context_window=200000,
                cost_per_1m_input_tokens=15.00,
                cost_per_1m_output_tokens=75.00,
                code_generation=10,
                reasoning=10,
                instruction_following=10,
                context_retention=10,
                speed_tokens_per_sec=50,
                max_output_tokens=4096,
                supports_tools=True,
                supports_vision=True
            ),
            
            "gpt-4-turbo": ModelCapability(
                model_id="gpt-4-turbo",
                provider=ModelProvider.OPENAI,
                context_window=128000,
                cost_per_1m_input_tokens=10.00,
                cost_per_1m_output_tokens=30.00,
                code_generation=9,
                reasoning=9,
                instruction_following=9,
                context_retention=9,
                speed_tokens_per_sec=60,
                max_output_tokens=4096,
                supports_tools=True,
                supports_vision=True
            ),
            
            # Standard models - Good balance
            "claude-sonnet-4": ModelCapability(
                model_id="claude-sonnet-4",
                provider=ModelProvider.ANTHROPIC,
                context_window=200000,
                cost_per_1m_input_tokens=3.00,
                cost_per_1m_output_tokens=15.00,
                code_generation=9,
                reasoning=8,
                instruction_following=9,
                context_retention=9,
                speed_tokens_per_sec=80,
                max_output_tokens=8192,
                supports_tools=True,
                supports_vision=True
            ),
            
            "gpt-4o": ModelCapability(
                model_id="gpt-4o",
                provider=ModelProvider.OPENAI,
                context_window=128000,
                cost_per_1m_input_tokens=2.50,
                cost_per_1m_output_tokens=10.00,
                code_generation=8,
                reasoning=8,
                instruction_following=9,
                context_retention=8,
                speed_tokens_per_sec=100,
                max_output_tokens=16384,
                supports_tools=True,
                supports_vision=True
            ),
            
            # Budget models - Cost-efficient
            "deepseek-v3": ModelCapability(
                model_id="deepseek-v3",
                provider=ModelProvider.DEEPSEEK,
                context_window=64000,
                cost_per_1m_input_tokens=0.14,
                cost_per_1m_output_tokens=0.28,
                code_generation=8,
                reasoning=7,
                instruction_following=7,
                context_retention=7,
                speed_tokens_per_sec=120,
                max_output_tokens=8192,
                supports_tools=True,
                supports_vision=False
            ),
            
            "qwen-2.5-coder-32b": ModelCapability(
                model_id="qwen-2.5-coder-32b",
                provider=ModelProvider.QWEN,
                context_window=32000,
                cost_per_1m_input_tokens=0.27,
                cost_per_1m_output_tokens=0.54,
                code_generation=8,
                reasoning=6,
                instruction_following=7,
                context_retention=6,
                speed_tokens_per_sec=150,
                max_output_tokens=4096,
                supports_tools=False,
                supports_vision=False
            ),
            
            "gpt-4o-mini": ModelCapability(
                model_id="gpt-4o-mini",
                provider=ModelProvider.OPENAI,
                context_window=128000,
                cost_per_1m_input_tokens=0.15,
                cost_per_1m_output_tokens=0.60,
                code_generation=7,
                reasoning=7,
                instruction_following=8,
                context_retention=7,
                speed_tokens_per_sec=150,
                max_output_tokens=16384,
                supports_tools=True,
                supports_vision=True
            )
        }
    
    async def _execute_task_impl(self, context: TaskContext) -> TaskResult:
        """
        Execute model routing task.
        
        Args:
            context: Task context with routing request
            
        Returns:
            TaskResult with routing decision
        """
        spec = context.specification
        
        # Extract routing request
        task_type = spec.get("task_type", "")
        task_description = spec.get("description", "")
        estimated_tokens = spec.get("estimated_tokens", {})
        budget_constraint = spec.get("budget_constraint")
        quality_requirement = spec.get("quality_requirement", "standard")
        requires_tools = spec.get("requires_tools", False)
        requires_vision = spec.get("requires_vision", False)
        
        # Analyze task complexity
        complexity = self._analyze_complexity(
            task_type=task_type,
            description=task_description,
            estimated_tokens=estimated_tokens
        )
        
        self.logger.info(
            f"Routing request for task type: {task_type}, complexity: {complexity}"
        )
        
        # Select optimal model
        routing_decision = self._select_optimal_model(
            complexity=complexity,
            task_type=task_type,
            estimated_tokens=estimated_tokens,
            budget_constraint=budget_constraint,
            quality_requirement=quality_requirement,
            requires_tools=requires_tools,
            requires_vision=requires_vision
        )
        
        # Generate routing rationale
        rationale = self._generate_rationale(routing_decision, complexity)
        
        # Store routing decision for learning
        if self.memory_client:
            await self.memory_client.store_routing_decision(
                task_id=context.task_id,
                decision=routing_decision.dict(),
                complexity=complexity
            )
        
        metrics = {
            "complexity": complexity,
            "primary_model": routing_decision.primary_model.model_id,
            "estimated_cost": routing_decision.primary_model.estimated_cost_usd,
            "fallback_options": len(routing_decision.fallback_strategy)
        }
        
        return TaskResult(
            task_id=context.task_id,
            status="completed",
            output={
                "routing_decision": routing_decision.dict(),
                "rationale": rationale,
                "complexity_analysis": complexity
            },
            metrics=metrics
        )
    
    def _analyze_complexity(
        self,
        task_type: str,
        description: str,
        estimated_tokens: Dict[str, int]
    ) -> TaskComplexity:
        """Analyze task complexity"""
        
        # Complexity indicators
        input_tokens = estimated_tokens.get("input", 0)
        output_tokens = estimated_tokens.get("output", 0)
        
        # Task type mapping
        complex_tasks = [
            "architecture_design",
            "security_review",
            "performance_optimization",
            "system_integration"
        ]
        
        moderate_tasks = [
            "api_implementation",
            "database_schema",
            "backend_service"
        ]
        
        simple_tasks = [
            "frontend_component",
            "unit_test",
            "documentation"
        ]
        
        # Analyze based on task type
        if task_type in complex_tasks:
            return TaskComplexity.CRITICAL
        
        if task_type in moderate_tasks:
            complexity = TaskComplexity.MODERATE
        elif task_type in simple_tasks:
            complexity = TaskComplexity.SIMPLE
        else:
            complexity = TaskComplexity.MODERATE  # Default
        
        # Adjust based on token count
        if input_tokens > 50000 or output_tokens > 4000:
            # Upgrade complexity for large context
            complexity_order = [
                TaskComplexity.TRIVIAL,
                TaskComplexity.SIMPLE,
                TaskComplexity.MODERATE,
                TaskComplexity.COMPLEX,
                TaskComplexity.CRITICAL
            ]
            current_idx = complexity_order.index(complexity)
            if current_idx < len(complexity_order) - 1:
                complexity = complexity_order[current_idx + 1]
        
        # Keyword-based analysis
        critical_keywords = [
            "security", "authentication", "encryption",
            "architecture", "scalability", "distributed"
        ]
        
        if any(keyword in description.lower() for keyword in critical_keywords):
            return TaskComplexity.CRITICAL
        
        return complexity
    
    def _select_optimal_model(
        self,
        complexity: TaskComplexity,
        task_type: str,
        estimated_tokens: Dict[str, int],
        budget_constraint: Optional[float],
        quality_requirement: str,
        requires_tools: bool,
        requires_vision: bool
    ) -> RoutingDecision:
        """Select optimal model based on requirements"""
        
        input_tokens = estimated_tokens.get("input", 1000)
        output_tokens = estimated_tokens.get("output", 500)
        
        # Filter models based on requirements
        candidate_models = []
        
        for model_id, model in self.model_registry.items():
            # Check tool requirement
            if requires_tools and not model.supports_tools:
                continue
            
            # Check vision requirement
            if requires_vision and not model.supports_vision:
                continue
            
            # Check context window
            if input_tokens > model.context_window:
                continue
            
            # Calculate estimated cost
            cost = (
                (input_tokens / 1_000_000) * model.cost_per_1m_input_tokens +
                (output_tokens / 1_000_000) * model.cost_per_1m_output_tokens
            )
            
            # Check budget constraint
            if budget_constraint and cost > budget_constraint:
                continue
            
            candidate_models.append((model, cost))
        
        if not candidate_models:
            # Fallback to cheapest model
            model = self.model_registry["gpt-4o-mini"]
            cost = (
                (input_tokens / 1_000_000) * model.cost_per_1m_input_tokens +
                (output_tokens / 1_000_000) * model.cost_per_1m_output_tokens
            )
            candidate_models = [(model, cost)]
        
        # Select based on complexity and quality requirement
        selected_model, estimated_cost = self._rank_and_select(
            candidate_models,
            complexity,
            quality_requirement
        )
        
        # Create primary model config
        primary_model = ModelConfig(
            model_id=selected_model.model_id,
            provider=selected_model.provider.value,
            reasoning=f"Selected for {complexity} task with {quality_requirement} quality requirement",
            estimated_cost_usd=estimated_cost,
            fallback_models=[],
            configuration={
                "temperature": self._get_temperature(task_type),
                "max_tokens": min(output_tokens * 2, selected_model.max_output_tokens),
                "top_p": 0.95
            }
        )
        
        # Select fallback models
        fallback_strategy = self._select_fallbacks(
            selected_model,
            candidate_models,
            complexity
        )
        
        # Cost analysis
        cost_analysis = {
            "primary_estimated": estimated_cost,
            "budget_remaining": (budget_constraint - estimated_cost) if budget_constraint else None,
            "alternatives": [
                {"model": m.model_id, "cost": c}
                for m, c in candidate_models[:3]
            ]
        }
        
        # Performance prediction
        performance_prediction = {
            "expected_quality": self._predict_quality(selected_model, complexity),
            "expected_latency_sec": output_tokens / selected_model.speed_tokens_per_sec,
            "success_probability": self._predict_success(selected_model, complexity)
        }
        
        return RoutingDecision(
            primary_model=primary_model,
            fallback_strategy=fallback_strategy,
            cost_analysis=cost_analysis,
            performance_prediction=performance_prediction
        )
    
    def _rank_and_select(
        self,
        candidates: List[tuple],
        complexity: TaskComplexity,
        quality_requirement: str
    ) -> tuple:
        """Rank candidates and select best option"""
        
        # Define quality thresholds
        quality_score_required = {
            "minimum": 6,
            "standard": 7,
            "high": 8,
            "premium": 9
        }.get(quality_requirement, 7)
        
        # Define complexity requirements
        complexity_requirements = {
            TaskComplexity.TRIVIAL: {"code": 6, "reasoning": 5},
            TaskComplexity.SIMPLE: {"code": 7, "reasoning": 6},
            TaskComplexity.MODERATE: {"code": 8, "reasoning": 7},
            TaskComplexity.COMPLEX: {"code": 9, "reasoning": 8},
            TaskComplexity.CRITICAL: {"code": 10, "reasoning": 10}
        }
        
        requirements = complexity_requirements[complexity]
        
        # Score each candidate
        scored_candidates = []
        for model, cost in candidates:
            # Check if model meets minimum requirements
            if (model.code_generation < requirements["code"] or
                model.reasoning < requirements["reasoning"]):
                continue
            
            # Calculate composite score (higher is better)
            quality_score = (
                model.code_generation * 0.4 +
                model.reasoning * 0.3 +
                model.instruction_following * 0.2 +
                model.context_retention * 0.1
            )
            
            # Penalize high cost
            cost_penalty = cost * 10  # Adjust weight
            
            # Final score: quality - cost_penalty
            final_score = quality_score - cost_penalty
            
            scored_candidates.append((model, cost, final_score))
        
        if not scored_candidates:
            # No candidate meets requirements, return cheapest
            return min(candidates, key=lambda x: x[1])
        
        # Return highest scoring candidate
        best = max(scored_candidates, key=lambda x: x[2])
        return (best[0], best[1])
    
    def _select_fallbacks(
        self,
        primary_model: ModelCapability,
        candidates: List[tuple],
        complexity: TaskComplexity
    ) -> List[ModelConfig]:
        """Select fallback models"""
        fallbacks = []
        
        # Select up to 2 fallback models
        for model, cost in candidates:
            if model.model_id == primary_model.model_id:
                continue
            
            # Prefer same provider first
            if model.provider == primary_model.provider:
                fallbacks.insert(0, ModelConfig(
                    model_id=model.model_id,
                    provider=model.provider.value,
                    reasoning="Same provider fallback",
                    estimated_cost_usd=cost
                ))
            else:
                fallbacks.append(ModelConfig(
                    model_id=model.model_id,
                    provider=model.provider.value,
                    reasoning="Alternative provider fallback",
                    estimated_cost_usd=cost
                ))
            
            if len(fallbacks) >= 2:
                break
        
        return fallbacks[:2]
    
    def _get_temperature(self, task_type: str) -> float:
        """Get optimal temperature for task type"""
        creative_tasks = ["documentation", "naming", "design"]
        deterministic_tasks = ["testing", "security_review", "debugging"]
        
        if task_type in creative_tasks:
            return 0.8
        elif task_type in deterministic_tasks:
            return 0.3
        else:
            return 0.5
    
    def _predict_quality(self, model: ModelCapability, complexity: TaskComplexity) -> str:
        """Predict output quality"""
        score = (model.code_generation + model.reasoning) / 2
        
        if score >= 9:
            return "excellent"
        elif score >= 8:
            return "high"
        elif score >= 7:
            return "good"
        else:
            return "acceptable"
    
    def _predict_success(self, model: ModelCapability, complexity: TaskComplexity) -> float:
        """Predict success probability"""
        complexity_penalties = {
            TaskComplexity.TRIVIAL: 0.0,
            TaskComplexity.SIMPLE: 0.05,
            TaskComplexity.MODERATE: 0.10,
            TaskComplexity.COMPLEX: 0.20,
            TaskComplexity.CRITICAL: 0.30
        }
        
        base_probability = 0.95
        capability_score = (model.code_generation + model.reasoning) / 20.0
        penalty = complexity_penalties[complexity]
        
        return min(base_probability * capability_score - penalty, 0.99)
    
    def _generate_rationale(
        self,
        decision: RoutingDecision,
        complexity: TaskComplexity
    ) -> str:
        """Generate human-readable rationale"""
        model = decision.primary_model
        cost = decision.cost_analysis["primary_estimated"]
        quality = decision.performance_prediction["expected_quality"]
        
        rationale = f"""Model Routing Decision:
        
Selected: {model.model_id} ({model.provider})
Reason: {model.reasoning}

Task Complexity: {complexity}
Expected Quality: {quality}
Estimated Cost: ${cost:.4f}

This model was selected because it provides the optimal balance of cost and quality 
for this task's complexity level. """
        
        if decision.fallback_strategy:
            rationale += f"\n\nFallback models available: {', '.join(f.model_id for f in decision.fallback_strategy)}"
        
        return rationale


if __name__ == "__main__":
    import asyncio
    import os
    
    config = AgentConfig(
        agent_id=f"model-router-{os.getenv('HOSTNAME', 'local')}",
        agent_type="model_router",
        version="2.1.0",
        max_concurrent_tasks=20,
        capabilities=[
            "model_selection",
            "cost_optimization",
            "fallback_routing",
            "performance_prediction"
        ]
    )
    
    agent = ModelRouterAgent(config)
    asyncio.run(agent.start())
