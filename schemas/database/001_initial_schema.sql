-- Multi-Agent Platform - Initial Database Schema
-- Version: 1.0.0
-- Date: 2026-06-18
-- Database: PostgreSQL 15+ with pgvector extension

-- =============================================================================
-- EXTENSIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Trigram for fuzzy search

-- =============================================================================
-- CUSTOM TYPES
-- =============================================================================

CREATE TYPE workflow_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled',
    'paused'
);

CREATE TYPE task_status AS ENUM (
    'pending',
    'queued',
    'assigned',
    'in_progress',
    'completed',
    'failed',
    'cancelled',
    'retrying'
);

CREATE TYPE task_category AS ENUM (
    'specification',
    'planning',
    'backend_coding',
    'frontend_coding',
    'devops_coding',
    'database_coding',
    'review',
    'testing',
    'evaluation',
    'approval'
);

CREATE TYPE agent_type AS ENUM (
    'orchestrator',
    'spec',
    'planner',
    'router',
    'backend_coding',
    'frontend_coding',
    'devops_coding',
    'database_coding',
    'review',
    'test',
    'evaluation',
    'approval'
);

CREATE TYPE agent_status AS ENUM (
    'idle',
    'busy',
    'offline',
    'error'
);

CREATE TYPE approval_status AS ENUM (
    'pending',
    'approved',
    'rejected',
    'timeout',
    'cancelled'
);

CREATE TYPE evaluation_dimension AS ENUM (
    'accuracy',
    'completeness',
    'security',
    'maintainability',
    'performance',
    'testability'
);

CREATE TYPE severity_level AS ENUM (
    'critical',
    'high',
    'medium',
    'low',
    'info'
);

CREATE TYPE tenant_tier AS ENUM (
    'free',
    'pro',
    'enterprise'
);

CREATE TYPE tenant_status AS ENUM (
    'active',
    'suspended',
    'deleted'
);

-- =============================================================================
-- TENANTS
-- =============================================================================

CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    status tenant_status NOT NULL DEFAULT 'active',
    tier tenant_tier NOT NULL DEFAULT 'free',
    resource_limits JSONB NOT NULL DEFAULT '{
        "max_concurrent_workflows": 10,
        "max_agents_per_workflow": 20,
        "max_cost_per_month_usd": 1000,
        "max_tokens_per_day": 10000000,
        "storage_limit_gb": 100
    }',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_tenants_status ON tenants(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_tenants_tier ON tenants(tier) WHERE deleted_at IS NULL;

-- =============================================================================
-- WORKFLOWS
-- =============================================================================

