variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "bucket_name" {
  description = "S3 bucket name for the datalake"
  type        = string
  default     = "datalake-bucket-for-airflow-and-delta"
}


variable "allowed_ip_for_airflow" {
  description = "IP address allowed to access Airflow web UI (format: x.x.x.x/32)"
  type        = string
  default     = "0.0.0.0/0" # WARNING: Default allows access from anywhere - CHANGE THIS!

  validation {
    condition     = can(cidrhost(var.allowed_ip_for_airflow, 0))
    error_message = "The allowed_ip_for_airflow must be a valid CIDR block (e.g., 203.0.113.1/32)."
  }
}

variable "enable_airflow_web_access" {
  description = "Enable web access to Airflow UI (set to false for maximum security)"
  type        = bool
  default     = true
}

