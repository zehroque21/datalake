output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.airflow_vm.id
}

output "instance_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.airflow_vm.private_ip
}

output "instance_state" {
  description = "State of the EC2 instance"
  value       = aws_instance.airflow_vm.instance_state
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.airflow_sg.id
}

output "iam_role_arn" {
  description = "ARN of the IAM role for the EC2 instance"
  value       = aws_iam_role.airflow_ec2_role.arn
}

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = data.aws_s3_bucket.datalake.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = data.aws_s3_bucket.datalake.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for monitoring"
  value       = aws_cloudwatch_log_group.airflow_logs.name
}

output "access_instructions" {
  description = "Instructions for secure access to the instance"
  value       = <<-EOT
    SECURE ACCESS INSTRUCTIONS:
    
    This instance has NO SSH access for security reasons.
    
    To access the instance securely, use AWS Systems Manager Session Manager:
    
    1. Install AWS CLI and configure with your credentials
    2. Use Session Manager to connect:
       aws ssm start-session --target ${aws_instance.airflow_vm.id}
    
    3. Or use the AWS Console:
       - Go to EC2 → Instances
       - Select the instance
       - Click "Connect" → "Session Manager"
    
    Instance ID: ${aws_instance.airflow_vm.id}
    Private IP: ${aws_instance.airflow_vm.private_ip}
  EOT
}

