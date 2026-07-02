# DevSecOps Pipeline Architecture

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DEVELOPER WORKFLOW                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ git push
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: CLONE & VALIDATION                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Clone repository                                          │   │
│  │  • Validate structure                                        │   │
│  │  • Cache dependencies                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: TEST & QUALITY                           │
│  ┌────────────────────────┐  ┌──────────────────────────────────┐  │
│  │   Unit Tests           │  │   Code Linting                   │  │
│  │   ────────────         │  │   ────────────                   │  │
│  │   • pytest (all 5)     │  │   • flake8                       │  │
│  │   • Coverage report    │  │   • black                        │  │
│  │   • JUnit XML          │  │   • isort                        │  │
│  └────────────────────────┘  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STAGE 3: SECURITY SCANNING                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐ │
│  │  SonarQube   │ │    OWASP     │ │   Bandit     │ │   Trivy   │ │
│  │  Analysis    │ │  Dependency  │ │  Security    │ │ Filesystem│ │
│  │  ──────────  │ │    Check     │ │    Scan      │ │   Scan    │ │
│  │  • Code      │ │  ──────────  │ │  ──────────  │ │ ────────  │ │
│  │    Quality   │ │  • CVE       │ │  • Python    │ │  • File   │ │
│  │  • Security  │ │    Detection │ │    Vulns     │ │    Vulns  │ │
│  │    Hotspots  │ │  • License   │ │  • Hardcoded │ │  • Config │ │
│  │  • Code      │ │    Issues    │ │    Secrets   │ │    Issues │ │
│  │    Smells    │ │              │ │              │ │           │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   STAGE 4: QUALITY GATES                             │
│  ┌────────────────────────┐  ┌──────────────────────────────────┐  │
│  │  SonarQube Gate        │  │   Security Gate                  │  │
│  │  ───────────────       │  │   ──────────────                 │  │
│  │  • Coverage > X%       │  │   • No CRITICAL vulns            │  │
│  │  • Duplications < Y%   │  │   • OWASP threshold              │  │
│  │  • Security Rating     │  │   • Trivy threshold              │  │
│  │  • MUST PASS ✓         │  │   • MUST PASS ✓                 │  │
│  └────────────────────────┘  └──────────────────────────────────┘  │
│                                                                      │
│  ❌ FAIL → Pipeline stops, fix issues required                      │
│  ✅ PASS → Continue to build                                        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      STAGE 5: BUILD                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Install dependencies (all services)                       │   │
│  │  • Run Django collectstatic                                  │   │
│  │  • Create deployment archive                                 │   │
│  │  • Store artifacts                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STAGE 6: DEPLOYMENT (Manual Trigger)                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. Transfer artifact to EC2 via SSH                         │   │
│  │  2. Backup current deployment                                │   │
│  │  3. Extract new version                                      │   │
│  │  4. Install dependencies (venv per service)                  │   │
│  │  5. Run database migrations                                  │   │
│  │  6. Restart systemd services                                 │   │
│  │  7. Run health checks                                        │   │
│  │  8. Cleanup                                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ROLLBACK (Manual Trigger)                                   │   │
│  │  • Restore from backup                                       │   │
│  │  • Restart services                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ✅ DEPLOYMENT COMPLETE
```

## Service Architecture on EC2

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS EC2 INSTANCE                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                     NGINX (Port 80)                         │ │
│  │                    Reverse Proxy                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │           │           │           │           │        │
│         ▼           ▼           ▼           ▼           ▼        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  Auth   │ │ Catalog │ │  Cart   │ │ Orders  │ │   UI    │  │
│  │ :8001   │ │ :8002   │ │ :8003   │ │ :8004   │ │ :8000   │  │
│  ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤  │
│  │ Django  │ │ Django  │ │ Django  │ │ Django  │ │ Django  │  │
│  │ Gunicorn│ │ Gunicorn│ │ Gunicorn│ │ Gunicorn│ │ Gunicorn│  │
│  │ systemd │ │ systemd │ │ systemd │ │ systemd │ │ systemd │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          /opt/retail-store/services/                      │  │
│  │          ├── auth/                                        │  │
│  │          ├── catalog/                                     │  │
│  │          ├── cart/                                        │  │
│  │          ├── orders/                                      │  │
│  │          └── ui/                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Source Code Security                                  │
│  ─────────────────────────────                                  │
│  • Bandit (Python-specific vulnerabilities)                     │
│  • SonarQube (Security hotspots, code quality)                  │
│  • Black, isort, flake8 (Code standards)                        │
│                                                                  │
│  Layer 2: Dependency Security                                   │
│  ─────────────────────────────                                  │
│  • OWASP Dependency-Check (Known CVEs)                          │
│  • Trivy (Filesystem vulnerabilities)                           │
│  • Python requirements.txt scanning                             │
│                                                                  │
│  Layer 3: Quality Gates                                         │
│  ──────────────────────────                                     │
│  • SonarQube Quality Gate (Enforced)                            │
│  • Security Gate (Critical vuln blocking)                       │
│  • Pipeline fails if standards not met                          │
│                                                                  │
│  Layer 4: Deployment Security                                   │
│  ─────────────────────────────                                  │
│  • SSH key-based authentication only                            │
│  • No passwords in code or CI/CD config                         │
│  • Environment variables for secrets                            │
│  • Automatic backups before deployment                          │
│                                                                  │
│  Layer 5: Runtime Security                                      │
│  ──────────────────────────                                     │
│  • systemd service isolation                                    │
│  • nginx reverse proxy                                          │
│  • EC2 security groups                                          │
│  • Health monitoring                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Branch Strategy & Pipeline Triggers

```
┌─────────────────────────────────────────────────────────────────┐
│  Feature Branch (feature/*)                                      │
│  ────────────────────────                                        │
│  Triggers: clone, test, lint                                     │
│  Purpose: Quick feedback for developers                          │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ Merge Request
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Merge Request Pipeline                                          │
│  ───────────────────────────                                     │
│  Triggers: Full pipeline (except deploy)                         │
│  • Clone + Test + Security Scans                                 │
│  • Quality Gates enforced                                        │
│  • Code review required                                          │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ Merge
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Develop Branch (develop)                                        │
│  ──────────────────────────                                      │
│  Triggers: Full pipeline with quality gates                      │
│  • All security scans                                            │
│  • Quality gates enforced                                        │
│  • Build artifacts created                                       │
│  • Ready for testing environment                                 │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ Merge to main
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Main Branch (main)                                              │
│  ────────────────────                                            │
│  Triggers: Full pipeline + manual deploy                         │
│  • All stages execute                                            │
│  • Deploy job available (manual trigger)                         │
│  • Rollback job available (manual trigger)                       │
│  • Production-ready artifacts                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Artifact Flow

```
┌─────────────────┐
│  Source Code    │
│  (5 services)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Build Stage                             │
│  • Install dependencies                  │
│  • Run collectstatic                     │
│  • Create tar.gz archive                 │
│  └─► retail-store-{commit}.tar.gz       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  GitLab Artifacts Storage                │
│  • Stored for 1 week                     │
│  • Available for download                │
│  • Used by deploy stage                  │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  SCP to EC2 (/tmp/)                      │
│  • Secure transfer via SSH               │
│  • Checksum verification                 │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Extract to /opt/retail-store/           │
│  • services/auth/                        │
│  • services/catalog/                     │
│  • services/cart/                        │
│  • services/orders/                      │
│  • services/ui/                          │
└─────────────────────────────────────────┘
```

## Performance & Caching

```
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Caching Strategy                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Pip Cache (.cache/pip/)                                 │
│     • Python packages                                        │
│     • Saves ~2-3 minutes per pipeline                       │
│                                                              │
│  2. SonarQube Cache (.sonar/cache/)                         │
│     • Analysis data                                          │
│     • Saves ~30 seconds per pipeline                        │
│                                                              │
│  3. Trivy Cache (.trivycache/)                              │
│     • Vulnerability database                                 │
│     • Saves ~1 minute per pipeline                          │
│                                                              │
│  Total Time Savings: ~4-5 minutes per pipeline run          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Monitoring                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GitLab CI/CD:                                              │
│  • Pipeline success/failure rates                           │
│  • Stage execution times                                     │
│  • Test coverage trends                                      │
│  • Artifact storage usage                                   │
│                                                              │
│  SonarQube Dashboard:                                       │
│  • Code quality metrics                                      │
│  • Security rating trends                                   │
│  • Technical debt                                           │
│  • Code coverage over time                                  │
│                                                              │
│  EC2 Monitoring:                                            │
│  • systemd service status                                   │
│  • journalctl logs                                          │
│  • Health check endpoints                                   │
│  • Application performance                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Cost Optimization

```
┌─────────────────────────────────────────────────────────────┐
│  Pipeline runs only on:                                      │
│  • Push to tracked branches                                  │
│  • Merge requests                                           │
│  • Manual triggers                                          │
│                                                              │
│  Caching reduces:                                           │
│  • Pipeline execution time                                   │
│  • Network bandwidth usage                                   │
│  • GitLab runner compute costs                             │
│                                                              │
│  Artifacts expire after 1 week:                             │
│  • Automatic cleanup                                        │
│  • Storage cost management                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

**Last Updated**: July 2026  
**Version**: 1.0  
**Maintained by**: DevOps Team
