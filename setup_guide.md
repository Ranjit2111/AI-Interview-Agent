# AI Interviewer Agent - Local Setup Guide

This guide will help you set up and run the AI Interviewer Agent locally on your machine. The project consists of a FastAPI backend and a React frontend with real-time voice capabilities.

## Prerequisites

- **Python 3.8+** (with pip)
- **Node.js 16+** (with npm)
- **Git** (to clone the repository)
- **Windows** (this guide uses the provided batch scripts)

## Step 1: Clone the Repository

```bash
git clone https://github.com/Ranjit2111/AI-Interview-Agent.git
cd AI-Interview-Agent
```

## Step 2: Obtain Required API Keys

The application requires several API keys to function properly. Here's how to get each one:

### 2.1 Google API Key (Required)
**Used for**: Search capabilities and additional AI features

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Sign up for a Google Cloud account (requires credit card but has $300 free credit)
3. Create a new project:
   - Click **"Select a project"** → **"New Project"**
   - Enter project name: `ai-interviewer-agent`
   - Click **"Create"**
4. Enable required APIs:
   - Go to **"APIs & Services"** → **"Library"**
   - Search and enable **"Custom Search API"**
   - Search and enable **"Places API"** (if needed)
5. Create API key:
   - Go to **"APIs & Services"** → **"Credentials"**
   - Click **"Create Credentials"** → **"API Key"**
   - Copy the generated key

**Cost**: $300 free credit, then pay-per-use

### 2.2 Serper API Key (Required)
**Used for**: Enhanced search functionality

