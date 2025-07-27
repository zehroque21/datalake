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
  value       = data.aws_iam_role.airflow_ec2_role.arn
}

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = data.aws_s3_bucket.datalake.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = data.aws_s3_bucket.datalake.arn
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


output "airflow_access_info" {
  description = "Information about accessing Airflow web UI"
  value = var.enable_airflow_web_access ? format(<<-EOT
    AIRFLOW WEB UI ACCESS:
    
    🌐 URL: http://%s:8080
    👤 Username: admin
    🔑 Password: Check /home/airflow/admin_password.txt on the instance
    
    🔒 SECURITY CONFIGURATION:
    - Allowed IP: %s
    - Web access: %s
    
    📋 TO ACCESS AIRFLOW:
    
    Option 1 - Direct Access (if your IP is allowed):
    1. Ensure your IP (%s) is correct
    2. Access: http://%s:8080
    
    Option 2 - Port Forwarding via Session Manager (more secure):
    1. Connect via Session Manager:
       aws ssm start-session --target %s
    2. Set up port forwarding:
       aws ssm start-session \
         --target %s \
         --document-name AWS-StartPortForwardingSession \
         --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}'
    3. Access: http://localhost:8080
    
    🔐 TO GET ADMIN PASSWORD:
    1. Connect to instance via Session Manager
    2. Run: sudo cat /home/airflow/admin_password.txt
    
    ⚠️  SECURITY RECOMMENDATIONS:
    - Change allowed_ip_for_airflow to your specific IP (x.x.x.x/32)
    - Set enable_airflow_web_access = false for maximum security
    - Use port forwarding instead of direct access when possible
  EOT
  , aws_instance.airflow_vm.private_ip, var.allowed_ip_for_airflow, "ENABLED", var.allowed_ip_for_airflow, aws_instance.airflow_vm.private_ip, aws_instance.airflow_vm.id, aws_instance.airflow_vm.id) : "Airflow web access is DISABLED for security. Set enable_airflow_web_access = true to enable."
}

output "security_recommendations" {
  description = "Security recommendations for production use"
  value       = <<-EOT
    🔒 SECURITY RECOMMENDATIONS:
    
    1. RESTRICT AIRFLOW ACCESS:
       - Set allowed_ip_for_airflow = "YOUR_IP/32"
       - Consider setting enable_airflow_web_access = false
    
    2. USE SECURE ACCESS METHODS:
       - Prefer Session Manager over direct IP access
       - Use port forwarding for Airflow UI access
    
    3. MONITOR AND AUDIT:
       - Check CloudWatch logs regularly
       - Monitor access patterns
       - Rotate admin password periodically
    
    4. PRODUCTION HARDENING:
       - Consider using Application Load Balancer with authentication
       - Implement VPN access for team members
       - Set up proper backup and disaster recovery
    
    Current Configuration:
    - Airflow web access: ${var.enable_airflow_web_access ? "ENABLED" : "DISABLED"}
    - Allowed IP: ${var.allowed_ip_for_airflow}
    - Instance ID: ${aws_instance.airflow_vm.id}
  EOT
}

