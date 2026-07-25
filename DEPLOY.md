# Deployment Guide

## Quick Deploy to Railway (Recommended)

### Prerequisites
- GitHub account
- Railway account (free $5/month credit)

### Steps

1. **Create GitHub repository**
```bash
cd fmhy-api
git init
git add .
git commit -m "Initial FMHY API"
git remote add origin https://github.com/YOUR-USERNAME/fmhy-api.git
git push -u origin main
```

2. **Deploy to Railway**
- Go to [railway.app](https://railway.app)
- Sign in with GitHub
- Click "New Project" → "Deploy from GitHub repo"
- Select your fmhy-api repository
- Railway will auto-detect the Python app and deploy

3. **Get your API URL**
- After deployment, click on the service
- Go to "Settings" → "Networking"
- Click "Generate Domain" for a free URL
- Your API is now live at `https://your-app.up.railway.app`

### Railway CLI (Alternative)
```bash
# Install CLI
npm i -g @railway/cli

# Login
railway login

# Init project
cd fmhy-api
railway init

# Deploy
railway up
```

---

## Deploy to Render

### Steps

1. **Push to GitHub** (same as above)

2. **Deploy to Render**
- Go to [render.com](https://render.com)
- Sign in with GitHub
- Click "New" → "Web Service"
- Connect your GitHub repository
- Configure:
  - Name: `fmhy-api`
  - Runtime: `Python`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `bash start.sh`
- Click "Create Web Service"

3. **Get your API URL**
- Render gives you a free URL like `https://fmhy-api.onrender.com`

---

## Deploy with Docker

### Build and run locally
```bash
docker build -t fmhy-api .
docker run -p 8000:8000 fmhy-api
```

### Deploy to any container platform
- AWS ECS
- Google Cloud Run
- Azure Container Apps
- DigitalOcean App Platform

---

## Deploy to VPS (DigitalOcean, Hetzner, etc.)

### Steps

1. **SSH into your server**
```bash
ssh root@your-server-ip
```

2. **Install dependencies**
```bash
# Ubuntu/Debian
apt update && apt install -y python3 python3-pip git

# Clone repo
git clone https://github.com/YOUR-USERNAME/fmhy-api.git
cd fmhy-api
pip3 install -r requirements.txt
```

3. **Setup as systemd service**
```bash
cat > /etc/systemd/system/fmhy-api.service << EOF
[Unit]
Description=FMHY API
After=network.target

[Service]
User=root
WorkingDirectory=/root/fmhy-api
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable fmhy-api
systemctl start fmhy-api
```

4. **Setup nginx reverse proxy (optional)**
```bash
apt install nginx
cat > /etc/nginx/sites-available/fmhy-api << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/fmhy-api /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## Environment Variables (Optional)

You can set these in your hosting platform:

- `PORT`: Port to run on (default: 8000)
- `DATABASE_PATH`: Path to SQLite database (default: fmhy.db)

---

## API URL Examples

After deployment, your API will be available at:

- Railway: `https://your-app.up.railway.app`
- Render: `https://fmhy-api.onrender.com`
- VPS: `http://your-server-ip:8000` or `https://your-domain.com`

### Test your deployment
```bash
curl https://your-app-url/api/stats
curl https://your-app-url/api/search?q=anime&limit=5
```

---

## Auto-Updates

The API includes a built-in update endpoint:
```bash
# Trigger update via API
curl -X POST https://your-app-url/api/update
```

Or setup the cron script on your server:
```bash
./setup-cron.sh
```
