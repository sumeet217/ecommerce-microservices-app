# GitLab CI/CD Quick Reference

## 📋 GitLab Variables Setup Checklist

### Required Variables (Settings > CI/CD > Variables)

```
☐ SONAR_HOST_URL          (e.g., https://sonarqube.example.com)
☐ SONAR_TOKEN             (Masked, from SonarQube)
☐ AWS_DEFAULT_REGION      (e.g., us-east-1)
☐ EC2_HOST                (e.g., 3.123.45.67)
☐ EC2_USER                (e.g., ubuntu)
☐ SSH_PRIVATE_KEY         (File, Masked, SSH private key content)
```

## 🚀 Quick Setup Commands

### 1. Initial EC2 Setup
```bash
# Copy setup script to EC2
scp setup-ec2.sh ubuntu@<EC2_HOST>:~/

# SSH into EC2 and run setup
ssh ubuntu@<EC2_HOST>
sudo ./setup-ec2.sh
```

### 2. Generate SSH Keys for GitLab CI
```bash
# Generate key pair
ssh-keygen -t ed25519 -C "gitlab-ci" -f gitlab-ci-key

# Copy public key to EC2
ssh-copy-id -i gitlab-ci-key.pub ubuntu@<EC2_HOST>

# Add private key content to GitLab CI variable SSH_PRIVATE_KEY
cat gitlab-ci-key
```

### 3. Configure Service Environment Files
```bash
# SSH into EC2
ssh ubuntu@<EC2_HOST>

# For each service, create .env file
cd /opt/retail-store/services/auth
cp /opt/retail-store/.env.template .env
nano .env  # Edit configuration

# Repeat for: catalog, cart, orders, ui
```

## 🔍 Pipeline Stages Overview

```
1. CLONE              → Clone repository and validate
2. TEST               → Unit tests + linting
3. SECURITY-SCAN      → SonarQube, OWASP, Bandit, Trivy
4. QUALITY-GATE       → Enforce quality standards
5. BUILD              → Create deployment artifacts
6. DEPLOY             → Deploy to EC2 (manual)
```

## 📊 Monitoring Commands

### Check Pipeline Status
```bash
# View active pipelines
# GitLab UI: CI/CD > Pipelines
```

### EC2 Service Management
```bash
# Check all services
sudo systemctl status retail-store-*

# Check specific service
sudo systemctl status retail-store-auth

# Restart service
sudo systemctl restart retail-store-auth

# View logs
sudo journalctl -u retail-store-auth -f

# Health check
/opt/retail-store/health-check.sh
```

### View Security Reports
```bash
# Download from GitLab artifacts:
# Pipeline > Jobs > [job name] > Browse/Download artifacts
```

## 🔧 Common Operations

### Trigger Manual Deployment
1. Go to: CI/CD > Pipelines
2. Select pipeline (must be on `main` branch)
3. Find `deploy_to_ec2` job
4. Click ▶️ Play button

### Rollback Deployment
1. Go to: CI/CD > Pipelines
2. Select pipeline (must be on `main` branch)
3. Find `rollback_deployment` job
4. Click ▶️ Play button

### Review SonarQube Results
1. Login to SonarQube instance
2. Navigate to project: retail-store-microservices
3. Review issues, code smells, vulnerabilities

### Fix Quality Gate Failures
```bash
# View SonarQube issues in dashboard
# Fix code issues locally
git add .
git commit -m "fix: resolve sonarqube issues"
git push

# Pipeline will re-run automatically
```

## 🛡️ Security Checklist

```
☐ All secrets in GitLab Variables (masked)
☐ SSH key-based authentication only
☐ EC2 security group allows SSH from GitLab runner IP only
☐ EC2 security group allows HTTP/HTTPS from required IPs
☐ Database credentials in .env files (not in code)
☐ SonarQube quality gate enabled
☐ OWASP dependency check running
☐ Trivy filesystem scan running
```

## 🐛 Troubleshooting

### Pipeline Fails at Clone Stage
- Check GitLab runner is active
- Verify runner has docker executor

### Tests Fail
- Check test dependencies in requirements.txt
- Review test logs in GitLab job output
- Run tests locally: `pytest`

### SonarQube Job Fails
- Verify SONAR_HOST_URL is reachable
- Check SONAR_TOKEN is valid
- Ensure SonarQube project exists

### Deployment Fails
- Verify SSH_PRIVATE_KEY is correct
- Check EC2 security group allows SSH
- Ensure EC2 instance is running
- Verify EC2_USER has sudo privileges

### Service Won't Start
```bash
# SSH into EC2
ssh ubuntu@<EC2_HOST>

# Check service status
sudo systemctl status retail-store-auth

# View full logs
sudo journalctl -u retail-store-auth -n 100 --no-pager

# Check if port is in use
sudo netstat -tulpn | grep 8001

# Test manually
cd /opt/retail-store/services/auth
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

## 📱 Useful URLs

```
GitLab Pipeline:     <your-gitlab-url>/retail-store/-/pipelines
SonarQube:          ${SONAR_HOST_URL}
Application (EC2):  http://${EC2_HOST}
Health Check:       http://${EC2_HOST}/health
```

## 🎯 Best Practices

1. **Never commit secrets** - Use GitLab variables
2. **Review security reports** before merging to main
3. **Run local tests** before pushing
4. **Use feature branches** for development
5. **Manual approval** for production deployments
6. **Backup verification** before rollback
7. **Monitor logs** after deployment
8. **Document suppressions** in OWASP suppression.xml

## 📞 Support Contacts

- DevOps Team: [your-contact]
- SonarQube Admin: [your-contact]
- AWS Admin: [your-contact]

---

**Files in this CI/CD setup:**
- `.gitlab-ci.yml` - Main pipeline configuration
- `sonar-project.properties` - SonarQube settings
- `suppression.xml` - OWASP suppression rules
- `setup-ec2.sh` - EC2 initialization script
- `CI_CD_SETUP.md` - Detailed documentation
- `QUICK_REFERENCE.md` - This file
