import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import VoiceFirstInterviewPanel from './VoiceFirstInterviewPanel';
import TranscriptDrawer from './TranscriptDrawer';
import OffScreenCoachFeedback from './OffScreenCoachFeedback';
import InterviewInstructionsModal from './InterviewInstructionsModal';
import { useVoiceFirstInterview } from '../hooks/useVoiceFirstInterview';
import { Message, CoachFeedbackState } from '@/hooks/useInterviewSession';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';

interface InterviewSessionProps {
  sessionId?: string; // Add sessionId for voice component integration
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onEndInterview: () => void;
  onVoiceSelect: (voiceId: string | null) => void;
  coachFeedbackStates: CoachFeedbackState;
}

const InterviewSession: React.FC<InterviewSessionProps> = ({
  sessionId,
  messages,
  isLoading,
  onSendMessage,
  onEndInterview,
  onVoiceSelect,
  coachFeedbackStates,
}) => {
  // State for emergency fallback mode
  // const [showFallbackMode, setShowFallbackMode] = useState(false);
  // const [fallbackInput, setFallbackInput] = useState('');
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [showInstructions, setShowInstructions] = useState(true);
  
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
      sessionId, // Pass sessionId for speech task tracking
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

  // Emergency exit button (top-right corner)
  const EmergencyExitButton = () => (
    <div className="fixed top-4 right-4 z-50 flex items-center space-x-2">
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

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Emergency Controls */}
      <EmergencyExitButton />

      {/* Transcript Toggle Button */}
      <button
        onClick={toggleTranscript}
        className={`
          fixed top-1/2 -translate-y-1/2 z-30 p-2 
          bg-gray-800/70 hover:bg-gray-700/90 backdrop-blur-sm
          border border-gray-600/80 hover:border-gray-500
          rounded-r-md shadow-lg text-white transition-all duration-300 ease-in-out
          ${transcriptVisible ? 'left-80 md:left-96' : 'left-0'}
        `}
        title={transcriptVisible ? 'Hide Transcript' : 'Show Transcript'}
        aria-label={transcriptVisible ? 'Hide Transcript' : 'Show Transcript'}
        aria-expanded={transcriptVisible}
      >
        {transcriptVisible ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

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
        accumulatedTranscript={accumulatedTranscript}
      />

      {/* Transcript Drawer */}
      <TranscriptDrawer
        isOpen={transcriptVisible}
        messages={messages}
        onClose={toggleTranscript}
        onPlayMessage={playTextToSpeech}
        onSendTextFromTranscript={onSendMessage}
      />

      {/* Off-Screen Coach Feedback */}
      <OffScreenCoachFeedback
        coachFeedbackStates={coachFeedbackStates}
        messages={messages}
        isOpen={coachFeedbackVisible}
        onToggle={toggleCoachFeedback}
        onClose={closeCoachFeedback}
      />

      {/* Interview Instructions Modal */}
      <InterviewInstructionsModal
        isOpen={showInstructions}
        onClose={() => setShowInstructions(false)}
      />
    </div>
  );
};

export default InterviewSession;
