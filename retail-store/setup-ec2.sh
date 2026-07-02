#!/bin/bash

#######################################################################
# EC2 Instance Setup Script for Retail Store Microservices
# 
# This script prepares an EC2 instance for deployment by:
# - Installing required system packages
# - Creating deployment directories
# - Setting up systemd service files
# - Configuring nginx as reverse proxy (optional)
#
# Usage: sudo ./setup-ec2.sh
#######################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/retail-store"
DEPLOY_USER="${DEPLOY_USER:-ubuntu}"
SERVICES=("auth" "catalog" "cart" "orders" "ui")

# Service ports
declare -A SERVICE_PORTS
SERVICE_PORTS[auth]=8001
SERVICE_PORTS[catalog]=8002
SERVICE_PORTS[cart]=8003
SERVICE_PORTS[orders]=8004
SERVICE_PORTS[ui]=8000

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Retail Store EC2 Setup Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Update system packages
echo -e "\n${YELLOW}[1/7] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Install required packages
echo -e "\n${YELLOW}[2/7] Installing required packages...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql-client \
    libpq-dev \
    nginx \
    supervisor \
    redis-tools \
    curl \
    wget \
    git \
    build-essential

# Create deployment directory
echo -e "\n${YELLOW}[3/7] Creating deployment directory...${NC}"
mkdir -p $DEPLOY_DIR
chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR
echo -e "${GREEN}✓ Created $DEPLOY_DIR${NC}"

# Create systemd service files
echo -e "\n${YELLOW}[4/7] Creating systemd service files...${NC}"

for service in "${SERVICES[@]}"; do
    cat > /etc/systemd/system/retail-store-$service.service <<EOF
[Unit]
Description=Retail Store ${service^} Service
After=network.target

[Service]
Type=notify
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$DEPLOY_DIR/services/$service
Environment="PATH=$DEPLOY_DIR/services/$service/venv/bin"
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=$DEPLOY_DIR/services/$service/.env

ExecStart=$DEPLOY_DIR/services/$service/venv/bin/gunicorn \\
          --config gunicorn.conf.py \\
          --bind 0.0.0.0:${SERVICE_PORTS[$service]} \\
          ${service}_service.wsgi:application

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Security settings
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=retail-store-$service

[Install]
WantedBy=multi-user.target
EOF
    
    echo -e "${GREEN}✓ Created systemd service for $service${NC}"
done

# Create health check endpoint service
echo -e "\n${YELLOW}[5/7] Creating health check script...${NC}"
cat > $DEPLOY_DIR/health-check.sh <<'EOF'
#!/bin/bash

# Health check script for all services
SERVICES=("auth:8001" "catalog:8002" "cart:8003" "orders:8004" "ui:8000")

echo "Checking service health..."
for service in "${SERVICES[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    
    if curl -f -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✓ $name service (port $port) is healthy"
    else
        echo "✗ $name service (port $port) is not responding"
    fi
done
EOF

chmod +x $DEPLOY_DIR/health-check.sh
chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR/health-check.sh

# Configure nginx as reverse proxy
echo -e "\n${YELLOW}[6/7] Configuring nginx reverse proxy...${NC}"

cat > /etc/nginx/sites-available/retail-store <<'EOF'
upstream auth_backend {
    server localhost:8001;
}

upstream catalog_backend {
    server localhost:8002;
}

upstream cart_backend {
    server localhost:8003;
}

upstream orders_backend {
    server localhost:8004;
}

upstream ui_backend {
    server localhost:8000;
}

# Main application server
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    # UI Service (main frontend)
    location / {
        proxy_pass http://ui_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Auth Service
    location /api/auth/ {
        proxy_pass http://auth_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Catalog Service
    location /api/catalog/ {
        proxy_pass http://catalog_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Cart Service
    location /api/cart/ {
        proxy_pass http://cart_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Orders Service
    location /api/orders/ {
        proxy_pass http://orders_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/retail-store /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Reload systemd and nginx
echo -e "\n${YELLOW}[7/7] Finalizing setup...${NC}"
systemctl daemon-reload

for service in "${SERVICES[@]}"; do
    systemctl enable retail-store-$service
    echo -e "${GREEN}✓ Enabled retail-store-$service${NC}"
done

systemctl restart nginx
echo -e "${GREEN}✓ Nginx configured and restarted${NC}"

# Create environment file template
echo -e "\n${YELLOW}Creating environment file template...${NC}"
cat > $DEPLOY_DIR/.env.template <<'EOF'
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=*

# Database Settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=retail_store
DB_USER=retail_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379

# Service URLs (for inter-service communication)
AUTH_SERVICE_URL=http://localhost:8001
CATALOG_SERVICE_URL=http://localhost:8002
CART_SERVICE_URL=http://localhost:8003
ORDERS_SERVICE_URL=http://localhost:8004
UI_SERVICE_URL=http://localhost:8000
EOF

chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR/.env.template

# Print summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nNext steps:"
echo -e "1. Copy .env.template to each service's .env file and configure"
echo -e "   Example: cp $DEPLOY_DIR/.env.template $DEPLOY_DIR/services/auth/.env"
echo -e "\n2. Run the first deployment from GitLab CI/CD"
echo -e "\n3. Check service status:"
echo -e "   ${YELLOW}systemctl status retail-store-*${NC}"
echo -e "\n4. Run health checks:"
echo -e "   ${YELLOW}$DEPLOY_DIR/health-check.sh${NC}"
echo -e "\n5. View logs:"
echo -e "   ${YELLOW}journalctl -u retail-store-auth -f${NC}"
echo -e "\nDeployment directory: ${GREEN}$DEPLOY_DIR${NC}"
echo -e "Service ports:"
for service in "${SERVICES[@]}"; do
    echo -e "  - $service: ${GREEN}${SERVICE_PORTS[$service]}${NC}"
done
echo -e "\nNginx will proxy all services through port 80"
echo -e "${GREEN}========================================${NC}\n"
