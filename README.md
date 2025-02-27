# AI Interview Coach

An interactive AI-powered interview coach that provides real-time feedback on your interview responses using voice interaction.

## Features

- Voice-based interview interactions
- Real-time speech-to-text conversion
- AI-powered response analysis
- Detailed feedback with strengths and areas for improvement
- Text-to-speech feedback playback
- Beautiful and responsive UI

## Tech Stack

### Frontend (Next.js + Vercel)
- Next.js 14
- TypeScript
- Tailwind CSS
- Web Speech API
- React Icons
- Axios

### Backend (FastAPI + Hugging Face Spaces)
- FastAPI
- Google Gemini API
- Coqui TTS
- Python 3.9+

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the backend directory with:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   ```

4. Run the backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Deployment

### Backend Deployment (Hugging Face Spaces)
1. Create a new Space on Hugging Face
2. Select FastAPI template
3. Upload the backend files
4. Add your environment variables in the Space settings

### Frontend Deployment (Vercel)
1. Push your code to GitHub
2. Create a new project on Vercel
3. Import your GitHub repository
4. Configure environment variables if needed
5. Deploy

## Usage

1. Open the application in your browser
2. Click the "Start Recording" button
3. Speak your response to the interview question
4. Click "Stop Recording" when finished
5. Wait for AI feedback
6. Review the detailed feedback and listen to the audio response

## Contributing

Feel free to open issues and pull requests for any improvements you'd like to add.

## License

MIT License 