import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import VoiceFirstInterviewPanel from './VoiceFirstInterviewPanel';
import TranscriptDrawer from './TranscriptDrawer';
import OffScreenCoachFeedback from './OffScreenCoachFeedback';
import { useVoiceFirstInterview } from '../hooks/useVoiceFirstInterview';
import { Message, CoachFeedbackState } from '@/hooks/useInterviewSession';
import { X } from 'lucide-react';

interface InterviewSessionProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onEndInterview: () => void;
  onVoiceSelect: (voiceId: string | null) => void;
  coachFeedbackStates: CoachFeedbackState;
}

const InterviewSession: React.FC<InterviewSessionProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onEndInterview,
  onVoiceSelect,
  coachFeedbackStates,
}) => {
  // State for emergency fallback mode
  const [showFallbackMode, setShowFallbackMode] = useState(false);
  const [fallbackInput, setFallbackInput] = useState('');
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  
  // Ref to track if we've set the default voice (avoids infinite loop)
  const defaultVoiceSetRef = useRef(false);

  // Initialize voice-first interview system with session data from props
  const {
    voiceState,
    microphoneActive,
    audioPlaying,
    transcriptVisible,
    coachFeedbackVisible,
    voiceActivityLevel,
    accumulatedTranscript,
    isListening,
    isProcessing,
    isDisabled,
    turnState,
    toggleMicrophone,
    toggleTranscript,
    toggleCoachFeedback,
    closeCoachFeedback,
    playTextToSpeech,
    lastExchange
  } = useVoiceFirstInterview(
    {
      messages,
      isLoading,
      state: 'interviewing', // We know it's interviewing since this component only renders in that state
      selectedVoice,
    }, 
    onSendMessage
  );

  // Auto-enable voice on component mount (only once)
  useEffect(() => {
    if (!defaultVoiceSetRef.current) {
      // Set local state and notify parent immediately on mount
      setSelectedVoice('Matthew');
      onVoiceSelect('Matthew');
      defaultVoiceSetRef.current = true;
      console.log('🔊 TTS enabled by default with Matthew voice');
    }
  }, []); // No dependencies - run only once on mount

  // Enhanced microphone toggle with voice transcription integration
  const handleMicrophoneToggle = async () => {
    if (isListening) {
      // Stop listening and process transcription
      toggleMicrophone();
      
      // The accumulated transcript will be automatically sent via the voice-first hook
      // No manual integration needed as it's handled in stopVoiceRecognition
    } else {
      // Start listening
      toggleMicrophone();
    }
  };

  // Emergency fallback to text input
  const handleFallbackSubmit = () => {
    if (fallbackInput.trim()) {
      onSendMessage(fallbackInput.trim());
      setFallbackInput('');
      setShowFallbackMode(false);
    }
  };

  // Emergency exit button (top-right corner)
  const EmergencyExitButton = () => (
    <div className="fixed top-4 right-4 z-50 flex items-center space-x-2">
      {/* Fallback Text Input Toggle */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowFallbackMode(!showFallbackMode)}
        className="
          bg-white/5 hover:bg-white/10 
          border-white/20 hover:border-white/30
          text-white/80 hover:text-white
          transition-all duration-300
        "
        title="Toggle text input mode"
      >
        Aa
      </Button>

      {/* End Interview Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={onEndInterview}
        disabled={isLoading}
        className="
          bg-red-900/20 hover:bg-red-900/40 
          border-red-500/30 hover:border-red-500/50
          text-red-300 hover:text-red-100
          transition-all duration-300
        "
      >
        <X className="w-4 h-4 mr-1" />
        End Interview
      </Button>
    </div>
  );

  // Fallback text input overlay
  const FallbackTextInput = () => {
    if (!showFallbackMode) return null;

    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 flex items-center justify-center p-4">
        <div className="bg-gray-900/90 backdrop-blur-xl border border-white/10 rounded-xl p-6 max-w-md w-full">
          <h3 className="text-lg font-semibold text-white mb-4">Text Input Mode</h3>
          <textarea
            value={fallbackInput}
            onChange={(e) => setFallbackInput(e.target.value)}
            placeholder="Type your response here..."
            className="
              w-full h-32 p-3 
              bg-gray-800/50 border border-gray-600 
              rounded-lg text-white placeholder-gray-400
              focus:border-blue-500 focus:ring-1 focus:ring-blue-500
              resize-none
            "
            autoFocus
          />
          <div className="flex justify-end space-x-2 mt-4">
            <Button
              variant="outline"
              onClick={() => setShowFallbackMode(false)}
              className="bg-white/5 hover:bg-white/10 border-white/20"
            >
              Cancel
            </Button>
            <Button
              onClick={handleFallbackSubmit}
              disabled={!fallbackInput.trim() || isLoading}
              className="bg-blue-600 hover:bg-blue-500"
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Emergency Controls */}
      <EmergencyExitButton />

      {/* Main Voice-First Interface */}
      <VoiceFirstInterviewPanel
        isListening={isListening}
        isProcessing={isProcessing || isLoading}
        isDisabled={isDisabled || audioPlaying}
        voiceActivity={voiceActivityLevel}
        turnState={audioPlaying ? 'ai' : turnState}
        messages={messages}
        onToggleMicrophone={handleMicrophoneToggle}
        onToggleTranscript={toggleTranscript}
        showMessages={true}
        showTranscriptButton={true}
      />

      {/* Transcript Drawer */}
      <TranscriptDrawer
        isOpen={transcriptVisible}
        messages={messages}
        onClose={toggleTranscript}
        onPlayMessage={playTextToSpeech}
      />

      {/* Off-Screen Coach Feedback */}
      <OffScreenCoachFeedback
        coachFeedbackStates={coachFeedbackStates}
        messages={messages}
        isOpen={coachFeedbackVisible}
        onToggle={toggleCoachFeedback}
        onClose={closeCoachFeedback}
      />

      {/* Fallback Text Input Mode */}
      <FallbackTextInput />

      {/* Loading Overlay for Interview State Changes */}
      {isLoading && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 flex items-center justify-center">
          <div className="bg-gray-900/90 backdrop-blur-xl border border-white/10 rounded-xl p-6">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6">
                <div className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              </div>
              <span className="text-white font-medium">Processing...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewSession;
