# Security Policy

## Overview

This repository implements security best practices for a data engineering platform on AWS. Security is a top priority, and this document outlines the measures taken to protect the infrastructure and data.

## Security Measures Implemented

### 🔒 Infrastructure Security

#### Network Security
- **No SSH Access**: EC2 instances have NO SSH access configured for security
- **Restrictive Security Groups**: Only necessary ports are opened
- **Private Networking**: Instances use private IPs where possible
- **Firewall Configuration**: UFW firewall enabled with deny-by-default policy

#### Access Control
- **AWS Systems Manager**: Secure access via Session Manager instead of SSH
- **IAM Roles**: Least privilege access with specific S3 permissions
- **No Public Keys**: No SSH key pairs associated with instances
- **Instance Profiles**: Secure credential management for AWS services

#### Data Protection
- **EBS Encryption**: All storage volumes are encrypted at rest
- **S3 Security**: Bucket access restricted to specific IAM roles
- **CloudWatch Logging**: Comprehensive monitoring and logging
- **Automatic Updates**: Security patches applied automatically

### 🛡️ Application Security

#### Airflow Security
- **Local Binding**: Airflow web UI only accessible on localhost (127.0.0.1)
- **Authentication**: Password-based authentication enabled
- **Secure Configuration**: Hardened airflow.cfg with security settings
- **Service Isolation**: Airflow runs as dedicated user with limited privileges
- **Random Passwords**: Admin passwords generated securely

#### Code Security
- **No Hardcoded Secrets**: All sensitive data managed via AWS services
- **Environment Isolation**: Virtual environments for Python dependencies
- **Secure Defaults**: Security-first configuration templates

### 📋 Repository Security

#### Secrets Management
- **GitHub Secrets**: AWS credentials stored as encrypted repository secrets
- **No Credentials in Code**: Zero tolerance for hardcoded credentials
- **Comprehensive .gitignore**: Prevents accidental commit of sensitive files

#### Access Control
- **Branch Protection**: Main branch protected from direct pushes
- **Review Requirements**: Changes require review before merge
- **Automated Scanning**: Security vulnerabilities detected automatically

## Access Methods

### Secure Instance Access

Since SSH is disabled for security, use these methods to access EC2 instances:

#### Method 1: AWS Systems Manager Session Manager (Recommended)
```bash
# Install AWS CLI and configure credentials
aws configure

# Start secure session
aws ssm start-session --target <INSTANCE_ID>
```

#### Method 2: AWS Console
1. Go to EC2 → Instances
2. Select your instance
3. Click "Connect" → "Session Manager"
4. Click "Connect"

### Airflow Web UI Access

The Airflow web UI is only accessible locally for security. To access it:

#### Port Forwarding via Session Manager
```bash
# Forward local port 8080 to instance
aws ssm start-session \
    --target <INSTANCE_ID> \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}'
```

Then access `http://localhost:8080` in your browser.

## Security Best Practices

### For Developers

1. **Never commit secrets**: Use environment variables or AWS services
2. **Regular updates**: Keep dependencies and systems updated
3. **Least privilege**: Request only necessary permissions
4. **Code review**: All changes must be reviewed
5. **Secure coding**: Follow OWASP guidelines

### For Operations

1. **Monitor access**: Review CloudWatch logs regularly
2. **Rotate credentials**: Regular rotation of access keys
3. **Backup strategy**: Secure backup and recovery procedures
4. **Incident response**: Have a plan for security incidents
5. **Compliance**: Follow industry standards and regulations

### For Infrastructure

1. **Network segmentation**: Isolate different environments
2. **Encryption everywhere**: Encrypt data at rest and in transit
3. **Access logging**: Log all access attempts
4. **Regular audits**: Periodic security assessments
5. **Disaster recovery**: Test recovery procedures regularly

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** create a public GitHub issue
2. Contact the repository maintainer directly
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before disclosure

## Security Checklist

Before deploying to production, ensure:

- [ ] All secrets are managed via AWS services or GitHub Secrets
- [ ] No hardcoded credentials in code
- [ ] Security groups follow least privilege principle
- [ ] EBS volumes are encrypted
- [ ] CloudWatch logging is enabled
- [ ] Systems Manager agent is installed and running
- [ ] Firewall is configured and enabled
- [ ] Automatic security updates are enabled
- [ ] IAM roles follow least privilege principle
- [ ] No SSH keys are associated with instances

## Compliance and Standards

This infrastructure follows:

- **AWS Well-Architected Framework** - Security Pillar
- **NIST Cybersecurity Framework**
- **CIS Controls** for AWS
- **OWASP Top 10** for application security

## Security Tools and Monitoring

### Implemented
- AWS CloudWatch for monitoring and logging
- AWS Systems Manager for secure access
- UFW firewall for network protection
- Automatic security updates

### Recommended Additional Tools
- AWS GuardDuty for threat detection
- AWS Config for compliance monitoring
- AWS Security Hub for centralized security findings
- AWS Inspector for vulnerability assessments

## Emergency Procedures

### In Case of Security Incident

1. **Immediate Response**
   - Isolate affected systems
   - Preserve evidence
   - Document the incident

2. **Investigation**
   - Review CloudWatch logs
   - Check access patterns
   - Identify scope of impact

3. **Recovery**
   - Apply security patches
   - Rotate compromised credentials
   - Update security configurations

4. **Post-Incident**
   - Conduct lessons learned
   - Update security procedures
   - Implement additional controls

## Contact Information

For security-related questions or concerns:
- Repository Maintainer: [Amado Roque](https://github.com/zehroque21)
- LinkedIn: [Amado Roque](https://www.linkedin.com/in/amado-roque/)

---

**Remember: Security is everyone's responsibility. When in doubt, choose the more secure option.**

