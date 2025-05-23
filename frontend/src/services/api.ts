// API service for all backend interactions
const API_BASE_URL = 'http://localhost:8000';
// WebSocket URL for streaming APIs
const WS_BASE_URL = 'ws://localhost:8000';

export interface InterviewStartRequest {
  job_role: string;
  job_description?: string;
  resume_content?: string;
  style?: 'formal' | 'casual' | 'aggressive' | 'technical';
  difficulty?: 'easy' | 'medium' | 'hard';
  target_question_count?: number;
  company_name?: string;
}

// Speech recognition types
export interface SpeechTranscriptionEvent {
  type: 'transcript' | 'error' | 'connected' | 'speech_started' | 'utterance_end';
  text?: string;
  is_final?: boolean;
  error?: string;
  message?: string;
  timestamp?: string;
  event_time?: string;
  last_spoken_at?: number;
}

export interface StreamingSpeechOptions {
  onTranscript: (transcript: string, isFinal: boolean) => void;
  onError: (error: string) => void;
  onConnected: () => void;
  onDisconnected: () => void;
  onSpeechStarted?: (timestamp: number) => void;
  onUtteranceEnd?: (lastSpokenAt: number) => void;
}

export class StreamingSpeechRecognition {
  private ws: WebSocket | null = null;
  private isConnected: boolean = false;
  private mediaStream: MediaStream | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private options: StreamingSpeechOptions;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  constructor(options: StreamingSpeechOptions) {
    this.options = options;
  }

  async start(): Promise<void> {
    try {
      // Get microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Connect WebSocket
      await this.connectWebSocket();
      
      // Start recording
      this.startRecording();
      
      return Promise.resolve();
    } catch (error) {
      return Promise.reject(error);
    }
  }

  stop(): void {
    // Stop recording
    if (this.mediaRecorder) {
      this.mediaRecorder.stop();
      this.mediaRecorder = null;
    }
    
    // Stop microphone
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    
    // Close WebSocket
    this.closeWebSocket();
  }

  private async connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Create WebSocket connection
      this.ws = new WebSocket(`${WS_BASE_URL}/api/speech-to-text/stream`);
      
      // Set binary type to arraybuffer
      this.ws.binaryType = 'arraybuffer';
      
      // Set up event handlers
      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        resolve();
      };
      
      this.ws.onclose = (event) => {
        this.isConnected = false;
        this.options.onDisconnected();
        console.log('WebSocket closed:', event);
      };
      
      this.ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        reject(new Error('WebSocket connection failed'));
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as SpeechTranscriptionEvent;
          
          switch (data.type) {
            case 'transcript':
              if (data.text !== undefined) {
                this.options.onTranscript(data.text, data.is_final || false);
              }
              break;
            case 'speech_started':
              if (data.timestamp !== undefined && this.options.onSpeechStarted) {
                this.options.onSpeechStarted(Number(data.timestamp));
              }
              break;
            case 'utterance_end':
              if (data.last_spoken_at !== undefined && this.options.onUtteranceEnd) {
                this.options.onUtteranceEnd(Number(data.last_spoken_at));
              }
              break;
            case 'error':
              if (data.error) {
                this.options.onError(data.error);
              }
              break;
            case 'connected':
              this.options.onConnected();
              break;
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
        }
      };
    });
  }

  private closeWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  private startRecording(): void {
    if (!this.mediaStream || !this.isConnected) return;
    
    // Create recorder with appropriate options
    // Using 16kHz mono audio for optimal STT performance
    const audioOptions = { mimeType: 'audio/webm' };
    
    try {
      this.mediaRecorder = new MediaRecorder(this.mediaStream, audioOptions);
      
      // Send data whenever it becomes available
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && this.ws && this.isConnected) {
          // Convert Blob to ArrayBuffer and send over WebSocket
          const reader = new FileReader();
          reader.onload = () => {
            if (this.ws && this.isConnected && reader.result) {
              this.ws.send(reader.result);
            }
          };
          reader.readAsArrayBuffer(event.data);
        }
      };
      
      // Start recording with small timeslices for low latency
      this.mediaRecorder.start(100);  // 100ms chunks
    } catch (error) {
      console.error('Error starting MediaRecorder:', error);
      this.options.onError(`Failed to start recording: ${error}`);
    }
  }
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

export interface ResumeUploadServerResponse {
  message: string;
  // Add other properties as needed based on what the server returns
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
  
  // File Processing API
  uploadResumeFile: async (file: File): Promise<ResumeUploadServerResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/files/upload-resume`, {
      method: 'POST',
      body: formData,
      // Note: Do not set Content-Type header when using FormData with fetch,
      // the browser will set it correctly including the boundary.
    });
    return handleResponse(response);
  },
  
  // Speech to Text API (batch processing with AssemblyAI)
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
  
  // Create streaming speech recognition instance
  createStreamingSpeechRecognition: (options: StreamingSpeechOptions): StreamingSpeechRecognition => {
    return new StreamingSpeechRecognition(options);
  },
  
  // Text to Speech API
  textToSpeech: async (text: string, voiceId: string = "Matthew", speed?: number): Promise<Blob> => {
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
