import { useState, useEffect, useRef } from 'react';

/**
 * SpeechRecognition component that uses the Web Speech API
 * to capture user speech and convert it to text.
 * 
 * @param {Object} props Component props
 * @param {Function} props.onTranscriptChange Callback for when transcript changes
 * @param {Function} props.onTranscriptComplete Callback for completed transcript
 * @param {boolean} props.continuousMode Whether to use continuous recording mode
 * @param {boolean} props.interimResults Whether to show partial results
 * @param {string} props.language Language code for speech recognition
 */
const SpeechRecognition = ({
  onTranscriptChange = () => {},
  onTranscriptComplete = () => {},
  continuousMode = true,
  interimResults = true,
  language = 'en-US'
}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState(null);
  const [isSupported, setIsSupported] = useState(true);
  
  const recognitionRef = useRef(null);

  // Check if Web Speech API is supported
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setIsSupported(false);
      setError('Speech recognition is not supported in this browser.');
    }
  }, []);

  // Initialize recognition
  useEffect(() => {
    if (!isSupported) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognition();
    
    // Configure recognition
    recognitionRef.current.continuous = continuousMode;
    recognitionRef.current.interimResults = interimResults;
    recognitionRef.current.lang = language;
    
    // Event handlers
    recognitionRef.current.onstart = () => {
      setIsListening(true);
    };
    
    recognitionRef.current.onend = () => {
      setIsListening(false);
      
      // Auto-restart if in continuous mode and no error occurred
      if (continuousMode && isListening && !error) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          console.error('Failed to restart speech recognition:', e);
        }
      }
    };
    
    recognitionRef.current.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }
      
      const fullTranscript = finalTranscript || interimTranscript;
      setTranscript(fullTranscript);
      onTranscriptChange(fullTranscript);
      
      if (finalTranscript && !interimResults) {
        onTranscriptComplete(finalTranscript);
      }
    };
    
    recognitionRef.current.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setError(`Error: ${event.error}`);
      setIsListening(false);
    };
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [continuousMode, interimResults, language, isSupported, onTranscriptChange, onTranscriptComplete, isListening, error]);

  // Start recognition
  const startListening = () => {
    setError(null);
    setTranscript('');
    
    if (!isSupported) {
      setError('Speech recognition is not supported in this browser.');
      return;
    }
    
    try {
      recognitionRef.current.start();
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      setError(`Failed to start: ${error.message}`);
    }
  };

  // Stop recognition
  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };

  return {
    transcript,
    isListening,
    error,
    isSupported,
    startListening,
    stopListening
  };
};

export default SpeechRecognition; 