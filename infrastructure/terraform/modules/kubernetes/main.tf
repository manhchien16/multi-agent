# Multi-Agent Platform - Kubernetes Cluster Module
# This module creates a production-ready Kubernetes cluster with multiple node pools

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.27"
}

# Network
resource "google_compute_network" "vpc" {
  name                    = "${var.cluster_name}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.cluster_name}-subnet"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.region
  network       = google_compute_network.vpc.id
  
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }
  
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/16"
  }
  
  project = var.project_id
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id
  
  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  
  # Kubernetes version
  min_master_version = var.kubernetes_version
  
  # Network configuration
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name
  
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
  
  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    
    horizontal_pod_autoscaling {
      disabled = false
    }
    
    network_policy_config {
      disabled = false
    }
    
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }
  
  # Network policy
  network_policy {
    enabled  = true
    provider = "PROVIDER_UNSPECIFIED"
  }
  
  # Master auth
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }
  
  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }
  
  # Binary authorization
  binary_authorization {
    evaluation_mode = var.environment == "production" ? "PROJECT_SINGLETON_POLICY_ENFORCE" : "DISABLED"
  }
  
  # Logging and monitoring
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }
  
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
    
    managed_prometheus {
      enabled = true
    }
  }
  
  # Resource labels
  resource_labels = {
    environment = var.environment
    managed_by  = "terraform"
    platform    = "multi-agent"
  }
}

# Control Plane Node Pool
resource "google_container_node_pool" "control_plane" {
  name       = "control-plane-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  project    = var.project_id
  
  # Node count
  initial_node_count = var.environment == "production" ? 3 : 2
  
  autoscaling {
    min_node_count = var.environment == "production" ? 3 : 2
    max_node_count = var.environment == "production" ? 10 : 5
  }
  
  # Node configuration
  node_config {
    machine_type = var.environment == "production" ? "n2-standard-8" : "n2-standard-4"
    disk_size_gb = 100
    disk_type    = "pd-standard"
    
    # Use Container-Optimized OS
    image_type = "COS_CONTAINERD"
    
    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    # Labels
    labels = {
      pool        = "control-plane"
      environment = var.environment
    }
    
    # Taints - prevent workloads from running on control plane nodes
    taint {
      key    = "pool"
      value  = "control-plane"
      effect = "NO_SCHEDULE"
    }
    
    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }
    
    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    # Security
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
  
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Execution Plane Node Pool (for agents)
resource "google_container_node_pool" "execution_plane" {
  name       = "execution-plane-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  project    = var.project_id
  
  initial_node_count = var.environment == "production" ? 5 : 2
  
  autoscaling {
    min_node_count = var.environment == "production" ? 5 : 2
    max_node_count = var.environment == "production" ? 200 : 50
  }
  
  node_config {
    machine_type = "n2-standard-4"
    disk_size_gb = 100
    disk_type    = "pd-standard"
    
    # Use preemptible instances for cost savings in non-production
    preemptible  = var.environment != "production"
    
    image_type = "COS_CONTAINERD"
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    labels = {
      pool        = "execution-plane"
      environment = var.environment
      preemptible = var.environment != "production" ? "true" : "false"
    }
    
    taint {
      key    = "pool"
      value  = "execution-plane"
      effect = "NO_SCHEDULE"
    }
    
    metadata = {
      disable-legacy-endpoints = "true"
    }
    
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
  
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Data Plane Node Pool (for databases, caches, message queues)
resource "google_container_node_pool" "data_plane" {
  name       = "data-plane-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  project    = var.project_id
  
  initial_node_count = 3
  
  autoscaling {
    min_node_count = 3
    max_node_count = var.environment == "production" ? 20 : 10
  }
  
  node_config {
    machine_type = var.environment == "production" ? "n2-highmem-16" : "n2-highmem-8"
    disk_size_gb = 500
    disk_type    = "pd-ssd"  # SSD for databases
    
    # Never use preemptible for data plane
    preemptible = false
    
    image_type = "COS_CONTAINERD"
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    labels = {
      pool        = "data-plane"
      environment = var.environment
    }
    
    taint {
      key    = "pool"
      value  = "data-plane"
      effect = "NO_SCHEDULE"
    }
    
    metadata = {
      disable-legacy-endpoints = "true"
    }
    
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
    
    # Local SSDs for high-performance workloads
    local_ssd_count = var.environment == "production" ? 2 : 0
  }
  
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Outputs
output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "network_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "subnet_name" {
  description = "Subnet name"
  value       = google_compute_subnetwork.subnet.name
}
