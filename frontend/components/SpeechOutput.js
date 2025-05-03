import { useState, useEffect, useRef } from 'react';

/**
 * SpeechOutput component that provides a user interface for text-to-speech output.
 * It handles fetching voices and playing TTS audio.
 * 
 * @param {Object} props Component props
 * @param {string} props.text Text to speak (optional if textFromResponse is provided)
 * @param {Function} props.onPlay Callback when speech starts playing
 * @param {Function} props.onEnd Callback when speech ends
 * @param {string} props.backendUrl Backend URL
 */
const SpeechOutput = ({ 
  text = '', 
  onPlay = () => {},
  onEnd = () => {},
  backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000' 
}) => {
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  
  const audioRef = useRef(null);
  
  // Fetch available voices on load
  useEffect(() => {
    fetchVoices();
  }, []);
  
  // Load speech when text changes
  useEffect(() => {
    if (text && selectedVoice && !isPlaying) {
      loadSpeech();
    }
  }, [text, selectedVoice]);
  
  // Fetch available voices
  const fetchVoices = async () => {
    setError(null);
    setVoices([]);
    
    try {
      const response = await fetch(`${backendUrl}/api/text-to-speech/voices`);
      
      if (!response.ok) {
        let errorMsg = `Error fetching voices: ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.detail || errorMsg;
        } catch (e) { /* Ignore if response is not JSON */ }
        throw new Error(errorMsg);
      }
      
      const data = await response.json();
      const formattedVoices = data.voices.map(voice => ({
          id: voice.name,
          name: voice.name,
          language: voice.language,
          description: voice.description
      }));
      setVoices(formattedVoices);
      
      if (formattedVoices.length > 0) {
        const defaultVoice = formattedVoices.find(v => v.id === 'af_heart') || formattedVoices[0];
        setSelectedVoice(defaultVoice.id);
      }
    } catch (err) {
      console.error('Error fetching voices:', err);
      setError(`Failed to load voices: ${err.message}. TTS might be unavailable.`);
    }
  };
  
  // Load speech audio
  const loadSpeech = async () => {
    if (!text || !selectedVoice) return;
    
    setIsLoading(true);
    setError(null);
    setAudioBlob(null);
    
    try {
      const formData = new FormData();
      formData.append('text', text);
      formData.append('voice_id', selectedVoice);
      formData.append('speed', 1.0);
      
      const response = await fetch(`${backendUrl}/api/text-to-speech`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        let errorMsg = `Error generating speech: ${response.statusText}`;
        try {
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorMsg;
            } else {
                 errorMsg = await response.text();
            }
        } catch (e) { /* Ignore parsing errors, use statusText */ }
        throw new Error(errorMsg);
      }
      
      const blob = await response.blob();
      setAudioBlob(blob);
    } catch (err) {
      console.error('Error loading speech:', err);
      setError(`Failed to generate speech: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Play speech
  const playAudio = () => {
    if (!audioBlob || !audioRef.current) return;
    
    try {
      const url = URL.createObjectURL(audioBlob);
      
      audioRef.current.src = url;
      audioRef.current.play();
      setIsPlaying(true);
      onPlay();
      
      audioRef.current.onended = () => {
        URL.revokeObjectURL(url);
        setIsPlaying(false);
        onEnd();
      };
      audioRef.current.onerror = (e) => {
         console.error('Audio playback error:', e);
         setError('Failed to play audio.');
         setIsPlaying(false);
         URL.revokeObjectURL(url);
         onEnd();
      }
    } catch (err) {
      console.error('Error playing audio:', err);
      setError(`Failed to play audio: ${err.message}`);
      setIsPlaying(false);
    }
  };
  
  // Stop audio playback
  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      onEnd();
    }
  };
  
  return (
    <div className="flex flex-col space-y-3">
      <div className="flex items-center space-x-2">
        <select
          value={selectedVoice || ''}
          onChange={(e) => setSelectedVoice(e.target.value)}
          className="px-3 py-1 rounded bg-gray-100 dark:bg-gray-800 text-sm"
          disabled={isLoading || isPlaying || voices.length === 0}
        >
          {voices.length === 0 && (
            <option value="">Loading voices...</option>
          )}
          
          {voices.map((voice) => (
            <option key={voice.id} value={voice.id}>
              {voice.name} ({voice.language})
            </option>
          ))}
        </select>
        
        <button
          onClick={isPlaying ? stopAudio : playAudio}
          disabled={isLoading || !audioBlob}
          className={`p-2 rounded-full ${
            isPlaying
              ? 'bg-red-600 hover:bg-red-700'
              : 'bg-blue-600 hover:bg-blue-700'
          } text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
          aria-label={isPlaying ? 'Stop speaking' : 'Speak text'}
        >
          {isPlaying ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <rect x="6" y="6" width="12" height="12" strokeWidth="2" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
          )}
        </button>
        
        {isLoading && (
          <div className="animate-pulse text-sm text-gray-500">
            Generating speech...
          </div>
        )}
      </div>
      
      {error && (
        <div className="text-red-500 text-sm">{error}</div>
      )}
      
      {/* Hidden audio element for playback */}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
};

export default SpeechOutput; 