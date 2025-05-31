import { useState } from 'react';
import { 
  AgentResponse, 
  InterviewStartRequest, 
  api, 
  PerTurnFeedbackItem,
  createSession,
  startInterview as apiStartInterview,
  sendMessage as apiSendMessage,
  endInterview as apiEndInterview,
  resetInterview as apiResetInterview
} from '../services/api';
import { useToast } from '@/hooks/use-toast';

// Define a more specific type for Coach Feedback content if desired
export interface CoachFeedbackContent {
  conciseness?: string;
  completeness?: string;
  technical_accuracy_depth?: string;
  contextual_alignment?: string;
  fixes_improvements?: string;
  star_support?: string;
  [key: string]: string | undefined;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string | CoachFeedbackContent; // Can be string or CoachFeedbackContent object
  agent?: 'interviewer' | 'coach';      // Optional agent field
  response_type?: string; // To store response_type from backend if needed
  timestamp?: string;     // To store timestamp
}

export type InterviewState = 'idle' | 'configuring' | 'interviewing' | 'reviewing_feedback' | 'completed';

export interface InterviewResults {
  coachingSummary: any;
  perTurnFeedback?: PerTurnFeedbackItem[];
}

export function useInterviewSession() {
  const [state, setState] = useState<InterviewState>('configuring');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<InterviewResults | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { toast } = useToast();

  const startInterview = async (config: InterviewStartRequest) => {
    try {
      setIsLoading(true);
      console.log('🚀 Starting interview with config:', config);
      
      // Step 1: Create a new session
      console.log('📝 Step 1: Creating session...');
      const sessionResponse = await createSession(config);
      const newSessionId = sessionResponse.session_id;
      setSessionId(newSessionId);
      console.log('✅ Session created:', newSessionId);
      
      // Step 2: Start the interview and get the initial introduction message
      console.log('🎬 Step 2: Starting interview and getting introduction...');
      const introResponse = await apiStartInterview(newSessionId, config);
      console.log('📨 Received intro response:', introResponse);
      
      if (!introResponse || !introResponse.content) {
        throw new Error('No introduction content received from server');
      }
      
      setState('interviewing');
      console.log('🔄 State changed to interviewing');
      
      // Initialize with the introduction message from the interviewer
      const introMessage: Message = {
        role: 'assistant',
        agent: introResponse.agent || 'interviewer',
        content: introResponse.content,
        response_type: introResponse.response_type,
        timestamp: introResponse.timestamp
      };
      
      console.log('💬 Setting intro message:', introMessage);
      setMessages([introMessage]);
      console.log('✅ Interview started successfully');
      
    } catch (error) {
      console.error('❌ Error starting interview:', error);
      const message = error instanceof Error ? error.message : 'Failed to start interview';
      let description = message;
      
      // Handle specific error types
      if (message.includes('403') || message.includes('Forbidden')) {
        description = 'Authentication error. Please try refreshing the page or logging in again.';
      } else if (message.includes('Invalid audience') || message.includes('JWT')) {
        description = 'Authentication token error. Please try logging in again.';
      }
      
      toast({
        title: 'Error',
        description: description,
        variant: 'destructive',
      });
      
      // Reset to configuring state on error
      setState('configuring');
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (message: string) => {
    if (!message.trim() || !sessionId) return;

    try {
      const userMessage: Message = { 
        role: 'user', 
        content: message,
        timestamp: new Date().toISOString() // Add timestamp for user message
      };
      setMessages((prev) => [...prev, userMessage]);
      
      setIsLoading(true);
      
      // Expecting a single AgentResponse from the API now
      const response: AgentResponse = await apiSendMessage(sessionId, { message });
      
      const agentMessage: Message = {
        role: response.role as 'assistant', 
        agent: response.agent, 
        content: response.content, 
        response_type: response.response_type,
        timestamp: response.timestamp
      };
      setMessages((prev) => [...prev, agentMessage]);

      if (selectedVoice && response.agent === 'interviewer' && typeof response.content === 'string') {
        playTextToSpeech(response.content);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to send message';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const endInterview = async () => {
    if (!sessionId) return;
    
    try {
      setIsLoading(true);
      const response = await apiEndInterview(sessionId);
      
      setResults({
        coachingSummary: response.results,
        perTurnFeedback: response.per_turn_feedback
      });
      
      // Transition to a new state for reviewing per-turn feedback first
      setState('reviewing_feedback');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to end interview';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const resetInterview = async () => {
    try {
      if (sessionId) {
        await apiResetInterview(sessionId);
      }
      setState('configuring');
      setMessages([]);
      setResults(null);
      setSessionId(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to reset interview';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    }
  };

  const proceedToFinalSummary = () => {
    if (state === 'reviewing_feedback') {
      setState('completed');
    }
  };

  const playTextToSpeech = async (text: string) => {
    if (!selectedVoice) return;
    
    try {
      const audioBlob = await api.textToSpeech(text, selectedVoice);
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      audio.play();
      
      // Clean up the URL object after the audio finishes playing
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
    } catch (error) {
      console.error('Failed to play text-to-speech', error);
      // Don't show a toast for TTS errors, as they are not critical
    }
  };

  return {
    state,
    messages,
    isLoading,
    results,
    selectedVoice,
    actions: {
      startInterview,
      sendMessage,
      endInterview,
      resetInterview,
      setSelectedVoice,
      proceedToFinalSummary,
    }
  };
}