CREATE TABLE workflows (
    workflow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    status workflow_status NOT NULL DEFAULT 'pending',
    workflow_type VARCHAR(100) NOT NULL,
    workflow_version VARCHAR(50) NOT NULL,
    
    -- Workflow definition
    definition JSONB NOT NULL,
    
    -- Execution context
    context JSONB DEFAULT '{}',
    
    -- Progress tracking
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    
    -- Resource tracking
    cost_consumed_usd DECIMAL(10, 4) DEFAULT 0,
    tokens_consumed BIGINT DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_completion TIMESTAMP,
    
    -- Metadata
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_workflows_tenant ON workflows(tenant_id);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created ON workflows(created_at DESC);
CREATE INDEX idx_workflows_type ON workflows(workflow_type);
CREATE INDEX idx_workflows_created_by ON workflows(created_by);

-- =============================================================================
-- TASKS
-- =============================================================================

CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(task_id),
    
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category task_category NOT NULL,
    status task_status NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 5,
    
    -- Task specification
    specification JSONB NOT NULL,
    
    -- Dependencies
    dependencies UUID[] DEFAULT '{}',
    
    -- Assignment
    assigned_agent_id VARCHAR(255),
    assigned_agent_type agent_type,
    assigned_at TIMESTAMP,
    
    -- Execution
    execution_context JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Output
    output JSONB,
    artifacts TEXT[],  -- URLs or paths to artifacts
    
    -- Resource tracking
    cost_usd DECIMAL(10, 4) DEFAULT 0,
    tokens_used BIGINT DEFAULT 0,
    model_used VARCHAR(100),
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    estimated_duration_ms INTEGER,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_tasks_workflow ON tasks(workflow_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_category ON tasks(category);
CREATE INDEX idx_tasks_assigned_agent ON tasks(assigned_agent_id);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);

-- =============================================================================
-- AGENTS
-- =============================================================================

CREATE TABLE agents (
    agent_id VARCHAR(255) PRIMARY KEY,
    agent_type agent_type NOT NULL,
    version VARCHAR(50) NOT NULL,
    status agent_status NOT NULL DEFAULT 'idle',
    
    -- Capacity
    max_concurrent_tasks INTEGER NOT NULL DEFAULT 1,
    current_task_count INTEGER NOT NULL DEFAULT 0,
    
    -- Configuration
    configuration JSONB DEFAULT '{}',
    capabilities TEXT[],
    
    -- Performance
    total_tasks_completed INTEGER DEFAULT 0,
    total_tasks_failed INTEGER DEFAULT 0,
    avg_task_duration_ms INTEGER,
    avg_cost_per_task_usd DECIMAL(10, 4),
    avg_evaluation_score DECIMAL(5, 2),
    
    -- Health
    last_heartbeat TIMESTAMP,
    health_status VARCHAR(50),
    health_details JSONB,
    
    -- Deployment
    instance_id VARCHAR(255),
    pod_name VARCHAR(255),
    node_name VARCHAR(255),
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_heartbeat ON agents(last_heartbeat DESC);
CREATE INDEX idx_agents_performance ON agents(avg_evaluation_score DESC);

-- =============================================================================
-- SPECIFICATIONS
-- =============================================================================

CREATE TABLE specifications (
    spec_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id),
    version INTEGER NOT NULL,
    
    -- Content
    content JSONB NOT NULL,
    markdown_content TEXT,
    
    -- Components
    user_stories JSONB DEFAULT '[]',
    acceptance_criteria JSONB DEFAULT '[]',
    database_schema JSONB,
    api_contracts JSONB DEFAULT '[]',
    architecture_diagrams TEXT[],
    
    -- Analysis
    requirements_count INTEGER,
    risk_assessment JSONB,
    complexity_score INTEGER,
    
    -- Embeddings for semantic search
    embedding vector(1536),
    
    -- Metadata
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(workflow_id, version)
);

CREATE INDEX idx_specifications_workflow ON specifications(workflow_id);
CREATE INDEX idx_specifications_version ON specifications(workflow_id, version DESC);
CREATE INDEX idx_specifications_embedding ON specifications USING ivfflat (embedding vector_cosine_ops);

-- =============================================================================
-- ARCHITECTURAL DECISIONS (ADRs)
-- =============================================================================

CREATE TABLE architecture_decisions (
    adr_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    spec_id UUID NOT NULL REFERENCES specifications(spec_id),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id),
    
    title VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- proposed, accepted, rejected, deprecated, superseded
    
    -- ADR content
    context TEXT NOT NULL,
    decision TEXT NOT NULL,
    consequences TEXT NOT NULL,
    alternatives TEXT,
    
    -- Relationships
    supersedes_adr_id UUID REFERENCES architecture_decisions(adr_id),
    related_adrs UUID[],
    
    -- Metadata
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_adrs_spec ON architecture_decisions(spec_id);
CREATE INDEX idx_adrs_workflow ON architecture_decisions(workflow_id);
CREATE INDEX idx_adrs_status ON architecture_decisions(status);

-- =============================================================================
-- EVALUATIONS
-- =============================================================================

CREATE TABLE evaluations (
    eval_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id),
    task_id UUID NOT NULL REFERENCES tasks(task_id),
    agent_id VARCHAR(255) REFERENCES agents(agent_id),
    
    output_type VARCHAR(100) NOT NULL,  -- specification, code, test, review
    
    -- Overall score
    overall_score DECIMAL(5, 2) NOT NULL,  -- 0-100
    pass_threshold DECIMAL(5, 2) NOT NULL DEFAULT 70,
    passed BOOLEAN NOT NULL,
    
    -- Dimension scores
    accuracy_score DECIMAL(5, 2),
    completeness_score DECIMAL(5, 2),
    security_score DECIMAL(5, 2),
    maintainability_score DECIMAL(5, 2),
    performance_score DECIMAL(5, 2),
    testability_score DECIMAL(5, 2),
    
    -- Detailed metrics
    metrics JSONB NOT NULL,
    
    -- Feedback
    feedback TEXT,
    recommendations TEXT[],
    
    -- Issues found
    issues JSONB DEFAULT '[]',
    critical_issues_count INTEGER DEFAULT 0,
    
    -- Evaluator info
    evaluator_agent_id VARCHAR(255),
    evaluation_model VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_evaluations_workflow ON evaluations(workflow_id);
CREATE INDEX idx_evaluations_task ON evaluations(task_id);
CREATE INDEX idx_evaluations_agent ON evaluations(agent_id);
CREATE INDEX idx_evaluations_score ON evaluations(overall_score DESC);
CREATE INDEX idx_evaluations_passed ON evaluations(passed);
CREATE INDEX idx_evaluations_created ON evaluations(created_at DESC);

-- =============================================================================
-- AGENT PERFORMANCE HISTORY
-- =============================================================================

CREATE TABLE agent_performance (
    perf_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id),
    task_category task_category NOT NULL,
    
    -- Performance metrics
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    total_count INTEGER NOT NULL DEFAULT 0,
    success_rate DECIMAL(5, 2),
    
    -- Resource usage
    avg_duration_ms INTEGER,
    p50_duration_ms INTEGER,
    p95_duration_ms INTEGER,
    avg_cost_usd DECIMAL(10, 4),
    total_cost_usd DECIMAL(10, 4),
    
    -- Quality metrics
    avg_evaluation_score DECIMAL(5, 2),
    min_evaluation_score DECIMAL(5, 2),
    max_evaluation_score DECIMAL(5, 2),
    
    -- Time period
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Metadata
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(agent_id, task_category, period_start)
);

