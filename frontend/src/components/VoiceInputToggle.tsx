import React, { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import VoiceRecorder from './VoiceRecorder';
import StreamingVoiceRecorder from './StreamingVoiceRecorder';

interface VoiceInputToggleProps {
  sessionId?: string;
  onTranscriptionComplete: (text: string) => void;
  isDisabled?: boolean;
}

const VoiceInputToggle: React.FC<VoiceInputToggleProps> = ({
  sessionId,
  onTranscriptionComplete,
  isDisabled = false
}) => {
  const [useStreaming, setUseStreaming] = useState(true);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [speechDetected, setSpeechDetected] = useState(false);
  const [accumulatedSegments, setAccumulatedSegments] = useState<string[]>([]);
  const { toast } = useToast();
  
  // Handle transcript updates from streaming mode
  const handleStreamingTranscript = (text: string, isFinal: boolean) => {
    if (isFinal) {
      // Set final transcript and clear interim
      setFinalTranscript(text);
      setInterimTranscript('');
      
      // When a final transcript is received, call the parent callback
      if (text.trim() !== '') {
        // Add to accumulated segments for visual feedback
        setAccumulatedSegments(prev => [...prev, text.trim()]);
        
        onTranscriptionComplete(text);
        
        // Clear the final transcript after a short delay, but keep accumulated segments longer
        setTimeout(() => {
          setFinalTranscript('');
        }, 2000);
        
        // Clear accumulated segments after a longer delay to show building process
        setTimeout(() => {
          setAccumulatedSegments(prev => prev.slice(1)); // Remove the oldest segment
        }, 5000);
      }
    } else {
      // Update the interim transcript
      setInterimTranscript(text);
    }
    
    // Speech is detected if there's text
    if (text && text.trim() !== '') {
      setSpeechDetected(true);
    }
  };
  
  // When speech ends, update UI
  const handleSpeechEnd = () => {
    setSpeechDetected(false);
  };
  
  const toggleMode = (checked: boolean) => {
    setUseStreaming(checked);
    // Clear transcripts when switching modes
    setInterimTranscript('');
    setFinalTranscript('');
    setAccumulatedSegments([]);
    setSpeechDetected(false);
    
    toast({
      title: checked ? 'Streaming Mode Enabled' : 'Batch Mode Enabled',
      description: checked 
        ? 'Your voice will be transcribed in real-time as you speak.'
        : 'Your voice will be recorded and then transcribed as a batch.'
    });
  };

  return (
    <div className="flex flex-col gap-4 w-full">
      <div className="flex items-center space-x-2 justify-end">
        <Label htmlFor="streaming-mode">Real-time Transcription</Label>
        <Switch 
          id="streaming-mode"
          checked={useStreaming}
          onCheckedChange={toggleMode}
          disabled={isDisabled}
        />
      </div>
      
      {/* Show transcripts when in streaming mode */}
      {useStreaming && (
        <div className="transition-all duration-300">
          {/* Accumulated segments to show building process */}
          {accumulatedSegments.length > 0 && (
            <div className="p-3 mb-2 rounded bg-purple-900/20 border border-purple-500/30 text-purple-200 text-sm">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-block h-2 w-2 rounded-full bg-purple-500 animate-pulse"></span>
                <strong>Building Answer:</strong>
                <span className="text-xs text-purple-400">({accumulatedSegments.length} segment{accumulatedSegments.length !== 1 ? 's' : ''})</span>
              </div>
              <div className="space-y-1">
                {accumulatedSegments.map((segment, index) => (
                  <div key={index} className="text-purple-100 opacity-80">
                    {index + 1}. {segment}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Final transcript with success styling */}
          {finalTranscript && (
            <div className="p-2 mb-2 rounded bg-emerald-900/30 border border-emerald-500/30 text-emerald-200 text-sm animate-fade-in">
              <strong>Just Added:</strong> {finalTranscript}
            </div>
          )}
          
          {/* Interim transcript with "in progress" styling */}
          {interimTranscript && (
            <div className={`p-2 rounded ${speechDetected ? 'bg-amber-900/20 border border-amber-500/30 text-amber-200' : 'bg-muted text-muted-foreground'} text-sm italic transition-all duration-300`}>
              {speechDetected ? <span className="inline-block h-2 w-2 rounded-full bg-green-500 mr-2 animate-pulse"></span> : null}
              <strong>Speaking:</strong> {interimTranscript}
            </div>
          )}
        </div>
      )}
      
      {/* Show appropriate voice input component based on selected mode */}
      <div className="flex justify-center">
        {useStreaming ? (
          <StreamingVoiceRecorder 
            sessionId={sessionId}
            onTranscriptUpdate={handleStreamingTranscript}
            isDisabled={isDisabled}
          />
        ) : (
          <VoiceRecorder
            onTranscriptionComplete={onTranscriptionComplete}
            isDisabled={isDisabled}
          />
        )}
      </div>
    </div>
  );
};

export default VoiceInputToggle; 