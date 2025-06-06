# 🚀 Azure App Service Deployment Checklist

## ✅ Pre-Deployment Setup

### 1. Docker Files Ready

- [X] `Dockerfile` created in project root
- [X] `.dockerignore` created in project root
- [X] `start.sh` script created and executable
- [X] `azure-env-template.txt` with environment variables

### 2. Azure Resources Setup

- [ ] Azure Container Registry created (`ranjitaiinterview`)
- [ ] Azure App Service Plan created (B1 or higher for WebSockets)
- [ ] Azure Web App created with Linux + Docker Container

### 3. Environment Variables Ready

- [ ] SUPABASE_URL
- [ ] SUPABASE_ANON_KEY
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] DEEPGRAM_API_KEY
- [ ] OPENAI_API_KEY
- [ ] GOOGLE_API_KEY (optional)

## 🐳 Docker Commands to Execute

Run these commands in your project root directory:

```bash
# 1. Login to Azure
az login

# 2. Login to your container registry
az acr login --name ranjitaiinterview

# 3. Build the Docker image
docker build -t aiinterviewer-backend .

# 4. Tag the image for Azure Container Registry
docker tag aiinterviewer-backend ranjitaiinterview.azurecr.io/aiinterviewer-backend:latest

# 5. Push the image to Azure Container Registry
docker push ranjitaiinterview.azurecr.io/aiinterviewer-backend:latest
```

## ⚙️ Azure Portal Configuration

### 1. Web App Configuration

1. Go to your Web App in Azure Portal
2. Configuration → General Settings:
   - **Web sockets**: On
   - **Always On**: On (recommended)
   - **Platform**: Linux
   - **Stack**: Docker

### 2. Container Settings

1. Go to Deployment Center
2. Set:
   - **Source**: Azure Container Registry
   - **Registry**: ranjitaiinterview
   - **Image**: aiinterviewer-backend
   - **Tag**: latest

### 3. Application Settings

Copy from `azure-env-template.txt`:

```
PYTHONPATH=/app
PORT=8000
WEBSITES_PORT=8000
SUPABASE_URL=your_actual_value
SUPABASE_ANON_KEY=your_actual_value
SUPABASE_SERVICE_ROLE_KEY=your_actual_value
DEEPGRAM_API_KEY=your_actual_value
OPENAI_API_KEY=your_actual_value
LOG_LEVEL=INFO
```

## 🧪 Testing Your Deployment

### 1. Health Check

```bash
curl https://your-app-name.azurewebsites.net/health
```

### 2. API Test

```bash
curl https://your-app-name.azurewebsites.net/
```

### 3. WebSocket Test

```javascript
// In browser console
const ws = new WebSocket('wss://your-app-name.azurewebsites.net/api/speech-to-text/stream');
ws.onopen = () => console.log('WebSocket connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

## 🔄 Update Frontend Environment Variables

After successful deployment, update your Vercel environment variables:

```bash
VITE_API_BASE_URL=https://your-app-name.azurewebsites.net
VITE_WS_BASE_URL=wss://your-app-name.azurewebsites.net
```

## 🚨 Troubleshooting

### Common Issues:

1. **Container won't start**: Check logs in Azure Portal → Monitoring → Log stream
2. **Environment variables not loading**: Restart the Web App after setting variables
3. **WebSocket connection fails**: Ensure Web sockets are enabled and using B1+ plan
4. **Import errors**: Check if all dependencies are in requirements.txt

### Useful Commands:

```bash
# Check if image exists in registry
az acr repository list --name ranjitaiinterview

# View Web App logs
az webapp log tail --name your-app-name --resource-group your-resource-group
```

## 📋 Final Steps

- [ ] Docker image built and pushed successfully
- [ ] Web App configured with correct container image
- [ ] Environment variables set in Azure Portal
- [ ] WebSockets enabled
- [ ] Health endpoint responds successfully
- [ ] Frontend updated with new backend URL
- [ ] End-to-end test completed

🎉 **Your AI Interviewer backend is ready for production!**
