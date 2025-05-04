
import { useState } from 'react';
import { AgentResponse, InterviewStartRequest, api } from '../services/api';
import { useToast } from '@/hooks/use-toast';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export type InterviewState = 'idle' | 'configuring' | 'interviewing' | 'completed';

export interface InterviewResults {
  coachingSummary: any;
  skillProfile: any;
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
      
      // Add first message from system to indicate the interview has started
      const firstMessage: Message = {
        role: 'assistant',
        content: `Hello! I'll be your interviewer today for the ${config.job_role} position${config.company_name ? ` at ${config.company_name}` : ''}. Let's get started with the interview.`,
      };
      
      setMessages([firstMessage]);
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
      // Add user message to the list
      const userMessage: Message = { role: 'user', content: message };
      setMessages((prev) => [...prev, userMessage]);
      
      setIsLoading(true);
      
      // Send the message to the API
      const response = await api.sendMessage({ message });
      
      // Add the agent's response
      const agentMessage: Message = { role: 'assistant', content: response.content };
      setMessages((prev) => [...prev, agentMessage]);

      // Automatically play TTS if a voice is selected
      if (selectedVoice) {
        playTextToSpeech(response.content);
      }
      
      return response;
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
        coachingSummary: response.results.coaching_summary,
        skillProfile: response.results.skill_profile,
      });
      
      setState('completed');
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
    }
  };
}