CREATE INDEX idx_agent_perf_agent ON agent_performance(agent_id);
CREATE INDEX idx_agent_perf_category ON agent_performance(task_category);
CREATE INDEX idx_agent_perf_success_rate ON agent_performance(success_rate DESC);
CREATE INDEX idx_agent_perf_period ON agent_performance(period_start DESC);

-- =============================================================================
-- CODEBASE EMBEDDINGS
-- =============================================================================

CREATE TABLE codebase_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    
    repository VARCHAR(500) NOT NULL,
    branch VARCHAR(255) NOT NULL DEFAULT 'main',
    commit_sha VARCHAR(40),
    
    file_path VARCHAR(1000) NOT NULL,
    chunk_index INTEGER NOT NULL,
    
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    
    -- Metadata
    language VARCHAR(50),
    file_type VARCHAR(50),
    line_start INTEGER,
    line_end INTEGER,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(repository, file_path, chunk_index, commit_sha)
);

CREATE INDEX idx_codebase_tenant ON codebase_embeddings(tenant_id);
CREATE INDEX idx_codebase_repo ON codebase_embeddings(repository);
CREATE INDEX idx_codebase_file ON codebase_embeddings(repository, file_path);
CREATE INDEX idx_codebase_embedding ON codebase_embeddings USING ivfflat (embedding vector_cosine_ops);

-- =============================================================================
-- LESSONS LEARNED
-- =============================================================================

CREATE TABLE lessons_learned (
    lesson_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id),
    
    category VARCHAR(100) NOT NULL,  -- coding, testing, deployment, architecture, etc.
    
    -- Lesson content
    situation TEXT NOT NULL,
    lesson TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    
    -- Impact
    impact severity_level,
    
    -- Context
    related_workflow_ids UUID[],
    tags TEXT[],
    
    -- Embeddings for semantic search
    embedding vector(1536),
    
    -- Usage tracking
    times_referenced INTEGER DEFAULT 0,
    last_referenced TIMESTAMP,
    
    -- Metadata
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lessons_tenant ON lessons_learned(tenant_id);
CREATE INDEX idx_lessons_category ON lessons_learned(category);
CREATE INDEX idx_lessons_impact ON lessons_learned(impact);
CREATE INDEX idx_lessons_embedding ON lessons_learned USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_lessons_tags ON lessons_learned USING gin(tags);

-- =============================================================================
-- APPROVALS
-- =============================================================================