1. Go to [Serper.dev](https://serper.dev)
2. Sign up with your email address
3. Verify your email and complete registration
4. Navigate to **"API Key"** section in dashboard
5. Copy your API key

**Cost**: Free tier includes 2,500 searches/month, then $5/1000 searches

### 2.3 AssemblyAI API Key (Required)
**Used for**: Advanced speech-to-text and audio analysis

1. Go to [AssemblyAI](https://www.assemblyai.com)
2. Sign up for a free account
3. Navigate to **"Your API token"** in the dashboard
4. Copy your API token

**Cost**: Free tier includes 5 hours/month, then $0.37/hour

### 2.4 AWS Credentials (Required for Voice Synthesis)
**Used for**: Text-to-speech using Amazon Polly

1. Go to [AWS Console](https://aws.amazon.com/console/)
2. Sign up for AWS account (requires credit card but has free tier)
3. Navigate to **IAM** service
4. Create a new user:
   - Click **"Users"** → **"Add users"**
   - Username: `ai-interviewer-user`
   - Select **"Access key - Programmatic access"**
   - Click **"Next: Permissions"**
5. Attach permissions:
   - Click **"Attach existing policies directly"**
   - Search and select **"AmazonPollyFullAccess"**
   - Click **"Next: Tags"** → **"Next: Review"** → **"Create user"**
6. Copy the credentials:
   - **Access Key ID**
   - **Secret Access Key**
   - Set region to: `us-east-1`

**Cost**: Free tier includes 5M characters/month for speech synthesis

### 2.5 Deepgram API Key (Required)
**Used for**: Real-time speech-to-text conversion

1. Go to [Deepgram Console](https://console.deepgram.com)
2. Sign up for a free account
3. Complete email verification
4. Navigate to **"API Keys"** in the dashboard
5. Copy your default API key

**Cost**: Free tier includes 12,000 minutes/month, then pay-per-use

### 2.6 Supabase Database (Required)
**Used for**: User authentication and data storage

1. Go to [Supabase](https://supabase.com)
2. Sign up and create a new project:
   - Click **"New project"**
   - Choose your organization
   - Enter project name: `ai-interviewer-agent`
   - Set database password (save this!)
   - Select region closest to you
   - Click **"Create new project"**
3. Wait for project setup (2-3 minutes)
4. Go to **Settings** → **API**
5. Copy these values:
   - **Project URL** (looks like `https://xxx.supabase.co`)
   - **Service Role Key** (starts with `eyJ`, this is the service key)
6. Go to **Settings** → **Auth** → **URL Configuration**
7. Copy the **JWT Secret**

**Cost**: Free tier includes 500MB database, 2GB bandwidth/month

## Step 3: Configure Environment Variables

1. Create a `.env` file in the project root directory
2. Copy the template below and replace all placeholder values with your actual API keys:

```env
# Google API Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Search Service
SERPER_API_KEY=your_serper_api_key_here

# Speech Recognition
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

# AWS Configuration for Text-to-Speech
AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
AWS_REGION=us-east-1

# Real-time Speech Recognition
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Database Configuration (Supabase)
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here
SUPABASE_JWT_SECRET=your_supabase_jwt_secret_here

# Amazon Polly TTS Configuration
# Engine options: "generative" (high quality, limited usage) or "long-form" (better for longer content)
POLLY_ENGINE=long-form
# Voice options for long-form: Gregory, Ruth, Danielle, Patrick (English), Alba, Raúl (Spanish)
# Voice options for generative: Matthew, Joanna, Danielle, Ruth, Stephen, etc.
POLLY_DEFAULT_VOICE=Gregory
```

## Step 4: Set Up Database Schema

1. Log into your Supabase project dashboard
2. Go to **SQL Editor**
3. Navigate to the project directory and find `backend/database/schema.sql`
4. Copy the entire contents of this file
5. Paste it into the Supabase SQL Editor and run it
6. This will create all necessary tables for user management and interview data

## Step 5: Run the Application

### Option A: Using the Automated Script (Recommended)

1. **Double-click** `no_stage.bat` or run from command prompt:
   ```cmd
   no_stage.bat
   ```

This script will:
- Create a Python virtual environment in the backend folder
- Install all backend dependencies
- Start the backend server on `http://localhost:8000`
- Install frontend dependencies
- Start the frontend on `http://localhost:8080`

### Option B: Manual Setup

**Backend (Terminal 1):**
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=%CD%\..
python -m uvicorn main:app --reload --port 8000
```

**Frontend (Terminal 2):**
```cmd
cd frontend
npm install
npm run dev
```

## Step 6: Verify Setup

1. **Backend Health Check**: Visit `http://localhost:8000/health`
   - Should return JSON with status information and TTS warmup details

2. **Frontend**: Visit `http://localhost:8080`
   - Should load the application interface

3. **Test Registration**: Create a new account to verify database connectivity

4. **Test Voice Features**: 
   - Ensure microphone permissions are granted in browser
   - Test speech-to-text functionality
   - Verify text-to-speech playback

## Step 7: Using the Application

Once everything is running:

1. **Register/Login**: Create an account or login with existing credentials
2. **Configure Interview**: 
   - Set target role
   - Upload resume (optional)
   - Add job description (optional)
   - Choose interview duration and difficulty
3. **Start Interview**: Click start and begin voice-based interview
4. **Review Results**: Get detailed feedback and coaching after completion

## Troubleshooting

### Common Issues:

**"Module not found" errors:**
- Ensure Python virtual environment is activated
- Run `pip install -r requirements.txt` again

**"Failed to fetch" on frontend:**
- Check if backend is running on port 8000
- Verify all environment variables are set correctly in `.env` file

**Speech features not working:**
- Verify Deepgram and AssemblyAI API keys are correct
- Check AWS credentials and Polly permissions
- Ensure microphone permissions in browser

**Database connection errors:**
- Verify Supabase URL, service key, and JWT secret
- Check if database schema was created successfully
- Ensure Supabase project is not paused

**Voice synthesis not working:**
- Check AWS credentials are correct
- Verify IAM user has AmazonPollyFullAccess policy
- Check AWS region is set to us-east-1

### Getting Help

If you encounter issues:

1. Check console output in both backend and frontend terminals
2. Verify all API keys are correctly set in `.env` file
3. Ensure all services (Supabase, AWS, etc.) are active and properly configured
4. Contact the developer:
   - **Email**: ranjitn.dev@gmail.com
   - **LinkedIn**: [Ranjit N](https://www.linkedin.com/in/ranjit-n/)

## Cost Summary

- **Google Cloud**: $300 free credit, minimal usage costs
- **Serper**: Free tier (2,500 searches/month) sufficient for testing
- **AssemblyAI**: Free tier (5 hours/month) sufficient for moderate use
- **AWS**: Free tier sufficient for moderate speech synthesis
- **Deepgram**: Free tier (12,000 minutes/month) sufficient for extensive testing
- **Supabase**: Free tier sufficient for personal use
- **Total estimated cost**: $0-10/month for regular personal use

## Project Features

Once running, you can:
- Practice realistic AI-powered interviews
- Get real-time voice coaching and feedback
- Upload resumes for personalized questions
- Add job descriptions for role-specific interviews
- Review comprehensive post-interview reports
- Track progress over multiple interview sessions

Enjoy your AI-powered interview practice! 🚀 