// API service for all backend interactions
const API_BASE_URL = 'http://localhost:8000';

export interface InterviewStartRequest {
  job_role: string;
  job_description?: string;
  resume_content?: string;
  style?: 'formal' | 'casual' | 'aggressive' | 'technical';
  difficulty?: 'easy' | 'medium' | 'hard';
  target_question_count?: number;
  company_name?: string;
}

export interface UserInput {
  message: string;
}

// This interface should match the structure returned by the /interview/message endpoint,
// which is based on the dictionary constructed in AgentSessionManager.process_message
export interface AgentResponse {
  role: 'user' | 'assistant' | 'system'; // Role can be user, assistant, or system
  agent?: 'interviewer' | 'coach';      // Optional: specifies the agent type for assistant messages
  content: any;                         // Can be string (interviewer) or object (coach feedback)
  response_type?: string;               // e.g., 'question', 'coaching_feedback', 'introduction', 'closing'
  metadata?: Record<string, any>;       // Any additional metadata
  timestamp?: string;                   // ISO string timestamp
  processing_time?: number;             // Optional processing time
  is_error?: boolean;                   // If it's a system error message
}

export interface PerTurnFeedbackItem {
  question: string;
  answer: string;
  feedback: string;
}

export interface EndResponse {
  results: {
    coaching_summary: any;
  };
  per_turn_feedback?: PerTurnFeedbackItem[];
}

export interface HistoryResponse {
  history: any[];
}

export interface StatsResponse {
  stats: any;
}

export interface ResetResponse {
  message: string;
}

export interface TTSVoice {
  id: string;
  name: string;
  [key: string]: any;
}

// Helper for handling response errors
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'An error occurred');
  }
  
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  
  return response;
};

// API methods
export const api = {
  // Health check
  checkHealth: async () => {
    const response = await fetch(`${API_BASE_URL}/`);
    return handleResponse(response);
  },
  
  // Interview API
  startInterview: async (config: InterviewStartRequest): Promise<ResetResponse> => {
    const response = await fetch(`${API_BASE_URL}/interview/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return handleResponse(response);
  },
  
  sendMessage: async (input: UserInput): Promise<AgentResponse> => {
    const response = await fetch(`${API_BASE_URL}/interview/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    });
    return handleResponse(response);
  },
  
  endInterview: async (): Promise<EndResponse> => {
    const response = await fetch(`${API_BASE_URL}/interview/end`, {
      method: 'POST',
    });
    return handleResponse(response);
  },
  
  getHistory: async (): Promise<HistoryResponse> => {
    const response = await fetch(`${API_BASE_URL}/interview/history`);
    return handleResponse(response);
  },
  
  getStats: async (): Promise<StatsResponse> => {
    const response = await fetch(`${API_BASE_URL}/interview/stats`);
    return handleResponse(response);
  },
  
  resetInterview: async (): Promise<ResetResponse> => {
    const response = await fetch(`${API_BASE_URL}/interview/reset`, {
      method: 'POST',
    });
    return handleResponse(response);
  },
  
  // Speech to Text API
  speechToText: async (audioBlob: Blob, language?: string): Promise<{ task_id: string, status: string }> => {
    const formData = new FormData();
    formData.append('audio_file', audioBlob);
    if (language) {
      formData.append('language', language);
    }
    
    const response = await fetch(`${API_BASE_URL}/api/speech-to-text`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(response);
  },
  
  checkSpeechToTextStatus: async (taskId: string): Promise<{ status: string, transcript?: string, error?: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/speech-to-text/status/${taskId}`);
    return handleResponse(response);
  },
  
  // Text to Speech API
  getVoices: async (): Promise<{ voices: TTSVoice[] }> => {
    const response = await fetch(`${API_BASE_URL}/api/text-to-speech/voices`);
    return handleResponse(response);
  },
  
  textToSpeech: async (text: string, voiceId: string, speed?: number): Promise<Blob> => {
    const formData = new URLSearchParams();
    formData.append('text', text);
    formData.append('voice_id', voiceId);
    if (speed !== undefined) {
      formData.append('speed', speed.toString());
    }
    
    const response = await fetch(`${API_BASE_URL}/api/text-to-speech`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'An error occurred with TTS');
    }
    
    return response.blob();
  },
};
