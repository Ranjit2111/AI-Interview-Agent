# 🚀 Azure App Service + Vercel Deployment Guide

## 📋 Deployment Architecture

- **Frontend**: Vercel (React/Vite)
- **Backend**: Azure App Service (FastAPI)
- **Database**: Supabase (already configured)
- **WebSockets**: Supported via Azure App Service

---

## 🔧 Azure App Service Backend Deployment

### **Step 1: Create Azure App Service**
1. Go to Azure Portal
2. Create new App Service
3. Choose:
   - **Runtime**: Python 3.10
   - **Region**: Your preferred region
   - **Pricing tier**: Basic B1 or higher (for WebSocket support)

### **Step 2: Configure Application Settings**
In Azure Portal → App Service → Configuration → Application Settings:

```bash
# Required Environment Variables
PYTHONPATH=/home/site/wwwroot
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DEEPGRAM_API_KEY=your_deepgram_api_key
OPENAI_API_KEY=your_openai_api_key
```

### **Step 3: Get Your Azure App Service URL**
Your backend URL will be: `https://your-app-name.azurewebsites.net`

---

## 🌐 Vercel Frontend Deployment

### **Step 1: Connect Repository**
1. Go to [Vercel Dashboard](https://vercel.com)
2. Import your GitHub repository
3. Select "Frontend" as root directory (or configure build settings)

### **Step 2: Configure Build Settings**
In Vercel Dashboard → Project Settings → General:

```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "cd frontend && npm install",
  "framework": "vite"
}
```

### **Step 3: Set Environment Variables**
In Vercel Dashboard → Project Settings → Environment Variables:

| Variable Name | Value | Environment |
|---------------|-------|-------------|
| `VITE_API_BASE_URL` | `https://your-app-name.azurewebsites.net` | Production |
| `VITE_WS_BASE_URL` | `wss://your-app-name.azurewebsites.net` | Production |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Development |
| `VITE_WS_BASE_URL` | `ws://localhost:8000` | Development |

---

## 🔄 Complete Deployment Steps

### **Backend (Azure App Service)**
1. Create App Service with Python 3.10
2. Configure application settings (environment variables)
3. Deploy code:
   ```bash
   # Option 1: GitHub Actions (Recommended)
   # Azure will auto-setup CI/CD from your repository
   
   # Option 2: Direct deployment
   cd backend
   zip -r ../backend.zip .
   # Upload via Azure Portal or Azure CLI
   ```

### **Frontend (Vercel)**
1. Connect GitHub repository to Vercel
2. Configure build settings (use provided `vercel.json`)
3. Set environment variables
4. Deploy automatically on push to main branch

---

## 🧪 Testing Your Deployment

### **Backend Testing**
```bash
# Health check
curl https://your-app-name.azurewebsites.net/health

# API test
curl https://your-app-name.azurewebsites.net/api/health
```

### **Frontend Testing**
```bash
# Visit your Vercel URL
https://your-frontend-name.vercel.app

# Check environment variables in browser console
console.log(import.meta.env.VITE_API_BASE_URL)
```

### **WebSocket Testing**
```javascript
// Test WebSocket connection in browser console
const ws = new WebSocket('wss://your-app-name.azurewebsites.net/api/speech-to-text/stream');
ws.onopen = () => console.log('WebSocket connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

---

## 🔧 Local Development Setup

### **With Environment Variables**
```bash
# Run the updated batch file
./run_venv.bat

# Or set manually:
set VITE_API_BASE_URL=http://localhost:8000
set VITE_WS_BASE_URL=ws://localhost:8000
cd frontend && npm run dev
```

---

## 🚨 Troubleshooting

### **Common Issues**

1. **CORS Errors**
   - Ensure Azure App Service allows your Vercel domain
   - Check CORS configuration in FastAPI

2. **WebSocket Connection Failures**
   - Verify Azure App Service tier supports WebSockets
   - Check WebSocket URL uses `wss://` for production

3. **Environment Variables Not Loading**
   - Verify all `VITE_` prefixed variables are set in Vercel
   - Check variable names match exactly

4. **Build Failures**
   - Ensure `vercel.json` is in project root
   - Check build command paths are correct

---

## 📝 Environment Variables Summary

### **Azure App Service (Backend)**
```env
PYTHONPATH=/home/site/wwwroot
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DEEPGRAM_API_KEY=your_deepgram_api_key
OPENAI_API_KEY=your_openai_api_key
```

### **Vercel (Frontend)**
```env
# Production
VITE_API_BASE_URL=https://your-app-name.azurewebsites.net
VITE_WS_BASE_URL=wss://your-app-name.azurewebsites.net

# Development  
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

---

## 🎯 Next Steps

1. **Create Azure App Service** with your chosen name
2. **Deploy backend** using GitHub Actions or direct upload
3. **Configure environment variables** in Azure Portal
4. **Deploy frontend** to Vercel with environment variables
5. **Test all functionality** including WebSockets
6. **Set up custom domains** (optional)

Your application will be accessible at:
- **Frontend**: `https://your-frontend-name.vercel.app`
- **Backend**: `https://your-app-name.azurewebsites.net` 