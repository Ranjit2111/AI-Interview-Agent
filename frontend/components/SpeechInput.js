import { useEffect, useState, useCallback } from 'react';
import SpeechRecognition from './SpeechRecognition';

/**
 * SpeechInput component that provides a user interface for speech recognition.
 * It handles both Web Speech API and fallback upload methods.
 * 
 * @param {Object} props Component props
 * @param {Function} props.onSpeechInput Callback when speech input is ready
 * @param {string} props.language Language code for speech recognition
 * @param {boolean} props.autoStart Whether to start recognition automatically
 */
const SpeechInput = ({ 
  onSpeechInput, 
  language = 'en-US', 
  autoStart = false 
}) => {
  const [initialLoad, setInitialLoad] = useState(true);
  const [showTranscript, setShowTranscript] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [isListening, setIsListening] = useState(autoStart);
  const [muted, setMuted] = useState(!autoStart);
  const [errorMessage, setErrorMessage] = useState('');
  const [recognition, setRecognition] = useState(null);
  
  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        setErrorMessage('Speech recognition not supported in this browser');
        return;
      }

      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = language;

      recognitionInstance.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('');
        
        const isFinal = event.results[event.results.length - 1].isFinal;
        
        if (isFinal && onSpeechInput) {
          onSpeechInput(transcript);
        }
      };

      recognitionInstance.onerror = (event) => {
        if (event.error === 'no-speech') {
          console.log('No speech detected');
        } else {
          setErrorMessage(`Error: ${event.error}`);
          console.error('Speech recognition error', event.error);
          setIsListening(false);
        }
      };

      recognitionInstance.onend = () => {
        // If we're still supposed to be listening, restart
        if (isListening && !muted) {
          recognitionInstance.start();
        } else {
          setIsListening(false);
        }
      };

      setRecognition(recognitionInstance);
      
      // Start recognition automatically if autoStart is true
      if (autoStart) {
        try {
          recognitionInstance.start();
        } catch (err) {
          console.error('Error starting speech recognition:', err);
        }
      }

      // Clean up
      return () => {
        try {
          recognitionInstance.stop();
        } catch (err) {
          // Ignore errors on cleanup
        }
      };
    }
  }, [language, onSpeechInput, autoStart]);
  
  // Handle toggling listening state
  const toggleListening = useCallback(() => {
    if (!recognition) return;
    
    try {
      if (isListening) {
        recognition.stop();
        setIsListening(false);
        setMuted(true);
      } else {
        recognition.start();
        setIsListening(true);
        setMuted(false);
      }
    } catch (err) {
      console.error('Error toggling speech recognition:', err);
      setErrorMessage(`Error: ${err.message}`);
    }
  }, [isListening, recognition]);
  
  // Handle file upload for AssemblyAI fallback
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadedFile(file);
    }
  };
  
  const handleFileUpload = async () => {
    if (!uploadedFile) return;
    
    setIsUploading(true);
    setUploadError(null);
    
    const formData = new FormData();
    formData.append('audio_file', uploadedFile);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/speech-to-text`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.transcript) {
        onSpeechInput(data.transcript);
      } else {
        throw new Error('No transcript returned from server');
      }
    } catch (error) {
      console.error('Error uploading audio file:', error);
      setUploadError(error.message);
    } finally {
      setIsUploading(false);
      setUploadedFile(null);
    }
  };
  
  return (
    <div className="flex flex-col space-y-4 w-full">
      {/* Speech Recognition UI */}
      {isListening ? (
        <div className="flex flex-col space-y-2">
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleListening}
              className={`p-3 rounded-full flex items-center justify-center transition-colors ${
                isListening && !muted 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-gray-600 hover:bg-gray-700'
              }`}
              aria-label={isListening && !muted ? 'Mute microphone' : 'Unmute microphone'}
            >
              {isListening && !muted ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                  <span className="w-2 h-2 bg-red-400 rounded-full ml-2 animate-pulse"></span>
                </>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  <line x1="1" y1="1" x2="23" y2="23" strokeWidth="2" stroke="currentColor" />
                </svg>
              )}
            </button>
            <span className="text-sm font-medium">
              {isListening ? 'Listening...' : 'Microphone off'}
            </span>
          </div>
          
          {/* Transcript display */}
          {transcript && (
            <div className="relative">
              <button
                onClick={() => setShowTranscript(!showTranscript)}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                {showTranscript ? 'Hide transcript' : 'Show transcript'}
              </button>
              
              {showTranscript && (
                <div className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-sm">
                  {transcript}
                </div>
              )}
            </div>
          )}
          
          {errorMessage && (
            <div className="text-red-500 text-sm">{errorMessage}</div>
          )}
        </div>
      ) : (
        /* Fallback for unsupported browsers */
        <div className="flex flex-col space-y-2">
          <p className="text-sm text-yellow-500 dark:text-yellow-400">
            Speech recognition is not supported in this browser. You can upload an audio file instead.
          </p>
          
          <div className="flex items-center space-x-2">
            <input
              type="file"
              accept="audio/*"
              onChange={handleFileChange}
              className="text-sm text-gray-500 dark:text-gray-400"
            />
            
            <button
              onClick={handleFileUpload}
              disabled={!uploadedFile || isUploading}
              className={`px-3 py-1 rounded ${
                uploadedFile && !isUploading
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-300 text-gray-700 cursor-not-allowed'
              }`}
            >
              {isUploading ? 'Processing...' : 'Upload'}
            </button>
          </div>
          
          {uploadError && (
            <div className="text-red-500 text-sm">{uploadError}</div>
          )}
        </div>
      )}
    </div>
  );
};

export default SpeechInput; 