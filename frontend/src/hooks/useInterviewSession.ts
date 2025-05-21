import { useState } from 'react';
import { AgentResponse, InterviewStartRequest, api, PerTurnFeedbackItem } from '../services/api';
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
  const { toast } = useToast();

  const startInterview = async (config: InterviewStartRequest) => {
    try {
      setIsLoading(true);
      await api.startInterview(config);
      setState('interviewing');
      
      // Initialize with empty messages array, the first message will come from the backend
      setMessages([]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start interview';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    try {
      const userMessage: Message = { 
        role: 'user', 
        content: message,
        timestamp: new Date().toISOString() // Add timestamp for user message
      };
      setMessages((prev) => [...prev, userMessage]);
      
      setIsLoading(true);
      
      // Expecting a single AgentResponse from the API now
      const response: AgentResponse = await api.sendMessage({ message });
      
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
    try {
      setIsLoading(true);
      const response = await api.endInterview();
      
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
      await api.resetInterview();
      setState('configuring');
      setMessages([]);
      setResults(null);
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
