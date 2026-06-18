"""
Review Agent

Performs comprehensive code review including:
- Security vulnerability detection
- Performance optimization opportunities
- Architecture review
- Code quality assessment
- Best practices compliance
- Dependency analysis
- OWASP Top 10 checks
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from agents.shared.base_agent import BaseAgent, AgentConfig, TaskContext, TaskResult


class Severity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    """Issue categories"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    ARCHITECTURE = "architecture"
    STYLE = "style"


class ReviewIssue(BaseModel):
    """Code review issue"""
    category: IssueCategory
    severity: Severity
    file_path: str
    line_number: Optional[int] = None
    title: str
    description: str
    recommendation: str
    code_snippet: Optional[str] = None
    references: List[str] = Field(default_factory=list)


class SecurityFinding(BaseModel):
    """Security-specific finding"""
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    owasp_category: Optional[str] = None
    vulnerability_type: str
    risk_level: Severity
    affected_code: str
    remediation: str
    false_positive_likelihood: str


class PerformanceIssue(BaseModel):
    """Performance-specific issue"""
    issue_type: str  # e.g., "N+1 query", "inefficient algorithm"
    impact: str  # e.g., "O(n²) complexity"
    current_approach: str
    optimized_approach: str
    expected_improvement: str


class CodeReview(BaseModel):
    """Complete code review"""
    overall_score: int = Field(..., ge=0, le=100)
    summary: str
    issues: List[ReviewIssue]
    security_findings: List[SecurityFinding]
    performance_issues: List[PerformanceIssue]
    strengths: List[str]
    recommendations: List[str]
    requires_changes: bool


