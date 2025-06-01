import { useState, useRef, useCallback, useEffect } from 'react';
import { useInterviewSession, Message } from './useInterviewSession';
import { api } from '../services/api';

export type VoiceState = {
  microphoneState: 'idle' | 'listening' | 'processing' | 'disabled';
  audioState: 'idle' | 'playing' | 'buffering';
  turnState: 'user' | 'ai' | 'idle';
  voiceActivity: {
    isDetected: boolean;
    volume: number; // 0-1 for glow intensity
    timestamp: number;
  };
};

export interface ExtendedInterviewState {
  voiceState: VoiceState;
  microphoneActive: boolean;
  audioPlaying: boolean;
  transcriptVisible: boolean;
  coachFeedbackVisible: boolean;
  lastExchange: {
    userMessage?: string;
    aiMessage?: string;
  };
}

export function useVoiceFirstInterview() {
  // Use the existing interview session hook
  const interviewSession = useInterviewSession();
  
  // Extended voice-first state
  const [voiceState, setVoiceState] = useState<VoiceState>({
    microphoneState: 'idle',
    audioState: 'idle',
    turnState: 'idle',
    voiceActivity: {
      isDetected: false,
      volume: 0,
      timestamp: Date.now()
    }
  });
  
  const [microphoneActive, setMicrophoneActive] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [transcriptVisible, setTranscriptVisible] = useState(false);
  const [coachFeedbackVisible, setCoachFeedbackVisible] = useState(false);
  const [voiceActivityLevel, setVoiceActivityLevel] = useState(0);
  
  // Refs for voice activity tracking
  const voiceActivityRef = useRef<number>(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  
  // Get last exchange messages for minimal display
  const getLastExchange = useCallback(() => {
    const { messages } = interviewSession;
    const userMessages = messages.filter(m => m.role === 'user');
    const aiMessages = messages.filter(m => m.role === 'assistant' && m.agent !== 'coach');
    
    const lastUserMessage = userMessages[userMessages.length - 1]?.content;
    const lastAIMessage = aiMessages[aiMessages.length - 1]?.content;
    
    return {
      userMessage: typeof lastUserMessage === 'string' ? lastUserMessage : '',
      aiMessage: typeof lastAIMessage === 'string' ? lastAIMessage : ''
    };
  }, [interviewSession.messages]);

  // Voice activity detection setup
  const setupVoiceActivityDetection = useCallback(async () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true, 
          noiseSuppression: true, 
          autoGainControl: true 
        } 
      });
      
      micStreamRef.current = stream;
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      
      source.connect(analyserRef.current);
      
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const updateVoiceActivity = () => {
        if (analyserRef.current && microphoneActive) {
          analyserRef.current.getByteFrequencyData(dataArray);
          
          // Calculate average volume
          const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
          const normalizedVolume = Math.min(1, average / 128);
          
          voiceActivityRef.current = normalizedVolume;
          setVoiceActivityLevel(normalizedVolume);
          
          setVoiceState(prev => ({
            ...prev,
            voiceActivity: {
              isDetected: normalizedVolume > 0.1,
              volume: normalizedVolume,
              timestamp: Date.now()
            }
          }));
        }
        
        if (microphoneActive) {
          requestAnimationFrame(updateVoiceActivity);
        }
      };
      
      updateVoiceActivity();
      
    } catch (error) {
      console.error('Error setting up voice activity detection:', error);
    }
  }, [microphoneActive]);

  // Voice control functions
  const toggleMicrophone = useCallback(async () => {
    if (microphoneActive) {
      // Stop listening
      setMicrophoneActive(false);
      setVoiceState(prev => ({
        ...prev,
        microphoneState: 'processing',
        turnState: 'idle'
      }));
      
      // Clean up audio resources
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach(track => track.stop());
        micStreamRef.current = null;
      }
      
      // Here you would typically send the recorded audio for transcription
      // This would integrate with your existing voice recording system
      
    } else {
      // Start listening
      setMicrophoneActive(true);
      setVoiceState(prev => ({
        ...prev,
        microphoneState: 'listening',
        turnState: 'user'
      }));
      
      await setupVoiceActivityDetection();
    }
  }, [microphoneActive, setupVoiceActivityDetection]);

  // TTS state management
  const handleTTSStart = useCallback(() => {
    setAudioPlaying(true);
    setVoiceState(prev => ({
      ...prev,
      audioState: 'playing',
      turnState: 'ai',
      microphoneState: 'disabled'
    }));
  }, []);

  const handleTTSEnd = useCallback(() => {
    setAudioPlaying(false);
    setVoiceState(prev => ({
      ...prev,
      audioState: 'idle',
      turnState: 'idle',
      microphoneState: 'idle'
    }));
  }, []);

  // Transcript and feedback controls
  const toggleTranscript = useCallback(() => {
    setTranscriptVisible(prev => !prev);
  }, []);

  const toggleCoachFeedback = useCallback(() => {
    setCoachFeedbackVisible(prev => !prev);
  }, []);

  const closeCoachFeedback = useCallback(() => {
    setCoachFeedbackVisible(false);
  }, []);

  // Independent TTS implementation (since it's not exported from the original hook)
  const playTextToSpeech = useCallback(async (text: string) => {
    const { selectedVoice } = interviewSession;
    if (!selectedVoice) return;
    
    handleTTSStart();
    
    try {
      const audioBlob = await api.textToSpeech(text, selectedVoice);
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      await audio.play();
      
      // Clean up the URL object after the audio finishes playing
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        handleTTSEnd();
      };
      
      // Also handle if audio fails to load
      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        handleTTSEnd();
      };
      
    } catch (error) {
      console.error('TTS playback failed:', error);
      handleTTSEnd();
    }
  }, [interviewSession.selectedVoice, handleTTSStart, handleTTSEnd]);

  // Auto-enable voice when new AI message arrives
  const { messages } = interviewSession;
  const lastMessage = messages[messages.length - 1];
  
  useEffect(() => {
    if (lastMessage && 
        lastMessage.role === 'assistant' && 
        lastMessage.agent !== 'coach' &&
        typeof lastMessage.content === 'string') {
      
      // Auto-play TTS for AI interviewer responses
      playTextToSpeech(lastMessage.content);
    }
  }, [lastMessage, playTextToSpeech]);

  // Determine overall interaction state
  const getInteractionState = useCallback(() => {
    if (voiceState.microphoneState === 'disabled' || audioPlaying) {
      return { isListening: false, isProcessing: false, isDisabled: true };
    }
    
    return {
      isListening: microphoneActive,
      isProcessing: voiceState.microphoneState === 'processing',
      isDisabled: interviewSession.state !== 'interviewing'
    };
  }, [voiceState, microphoneActive, audioPlaying, interviewSession.state]);

  return {
    // Original interview session functionality
    ...interviewSession,
    
    // Extended voice-first state
    voiceState,
    microphoneActive,
    audioPlaying,
    transcriptVisible,
    coachFeedbackVisible,
    voiceActivityLevel,
    
    // Enhanced interaction state
    ...getInteractionState(),
    
    // Voice control actions
    toggleMicrophone,
    toggleTranscript,
    toggleCoachFeedback,
    closeCoachFeedback,
    handleTTSStart,
    handleTTSEnd,
    
    // Enhanced TTS
    playTextToSpeech,
    
    // Computed values
    lastExchange: getLastExchange(),
    turnState: voiceState.turnState
  };
}

// Re-export types for convenience
export type { Message, CoachFeedbackState } from './useInterviewSession'; 