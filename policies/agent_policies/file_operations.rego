# Multi-Agent Platform - File Operations Policy
# This policy controls what file operations agents can perform

package agent.file_operations

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# =============================================================================
# READ OPERATIONS
# =============================================================================

# Allow reading from workspace directories
allow if {
    input.operation == "read"
    startswith(input.path, "/workspace/")
    not is_sensitive_file(input.path)
    not is_protected_path(input.path)
}

# Allow reading from temporary directories
allow if {
    input.operation == "read"
    startswith(input.path, "/tmp/")
}

# =============================================================================
# WRITE OPERATIONS
# =============================================================================

# Allow writing to workspace (with size limit)
allow if {
    input.operation == "write"
    startswith(input.path, "/workspace/")
    not is_protected_path(input.path)
    not is_sensitive_file(input.path)
    input.file_size < 10485760  # 10MB limit
    valid_file_type(input.path)
}

# Allow writing to temporary directories
allow if {
    input.operation == "write"
    startswith(input.path, "/tmp/")
    input.file_size < 104857600  # 100MB limit for temp files
}

# =============================================================================
# DELETE OPERATIONS
# =============================================================================

# Allow deleting from workspace (excluding protected paths)
allow if {
    input.operation == "delete"
    startswith(input.path, "/workspace/")
    not is_protected_path(input.path)
    not is_critical_file(input.path)
}

# Allow deleting from temporary directories
allow if {
    input.operation == "delete"
    startswith(input.path, "/tmp/")
}

# =============================================================================
# DENY RULES (explicit denials with reasons)
# =============================================================================

# Deny access to system paths
deny[msg] if {
    prohibited_prefixes := [
        "/etc/",
        "/sys/",
        "/proc/",
        "/root/",
        "/boot/",
        "/dev/"
    ]
    some prefix in prohibited_prefixes
    startswith(input.path, prefix)
    msg := sprintf("Access denied: System path %s is prohibited", [input.path])
}

# Deny access to sensitive files
deny[msg] if {
    is_sensitive_file(input.path)
    msg := sprintf("Access denied: File contains sensitive data %s", [input.path])
}

# Deny write operations on protected paths
deny[msg] if {
    input.operation in ["write", "delete"]
    is_protected_path(input.path)
    msg := sprintf("Access denied: Path %s is protected from modification", [input.path])
}

# Deny files that are too large
deny[msg] if {
    input.operation == "write"
    input.file_size > 10485760
    msg := sprintf("Access denied: File size %d bytes exceeds limit of 10MB", [input.file_size])
}

# Deny unauthorized file types
deny[msg] if {
    input.operation == "write"
    not valid_file_type(input.path)
    msg := sprintf("Access denied: File type not allowed for %s", [input.path])
}

# Deny operations outside tenant workspace
deny[msg] if {
    not startswith(input.path, "/workspace/")
    not startswith(input.path, "/tmp/")
    msg := sprintf("Access denied: Path %s is outside allowed directories", [input.path])
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Check if file is sensitive (contains secrets, keys, passwords)
is_sensitive_file(path) if {
    sensitive_patterns := [
        "*.key",
        "*.pem",
        "*.p12",
        "*.pfx",
        "*secret*",
        "*password*",
        "*token*",
        ".env",
        ".env.*",
        "*.credential*",
        "id_rsa",
        "id_dsa"
    ]
    some pattern in sensitive_patterns
    glob.match(pattern, ["**"], path)
}

# Check if path is protected from modification
is_protected_path(path) if {
    protected_prefixes := [
        "/workspace/.git/",
        "/workspace/node_modules/",
        "/workspace/.next/",
        "/workspace/build/",
        "/workspace/dist/",
        "/workspace/vendor/"
    ]
    some prefix in protected_prefixes
    startswith(path, prefix)
}

# Check if file is critical (should not be deleted)
is_critical_file(path) if {
    critical_files := [
        "/workspace/package.json",
        "/workspace/package-lock.json",
        "/workspace/requirements.txt",
        "/workspace/pyproject.toml",
        "/workspace/Cargo.toml",
        "/workspace/go.mod",
        "/workspace/.gitignore",
        "/workspace/README.md",
        "/workspace/LICENSE"
    ]
    path in critical_files
}

# Check if file type is allowed
valid_file_type(path) if {
    allowed_extensions := [
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".swift",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".rb",
        ".php",
        ".sql",
        ".sh",
        ".bash",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".md",
        ".txt",
        ".html",
        ".css",
        ".scss",
        ".sass",
        ".svg",
        ".xml",
        ".proto"
    ]
    some ext in allowed_extensions
    endswith(path, ext)
}

# Check if operation is within rate limits
within_rate_limit if {
    # Get recent operations count from cache
    recent_ops := data.rate_limits[input.agent_id].file_operations_last_minute
    recent_ops < 1000  # Max 1000 file operations per minute
}

# =============================================================================
# AUDIT REQUIREMENTS
# =============================================================================

# All file operations must be audited
audit_required := true

# Determine severity level for audit log
audit_severity := severity if {
    input.operation == "delete"
    is_critical_file(input.path)
    severity := "high"
} else := severity if {
    input.operation in ["write", "delete"]
    severity := "medium"
} else := "low"

# =============================================================================
# POLICY METADATA
# =============================================================================

policy_metadata := {
    "name": "file_operations",
    "version": "1.0.0",
    "description": "Controls agent file system access",
    "owner": "security-team",
    "last_updated": "2026-06-18"
}
