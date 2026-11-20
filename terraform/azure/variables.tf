variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  default     = "e101a3ca-fcc4-42a1-a143-b3654461f0d2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cyber-analyzer"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "cyber-analyzer-rg"
}

variable "openai_api_key" {
  description = "OpenAI API key for the application"
  type        = string
  sensitive   = true
  default     = ""
}

variable "gemini_api_key" {
  description = "Google Gemini API key for the application"
  type        = string
  sensitive   = true
  default     = ""
}

variable "gemini_model" {
  description = "Google Gemini model name"
  type        = string
  default     = "gemini-3.5-flash"
}

variable "semgrep_app_token" {
  description = "Semgrep app token for security scanning"
  type        = string
  sensitive   = true
  default     = ""
}

variable "docker_image_tag" {
  description = "Tag for the Docker image"
  type        = string
  default     = "latest"
}