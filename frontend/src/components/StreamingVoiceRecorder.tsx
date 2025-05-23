import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Volume2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { api, StreamingSpeechRecognition } from '@/services/api';

interface StreamingVoiceRecorderProps {
  onTranscriptUpdate: (text: string, isFinal: boolean) => void;
  isDisabled?: boolean;
}

const StreamingVoiceRecorder: React.FC<StreamingVoiceRecorderProps> = ({
  onTranscriptUpdate,
  isDisabled = false
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speakingTimestamp, setSpeakingTimestamp] = useState<number | null>(null);
  const { toast } = useToast();
  
  // Reference to the streaming recognition instance
  const recognitionRef = useRef<StreamingSpeechRecognition | null>(null);
  
  // Timeout ID for clearing the speaking state
  const speakingTimeoutRef = useRef<number | null>(null);
  
  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (speakingTimeoutRef.current) {
        window.clearTimeout(speakingTimeoutRef.current);
      }
    };
  }, []);

  // Reset speaking state after a period of silence
  useEffect(() => {
    if (isSpeaking && !isDisabled && isRecording) {
      // Visual feedback that continues for a short time after utterance ends
      if (speakingTimeoutRef.current) {
        window.clearTimeout(speakingTimeoutRef.current);
      }
    }
  }, [isSpeaking, isDisabled, isRecording]);

  const startRecording = async () => {
    try {
      setIsConnecting(true);
      
      // Create streaming recognition instance
      recognitionRef.current = api.createStreamingSpeechRecognition({
        onConnected: () => {
          console.log('Connected to streaming STT service');
          toast({
            title: 'Connected',
            description: 'Ready to capture your speech',
          });
        },
        onDisconnected: () => {
          console.log('Disconnected from streaming STT service');
          setIsRecording(false);
          setIsConnecting(false);
          setIsSpeaking(false);
        },
        onTranscript: (text, isFinal) => {
          if (text && text.trim() !== '') {
            onTranscriptUpdate(text, isFinal);
            
            // Any transcript indicates speaking
            if (!isSpeaking) {
              setIsSpeaking(true);
            }
          }
        },
        onSpeechStarted: (timestamp) => {
          console.log('Speech detected at timestamp:', timestamp);
          setIsSpeaking(true);
          setSpeakingTimestamp(timestamp);
          
          // Optional notification
          /* toast({
            title: 'Speech Detected',
            description: 'Started speaking',
          }); */
        },
        onUtteranceEnd: (lastSpokenAt) => {
          console.log('Utterance ended, last spoken at:', lastSpokenAt);
          
          // Set a timeout to clear the speaking state after a short delay
          // This gives better UX by not immediately toggling the UI
          if (speakingTimeoutRef.current) {
            window.clearTimeout(speakingTimeoutRef.current);
          }
          
          speakingTimeoutRef.current = window.setTimeout(() => {
            setIsSpeaking(false);
            setSpeakingTimestamp(null);
          }, 1000); // Keep "speaking" state for 1 second after utterance ends
        },
        onError: (error) => {
          console.error('Streaming STT error:', error);
          toast({
            title: 'Speech Recognition Error',
            description: error || 'An error occurred during speech recognition',
            variant: 'destructive',
          });
          stopRecording();
        },
      });
      
      // Start recognition
      await recognitionRef.current.start();
      setIsRecording(true);
      setIsConnecting(false);
      
    } catch (error) {
      console.error('Failed to start streaming recognition:', error);
      toast({
        title: 'Microphone Error',
        description: 'Could not access your microphone or connect to the speech service.',
        variant: 'destructive',
      });
      setIsRecording(false);
      setIsConnecting(false);
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsRecording(false);
    setIsConnecting(false);
    setIsSpeaking(false);
    setSpeakingTimestamp(null);
    
    if (speakingTimeoutRef.current) {
      window.clearTimeout(speakingTimeoutRef.current);
      speakingTimeoutRef.current = null;
    }
  };

  return (
    <div className="flex items-center gap-2">
      {isConnecting ? (
        <Button variant="ghost" size="icon" disabled>
          <div className="flex items-center justify-center">
            <span className="relative flex h-3 w-3 me-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-interview-secondary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-interview-secondary"></span>
            </span>
            <span>Connecting...</span>
          </div>
        </Button>
      ) : isRecording ? (
        <>
          {isSpeaking && (
            <div className="flex items-center animation-pulse">
              <Volume2 
                className="h-5 w-5 text-green-400 animate-pulse" 
                title={`Speaking detected at ${speakingTimestamp || 'unknown'}`}
              />
            </div>
          )}
          <Button 
            variant="destructive" 
            onClick={stopRecording}
            disabled={isDisabled}
            className={isSpeaking ? "border-2 border-green-500 shadow-green-500/20" : ""}
          >
            <MicOff className="h-4 w-4 mr-2" /> Stop Listening
          </Button>
        </>
      ) : (
        <Button 
          variant="secondary" 
          onClick={startRecording}
          disabled={isDisabled}
        >
          <Mic className="h-4 w-4 mr-2" /> Start Listening
        </Button>
      )}
    </div>
  );
};

export default StreamingVoiceRecorder; 