CREATE TABLE approvals (
    approval_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id),
    task_id UUID REFERENCES tasks(task_id),
    
    operation_type VARCHAR(100) NOT NULL,  -- deployment, migration, merge, etc.
    status approval_status NOT NULL DEFAULT 'pending',
    
    -- Approval request
    request_description TEXT NOT NULL,
    risk_assessment JSONB,
    impact_analysis TEXT,
    rollback_plan TEXT,
    artifacts TEXT[],
    
    -- Approval configuration
    required_approvers TEXT[] NOT NULL,
    approval_threshold INTEGER DEFAULT 1,  -- Number of approvals needed
    timeout_hours INTEGER DEFAULT 24,
    timeout_action VARCHAR(50) DEFAULT 'deny',  -- deny, approve, escalate
    
    -- Approvals received
    approvers JSONB DEFAULT '[]',  -- [{user, decision, reason, timestamp}]
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    
    -- Outcome
    final_decision approval_status,
    decided_by VARCHAR(255),
    decided_at TIMESTAMP,
    decision_reason TEXT,
    
    -- Timing
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_approvals_workflow ON approvals(workflow_id);
CREATE INDEX idx_approvals_status ON approvals(status);
CREATE INDEX idx_approvals_requested ON approvals(requested_at DESC);
CREATE INDEX idx_approvals_expires ON approvals(expires_at);

-- =============================================================================
-- MODEL USAGE
-- =============================================================================

CREATE TABLE model_usage (
    usage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflows(workflow_id),
    task_id UUID REFERENCES tasks(task_id),
    agent_id VARCHAR(255) REFERENCES agents(agent_id),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    
    -- Model info
    model_id VARCHAR(100) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    
    -- Usage metrics
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    
    -- Cost
    cost_usd DECIMAL(10, 6) NOT NULL,
    
    -- Performance
    latency_ms INTEGER,
    
    -- Context
    task_category task_category,
    
    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_model_usage_workflow ON model_usage(workflow_id);
CREATE INDEX idx_model_usage_tenant ON model_usage(tenant_id);
CREATE INDEX idx_model_usage_agent ON model_usage(agent_id);
CREATE INDEX idx_model_usage_model ON model_usage(model_id);
CREATE INDEX idx_model_usage_created ON model_usage(created_at DESC);
CREATE INDEX idx_model_usage_cost ON model_usage(cost_usd DESC);

-- =============================================================================
-- AUDIT LOGS
-- =============================================================================

CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Actor
    actor_type VARCHAR(50) NOT NULL,  -- user, agent, system
    actor_id VARCHAR(255) NOT NULL,
    tenant_id UUID REFERENCES tenants(tenant_id),
    
    -- Action
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    
    -- Outcome
    outcome VARCHAR(50) NOT NULL,  -- success, failure, denied
    
    -- Policy decision
    policy_decision JSONB,
    policies_evaluated TEXT[],
    
    -- Details
    details JSONB DEFAULT '{}',
    
    -- Context
    workflow_id UUID,
    task_id UUID,
    ip_address INET,
    user_agent TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Partitioning for efficient queries and retention
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_outcome ON audit_logs(outcome);

-- =============================================================================
-- POLICY VIOLATIONS
-- =============================================================================

CREATE TABLE policy_violations (
    violation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Violator
    agent_id VARCHAR(255),
    workflow_id UUID,
    task_id UUID,
    tenant_id UUID REFERENCES tenants(tenant_id),
    
    -- Violation details
    policy_name VARCHAR(255) NOT NULL,
    severity severity_level NOT NULL,
    violation_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Context
    attempted_action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    
    -- Policy decision
    policy_decision JSONB NOT NULL,
    
    -- Response
    action_taken VARCHAR(100) NOT NULL,  -- blocked, warned, logged
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_violations_timestamp ON policy_violations(timestamp DESC);
CREATE INDEX idx_violations_agent ON policy_violations(agent_id);
CREATE INDEX idx_violations_workflow ON policy_violations(workflow_id);
CREATE INDEX idx_violations_severity ON policy_violations(severity);
CREATE INDEX idx_violations_policy ON policy_violations(policy_name);

-- =============================================================================
-- COST TRACKING
-- =============================================================================

CREATE TABLE cost_tracking (
    cost_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    workflow_id UUID REFERENCES workflows(workflow_id),
    
    -- Time period
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Cost breakdown
    llm_cost_usd DECIMAL(10, 4) DEFAULT 0,
    compute_cost_usd DECIMAL(10, 4) DEFAULT 0,
    storage_cost_usd DECIMAL(10, 4) DEFAULT 0,
    network_cost_usd DECIMAL(10, 4) DEFAULT 0,
    other_cost_usd DECIMAL(10, 4) DEFAULT 0,
    total_cost_usd DECIMAL(10, 4) NOT NULL,
    
    -- Usage metrics
    total_tokens BIGINT DEFAULT 0,
    compute_hours DECIMAL(10, 2) DEFAULT 0,
    storage_gb DECIMAL(10, 2) DEFAULT 0,
    network_gb DECIMAL(10, 2) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_cost_tenant ON cost_tracking(tenant_id);
CREATE INDEX idx_cost_workflow ON cost_tracking(workflow_id);
CREATE INDEX idx_cost_period ON cost_tracking(period_start DESC);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Calculate workflow progress
CREATE OR REPLACE FUNCTION calculate_workflow_progress()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE workflows
    SET 
        total_tasks = (SELECT COUNT(*) FROM tasks WHERE workflow_id = NEW.workflow_id),
        completed_tasks = (SELECT COUNT(*) FROM tasks WHERE workflow_id = NEW.workflow_id AND status = 'completed'),
        failed_tasks = (SELECT COUNT(*) FROM tasks WHERE workflow_id = NEW.workflow_id AND status = 'failed')
    WHERE workflow_id = NEW.workflow_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workflow_progress AFTER INSERT OR UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION calculate_workflow_progress();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active workflows summary
CREATE VIEW active_workflows_summary AS
SELECT 
    w.workflow_id,
    w.tenant_id,
    w.name,
    w.status,
    w.total_tasks,
    w.completed_tasks,
    w.failed_tasks,
    ROUND((w.completed_tasks::DECIMAL / NULLIF(w.total_tasks, 0)) * 100, 2) as progress_percentage,
    w.cost_consumed_usd,
    w.tokens_consumed,
    w.started_at,
    w.estimated_completion,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - w.started_at))/60 as running_minutes
FROM workflows w
WHERE w.status IN ('pending', 'in_progress');

-- Agent performance summary
CREATE VIEW agent_performance_summary AS
SELECT 
    a.agent_id,
    a.agent_type,
    a.status,
    a.current_task_count,
    a.max_concurrent_tasks,
    a.total_tasks_completed,
    a.total_tasks_failed,
    ROUND((a.total_tasks_completed::DECIMAL / NULLIF(a.total_tasks_completed + a.total_tasks_failed, 0)) * 100, 2) as success_rate,
    a.avg_evaluation_score,
    a.avg_task_duration_ms,
    a.avg_cost_per_task_usd,
    a.last_heartbeat,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - a.last_heartbeat))/60 as minutes_since_heartbeat
