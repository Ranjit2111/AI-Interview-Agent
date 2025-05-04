import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, MicOff } from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface VoiceRecorderProps {
  onTranscriptionComplete: (text: string) => void;
  isDisabled?: boolean;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ 
  onTranscriptionComplete,
  isDisabled = false
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const { toast } = useToast();

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processAudio(audioBlob);
        
        // Stop all tracks to release the microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      toast({
        title: 'Microphone Error',
        description: 'Could not access your microphone. Please check permissions.',
        variant: 'destructive',
      });
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    try {
      setIsProcessing(true);
      
      // Send audio to the speech-to-text API
      const response = await api.speechToText(audioBlob);
      const taskId = response.task_id;
      
      console.log("Started STT process with task ID:", taskId);
      
      // Poll for results
      let status = 'processing';
      let transcript = '';
      let attempts = 0;
      const maxAttempts = 30; // Maximum polling attempts (30 seconds)
      
      while (status === 'processing' || status === 'uploading' || status === 'transcribing') {
        // Wait a bit before polling again
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const statusResponse = await api.checkSpeechToTextStatus(taskId);
        status = statusResponse.status;
        console.log("STT status check:", status, statusResponse);
        
        if (status === 'completed' && statusResponse.transcript) {
          transcript = statusResponse.transcript;
          console.log("Received transcript:", transcript);
          break; // Exit the loop once we have a transcript
        } else if (status === 'error') {
          console.error("Error from STT service:", statusResponse.error);
          throw new Error(statusResponse.error || 'An error occurred during speech recognition');
        }
        
        attempts++;
        if (attempts >= maxAttempts) {
          console.warn("STT polling timed out after 30 seconds");
          throw new Error('Speech recognition timed out. Please try again.');
        }
      }
      
      // Verify transcript is not empty before calling the callback
      if (!transcript || transcript.trim() === '') {
        console.warn("Empty transcript received!");
        toast({
          title: 'Empty Transcription',
          description: 'No speech was detected. Please try speaking more clearly or check your microphone.',
          variant: 'destructive',
        });
        return;
      }
      
      // Update the input field with the transcription
      console.log("Calling onTranscriptionComplete with:", transcript);
      onTranscriptionComplete(transcript);
      
    } catch (error) {
      console.error("Speech processing error details:", error);
      toast({
        title: 'Speech Recognition Error',
        description: error instanceof Error ? error.message : 'Failed to process speech',
        variant: 'destructive',
      });
      console.error('Speech processing error:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex items-center">
      {isProcessing ? (
        <Button variant="ghost" size="icon" disabled>
          <div className="flex items-center justify-center">
            <span className="relative flex h-3 w-3 me-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-interview-secondary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-interview-secondary"></span>
            </span>
            <span>Transcribing...</span>
          </div>
        </Button>
      ) : isRecording ? (
        <Button 
          variant="destructive" 
          onClick={stopRecording}
          disabled={isDisabled}
        >
          <MicOff className="h-4 w-4 mr-2" /> Stop Recording
        </Button>
      ) : (
        <Button 
          variant="secondary" 
          onClick={startRecording}
          disabled={isDisabled}
        >
          <Mic className="h-4 w-4 mr-2" /> Record Answer
        </Button>
      )}
    </div>
  );
};

export default VoiceRecorder;