class ReviewAgent(BaseAgent):
    """
    Review Agent for comprehensive code analysis.
    """
    
    def __init__(self, config: AgentConfig, **kwargs):
        super().__init__(config, **kwargs)
        self.llm = None
        self.system_prompt = self._load_system_prompt()
        self.review_prompt = self._load_review_prompt()
        
    def _load_system_prompt(self) -> str:
        """Load system prompt"""
        return """You are an expert Security Engineer and Senior Code Reviewer with expertise in:

Security:
- OWASP Top 10 vulnerabilities
- CWE/SANS Top 25 security flaws
- SQL injection, XSS, CSRF prevention
- Authentication and authorization flaws
- Cryptographic vulnerabilities
- Dependency vulnerabilities
- Secrets in code detection

Performance:
- Algorithm complexity analysis
- Database query optimization (N+1, missing indexes)
- Memory leaks and resource management
- Caching strategies
- Async/await patterns
- Bottleneck identification

Architecture:
- SOLID principles adherence
- Design patterns appropriateness
- Separation of concerns
- Dependency injection
- Error handling strategies
- Logging and observability

Code Quality:
- DRY, KISS, YAGNI principles
- Code smells (long methods, god classes)
- Test coverage
- Documentation quality
- Type safety
- Error handling

Your reviews are:
- Thorough: Check every security concern
- Constructive: Provide actionable recommendations
- Prioritized: CRITICAL issues first
- Specific: Reference line numbers and code
- Educational: Explain why issues matter
- Balanced: Acknowledge good practices too

Be strict on security issues. Be pragmatic on style issues."""
    
    def _load_review_prompt(self) -> ChatPromptTemplate:
        """Load review prompt template"""
        template = """Perform a comprehensive code review of the following code.

# Code to Review

{code_artifacts}

# Context
Language: {language}
Framework: {framework}
Purpose: {purpose}

# Review Checklist

## Security (HIGHEST PRIORITY)
- [ ] SQL injection vulnerabilities
- [ ] XSS vulnerabilities
- [ ] Authentication/Authorization flaws
- [ ] Insecure cryptography
- [ ] Secrets in code
- [ ] Input validation
- [ ] Output encoding
- [ ] CSRF protection
- [ ] Insecure dependencies
- [ ] Path traversal

## Performance
- [ ] Algorithm complexity
- [ ] Database query efficiency
- [ ] N+1 query problems
- [ ] Missing indexes
- [ ] Memory leaks
- [ ] Resource cleanup
- [ ] Caching opportunities

## Architecture & Design
- [ ] SOLID principles
- [ ] Separation of concerns
- [ ] Error handling
- [ ] Logging strategy
- [ ] Code organization
- [ ] Dependency management

## Code Quality
- [ ] Code duplication
- [ ] Long methods/classes
- [ ] Naming conventions
- [ ] Comments and documentation
- [ ] Type safety
- [ ] Test coverage
- [ ] Edge case handling

# Instructions

1. Review code systematically using the checklist
2. Identify ALL security vulnerabilities (CRITICAL priority)
3. Find performance bottlenecks and optimization opportunities
4. Assess architecture and design quality
5. Note code quality issues
6. Provide specific, actionable recommendations
7. Include code examples for fixes
8. Assign appropriate severity levels
9. Calculate overall quality score (0-100)
10. List what was done well

Be thorough. Security issues are CRITICAL.

Generate the code review now:"""
        
        return ChatPromptTemplate.from_template(template)
    
    async def _execute_task_impl(self, context: TaskContext) -> TaskResult:
        """Execute code review"""
        spec = context.specification
        
        # Extract code artifacts
        code_artifacts = spec.get("code_artifacts", [])
        language = spec.get("language", "python")
        framework = spec.get("framework", "")
        purpose = spec.get("purpose", "")
        
        if not code_artifacts:
            raise ValueError("No code artifacts provided for review")
        
        # Prepare code for review
        code_text = self._format_code_for_review(code_artifacts)
        
        # Request model routing (use high-quality model for security review)
        model_config = await self._request_model_routing(context, spec)
        self.llm = self._initialize_llm(model_config)
        
        # Perform review
        self.logger.info(f"Reviewing {len(code_artifacts)} code artifacts")
        
        prompt = self.review_prompt.format(
            code_artifacts=code_text,
            language=language,
            framework=framework,
            purpose=purpose
        )
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm.agenerate([messages])
        review_text = response.generations[0][0].text
        
        # Parse review (simplified - in production use structured output)
        review = self._parse_review(review_text)
        
        # Run automated security scanners
        security_scan = await self._run_security_scanners(code_artifacts, language)
        
        # Merge automated findings with LLM review
        review = self._merge_security_findings(review, security_scan)
        
        # Generate review report
        report = self._generate_review_report(review)
        
        # Determine if changes are required
        critical_issues = [
            i for i in review.issues
            if i.severity in [Severity.CRITICAL, Severity.HIGH]
        ]
        
        metrics = {
            "overall_score": review.overall_score,
            "total_issues": len(review.issues),
            "critical_issues": len([i for i in review.issues if i.severity == Severity.CRITICAL]),
            "high_issues": len([i for i in review.issues if i.severity == Severity.HIGH]),
            "security_findings": len(review.security_findings),
            "performance_issues": len(review.performance_issues),
            "requires_changes": review.requires_changes,
            "model_used": model_config.get("model_id")
        }
        
        return TaskResult(
            task_id=context.task_id,
            status="completed",
            output={
                "review": review.dict(),
                "report": report,
                "requires_changes": review.requires_changes,
                "critical_issues": [i.dict() for i in critical_issues]
            },
            artifacts=[f"review-{context.task_id}.md", f"review-{context.task_id}.json"],
            metrics=metrics
        )
    
    def _format_code_for_review(self, code_artifacts: List[Dict[str, Any]]) -> str:
        """Format code artifacts for review"""
        formatted = ""
        
        for artifact in code_artifacts:
            file_path = artifact.get("file_path", "unknown")
            content = artifact.get("content", "")
            
            formatted += f"\n\n# File: {file_path}\n\n```\n{content}\n```\n"
        
        return formatted
    
    def _parse_review(self, review_text: str) -> CodeReview:
        """Parse review text into structured format"""
        # Simplified parsing - in production, use structured output
        # or more sophisticated parsing
        
        # Count critical keywords
        critical_keywords = ["vulnerability", "security", "injection", "xss", "csrf"]
        critical_count = sum(review_text.lower().count(kw) for kw in critical_keywords)
        
        # Calculate score based on issues found
        base_score = 85
        penalty = min(critical_count * 10, 50)
        overall_score = max(base_score - penalty, 30)
        
        # Create basic review structure
        issues = []
        security_findings = []
        
        # Look for explicit security issues in text
        if "sql injection" in review_text.lower():
            security_findings.append(SecurityFinding(
                cwe_id="CWE-89",
                owasp_category="A03:2021 - Injection",
                vulnerability_type="SQL Injection",
                risk_level=Severity.CRITICAL,
                affected_code="Database query construction",
                remediation="Use parameterized queries or ORM",
                false_positive_likelihood="low"
            ))
        
        if "xss" in review_text.lower() or "cross-site scripting" in review_text.lower():
            security_findings.append(SecurityFinding(
                cwe_id="CWE-79",
                owasp_category="A03:2021 - Injection",
                vulnerability_type="Cross-Site Scripting (XSS)",
                risk_level=Severity.HIGH,
                affected_code="HTML output generation",
                remediation="Sanitize and encode all user input before output",
                false_positive_likelihood="low"
            ))
        
        return CodeReview(
            overall_score=overall_score,
            summary=review_text[:500],  # First 500 chars as summary
            issues=issues,
            security_findings=security_findings,
            performance_issues=[],
            strengths=["Code structure", "Error handling"] if overall_score > 70 else [],
            recommendations=["Review security best practices", "Add input validation"],
            requires_changes=len(security_findings) > 0 or overall_score < 70
        )
    
    async def _run_security_scanners(
        self,
        code_artifacts: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """Run automated security scanners"""
        findings = {
            "secrets_found": [],
            "vulnerabilities": [],
            "dependency_issues": []
        }
        
        # In production, integrate:
        # - Bandit (Python security)
        # - Semgrep (multi-language SAST)
        # - TruffleHog (secrets detection)
        # - Safety/Snyk (dependency scanning)
        
        for artifact in code_artifacts:
            content = artifact.get("content", "")
            
            # Simple secrets detection
            secret_patterns = [
                "password", "api_key", "secret_key",
                "private_key", "token", "aws_access"
            ]
            
            for pattern in secret_patterns:
                if pattern in content.lower() and "=" in content:
                    findings["secrets_found"].append({
                        "file": artifact.get("file_path"),
                        "pattern": pattern,
                        "severity": "high"
                    })
        
        return findings
    
    def _merge_security_findings(
        self,
        review: CodeReview,
        security_scan: Dict[str, Any]
    ) -> CodeReview:
        """Merge automated security findings with LLM review"""
        # Add automated findings to review
        for secret in security_scan.get("secrets_found", []):
            review.security_findings.append(SecurityFinding(
                cwe_id="CWE-798",
                owasp_category="A07:2021 - Identification and Authentication Failures",
                vulnerability_type="Hardcoded Secret",
                risk_level=Severity.CRITICAL,
                affected_code=f"File: {secret['file']}",
                remediation="Move secrets to environment variables or secure vault",
                false_positive_likelihood="medium"
            ))
        
        # Recalculate requires_changes
        review.requires_changes = review.requires_changes or len(security_scan.get("secrets_found", [])) > 0
        
        return review
    
    def _generate_review_report(self, review: CodeReview) -> str:
        """Generate markdown review report"""
        report = f"""# Code Review Report

## Overall Assessment

**Score: {review.overall_score}/100**

**Status: {'⚠️ CHANGES REQUIRED' if review.requires_changes else '✅ APPROVED'}**

## Summary

{review.summary}

---

## Security Findings ({len(review.security_findings)})

"""
        if review.security_findings:
            for finding in review.security_findings:
                report += f"""
### 🔴 {finding.vulnerability_type} ({finding.risk_level.upper()})

**CWE:** {finding.cwe_id}  
**OWASP:** {finding.owasp_category}

**Affected Code:**
```
{finding.affected_code}
```

**Remediation:**
{finding.remediation}

---
"""
        else:
            report += "✅ No security vulnerabilities detected.\n\n"
        
        report += f"""
## Performance Issues ({len(review.performance_issues)})

"""
        if review.performance_issues:
            for issue in review.performance_issues:
                report += f"- **{issue.issue_type}**: {issue.impact}\n"
        else:
            report += "✅ No significant performance issues detected.\n"
        
        report += f"""

## Strengths

"""
        for strength in review.strengths:
            report += f"- {strength}\n"
        
        report += f"""

## Recommendations

"""
        for rec in review.recommendations:
            report += f"- {rec}\n"
        
        return report
    
    async def _request_model_routing(
        self,
        context: TaskContext,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request model from router"""
        # Use high-quality model for security review
        return {
            "model_id": "claude-opus-4",
            "provider": "anthropic",
            "cost_per_1m_tokens": 15.00
        }
    
    def _initialize_llm(self, model_config: Dict[str, Any]):
        """Initialize LLM"""
        provider = model_config.get("provider")
        model_id = model_config.get("model_id")
        
        if provider == "anthropic":
            return ChatAnthropic(model=model_id, temperature=0.2, max_tokens=8192)
        elif provider == "openai":
            return ChatOpenAI(model=model_id, temperature=0.2, max_tokens=8192)
        else:
            raise ValueError(f"Unsupported provider: {provider}")


if __name__ == "__main__":
    import asyncio
    import os
    
    config = AgentConfig(
        agent_id=f"review-agent-{os.getenv('HOSTNAME', 'local')}",
        agent_type="review",
        version="2.1.0",
        max_concurrent_tasks=10,
        capabilities=[
            "security_review",
            "performance_review",
            "architecture_review",
            "code_quality_review"
        ]
    )
    
    agent = ReviewAgent(config)
    asyncio.run(agent.start())
