# 🚀 DevSecOps CI/CD Pipeline for Django Microservices

> **Production-ready GitLab CI/CD pipeline following DevSecOps best practices**

[![Pipeline](https://img.shields.io/badge/Pipeline-GitLab%20CI%2FCD-orange)](https://gitlab.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Security](https://img.shields.io/badge/Security-DevSecOps-green)](https://devsecops.org)
[![Django](https://img.shields.io/badge/Django-Microservices-green)](https://djangoproject.com)

---

## 📦 What's Included

This implementation provides a complete CI/CD pipeline with:

✅ **Automated Testing** - Unit tests, coverage, and linting  
✅ **Security Scanning** - SonarQube, OWASP, Bandit, Trivy  
✅ **Quality Gates** - Enforced code quality and security standards  
✅ **AWS Deployment** - Automated EC2 deployment with rollback  
✅ **Complete Documentation** - Setup guides and quick references  

---

## 📁 Files Created

| File | Size | Purpose |
|------|------|---------|
| **`.gitlab-ci.yml`** | 14 KB | Main CI/CD pipeline configuration |
| **`sonar-project.properties`** | 1.3 KB | SonarQube analysis configuration |
| **`suppression.xml`** | 758 B | OWASP false positive suppressions |
| **`setup-ec2.sh`** | 8.0 KB | EC2 instance setup automation |
| **`CI_CD_SETUP.md`** | 8.3 KB | Detailed setup instructions |
| **`QUICK_REFERENCE.md`** | 5.1 KB | Quick reference guide |
| **`PIPELINE_ARCHITECTURE.md`** | 28 KB | Visual architecture documentation |
| **`IMPLEMENTATION_SUMMARY.md`** | 7.5 KB | Implementation summary |

**Total**: 8 files | 2,027 lines of configuration and documentation

---

## 🎯 Pipeline Stages

```
┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌──────────────┐   ┌───────┐   ┌────────┐
│  CLONE   │ → │   TEST   │ → │   SECURITY   │ → │   QUALITY    │ → │ BUILD │ → │ DEPLOY │
│          │   │          │   │     SCAN     │   │     GATE     │   │       │   │        │
└──────────┘   └──────────┘   └──────────────┘   └──────────────┘   └───────┘   └────────┘
    ~10s           ~4m             ~7m                 ~30s            ~3m         ~4m
```

**Total Pipeline Time**: ~15-20 minutes (with caching)

---

## 🛡️ Security Features

### Four Layers of Security Scanning

1. **SonarQube** - Code quality & security hotspots
2. **OWASP Dependency Check** - Known CVE detection
3. **Bandit** - Python-specific security linting
4. **Trivy** - Filesystem vulnerability scanning

### Quality Gates

- ✅ SonarQube quality gate (enforced)
- ✅ Security vulnerability threshold
- ✅ Critical issues block deployment
- ✅ Manual approval for production

---

## 🚀 Quick Start

### 1. Configure GitLab Variables

Go to **Settings → CI/CD → Variables** and add:

```bash
SONAR_HOST_URL          # https://sonarqube.example.com
SONAR_TOKEN             # squ_abc123... (Masked)
AWS_DEFAULT_REGION      # us-east-1
EC2_HOST                # 3.123.45.67
EC2_USER                # ubuntu
SSH_PRIVATE_KEY         # <private key content> (File, Masked)
```

### 2. Setup EC2 Instance

```bash
# Copy setup script to EC2
scp setup-ec2.sh ubuntu@<EC2_HOST>:~/

# SSH and run setup
ssh ubuntu@<EC2_HOST>
sudo ./setup-ec2.sh
```

### 3. Configure Services

```bash
# Create .env files for each service
cd /opt/retail-store/services/auth
cp /opt/retail-store/.env.template .env
nano .env  # Edit configuration

# Repeat for: catalog, cart, orders, ui
```

### 4. Push Code

```bash
git add .gitlab-ci.yml sonar-project.properties suppression.xml
git commit -m "feat: add DevSecOps CI/CD pipeline"
git push
```

**Pipeline will automatically run!** 🎉

---

## 📊 Service Architecture

```
                         ┌─────────────────────┐
                         │   AWS EC2 INSTANCE  │
                         │                     │
                         │  ┌───────────────┐ │
                         │  │  Nginx :80    │ │
                         │  └───────┬───────┘ │
                         │          │         │
                ┌────────┼──────────┼─────────┼────────┐
                │        │          │         │        │
                ▼        ▼          ▼         ▼        ▼
           ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
           │  Auth  │ │Catalog │ │  Cart  │ │ Orders │ │   UI   │
           │  :8001 │ │ :8002  │ │ :8003  │ │ :8004  │ │ :8000  │
           └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

All services managed by **systemd** and proxied through **nginx**

---

## 📚 Documentation

| Document | Use Case |
|----------|----------|
| **[CI_CD_SETUP.md](CI_CD_SETUP.md)** | Complete setup guide with troubleshooting |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Daily operations and common commands |
| **[PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)** | Understanding the pipeline design |
| **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** | Overview of implementation |

---

## 🔧 Common Operations

### Deploy to Production
```bash
# In GitLab UI:
CI/CD → Pipelines → Select pipeline → deploy_to_ec2 → Play ▶️
```

### Rollback Deployment
```bash
# In GitLab UI:
CI/CD → Pipelines → Select pipeline → rollback_deployment → Play ▶️
```

### Check Service Health
```bash
ssh ubuntu@<EC2_HOST>
/opt/retail-store/health-check.sh
```

### View Logs
```bash
ssh ubuntu@<EC2_HOST>
sudo journalctl -u retail-store-auth -f
```

---

## 🎓 Best Practices Implemented

### Code Quality
- ✅ Unit tests with pytest
- ✅ Code coverage reporting (Cobertura)
- ✅ Linting (flake8, black, isort)
- ✅ Automated quality gates

### Security
- ✅ Multiple security scanning tools
- ✅ Dependency vulnerability checks
- ✅ No hardcoded secrets
- ✅ SSH key authentication

### Deployment
- ✅ Blue-green deployment pattern
- ✅ Automatic backups
- ✅ Health checks
- ✅ Rollback capability
- ✅ Manual approval for production

### DevOps
- ✅ Infrastructure as Code
- ✅ Automated provisioning
- ✅ Centralized logging
- ✅ Service orchestration

---

## 📈 Monitoring

### Pipeline Metrics
- Test coverage trends
- Security vulnerability counts
- Quality gate pass/fail rates
- Deployment frequency

### Application Metrics
- Service health status
- Response times
- Error rates
- Resource utilization

---

## 🐛 Troubleshooting

### Pipeline Fails?
1. Check job logs in GitLab
2. Review error messages
3. Consult [CI_CD_SETUP.md](CI_CD_SETUP.md) troubleshooting section

### Deployment Fails?
1. Verify SSH connectivity
2. Check EC2 security groups
3. Review service logs on EC2

### Quality Gate Fails?
1. Review SonarQube dashboard
2. Fix code issues
3. Re-run pipeline

**Detailed troubleshooting**: See [CI_CD_SETUP.md](CI_CD_SETUP.md#troubleshooting)

---

## 🏆 Success Criteria

Your pipeline is successful when:

- ✅ All tests pass
- ✅ Security scans show no critical vulnerabilities
- ✅ Quality gates pass
- ✅ Deployment completes successfully
- ✅ Health checks pass
- ✅ All services running

---

## 🤝 Contributing

When modifying the pipeline:

1. Test changes in feature branch
2. Review security implications
3. Update documentation
4. Get approval before merging to main

---

## 📄 License

This CI/CD configuration is provided as-is for the Retail Store Microservices project.

---

## 📞 Support

- **Pipeline Issues**: Check GitLab job logs
- **Security Questions**: Review security scan reports
- **Deployment Help**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

## 🎉 What's Next?

1. ✅ Files created and validated
2. 📝 Add GitLab CI/CD variables
3. 🔧 Run setup-ec2.sh on EC2
4. 🚀 Push code to trigger first pipeline
5. 🎯 Review security reports
6. 🏁 Deploy to production

---

<div align="center">

**Built with ❤️ following DevSecOps best practices**

Pipeline Version 1.0 | July 2026

[Documentation](CI_CD_SETUP.md) • [Quick Reference](QUICK_REFERENCE.md) • [Architecture](PIPELINE_ARCHITECTURE.md)

</div>
