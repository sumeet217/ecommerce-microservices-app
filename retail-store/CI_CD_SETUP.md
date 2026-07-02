# GitLab CI/CD Setup Guide

This document describes the DevSecOps CI/CD pipeline configuration for the Retail Store Microservices project.

## Pipeline Overview

The pipeline follows DevSecOps best practices with the following stages:

1. **Clone** - Repository cloning and validation
2. **Test** - Unit tests, coverage, and linting
3. **Security Scan** - Multiple security scanning tools
4. **Quality Gate** - SonarQube and security quality gates
5. **Build** - Artifact creation
6. **Deploy** - AWS EC2 deployment

## Pipeline Features

### Testing & Quality
- ✅ Unit tests with pytest for all 5 microservices
- ✅ Code coverage reporting (Cobertura format)
- ✅ Code linting (flake8, pylint, black, isort)
- ✅ JUnit test reports

### Security Scanning
- ✅ **SonarQube** - Code quality and security analysis
- ✅ **OWASP Dependency Check** - Vulnerable dependency detection
- ✅ **Bandit** - Python security linting
- ✅ **Trivy** - Filesystem vulnerability scanning

### Quality Gates
- ✅ SonarQube Quality Gate enforcement
- ✅ Security gate with critical vulnerability checks
- ✅ Automatic pipeline failure on quality issues

### Deployment
- ✅ Automated EC2 deployment via SSH
- ✅ Blue-green deployment pattern support
- ✅ Automatic backup before deployment
- ✅ Health checks post-deployment
- ✅ Manual rollback capability

## Required GitLab CI/CD Variables

Configure these variables in **Settings > CI/CD > Variables** in your GitLab project:

### SonarQube Configuration
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `SONAR_HOST_URL` | Variable | SonarQube server URL | `https://sonarqube.example.com` |
| `SONAR_TOKEN` | Variable (Masked) | SonarQube authentication token | `squ_abc123...` |

### AWS Configuration
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `AWS_DEFAULT_REGION` | Variable | AWS region for deployment | `us-east-1` |
| `EC2_HOST` | Variable | EC2 instance IP or hostname | `3.123.45.67` or `app.example.com` |
| `EC2_USER` | Variable | SSH user for EC2 | `ubuntu` or `ec2-user` |
| `SSH_PRIVATE_KEY` | File (Masked) | SSH private key for EC2 access | Contents of your private key |

### Optional Variables
| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `PYTHON_VERSION` | Variable | Python version to use | `3.11` |

## Setup Instructions

### 1. SonarQube Setup

1. Install and configure SonarQube server (or use SonarCloud)
2. Create a new project in SonarQube
3. Generate an authentication token
4. Add `SONAR_HOST_URL` and `SONAR_TOKEN` to GitLab CI/CD variables

### 2. AWS EC2 Setup

#### Prepare EC2 Instance

```bash
# SSH into your EC2 instance
ssh ubuntu@<EC2_HOST>

# Install Python and dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv postgresql-client

# Create deployment directory
sudo mkdir -p /opt/retail-store
sudo chown ubuntu:ubuntu /opt/retail-store

# Install and configure systemd services for each microservice
# (Create service files as shown below)
```

#### Create Systemd Service Files

Create service files for each microservice (example for auth service):

```bash
sudo nano /etc/systemd/system/retail-store-auth.service
```

```ini
[Unit]
Description=Retail Store Auth Service
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/retail-store/services/auth
Environment="PATH=/opt/retail-store/services/auth/venv/bin"
ExecStart=/opt/retail-store/services/auth/venv/bin/gunicorn \
          --config gunicorn.conf.py \
          auth_service.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Repeat for all services: catalog, cart, orders, ui

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable retail-store-auth
sudo systemctl enable retail-store-catalog
sudo systemctl enable retail-store-cart
sudo systemctl enable retail-store-orders
sudo systemctl enable retail-store-ui
```

#### Configure SSH Access