FROM agents a;

-- Cost summary by tenant
CREATE VIEW tenant_cost_summary AS
SELECT 
    t.tenant_id,
    t.name as tenant_name,
    t.tier,
    SUM(w.cost_consumed_usd) as total_cost_usd,
    SUM(w.tokens_consumed) as total_tokens,
    COUNT(DISTINCT w.workflow_id) as workflow_count,
    AVG(w.cost_consumed_usd) as avg_cost_per_workflow,
    MAX(w.cost_consumed_usd) as max_workflow_cost
FROM tenants t
LEFT JOIN workflows w ON t.tenant_id = w.tenant_id
WHERE t.status = 'active'
GROUP BY t.tenant_id, t.name, t.tier;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Create default system tenant
INSERT INTO tenants (tenant_id, name, status, tier, resource_limits)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'System',
    'active',
    'enterprise',
    '{"max_concurrent_workflows": 1000, "max_agents_per_workflow": 100, "max_cost_per_month_usd": 100000, "max_tokens_per_day": 1000000000, "storage_limit_gb": 10000}'
);

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE workflows IS 'Stores workflow execution state and metadata';
COMMENT ON TABLE tasks IS 'Individual tasks within workflows';
COMMENT ON TABLE agents IS 'Agent registry and health tracking';
COMMENT ON TABLE specifications IS 'Technical specifications generated by spec agent';
COMMENT ON TABLE evaluations IS 'Quality evaluations of agent outputs';
COMMENT ON TABLE audit_logs IS 'Immutable audit trail of all system actions';
COMMENT ON TABLE policy_violations IS 'Record of policy enforcement actions';
COMMENT ON TABLE model_usage IS 'Tracking of LLM API usage and costs';

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
