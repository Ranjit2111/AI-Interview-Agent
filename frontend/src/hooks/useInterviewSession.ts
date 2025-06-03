import { useState, useEffect, useRef } from 'react';
import { 
  AgentResponse, 
  InterviewStartRequest, 
  api, 
  PerTurnFeedbackItem,
  createSession,
  startInterview as apiStartInterview,
  sendMessage as apiSendMessage,
  endInterview as apiEndInterview,
  resetInterview as apiResetInterview,
  getPerTurnFeedback
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

// Add real-time coach feedback tracking
export interface CoachFeedbackState {
  [messageIndex: number]: {
    isAnalyzing: boolean;
    feedback?: string;
    hasChecked: boolean;
  };
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
  
  // Real-time coach feedback tracking
  const [coachFeedbackStates, setCoachFeedbackStates] = useState<CoachFeedbackState>({});
  const [lastFeedbackCount, setLastFeedbackCount] = useState(0);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const { toast } = useToast();

  // Polling for real-time coach feedback
  useEffect(() => {
    // Only run if we have a session and are interviewing
    if (!sessionId || state !== 'interviewing') {
      // Clear any existing polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      return;
    }

      const pollForFeedback = async () => {
        try {
          const feedback = await getPerTurnFeedback(sessionId);
          
          // Update coach feedback states based on current feedback
          if (feedback.length > lastFeedbackCount) {
            setCoachFeedbackStates(prev => {
              const newState = { ...prev };
              
              // Mark analyzing for new user messages that don't have feedback yet
              const userMessageIndexes = messages
                .map((msg, index) => ({ msg, index }))
                .filter(({ msg }) => msg.role === 'user')
                .map(({ index }) => index);
              
              userMessageIndexes.forEach((msgIndex, userMsgNumber) => {
                if (userMsgNumber < feedback.length) {
                  // Feedback is available
                  newState[msgIndex] = {
                    isAnalyzing: false,
                    feedback: feedback[userMsgNumber].feedback,
                    hasChecked: true
                  };
                } else {
                  // No feedback yet, should be analyzing if not already checked
                  if (!newState[msgIndex]?.hasChecked) {
                    newState[msgIndex] = {
                      isAnalyzing: true,
                      hasChecked: false
                    };
                  }
                }
              });
              
              return newState;
            });
            
            setLastFeedbackCount(feedback.length);
          }
        } catch (error) {
          // Silently handle polling errors to avoid UI disruption
          console.log('Polling for feedback failed:', error);
        }
      };

    // FIXED: Only poll if there are pending messages that need analysis
    const userMessageCount = messages.filter(m => m.role === 'user').length;
    const shouldPoll = userMessageCount > 0 && lastFeedbackCount < userMessageCount;

    if (shouldPoll && !pollingIntervalRef.current) {
      // Start polling only when there's something to analyze AND not already polling
      console.log('Starting coach feedback polling for', userMessageCount - lastFeedbackCount, 'pending messages');
      pollForFeedback();
      pollingIntervalRef.current = setInterval(pollForFeedback, 2000);
    } else if (!shouldPoll && pollingIntervalRef.current) {
      // Stop polling when all messages have been analyzed
      console.log('Stopping coach feedback polling - all messages analyzed');
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
  }, [sessionId, state, messages.length]); // REMOVED lastFeedbackCount to prevent loops

  // Cleanup polling on unmount or session change
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [sessionId, state]);

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
      
      // Get the index where this user message will be placed
      const userMessageIndex = messages.length;
      
      setMessages((prev) => [...prev, userMessage]);
      
      // Mark coach as analyzing for this user message
      setCoachFeedbackStates(prev => ({
        ...prev,
        [userMessageIndex]: {
          isAnalyzing: true,
          hasChecked: false
        }
      }));
      
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

      // REMOVED: Duplicate TTS call - already handled by voice-first hook
      // if (selectedVoice && response.agent === 'interviewer' && typeof response.content === 'string') {
      //   playTextToSpeech(response.content);
      // }
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
      console.log('🔄 Starting endInterview API call...');
      
      const response = await apiEndInterview(sessionId);
      console.log('📥 Raw API response:', response);
      console.log('📥 Response type:', typeof response);
      console.log('📥 Response.results:', response.results);
      console.log('📥 Response.results type:', typeof response.results);
      console.log('📥 Response.per_turn_feedback:', response.per_turn_feedback);
      
      const resultsToSet = {
        coachingSummary: response.results,
        perTurnFeedback: response.per_turn_feedback
      };
      
      console.log('📦 Setting results state to:', resultsToSet);
      console.log('📦 coachingSummary will be:', resultsToSet.coachingSummary);
      console.log('📦 coachingSummary type:', typeof resultsToSet.coachingSummary);
      
      setResults(resultsToSet);
      
      console.log('🔄 Transitioning to reviewing_feedback state');
      // Transition to a new state for reviewing per-turn feedback first
      setState('reviewing_feedback');
    } catch (error) {
      console.error('❌ Error in endInterview:', error);
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
      // Reset coach feedback states
      setCoachFeedbackStates({});
      setLastFeedbackCount(0);
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
    console.log('🎯 proceedToFinalSummary called');
    console.log('🎯 Current state:', state);
    console.log('🎯 Results available:', !!results);
    console.log('🎯 coachingSummary available:', !!results?.coachingSummary);
    console.log('🎯 Full results object:', results);
    
    if (state === 'reviewing_feedback') {
      console.log('🎯 Transitioning state from reviewing_feedback to completed');
      setState('completed');
    } else {
      console.log('🎯 State transition blocked - not in reviewing_feedback state');
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
    coachFeedbackStates,
    sessionId,
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
