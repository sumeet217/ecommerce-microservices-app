# Django Microservices - CI/CD & Services

This directory contains the Django microservices and their associated CI/CD pipeline configuration.

## 📁 Directory Structure

```
retail-store/
├── services/                    # Django microservices
│   ├── auth/                   # Authentication service (JWT)
│   ├── catalog/                # Product catalog service
│   ├── cart/                   # Shopping cart service (Redis)
│   ├── orders/                 # Order management service
│   └── ui/                     # Frontend UI service
│
├── .gitlab-ci.yml              # 🚀 Main CI/CD pipeline configuration
├── sonar-project.properties    # SonarQube analysis configuration
├── suppression.xml             # OWASP suppression rules
├── setup-ec2.sh                # EC2 instance setup automation
│
└── Documentation/
    ├── README_CI_CD.md             # CI/CD overview (START HERE)
    ├── CI_CD_SETUP.md              # Detailed setup guide
    ├── QUICK_REFERENCE.md          # Common commands
    ├── PIPELINE_ARCHITECTURE.md    # Visual architecture
    └── IMPLEMENTATION_SUMMARY.md   # Implementation details
```

## 🚀 Quick Start

### For Development (Local Docker)
```bash
# From project root
docker compose up --build -d
```

See parent [README.md](../README.md) for complete local development setup.

### For CI/CD Deployment

**Start with**: [README_CI_CD.md](README_CI_CD.md)

1. Configure GitLab CI/CD variables
2. Setup EC2 instance with `setup-ec2.sh`
3. Push code to trigger pipeline
4. Review security reports
5. Deploy to production

## 📊 Services Overview

| Service | Port | Purpose | Technology |
|---------|------|---------|------------|
| **auth** | 8001 | User authentication & JWT tokens | Django + PostgreSQL |
| **catalog** | 8002 | Product catalog & search | Django REST + PostgreSQL |
| **cart** | 8003 | Shopping cart management | Django REST + Redis |
| **orders** | 8004 | Order processing | Django REST + PostgreSQL |
| **ui** | 8000 | Frontend application | Django Templates + Bootstrap |

## 🛡️ CI/CD Pipeline

### Pipeline Stages
```
1. CLONE          → Code checkout & validation
2. TEST           → Unit tests, coverage, linting
3. SECURITY-SCAN  → SonarQube, OWASP, Bandit, Trivy
4. QUALITY-GATE   → Enforce quality standards
5. BUILD          → Create deployment artifacts
6. DEPLOY         → AWS EC2 deployment
```

### Security Scanning Tools

| Tool | What it checks | Blocks pipeline? |
|------|----------------|------------------|
| **SonarQube** | Code quality, security hotspots, duplications | ✅ Yes |
| **OWASP** | Known CVEs in dependencies | ✅ Critical only |
| **Bandit** | Python security patterns | ⚠️ Warning |
| **Trivy** | Filesystem vulnerabilities | ✅ Critical only |

## 📚 Documentation

### For DevOps / CI/CD Setup
1. **[README_CI_CD.md](README_CI_CD.md)** - Overview with badges and quick start
2. **[CI_CD_SETUP.md](CI_CD_SETUP.md)** - Complete setup instructions
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Daily operations commands

### For Understanding Architecture
- **[PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)** - Visual pipeline flow
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - What was implemented

### For Service Development
See individual service README files:
- `services/auth/README.md` (if exists)
- `services/catalog/README.md` (if exists)
- etc.

## 🔧 Common Operations

### View Pipeline Status
```bash
# GitLab UI: CI/CD → Pipelines
```

### Deploy to EC2
```bash
# In GitLab UI:
# Pipelines → Select pipeline → deploy_to_ec2 → Play ▶️
```

### Check Service Health on EC2
```bash
ssh ubuntu@<EC2_HOST>
/opt/retail-store/health-check.sh
```

### View Service Logs on EC2
```bash
ssh ubuntu@<EC2_HOST>
sudo journalctl -u retail-store-auth -f
```

## 🎯 Quick Troubleshooting

### Pipeline Fails?
1. Check job logs in GitLab
2. Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md) troubleshooting section
3. Verify GitLab CI/CD variables are set

### Deployment Fails?
1. Verify SSH connectivity to EC2
2. Check EC2 security groups
3. Review service logs on EC2

### Quality Gate Fails?
1. View SonarQube dashboard
2. Fix reported issues
3. Push changes to re-trigger pipeline

## 🏗️ Infrastructure

### Local Development
- **Docker Compose**: All services + databases + Redis
- **Ports**: 80 (nginx), 8000-8004 (services)

### Production (EC2)
- **Systemd**: Service management
- **Nginx**: Reverse proxy (port 80)
- **Gunicorn**: WSGI server per service
- **PostgreSQL**: Per-service databases
- **Redis**: Cart storage

## 🔐 Security Best Practices

✅ **Never commit secrets** - Use GitLab masked variables  
✅ **Review security reports** before merging  
✅ **Quality gates enforced** - Fix critical issues  
✅ **Automated backups** before deployment  
✅ **SSH key authentication** only  

## 📞 Getting Help

- **CI/CD Issues**: See [CI_CD_SETUP.md](CI_CD_SETUP.md#troubleshooting)
- **Service Issues**: Check individual service documentation
- **Pipeline Questions**: Review [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)

## 🎓 Learning Path

1. **New to the project?** Start with parent [README.md](../README.md)
2. **Setting up CI/CD?** Read [README_CI_CD.md](README_CI_CD.md)
3. **Daily operations?** Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
4. **Understanding architecture?** See [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)

---

**Part of**: [RetailStore E-Commerce Microservices](../README.md)  
**CI/CD Version**: 1.0  
**Last Updated**: July 2026
