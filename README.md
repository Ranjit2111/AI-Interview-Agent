# AI Interviewer Agent 🚀

[![License: MIT](httpss://img.shields.io/badge/License-MIT-yellow.svg)](httpss://opensource.org/licenses/MIT)

The **AI Interviewer Agent** is a sophisticated, AI-powered platform designed to help users practice and excel in job interviews. It leverages a multi-agent system to provide a realistic, interactive, and adaptive interview experience, complete with real-time coaching, in-depth performance analysis, and personalized learning recommendations.

The frontend is a sleek, modern single-page application built with React and Vite, designed for an intuitive user experience and deployed on **Vercel**. The powerful backend is a FastAPI application, containerized with Docker and deployed on **Microsoft Azure**, ensuring scalability and reliability.

---

## ✨ Core Features

This platform is more than just a Q&A bot. It's a comprehensive interview preparation ecosystem.

### 1. Dynamic AI Interviewer Agent

- **Adaptive Questioning**: The AI interviewer doesn't just follow a script. It generates relevant questions based on the job role, job description, and the content of your resume. It also asks insightful follow-up questions based on your answers.
- **Multiple Interview Styles**: You can choose from various interview styles (`Formal`, `Casual`, `Technical`, `Aggressive`) to simulate different real-world scenarios.
- **Configurable Difficulty**: Adjust the interview's difficulty (`Easy`, `Medium`, `Hard`) to match your preparation level.
- **Time-Aware Sessions**: Practice under pressure with timed interviews, forcing you to give concise and effective answers.

### 2. Real-time Agentic Coach

- **Turn-by-Turn Feedback**: As you answer each question, a silent "Coach Agent" analyzes your response in the background. It provides immediate, private feedback on your clarity, confidence, and the substance of your answer.
- **In-depth Performance Metrics**: The coach tracks various aspects of your performance throughout the session.

### 3. Personalized Learning Engine

- **Intelligent Resource Recommendations**: After the interview, the system identifies your key areas for improvement.
- **Curated Learning Materials**: Based on this analysis, the Coach Agent performs a targeted web search to find and recommend high-quality articles, guides, and videos to help you strengthen your weak spots. Each recommendation comes with a justification for why it's relevant to you.

### 4. Advanced Speech & Voice Integration

- **High-Fidelity STT/TTS**: Experience seamless, natural-sounding conversations thanks to advanced Speech-to-Text and Text-to-Speech services.
- **Voice Selection**: Choose the voice for your AI interviewer to personalize the experience.

### 5. Comprehensive Interview Customization

- **Tailor Your Practice**: Before starting, you can configure every aspect of the interview:
  - **Job Role & Company**: Target a specific role and company.
  - **Job Description**: Paste a real job description for hyper-relevant questions.
  - **Resume Upload**: Upload your resume (TXT, PDF, DOCX) to have the AI ask questions based on your experience.
  - **Duration & More**: Set the desired length and other parameters.

### 6. In-depth Post-Interview Analysis

- **Final Coaching Summary**: Once the session is over, you receive a detailed report that includes:
  - **Overall Performance Score**: A holistic evaluation of your interview.
  - **Strengths & Weaknesses**: A breakdown of what you did well and where you can improve.
  - **Actionable Improvement Plan**: Concrete steps to take next.
- **Full Transcript Review**: Replay the entire interview, complete with your answers and the coach's per-turn feedback.

### 7. Secure Session Management & Authentication

- **User Accounts**: Sign up and log in to track your progress across multiple sessions.
- **Persistent Sessions**: Your interview sessions are saved to a **Supabase** PostgreSQL database, so you can review them later.
- **Data Security**: Your data is handled securely, with user authentication and managed sessions.

### 8. Interactive & Modern UI

- **Built with React & Shadcn/UI**: A beautiful, responsive, and intuitive user interface that makes practicing a pleasure.
- **Dynamic Visualizations**: The UI includes engaging animations and visual cues to provide a rich, interactive experience.

---

## 🏗️ System Architecture

The application is built on a modern, decoupled architecture, with a React frontend and a Python backend. The core of the application is a multi-agent system orchestrated by a central session manager.

- **Frontend**: A [Vite](httpss://vitejs.dev/)-powered [React](httpss://reactjs.org/) application using [TypeScript](httpss://www.typescriptlang.org/) and the [Shadcn/UI](httpss://ui.shadcn.com/) component library. It communicates with the backend via a RESTful API.
- **Backend**: A [FastAPI](httpss://fastapi.tiangolo.com/) application that serves the API. Its key components are:

  - **`AgentSessionManager` (Orchestrator)**: The central coordinator. It manages the lifecycle of an interview session, routes messages between the user and the agents, and maintains the state.
  - **`InterviewerAgent`**: Responsible for conducting the interview. It generates questions, decides the next action (e.g., ask a question, follow up, conclude), and adapts its behavior based on the session configuration.
  - **`AgenticCoachAgent`**: The "silent partner." It evaluates user responses, provides turn-by-turn feedback, generates the final comprehensive summary, and finds relevant learning resources.
  - **Services**: A collection of services for interacting with external systems, including the LLM (`LLMService`), web search (`SearchService`), and database persistence (`ThreadSafeSessionRegistry`).
- **Database**: [Supabase](httpss://supabase.io/) (PostgreSQL) is used for user authentication and for storing session data, including conversation history and feedback.
- **LLM**: The AI's intelligence is powered by Google's **Gemini** models.

---

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, LangChain, Google Gemini
- **Frontend**: React, TypeScript, Vite, TailwindCSS, Shadcn/UI
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Docker, Azure Web Apps (Backend), Vercel (Frontend)
- **Core Libraries**: `pydantic`, `asyncio`, `axios`

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- Docker
- Access to Google AI (Gemini) API key
- A Supabase project for database and auth
- A Serper API key for search

### Backend Setup (Local)

1. **Clone the repository:**
   ```bash
   git clone httpss://github.com/your-username/ai-interviewer-agent.git
   cd ai-interviewer-agent
   ```
2. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```
3. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Create a `.env` file** in the `backend` directory and add your environment variables:
   ```env
   GOOGLE_API_KEY="your-gemini-api-key"
   SUPABASE_URL="your-supabase-project-url"
   SUPABASE_KEY="your-supabase-service-role-key"
   SERPER_API_KEY="your-serper-api-key"
   # ... other variables as needed from azure-env-template.txt
   ```
6. **Run the backend server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup (Local)

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Create a `.env.local` file** in the `frontend` directory and add your environment variables:
   ```env
   VITE_API_BASE_URL="http://localhost:8000"
   VITE_SUPABASE_URL="your-supabase-project-url"
   VITE_SUPABASE_ANON_KEY="your-supabase-anon-key"
   ```
4. **Run the frontend development server:**
   ```bash
   npm run dev
   ```
5. Open your browser and navigate to `http://localhost:5173`.

---

## ☁️ Deployment

### Backend on Microsoft Azure (App Service)

The backend is designed to be containerized with Docker and deployed as a Web App on Azure.

#### Step 1: Create Azure Resource Group

- A resource group is a container for your Azure resources.

1. Login to the [Azure Portal](httpss://portal.azure.com/).
2. Go to **Resource groups** > **+ Create**.
3. Set a name (e.g., `ai-interviewer-rg`) and region.
4. Click **Review + create**, then **Create**.

#### Step 2: Create Azure Container Registry (ACR)

- ACR stores your private Docker container images.

1. In the Azure Portal, search for **Container Registry** and click **Create**.
2. Configure it:
   - **Resource group**: Select the one you just created.
   - **Registry name**: A globally unique name (e.g., `ai-interviewer-registry`).
   - **SKU**: **Basic** is a good starting point.
3. Click **Review + create**, then **Create**.
4. Once created, go to **Access keys** in your ACR resource and **Enable Admin user**. Note the username and password.

#### Step 3: Build and Push Docker Image to ACR

1. **Login to your ACR instance** from your local machine:
   ```bash
   docker login your-registry-name.azurecr.io
   # Use the admin username and password from the previous step.
   ```
2. **Build the Docker image** from the root of the project:
   ```bash
   docker build -t your-registry-name.azurecr.io/ai-interviewer-backend:latest .
   ```
3. **Push the image to ACR:**
   ```bash
   docker push your-registry-name.azurecr.io/ai-interviewer-backend:latest
   ```

#### Step 4: Create Azure App Service Plan

- This defines the compute resources for your app.

1. In the Azure Portal, search for **App Service Plan** and click **Create**.
2. Configure it:
   - **Resource group**: Use the same one.
   - **Name**: e.g., `ai-interviewer-plan`.
   - **Operating System**: **Linux**.
   - **Pricing tier**: Choose a suitable tier (e.g., `B1` or `P1V2`).

#### Step 5: Create Azure Web App (App Service)

- This is the service that will run your Docker container.

1. In the Azure Portal, search for **Web App** and click **Create**.
2. **Basics Tab**:
   - **Resource group**: Use the same one.
   - **Name**: A unique name for your app (e.g., `ai-interviewer-api`). This will be part of your URL.
   - **Publish**: **Docker Container**.
   - **Operating System**: **Linux**.
   - **App Service Plan**: Select the plan you created.
3. **Docker Tab**:
   - **Image Source**: **Azure Container Registry**.
   - **Registry**: Select your ACR instance.
   - **Image**: Select your `ai-interviewer-backend` image.
   - **Tag**: `latest`.
4. **Configuration**:
   - After creation, go to your App Service resource.
   - In **Settings > Configuration > Application settings**, add all the environment variables from your `.env` file (e.g., `GOOGLE_API_KEY`, `SUPABASE_URL`, etc.).
   - **Crucially, add a `WEBSITES_PORT` setting with the value `8000`** to tell Azure which port your FastAPI app is running on inside the container.
5. Click **Save**. Azure will pull the image and start your application. Your backend will be available at `httpss://your-app-name.azurewebsites.net`.

### Frontend on Vercel

The frontend can be easily deployed with Vercel.

1. **Push your code to a Git repository** (GitHub, GitLab, Bitbucket).
2. **Sign up or log in to [Vercel](httpss://vercel.com/)** with your Git provider account.
3. **Create a New Project** and import your repository.
4. **Configure the project**:
   - Vercel should automatically detect that you are using Vite.
   - **Set the Root Directory** to `frontend`.
   - **Add Environment Variables**: In the project settings, add your frontend environment variables (e.g., `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`). Use your deployed Azure backend URL for `VITE_API_BASE_URL`.
5. Click **Deploy**. Vercel will build and deploy your site.

The `vercel.json` file in the root directory ensures that Vercel correctly handles routing for the single-page application.

---

## 📂 Project Structure

```
.
├── backend/
│   ├── api/            # FastAPI routers for different features
│   ├── agents/         # Core logic for Interviewer and Coach agents
│   ├── services/       # Services for DB, LLMs, Search, etc.
│   ├── database/       # Database management (Supabase)
│   ├── middleware/     # Custom FastAPI middleware
│   ├── schemas/        # Pydantic models for data validation
│   ├── utils/          # Helper functions and utilities
│   ├── main.py         # FastAPI app entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/ # Reusable React components
│   │   ├── pages/      # Main application pages
│   │   ├── hooks/      # Custom React hooks (e.g., useInterviewSession)
│   │   ├── services/   # API communication layer (axios)
│   │   ├── contexts/   # React context providers (e.g., AuthContext)
│   │   └── App.tsx     # Main application component
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── Dockerfile          # For containerizing the backend
└── README.md
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
