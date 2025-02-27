'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaMicrophone, FaStop } from 'react-icons/fa';
import type { 
  SpeechRecognition, 
  SpeechRecognitionEvent, 
  SpeechRecognitionResult,
  SpeechRecognitionAlternative 
} from '@/types';

interface FeedbackData {
  overall_score: number;
  strengths: string[];
  areas_for_improvement: string[];
  technical_analysis: string;
  communication_analysis: string;
  suggested_improvement: string;
}

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [feedback, setFeedback] = useState<FeedbackData | null>(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState('Tell me about yourself.');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        setRecognition(recognition);

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          const results = Array.from(event.results) as SpeechRecognitionResult[];
          const transcript = results
            .map(result => (result[0] as SpeechRecognitionAlternative).transcript)
            .join('');
          setTranscript(transcript);
        };
      }
    }
  }, []);

  const startRecording = () => {
    if (recognition) {
      recognition.start();
      setIsRecording(true);
    }
  };

  const stopRecording = async () => {
    if (recognition) {
      recognition.stop();
      setIsRecording(false);
      
      try {
        const response = await axios.post('http://localhost:8000/evaluate', {
          question: currentQuestion,
          user_response: transcript
        });

        const feedbackData = response.data.feedback;
        setFeedback(typeof feedbackData === 'string' ? JSON.parse(feedbackData) : feedbackData);
        
        // Convert base64 audio to URL
        const audioBlob = new Blob(
          [Uint8Array.from(atob(response.data.audio), c => c.charCodeAt(0))],
          { type: 'audio/wav' }
        );
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
      } catch (error) {
        console.error('Error getting feedback:', error);
      }
    }
  };

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">AI Interview Coach</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-2xl mb-4">Current Question:</h2>
          <p className="text-xl text-blue-400 mb-6">{currentQuestion}</p>
          
          <div className="flex justify-center mb-6">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`flex items-center space-x-2 px-6 py-3 rounded-full text-lg ${
                isRecording ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isRecording ? (
                <React.Fragment>
                  <FaStop className="mr-2" />
                  Stop Recording
                </React.Fragment>
              ) : (
                <React.Fragment>
                  <FaMicrophone className="mr-2" />
                  Start Recording
                </React.Fragment>
              )}
            </button>
          </div>

          {transcript && (
            <div className="mb-6">
              <h3 className="text-xl mb-2">Your Response:</h3>
              <p className="bg-gray-700 p-4 rounded">{transcript}</p>
            </div>
          )}
        </div>

        {feedback && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl mb-4">AI Feedback</h2>
            
            <div className="grid gap-6">
              <div>
                <h3 className="text-xl text-blue-400 mb-2">Overall Score</h3>
                <div className="flex items-center">
                  <div className="w-full bg-gray-700 rounded-full h-4">
                    <div
                      className="bg-blue-600 h-4 rounded-full"
                      style={{ width: `${(feedback.overall_score / 10) * 100}%` }}
                    ></div>
                  </div>
                  <span className="ml-4">{feedback.overall_score}/10</span>
                </div>
              </div>

              <div>
                <h3 className="text-xl text-green-400 mb-2">Strengths</h3>
                <ul className="list-disc list-inside">
                  {feedback.strengths.map((strength: string, index: number) => (
                    <li key={index} className="mb-1">{strength}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-xl text-yellow-400 mb-2">Areas for Improvement</h3>
                <ul className="list-disc list-inside">
                  {feedback.areas_for_improvement.map((area: string, index: number) => (
                    <li key={index} className="mb-1">{area}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-xl text-purple-400 mb-2">Technical Analysis</h3>
                <p className="bg-gray-700 p-4 rounded">{feedback.technical_analysis}</p>
              </div>

              <div>
                <h3 className="text-xl text-pink-400 mb-2">Communication Analysis</h3>
                <p className="bg-gray-700 p-4 rounded">{feedback.communication_analysis}</p>
              </div>

              <div>
                <h3 className="text-xl text-orange-400 mb-2">Suggested Improvement</h3>
                <p className="bg-gray-700 p-4 rounded">{feedback.suggested_improvement}</p>
              </div>
            </div>

            {audioUrl && (
              <div className="mt-6">
                <h3 className="text-xl mb-2">Audio Feedback</h3>
                <audio controls src={audioUrl} className="w-full" />
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
} 