```bash
# Generate SSH key pair on your local machine
ssh-keygen -t ed25519 -C "gitlab-ci" -f gitlab-ci-key

# Copy public key to EC2
ssh-copy-id -i gitlab-ci-key.pub ubuntu@<EC2_HOST>

# Add private key to GitLab CI/CD variables
# Copy contents of gitlab-ci-key (private key) to SSH_PRIVATE_KEY variable
```

### 3. GitLab Runner Setup

Ensure you have GitLab runners with Docker executor:

```bash
# Register a GitLab runner
gitlab-runner register \
  --url "https://gitlab.com/" \
  --registration-token "YOUR_TOKEN" \
  --executor "docker" \
  --docker-image "python:3.11-slim" \
  --description "docker-runner" \
  --tag-list "docker" \
  --run-untagged="false" \
  --locked="false"
```

### 4. Project Configuration Files

Ensure these files are present in your repository:
- ✅ `.gitlab-ci.yml` - Main pipeline configuration
- ✅ `sonar-project.properties` - SonarQube configuration
- ✅ `suppression.xml` - OWASP suppression file

## Pipeline Execution

### Automatic Triggers
- **Push to any branch** - Runs clone, test stages
- **Merge requests** - Full pipeline including security scans
- **Push to main/develop** - Full pipeline including quality gates

### Manual Triggers
- **Deploy to EC2** - Manual deployment to production (main branch only)
- **Rollback** - Manual rollback to previous version

## Security Best Practices

### 1. Secret Management
- ✅ All secrets stored as masked GitLab CI/CD variables
- ✅ Never commit credentials to the repository
- ✅ Use `.env.example` files, never `.env` files

### 2. Dependency Management
- ✅ Pin dependency versions in `requirements.txt`
- ✅ Regular OWASP dependency scans
- ✅ Automated security vulnerability detection

### 3. Code Quality
- ✅ Enforce SonarQube quality gates
- ✅ Minimum code coverage requirements
- ✅ Static code analysis with multiple tools

### 4. Deployment Security
- ✅ SSH key-based authentication only
- ✅ Backup before every deployment
- ✅ Health checks after deployment
- ✅ Manual approval for production deployments

## Monitoring and Maintenance

### View Pipeline Results
1. Go to **CI/CD > Pipelines** in GitLab
2. Click on a pipeline to see stage details
3. Review artifacts and reports

### Review Security Reports
- **SonarQube**: Access your SonarQube instance
- **Dependency Check**: Download artifacts from `owasp_dependency_check` job
- **Trivy**: Download artifacts from `trivy_filesystem_scan` job
- **Bandit**: Download artifacts from `bandit_security_scan` job

### Health Checks
```bash
# SSH into EC2 and check service status
ssh ubuntu@<EC2_HOST>
sudo systemctl status retail-store-*

# Check logs
sudo journalctl -u retail-store-auth -f
```

## Troubleshooting

### Pipeline Fails at SonarQube Stage
- Verify `SONAR_HOST_URL` and `SONAR_TOKEN` are correct
- Check SonarQube server is accessible from GitLab runner
- Review SonarQube server logs

### Deployment Fails
- Verify SSH key is correct and added to EC2
- Check EC2 security group allows SSH (port 22)
- Ensure EC2 instance has sufficient disk space
- Review GitLab job logs for specific errors

### Quality Gate Fails
- Review SonarQube project dashboard
- Fix code quality issues or security vulnerabilities
- Adjust quality gate rules if needed (with proper justification)

### Service Fails to Start After Deployment
- SSH into EC2 and check service logs
- Verify environment variables are set
- Check database connectivity
- Ensure all dependencies are installed

## Performance Optimization

### Cache Configuration
The pipeline uses caching for:
- Pip packages (`.cache/pip`)
- SonarQube analysis (`.sonar/cache`)
- Trivy database (`.trivycache/`)

### Parallel Execution
- Tests run for all services in single job
- Security scans run in parallel
- Can be optimized with parallel matrix jobs

## Additional Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [SonarQube Documentation](https://docs.sonarqube.org/)
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)

## Support

For issues or questions:
1. Check pipeline job logs in GitLab
2. Review this documentation
3. Contact your DevOps team
4. Consult tool-specific documentation

---

**Last Updated**: July 2026  
**Pipeline Version**: 1.0
