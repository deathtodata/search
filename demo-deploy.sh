#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Death2Data - One-Command VPS Deployment
# Run this on a fresh Ubuntu 22.04 VPS to deploy everything
# ═══════════════════════════════════════════════════════════════

set -e

echo "
╔══════════════════════════════════════════════════════════════╗
║  Death2Data - VPS Deployment                                 ║
╚══════════════════════════════════════════════════════════════╝
"

# 1. Update system
echo "[1/5] Updating system..."
apt update && apt upgrade -y

# 2. Install dependencies
echo "[2/5] Installing Docker..."
apt install -y docker.io docker-compose git python3

# 3. Clone repository
echo "[3/5] Cloning repository..."
cd /opt
git clone https://github.com/deathtodata/search.git
cd search

# 4. Start services
echo "[4/5] Starting services..."
docker-compose up -d

# Wait for SearXNG to be ready
echo "Waiting for SearXNG to start..."
sleep 10

# 5. Generate demo token
echo "[5/5] Generating access token..."
TOKEN=$(python3 gateway.py --generate-token 2>&1 | grep "Token:" | awk '{print $2}')

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo "
╔══════════════════════════════════════════════════════════════╗
║  DEPLOYMENT COMPLETE                                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Access your search engine:                                  ║
║  http://$PUBLIC_IP:3000/?token=$TOKEN
║                                                              ║
║  Services running:                                           ║
║  - Gateway (port 3000)                                       ║
║  - SearXNG (port 8888)                                       ║
║                                                              ║
║  To generate more tokens:                                    ║
║  cd /opt/search && python3 gateway.py --generate-token       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"

# Save token to file
echo "$TOKEN" > /root/d2d-demo-token.txt
echo "Token also saved to: /root/d2d-demo-token.txt"
