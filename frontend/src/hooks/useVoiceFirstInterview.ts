import { useState, useRef, useCallback, useEffect } from 'react';
import { Message } from './useInterviewSession';
import { api, StreamingSpeechRecognition } from '../services/api';
import { useToast } from './use-toast';

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

// Interface for session data that will be passed as parameters
export interface SessionData {
  messages: Message[];
  isLoading: boolean;
  state: string;
  selectedVoice: string | null;
  sessionId?: string; // Add sessionId for speech task tracking
  results?: any; // Add results field
}

export function useVoiceFirstInterview(
  sessionData: SessionData,
  onSendMessage?: (message: string) => void
) {
  const { toast } = useToast();
  
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
  const [accumulatedTranscript, setAccumulatedTranscript] = useState('');
  
  // Refs for voice management
  const recognitionRef = useRef<StreamingSpeechRecognition | null>(null);
  const voiceActivityRef = useRef<number>(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  
  // Use refs to avoid closure issues
  const accumulatedTranscriptRef = useRef(accumulatedTranscript);
  const onSendMessageRef = useRef(onSendMessage);
  
  // Get last exchange messages for minimal display
  const getLastExchange = useCallback(() => {
    const { messages } = sessionData;
    const userMessages = messages.filter(m => m.role === 'user');
    const aiMessages = messages.filter(m => m.role === 'assistant' && m.agent !== 'coach');
    
    const lastUserMessage = userMessages[userMessages.length - 1]?.content;
    const lastAIMessage = aiMessages[aiMessages.length - 1]?.content;
    
    return {
      userMessage: typeof lastUserMessage === 'string' ? lastUserMessage : '',
      aiMessage: typeof lastAIMessage === 'string' ? lastAIMessage : ''
    };
  }, [sessionData.messages]);

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
      toast({
        title: 'Microphone Error',
        description: 'Could not access your microphone for voice activity detection.',
        variant: 'destructive',
      });
    }
  }, [microphoneActive, toast]);

  // Start streaming voice recognition
  const startVoiceRecognition = useCallback(async () => {
    try {
      setVoiceState(prev => ({
        ...prev,
        microphoneState: 'listening',
        turnState: 'user'
      }));

      // Clear any previous accumulated transcript when starting fresh
      setAccumulatedTranscript('');
      
      // Create streaming recognition instance
      recognitionRef.current = api.createStreamingSpeechRecognition({
        sessionId: sessionData.sessionId,
        onConnected: () => {
          console.log('Connected to streaming STT service');
          setMicrophoneActive(true);
          setupVoiceActivityDetection();
        },
        onDisconnected: () => {
          console.log('Disconnected from streaming STT service');
          setMicrophoneActive(false);
          setVoiceState(prev => ({
            ...prev,
            microphoneState: 'idle',
            turnState: 'idle'
          }));
        },
        onTranscript: (text, isFinal) => {
          if (text && text.trim() !== '') {
            if (isFinal) {
              // Append final transcript to accumulated text and clear interim
              setAccumulatedTranscript(prev => {
                const newText = prev.trim() ? prev + ' ' + text : text;
                console.log('📝 Final transcript accumulated:', text);
                return newText;
              });
            }
          }
        },
        onSpeechStarted: () => {
          setVoiceState(prev => ({
            ...prev,
            voiceActivity: {
              ...prev.voiceActivity,
              isDetected: true
            }
          }));
        },
        onUtteranceEnd: () => {
          // CHANGED: Do NOT automatically send on utterance end
          // Just clear speech detection UI after a delay
          setTimeout(() => {
            setVoiceState(prev => ({
              ...prev,
              voiceActivity: {
                ...prev.voiceActivity,
                isDetected: false
              }
            }));
          }, 1000);
        },
        onError: (error) => {
          console.error('Streaming STT error:', error);
          toast({
            title: 'Speech Recognition Error',
            description: error || 'An error occurred during speech recognition',
            variant: 'destructive',
          });
          stopVoiceRecognition();
        },
      });
      
      // Start recognition
      await recognitionRef.current.start();
      
    } catch (error) {
      console.error('Failed to start streaming recognition:', error);
      toast({
        title: 'Microphone Error',
        description: 'Could not access your microphone or connect to the speech service.',
        variant: 'destructive',
      });
      stopVoiceRecognition();
    }
  }, [setupVoiceActivityDetection, toast]);

  // Stop voice recognition
  const stopVoiceRecognition = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    
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
    
    // CHANGED: Use ref to get latest value without dependency issues
    // Combine accumulated final transcript with current interim text
    const finalText = accumulatedTranscriptRef.current.trim();
    
    let completeTranscript = '';
    if (finalText) {
      completeTranscript = finalText;
    }
    
    if (completeTranscript) {
      console.log('📤 Sending complete transcript on manual stop:', completeTranscript);
      if (onSendMessageRef.current) {
        onSendMessageRef.current(completeTranscript);
      } else {
        console.log('📝 Complete transcript ready:', completeTranscript);
      }
      setAccumulatedTranscript('');
    } else {
      console.log('⚠️ No transcript to send - user may have stopped without speaking');
    }
    
    // Reset to idle after processing
    setTimeout(() => {
      setVoiceState(prev => ({
        ...prev,
        microphoneState: 'idle'
      }));
    }, 1000);
  }, []); // NO DEPENDENCIES - use refs instead

  // Voice control functions
  const toggleMicrophone = useCallback(async () => {
    if (microphoneActive) {
      stopVoiceRecognition();
    } else {
      await startVoiceRecognition();
    }
  }, [microphoneActive, startVoiceRecognition, stopVoiceRecognition]);

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

  // Enhanced TTS implementation
  const playTextToSpeech = useCallback(async (text: string) => {
    const { selectedVoice } = sessionData;
    
    if (!selectedVoice) {
      console.warn('⚠️ No selectedVoice available for TTS');
      return;
    }
    
    handleTTSStart();
    
    try {
      const audioBlob = await api.textToSpeech(text, selectedVoice);
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Stop any currently playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;
      
      await audio.play();
      
      // Clean up the URL object after the audio finishes playing
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
        handleTTSEnd();
      };
      
      // Also handle if audio fails to load
      audio.onerror = (error) => {
        console.error('🔊 Audio playback error:', error);
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
        handleTTSEnd();
      };
      
    } catch (error) {
      console.error('TTS playback failed:', error);
      handleTTSEnd();
      toast({
        title: 'Audio Playback Error',
        description: 'Could not play the AI response audio.',
        variant: 'destructive',
      });
    }
  }, [sessionData, handleTTSStart, handleTTSEnd, toast]);

  // Auto-enable voice when new AI message arrives
  const { messages } = sessionData;
  const lastMessage = messages[messages.length - 1];
  const lastProcessedMessageRef = useRef<string | null>(null);
  
  useEffect(() => {
    if (lastMessage && 
        lastMessage.role === 'assistant' && 
        lastMessage.agent !== 'coach' &&
        typeof lastMessage.content === 'string') {
      
      // Create a unique key from message index and content
      const messageKey = `${messages.length - 1}-${lastMessage.content.slice(0, 50)}`;
      
      if (messageKey !== lastProcessedMessageRef.current) {
        // Mark this message as processed to avoid re-triggering
        lastProcessedMessageRef.current = messageKey;
        
        console.log('🔊 Auto-playing TTS for AI response');
        // Auto-play TTS for AI interviewer responses
        playTextToSpeech(lastMessage.content);
      }
    }
  }, [lastMessage]); // REMOVED playTextToSpeech dependency that was causing loops

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopVoiceRecognition();
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
    };
  }, [stopVoiceRecognition]);

  // Determine overall interaction state
  const getInteractionState = useCallback(() => {
    const disabled = voiceState.microphoneState === 'disabled' || audioPlaying;
    const sessionNotReady = sessionData.state !== 'interviewing';
    
    if (disabled || audioPlaying) {
      return { isListening: false, isProcessing: false, isDisabled: true };
    }
    
    return {
      isListening: microphoneActive,
      isProcessing: voiceState.microphoneState === 'processing',
      isDisabled: sessionNotReady
    };
  }, [voiceState, microphoneActive, audioPlaying, sessionData.state]);

  // Calculate interaction state once
  const interactionState = getInteractionState();

  // Update refs when values change
  useEffect(() => {
    accumulatedTranscriptRef.current = accumulatedTranscript;
  }, [accumulatedTranscript]);
  
  useEffect(() => {
    onSendMessageRef.current = onSendMessage;
  }, [onSendMessage]);

  return {
    // Selected interview session functionality (avoid spreading entire object)
    messages: sessionData.messages,
    isLoading: sessionData.isLoading,
    state: sessionData.state,
    results: sessionData.results,
    selectedVoice: sessionData.selectedVoice,
    // Note: coachFeedbackStates and actions excluded to prevent re-render loops
    
    // Extended voice-first state
    voiceState,
    microphoneActive,
    audioPlaying,
    transcriptVisible,
    coachFeedbackVisible,
    voiceActivityLevel,
    accumulatedTranscript,
    
    // Enhanced interaction state (don't spread to avoid re-creation)
    isListening: interactionState.isListening,
    isProcessing: interactionState.isProcessing,
    isDisabled: interactionState.isDisabled,
    
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