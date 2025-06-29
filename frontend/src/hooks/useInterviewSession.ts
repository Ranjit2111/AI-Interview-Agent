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
  getPerTurnFeedback,
  getFinalSummaryStatus,
  getSessionTimeRemaining,
  pingSession,
  cleanupSession
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

export type InterviewState = 'idle' | 'configuring' | 'interviewing' | 'post_interview' | 'completed';

export interface PostInterviewState {
  perTurnFeedback: PerTurnFeedbackItem[];
  finalSummary: {
    status: 'loading' | 'completed' | 'error';
    data?: any;
    error?: string;
  };
  resources: {
    status: 'loading' | 'completed' | 'error';
    data?: any[];
    error?: string;
  };
}

export interface InterviewResults {
  coachingSummary: any;
  perTurnFeedback?: PerTurnFeedbackItem[];
}

export function useInterviewSession() {
  const [state, setState] = useState<InterviewState>('configuring');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<InterviewResults | null>(null);
  const [postInterviewState, setPostInterviewState] = useState<PostInterviewState | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Session warning and management state
  const [showSessionWarning, setShowSessionWarning] = useState(false);
  const [sessionTimeRemaining, setSessionTimeRemaining] = useState<number | null>(null);
  
  // Real-time coach feedback tracking
  const [coachFeedbackStates, setCoachFeedbackStates] = useState<CoachFeedbackState>({});
  const [lastFeedbackCount, setLastFeedbackCount] = useState(0);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const finalSummaryPollingRef = useRef<NodeJS.Timeout | null>(null);
  const sessionWarningIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const { toast } = useToast();

  // Session timeout handler
  const handleSessionTimeout = () => {
    setShowSessionWarning(false);
    setSessionTimeRemaining(null);
    setState('configuring');
    setMessages([]);
    setResults(null);
    setPostInterviewState(null);
    setSessionId(null);
    setCoachFeedbackStates({});
    setLastFeedbackCount(0);
    
    // Stop all polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    if (finalSummaryPollingRef.current) {
      clearInterval(finalSummaryPollingRef.current);
      finalSummaryPollingRef.current = null;
    }
    if (sessionWarningIntervalRef.current) {
      clearInterval(sessionWarningIntervalRef.current);
      sessionWarningIntervalRef.current = null;
    }

    toast({
      title: 'Session Expired',
      description: 'Your interview session has expired due to inactivity. Please start a new interview.',
      variant: 'destructive',
    });
  };

  // Session extension function
  const extendSession = async () => {
    if (!sessionId) return;
    
    try {
      const response = await pingSession(sessionId);
      if (response.success) {
        setShowSessionWarning(false);
        setSessionTimeRemaining(response.new_expiry_minutes);
        toast({
          title: 'Session Extended',
          description: 'Your session has been extended for another 15 minutes.',
          variant: 'default',
        });
      } else {
        handleSessionTimeout();
      }
    } catch (error) {
      console.error('Failed to extend session:', error);
      handleSessionTimeout();
    }
  };

  // Session warning management
  useEffect(() => {
    if (sessionWarningIntervalRef.current) {
      clearInterval(sessionWarningIntervalRef.current);
      sessionWarningIntervalRef.current = null;
    }

    if (!sessionId || state !== 'interviewing') {
      setShowSessionWarning(false);
      setSessionTimeRemaining(null);
      return;
    }

    const checkSessionTime = async () => {
      try {
        const response = await getSessionTimeRemaining(sessionId);
        setSessionTimeRemaining(response.time_remaining_minutes);
        
        if (!response.session_active) {
          handleSessionTimeout();
          return;
        }
        
        if (response.time_remaining_minutes <= 2 && response.time_remaining_minutes > 0) {
          setShowSessionWarning(true);
        } else {
          setShowSessionWarning(false);
        }
      } catch (error) {
        if (error instanceof Error && error.message.includes('session')) {
          handleSessionTimeout();
        } else {
          console.log('Session time check failed:', error);
        }
      }
    };

    checkSessionTime();
    sessionWarningIntervalRef.current = setInterval(checkSessionTime, 60000);

    return () => {
      if (sessionWarningIntervalRef.current) {
        clearInterval(sessionWarningIntervalRef.current);
        sessionWarningIntervalRef.current = null;
      }
    };
  }, [sessionId, state]);

  // Tab close detection
  useEffect(() => {
    if (!sessionId) return;

    const handleBeforeUnload = () => {
      if (!sessionId) return;

      const cleanupUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/interview/session/cleanup`;

      // Prefer fetch with keepalive so we can include the required header
      try {
        // Using keepalive ensures the request is allowed to outlive the page lifecycle
        fetch(cleanupUrl, {
          method: 'POST',
          headers: {
            'X-Session-ID': sessionId,
          },
          // keepalive is critical for requests fired during the unload phase
          keepalive: true,
        });
      } catch (err) {
        // Fallback: if fetch with keepalive is not supported, attempt sendBeacon with a query param
        if (navigator.sendBeacon) {
          const beaconUrl = `${cleanupUrl}?session_id=${encodeURIComponent(sessionId)}`;
          navigator.sendBeacon(beaconUrl);
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [sessionId]);

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

    // Only poll if there are pending messages that need analysis
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
  }, [sessionId, state, messages.length, lastFeedbackCount]); // FIXED: Added lastFeedbackCount to dependencies

  // Cleanup polling on unmount or session change
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      if (finalSummaryPollingRef.current) {
        clearInterval(finalSummaryPollingRef.current);
        finalSummaryPollingRef.current = null;
      }
      if (sessionWarningIntervalRef.current) {
        clearInterval(sessionWarningIntervalRef.current);
        sessionWarningIntervalRef.current = null;
      }
    };
  }, [sessionId]); // FIXED: Removed 'state' dependency to prevent cleanup during state transitions

  // Final summary polling function
  const startFinalSummaryPolling = () => {
    console.log('≡ƒöä startFinalSummaryPolling called');
    console.log('≡ƒöä Current sessionId:', sessionId);
    console.log('≡ƒöä Current finalSummaryPollingRef:', finalSummaryPollingRef.current);
    
    if (finalSummaryPollingRef.current) {
      console.log('≡ƒöä Clearing existing polling interval');
      clearInterval(finalSummaryPollingRef.current);
    }

    const pollFinalSummary = async () => {
      if (!sessionId) {
        console.log('Γ¥î No sessionId available for polling');
        return;
      }

      console.log('≡ƒöì Polling final summary status...');

      try {
        // Use the new dedicated status endpoint
        const statusResponse = await getFinalSummaryStatus(sessionId);
        console.log('≡ƒôí Final summary status response:', statusResponse);
        console.log('≡ƒôí Response status:', statusResponse.status);
        console.log('≡ƒôí Response results:', statusResponse.results);
        console.log('≡ƒôí Response error:', statusResponse.error);
        
        if (statusResponse.status === 'completed' && statusResponse.results) {
          console.log('Γ£à Final summary completed! Updating state...');
          console.log('≡ƒôè Results data:', JSON.stringify(statusResponse.results, null, 2));
          console.log('≡ƒôÜ Recommended resources:', statusResponse.results.recommended_resources);
          
          // Update the post-interview state with completed data
          setPostInterviewState(prev => {
            console.log('≡ƒô¥ Previous postInterviewState:', prev);
            const newState = prev ? {
              ...prev,
              finalSummary: {
                status: 'completed' as const,
                data: statusResponse.results
              },
              resources: {
                status: statusResponse.results.recommended_resources ? 'completed' as const : prev.resources.status,
                data: statusResponse.results.recommended_resources || prev.resources.data
              }
            } : null;
            console.log('≡ƒô¥ New postInterviewState:', newState);
            return newState;
          });

          // Stop polling when both summary and resources are complete
          if (statusResponse.results.recommended_resources) {
            console.log('≡ƒ¢æ Stopping polling - both summary and resources complete');
            clearInterval(finalSummaryPollingRef.current!);
            finalSummaryPollingRef.current = null;
          } else {
            console.log('ΓÅ│ Resources still loading, continuing to poll...');
          }
        } else if (statusResponse.status === 'error') {
          console.log('Γ¥î Final summary generation failed:', statusResponse.error);
          
          // Update state to show error
          setPostInterviewState(prev => prev ? {
            ...prev,
            finalSummary: {
              status: 'error' as const,
              error: statusResponse.error || 'Failed to load final summary'
            },
            resources: {
              status: 'error' as const, 
              error: statusResponse.error || 'Failed to load resources'
            }
          } : null);
          
          clearInterval(finalSummaryPollingRef.current!);
          finalSummaryPollingRef.current = null;
        } else {
          console.log('ΓÅ│ Final summary still generating, continuing to poll...');
        }
        // If status is 'generating', continue polling
      } catch (error) {
        console.error('Γ¥î Error polling final summary:', error);
        // Update state to show error
        setPostInterviewState(prev => prev ? {
          ...prev,
          finalSummary: {
            status: 'error' as const,
            error: 'Failed to check final summary status'
          },
          resources: {
            status: 'error' as const, 
            error: 'Failed to check resource status'
          }
        } : null);
        
        clearInterval(finalSummaryPollingRef.current!);
        finalSummaryPollingRef.current = null;
      }
    };

    console.log('ΓÅ░ Setting up polling interval (every 1 second)');
    // Poll every 1 second for final summary completion (reduced from 3 seconds for faster response)
    finalSummaryPollingRef.current = setInterval(pollFinalSummary, 1000);
    
    // Also run once immediately
    console.log('≡ƒÜÇ Running initial poll immediately');
    pollFinalSummary();
    
    // Set a timeout to stop polling after 2 minutes
    setTimeout(() => {
      if (finalSummaryPollingRef.current) {
        console.log('ΓÅ░ Polling timeout reached - stopping polling');
        clearInterval(finalSummaryPollingRef.current);
        finalSummaryPollingRef.current = null;
        
        setPostInterviewState(prev => prev ? {
          ...prev,
          finalSummary: prev.finalSummary.status === 'loading' ? {
            status: 'error' as const,
            error: 'Final summary generation timed out'
          } : prev.finalSummary,
          resources: prev.resources.status === 'loading' ? {
            status: 'error' as const,
            error: 'Resource search timed out'
          } : prev.resources
        } : null);
      }
    }, 120000); // 2 minutes timeout
  };

  const startInterview = async (config: InterviewStartRequest) => {
    try {
      setIsLoading(true);
      console.log('≡ƒÜÇ Starting interview with config:', config);
      
      // Step 1: Create a new session
      console.log('≡ƒô¥ Step 1: Creating session...');
      const sessionResponse = await createSession(config);
      const newSessionId = sessionResponse.session_id;
      setSessionId(newSessionId);
      console.log('Γ£à Session created:', newSessionId);
      
      // Step 2: Start the interview and get the initial introduction message
      console.log('≡ƒÄ¼ Step 2: Starting interview and getting introduction...');
      const introResponse = await apiStartInterview(newSessionId, config);
      console.log('≡ƒô¿ Received intro response:', introResponse);
      
      if (!introResponse || !introResponse.content) {
        throw new Error('No introduction content received from server');
      }
      
      setState('interviewing');
      console.log('≡ƒöä State changed to interviewing');
      
      // Initialize with the introduction message from the interviewer
      const introMessage: Message = {
        role: 'assistant',
        agent: introResponse.agent || 'interviewer',
        content: introResponse.content,
        response_type: introResponse.response_type,
        timestamp: introResponse.timestamp
      };
      
      console.log('≡ƒÆ¼ Setting intro message:', introMessage);
      setMessages([introMessage]);
      console.log('Γ£à Interview started successfully');
      
    } catch (error) {
      console.error('Γ¥î Error starting interview:', error);
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

    // 1️⃣ Immediately transition UI to the post-interview screen with placeholders
    console.log('🚀 endInterview: switching UI to post_interview immediately');

    const placeholderPostState: PostInterviewState = {
      perTurnFeedback: [],
      finalSummary: { status: 'loading' },
      resources: { status: 'loading' }
    };

    setPostInterviewState(placeholderPostState);
    setState('post_interview');

    // Allow UI to render without global spinner
    setIsLoading(false);

    try {
      console.log('🔄 Calling /end-interview in background…');
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
      setResults(resultsToSet);

      // **NEW: Set up progressive loading state**
      // Immediately show per-turn feedback, set final summary and resources as loading
      const hasValidResults = response.results && Object.keys(response.results).length > 0 && !response.results.error;
      const hasValidResources = hasValidResults && response.results.recommended_resources && response.results.recommended_resources.length > 0;
      
      console.log('≡ƒöì hasValidResults evaluation:');
      console.log('  - response.results exists:', !!response.results);
      console.log('  - response.results keys length:', response.results ? Object.keys(response.results).length : 0);
      console.log('  - response.results keys:', response.results ? Object.keys(response.results) : []);
      console.log('  - response.results.error:', response.results ? response.results.error : 'N/A');
      console.log('  - hasValidResults final:', hasValidResults);
      
      console.log('≡ƒöì hasValidResources evaluation:');
      console.log('  - hasValidResults:', hasValidResults);
      console.log('  - recommended_resources exists:', hasValidResults ? !!response.results.recommended_resources : false);
      console.log('  - recommended_resources length:', hasValidResults && response.results.recommended_resources ? response.results.recommended_resources.length : 0);
      console.log('  - hasValidResources final:', hasValidResources);
      
      const initialPostInterviewState: PostInterviewState = {
        perTurnFeedback: response.per_turn_feedback || [],
        finalSummary: {
          status: hasValidResults ? 'completed' : 'loading',
          data: hasValidResults ? response.results : undefined,
          error: undefined
        },
        resources: {
          status: hasValidResources ? 'completed' : 'loading',
          data: hasValidResources ? response.results.recommended_resources : undefined,
          error: undefined
        }
      };

      console.log('≡ƒô¥ Setting initial postInterviewState:', initialPostInterviewState);
      setPostInterviewState(initialPostInterviewState);
      
      console.log('≡ƒöä Transitioning to post_interview state');
      console.log('≡ƒôè hasValidResults:', hasValidResults, 'hasValidResources:', hasValidResources);
      // Transition to a new state for post-interview
      setState('post_interview');

      // If summary or resources are still loading, start polling
      const shouldStartPolling = !hasValidResults || !hasValidResources;
      console.log('≡ƒñö Should start polling?', shouldStartPolling);
      console.log('  - Reason: !hasValidResults =', !hasValidResults, '|| !hasValidResources =', !hasValidResources);
      
      if (shouldStartPolling) {
        console.log('≡ƒÜÇ Starting final summary polling...');
        startFinalSummaryPolling();
      } else {
        console.log('Γ£à Both results and resources are complete, no polling needed');
      }
      
    } catch (error) {
      console.error('Γ¥î Error in endInterview:', error);
      const message = error instanceof Error ? error.message : 'Failed to end interview';
      
      // Set error state for post-interview
      const errorPostInterviewState: PostInterviewState = {
        perTurnFeedback: [],
        finalSummary: {
          status: 'error',
          error: message
        },
        resources: {
          status: 'error',
          error: message
        }
      };
      setPostInterviewState(errorPostInterviewState);
      setState('post_interview');
      
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
      setPostInterviewState(null);
      setSessionId(null);
      setShowSessionWarning(false);
      setSessionTimeRemaining(null);
      
      // Reset coach feedback states
      setCoachFeedbackStates({});
      setLastFeedbackCount(0);
      
      // Stop any ongoing polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      if (finalSummaryPollingRef.current) {
        clearInterval(finalSummaryPollingRef.current);
        finalSummaryPollingRef.current = null;
      }
      if (sessionWarningIntervalRef.current) {
        clearInterval(sessionWarningIntervalRef.current);
        sessionWarningIntervalRef.current = null;
      }
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
    console.log('≡ƒÄ» proceedToFinalSummary called');
    console.log('≡ƒÄ» Current state:', state);
    console.log('≡ƒÄ» Results available:', !!results);
    console.log('≡ƒÄ» coachingSummary available:', !!results?.coachingSummary);
    console.log('≡ƒÄ» Full results object:', results);
    
    if (state === 'post_interview') {
      console.log('≡ƒÄ» Transitioning state from post_interview to completed');
      setState('completed');
    } else {
      console.log('≡ƒÄ» State transition blocked - not in post_interview state');
    }
  };

  const playTextToSpeech = async (text: string) => {
    if (!selectedVoice) return;
    
    try {
      const audioBlob = await api.textToSpeech(text);
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
    postInterviewState,
    selectedVoice,
    coachFeedbackStates,
    sessionId,
    showSessionWarning,
    sessionTimeRemaining,
    actions: {
      startInterview,
      sendMessage,
      endInterview,
      resetInterview,
      setSelectedVoice,
      proceedToFinalSummary,
      extendSession,
      handleSessionTimeout,
    }
  };
}
