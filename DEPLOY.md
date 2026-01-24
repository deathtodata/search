# Deployment Guide

Complete guide to deploying Death2Data in production.

---

## Table of Contents

1. [Local Development](#local-development)
2. [VPS Deployment](#vps-deployment)
3. [Tunnel Deployment (ngrok/Cloudflare)](#tunnel-deployment)
4. [Docker Deployment](#docker-deployment)
5. [SSL/TLS Setup](#ssltls-setup)
6. [Performance Tuning](#performance-tuning)
7. [Monitoring](#monitoring)

---

## Local Development

**Requirements:**
- Python 3.7+
- Docker (for SearXNG)

**Steps:**

```bash
# 1. Start SearXNG
docker run -d -p 8080:8080 --name searxng searxng/searxng

# 2. Run Death2Data
python3 gateway.py

# 3. Generate token
python3 gateway.py --generate-token

# 4. Test
open "http://localhost:3000/?token=YOUR_TOKEN"
```

**Environment Variables:**
```bash
export PORT=3000                              # Gateway port
export SEARXNG_URL="http://localhost:8080"    # SearXNG endpoint
export DATABASE_PATH="./data/d2d.db"          # SQLite database
```

---

## VPS Deployment

### Option A: $5/month VPS (DigitalOcean, Vultr, Hetzner)

**1. Create VPS**
```bash
# Ubuntu 22.04 LTS
# 1GB RAM minimum
# $5-10/month
```

**2. Install Dependencies**
```bash
# SSH into VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Python & Docker
apt install -y python3 python3-pip docker.io docker-compose
systemctl enable docker
systemctl start docker
```

**3. Deploy Code**
```bash
# Clone repository
git clone https://github.com/deathtodata/search.git
cd search

# Start with Docker Compose
docker-compose up -d

# Or manual:
docker run -d -p 8080:8080 searxng/searxng
python3 gateway.py &
```

**4. Configure Firewall**
```bash
# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp  # SSH
ufw enable
```

**5. Setup Systemd Service**

Create `/etc/systemd/system/death2data.service`:
```ini
[Unit]
Description=Death2Data Search Gateway
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/death2data
Environment="PORT=3000"
Environment="SEARXNG_URL=http://localhost:8080"
ExecStart=/usr/bin/python3 /opt/death2data/gateway.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable death2data
systemctl start death2data
systemctl status death2data
```

---

## Tunnel Deployment

Run on your local machine, expose via tunnel.

### Option A: ngrok

```bash
# 1. Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# 2. Start Death2Data locally
python3 gateway.py

# 3. Tunnel
ngrok http 3000
```

You'll get: `https://abc123.ngrok.io` → Share this URL with users

**Pros:** Free, instant setup
**Cons:** Random URL, requires local machine online

### Option B: Cloudflare Tunnel

```bash
# 1. Install cloudflared
brew install cloudflared  # macOS

# 2. Login
cloudflared tunnel login

# 3. Create tunnel
cloudflared tunnel create death2data

# 4. Configure tunnel
cat > ~/.cloudflared/config.yml <<EOF
url: http://localhost:3000
tunnel: death2data
credentials-file: /path/to/credentials.json
EOF

# 5. Start tunnel
cloudflared tunnel run death2data
```

**Pros:** Free, custom domain, persistent
**Cons:** Requires Cloudflare account

---

## Docker Deployment

### docker-compose.yml

```yaml
version: '3'

services:
  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng
    restart: always

  gateway:
    build: .
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
      - SEARXNG_URL=http://searxng:8080
      - DATABASE_PATH=/data/d2d.db
    volumes:
      - ./data:/data
    depends_on:
      - searxng
    restart: always
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY gateway.py .
COPY index.html .

RUN mkdir -p /data

EXPOSE 3000

CMD ["python3", "gateway.py"]
```

### Deploy

```bash
docker-compose up -d
docker-compose logs -f
```

---

## SSL/TLS Setup

### Option A: Caddy (Easiest)

**Install Caddy:**
```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install caddy
```

**Caddyfile:**
```
search.yourdomain.com {
    reverse_proxy localhost:3000
}
```

**Start:**
```bash
caddy run
# SSL certificates are automatic (Let's Encrypt)
```

### Option B: nginx + certbot

**Install:**
```bash
apt install -y nginx certbot python3-certbot-nginx
```

**/etc/nginx/sites-available/death2data:**
```nginx
server {
    listen 80;
    server_name search.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Enable and get SSL:**
```bash
ln -s /etc/nginx/sites-available/death2data /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
certbot --nginx -d search.yourdomain.com
```

---

## Performance Tuning

### For High Traffic

**Use multiple gateway processes:**
```bash
# Install gunicorn or similar
pip3 install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:3000 gateway:app
```

**Or use systemd socket activation:**
```ini
# /etc/systemd/system/death2data.socket
[Socket]
ListenStream=3000
Accept=yes

[Install]
WantedBy=sockets.target
```

### Database Optimization

**Use WAL mode for better concurrency:**
```bash
sqlite3 data/d2d.db "PRAGMA journal_mode=WAL;"
```

### SearXNG Performance

**Increase workers:**
```yaml
# searxng/settings.yml
server:
  limiter: false
  workers: 4
```

---

## Monitoring

### Health Check

```bash
curl http://localhost:3000/health
```

### Log Monitoring

```bash
# Gateway logs
journalctl -u death2data -f

# SearXNG logs
docker logs -f searxng

# nginx logs
tail -f /var/log/nginx/access.log
```

### Uptime Monitoring

Use:
- **UptimeRobot** (free, 50 monitors)
- **Healthchecks.io** (free, 20 checks)
- **Better Uptime** (free tier available)

**Example healthcheck:**
```bash
#!/bin/bash
# /usr/local/bin/health-check.sh

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health)

if [ "$response" != "200" ]; then
    systemctl restart death2data
    echo "Death2Data restarted at $(date)" >> /var/log/death2data-restarts.log
fi
```

**Crontab:**
```bash
*/5 * * * * /usr/local/bin/health-check.sh
```

---

## Security Checklist

- [ ] Firewall configured (only 80, 443, 22 open)
- [ ] SSL/TLS enabled (Let's Encrypt)
- [ ] Database file permissions restricted (`chmod 600 data/d2d.db`)
- [ ] Regular updates (`apt update && apt upgrade`)
- [ ] Fail2ban installed (SSH protection)
- [ ] Non-root user running services
- [ ] Logs rotated (logrotate)
- [ ] Backups configured (database only)

---

## Backup & Recovery

### Backup Script

```bash
#!/bin/bash
# /usr/local/bin/backup-d2d.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/death2data"

mkdir -p $BACKUP_DIR

# Backup database
sqlite3 /opt/death2data/data/d2d.db ".backup $BACKUP_DIR/d2d-$DATE.db"

# Keep only last 7 days
find $BACKUP_DIR -name "d2d-*.db" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Crontab:**
```bash
0 2 * * * /usr/local/bin/backup-d2d.sh
```

### Restore

```bash
cp /backups/death2data/d2d-20260124.db /opt/death2data/data/d2d.db
systemctl restart death2data
```

---

## Troubleshooting

### Gateway won't start

```bash
# Check logs
journalctl -u death2data -n 50

# Check if port is in use
lsof -i :3000

# Check SearXNG is running
docker ps | grep searxng
```

### SearXNG returns errors

```bash
# Check SearXNG logs
docker logs searxng

# Restart SearXNG
docker restart searxng

# Update SearXNG
docker pull searxng/searxng:latest
docker-compose up -d
```

### Database locked errors

```bash
# Enable WAL mode
sqlite3 data/d2d.db "PRAGMA journal_mode=WAL;"

# Check permissions
ls -la data/d2d.db
chmod 644 data/d2d.db
```

---

## Cost Estimate

| Option | Monthly Cost |
|--------|-------------|
| Local + ngrok | $0 (free tier) |
| VPS (DigitalOcean) | $5-10 |
| VPS + Domain | $6-11 |
| VPS + Cloudflare | $5-10 (CF is free) |

**Recommended:** $5 VPS + Cloudflare (free) = $5/month total

---

## Production Checklist

**Before launching:**
- [ ] Domain configured (DNS pointing to VPS)
- [ ] SSL certificate working
- [ ] Health checks passing
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Firewall configured
- [ ] Tokens generated for initial users
- [ ] Documentation link shared

**After launching:**
- [ ] Monitor logs for errors
- [ ] Check uptime daily (first week)
- [ ] Collect user feedback
- [ ] Update security patches weekly

---

**Questions? Open an issue: https://github.com/deathtodata/search/issues**
