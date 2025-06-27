import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import VoiceFirstInterviewPanel from './VoiceFirstInterviewPanel';
import TranscriptDrawer from './TranscriptDrawer';
import InterviewInstructionsModal from './InterviewInstructionsModal';
import { SessionWarningDialog } from './SessionWarningDialog';
import { useVoiceFirstInterview } from '../hooks/useVoiceFirstInterview';
import { useIsMobile } from '@/hooks/use-mobile';
import { Message, CoachFeedbackState } from '@/hooks/useInterviewSession';
import { 
  X, ChevronLeft, ChevronRight, Mic, MicOff, Brain, Activity, 
  MessageCircle, Timer, Sparkles, Zap, Eye, Volume2, VolumeX,
  BarChart3, Target, ArrowRight, Circle, Square,
  Triangle, Hexagon, Play, Pause, RotateCcw, FastForward, Loader2
} from 'lucide-react';

interface InterviewSessionProps {
  sessionId?: string;
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onEndInterview: () => void;
  onVoiceSelect: (voiceId: string | null) => void;
  coachFeedbackStates: CoachFeedbackState;
  showSessionWarning: boolean;
  sessionTimeRemaining: number | null;
  onExtendSession: () => void;
  onSessionTimeout: () => void;
}

const InterviewSession: React.FC<InterviewSessionProps> = ({
  sessionId,
  messages,
  isLoading,
  onSendMessage,
  onEndInterview,
  onVoiceSelect,
  coachFeedbackStates,
  showSessionWarning,
  sessionTimeRemaining,
  onExtendSession,
  onSessionTimeout,
}) => {
  // Enhanced state management
  const isMobile = useIsMobile();
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [showInstructions, setShowInstructions] = useState(true);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [ambientIntensity, setAmbientIntensity] = useState(0.4);
  const [isFullscreen, setIsFullscreen] = useState(true);
  const [sessionStartTime] = useState(Date.now());
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; vx: number; vy: number; size: number; color: string; life: number }>>([]);
  const [showCoachNotification, setShowCoachNotification] = useState(false);
  const [lastFeedbackCount, setLastFeedbackCount] = useState(0);
  const [latestFeedbackToggled, setLatestFeedbackToggled] = useState(false);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const defaultVoiceSetRef = useRef(false);

  // Initialize voice-first interview system
  const {
    voiceState,
    microphoneActive,
    audioPlaying,
    transcriptVisible,
    voiceActivityLevel,
    accumulatedTranscript,
    isListening,
    isProcessing,
    isDisabled,
    turnState,
    toggleMicrophone,
    toggleTranscript,
    playTextToSpeech,
    lastExchange
  } = useVoiceFirstInterview(
    {
      messages,
      isLoading,
      state: 'interviewing',
      selectedVoice,
      sessionId,
      disableAutoTTS: showInstructions,
    }, 
    onSendMessage
  );

  // Enhanced mouse tracking for 3D effects
  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    setMousePosition({ x, y });
  };

  // Time tracking
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Dynamic ambient intensity based on interview state
  useEffect(() => {
    if (turnState === 'ai' || audioPlaying) {
      setAmbientIntensity(0.8);
    } else if (isListening) {
      setAmbientIntensity(0.6 + (voiceActivityLevel || 0) * 0.4);
    } else if (isProcessing) {
      setAmbientIntensity(0.7);
    } else {
      setAmbientIntensity(0.4);
    }
  }, [turnState, audioPlaying, isListening, voiceActivityLevel, isProcessing]);

  // Advanced particle system
  useEffect(() => {
    if (isListening || turnState === 'ai' || isProcessing) {
      const particleCount = turnState === 'ai' ? 12 : 8;
      const newParticles = Array.from({ length: particleCount }, (_, i) => ({
        id: Date.now() + i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 3 + 1,
        color: turnState === 'ai' ? 'orange' : isListening ? 'cyan' : 'purple',
        life: 1
      }));
      setParticles(newParticles);
      
      const animationInterval = setInterval(() => {
        setParticles(prev => prev.map(p => ({
          ...p,
          x: (p.x + p.vx + 100) % 100,
          y: (p.y + p.vy + 100) % 100,
          life: Math.max(0, p.life - 0.02)
        })).filter(p => p.life > 0));
      }, 50);
      
      return () => clearInterval(animationInterval);
    } else {
      setParticles([]);
    }
  }, [isListening, turnState, isProcessing]);

  // Auto-enable voice on component mount
  useEffect(() => {
    if (!defaultVoiceSetRef.current) {
      setSelectedVoice('enabled');
      onVoiceSelect('enabled');
      defaultVoiceSetRef.current = true;
    }
  }, []);

  // Track coach feedback and show notifications
  useEffect(() => {
    const feedbackEntries = Object.values(coachFeedbackStates);
    const completedFeedback = feedbackEntries.filter(state => state.feedback && !state.isAnalyzing).length;
    
    if (completedFeedback > lastFeedbackCount) {
      setShowCoachNotification(true);
      setLastFeedbackCount(completedFeedback);
      
      // Hide notification after 2 seconds
      setTimeout(() => {
        setShowCoachNotification(false);
      }, 2000);
    }
  }, [coachFeedbackStates, lastFeedbackCount]);

  // Enhanced microphone toggle
  const handleMicrophoneToggle = async () => {
    if (isListening) {
      toggleMicrophone();
      } else {
      toggleMicrophone();
      }
  };

  // Find the latest user message with coach feedback
  const getLatestFeedbackMessageIndex = () => {
    const userMessageIndexes = messages
      .map((msg, index) => ({ msg, index }))
      .filter(({ msg }) => msg.role === 'user')
      .map(({ index }) => index)
      .reverse(); // Start from latest

    for (const messageIndex of userMessageIndexes) {
      const feedbackState = coachFeedbackStates[messageIndex];
      if (feedbackState?.feedback && !feedbackState.isAnalyzing) {
        return messageIndex;
      }
    }
    return null;
  };

  // Handle coach icon button click
  const handleCoachButtonClick = () => {
    const latestFeedbackIndex = getLatestFeedbackMessageIndex();
    
    if (latestFeedbackIndex === null) {
      // No feedback available yet
      return;
    }

    // If transcript is not visible, open it first
    if (!transcriptVisible) {
      toggleTranscript();
      // Wait a bit for the drawer to open, then toggle feedback
      setTimeout(() => {
        setLatestFeedbackToggled(!latestFeedbackToggled);
      }, 300);
    } else {
      // Transcript is already open, just toggle the feedback
      setLatestFeedbackToggled(!latestFeedbackToggled);
      }
  };

  // Reset latest feedback toggle when transcript is closed
  useEffect(() => {
    if (!transcriptVisible) {
      setLatestFeedbackToggled(false);
    }
  }, [transcriptVisible]);

  // Calculate session duration
  const sessionDuration = Math.floor((currentTime - sessionStartTime) / 1000);
  const minutes = Math.floor(sessionDuration / 60);
  const seconds = sessionDuration % 60;

  // Get current question count
  const questionCount = messages.filter(m => m.role === 'assistant' && m.agent === 'interviewer').length;
  const responseCount = messages.filter(m => m.role === 'user').length;

  // Advanced background system
  const renderAdvancedBackground = () => (
    <div className="absolute inset-0 overflow-hidden">
      {/* Primary ambient gradient */}
      <div 
        className="absolute inset-0 transition-all duration-1000 ease-out"
        style={{
          background: `
            radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, 
              rgba(34, 211, 238, ${ambientIntensity * 0.15}) 0%, 
              rgba(168, 85, 247, ${ambientIntensity * 0.08}) 30%, 
              transparent 70%),
            radial-gradient(circle at ${100 - mousePosition.x}% ${100 - mousePosition.y}%, 
              rgba(236, 72, 153, ${ambientIntensity * 0.12}) 0%, 
              rgba(34, 197, 94, ${ambientIntensity * 0.06}) 40%, 
              transparent 80%),
            linear-gradient(135deg, 
              rgba(0, 0, 0, 0.95) 0%, 
              rgba(15, 23, 42, 0.98) 50%, 
              rgba(0, 0, 0, 0.95) 100%)
          `
        }}
      />

      {/* Dynamic floating orbs based on interview state */}
      <div 
        className="absolute w-96 h-96 rounded-full opacity-30 blur-3xl transition-all duration-[4000ms] ease-in-out"
        style={{
          background: turnState === 'ai' 
            ? 'radial-gradient(circle, rgba(255, 149, 0, 0.6) 0%, rgba(236, 72, 153, 0.3) 50%, transparent 100%)'
            : isListening 
            ? 'radial-gradient(circle, rgba(34, 211, 238, 0.6) 0%, rgba(168, 85, 247, 0.3) 50%, transparent 100%)'
            : 'radial-gradient(circle, rgba(168, 85, 247, 0.4) 0%, rgba(34, 211, 238, 0.2) 50%, transparent 100%)',
          transform: `translate(${60 + mousePosition.x * 0.3}px, ${20 + mousePosition.y * 0.2}px) scale(${ambientIntensity})`,
          top: '10%',
          right: '5%',
        }}
      />
      
      <div 
        className="absolute w-80 h-80 rounded-full opacity-25 blur-2xl transition-all duration-[3000ms] ease-in-out"
        style={{
          background: isProcessing
            ? 'radial-gradient(circle, rgba(139, 92, 246, 0.5) 0%, rgba(34, 211, 238, 0.3) 50%, transparent 100%)'
            : 'radial-gradient(circle, rgba(34, 197, 94, 0.4) 0%, rgba(168, 85, 247, 0.2) 50%, transparent 100%)',
          transform: `translate(${-mousePosition.x * 0.4}px, ${-mousePosition.y * 0.3}px) scale(${0.8 + ambientIntensity * 0.4})`,
          bottom: '15%',
          left: '8%',
        }}
      />

      {/* Advanced particle system */}
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="absolute w-1 h-1 rounded-full transition-opacity duration-500"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            backgroundColor: particle.color === 'orange' ? '#FF9500' : particle.color === 'cyan' ? '#22D3EE' : '#A855F7',
            opacity: particle.life * ambientIntensity,
            transform: `scale(${particle.size})`,
            boxShadow: `0 0 ${particle.size * 4}px currentColor`,
          }}
        />
      ))}

      {/* Geometric accent elements */}
      <div className="absolute top-1/4 left-1/3 opacity-20">
        <Circle className="w-3 h-3 text-cyan-400 animate-pulse" style={{ animationDelay: '0s' }} />
      </div>
      <div className="absolute top-2/3 right-1/4 opacity-15">
        <Square className="w-2 h-2 text-purple-400 animate-bounce" style={{ animationDelay: '1s' }} />
      </div>
      <div className="absolute bottom-1/3 left-1/4 opacity-25">
        <Triangle className="w-4 h-4 text-pink-400 animate-pulse" style={{ animationDelay: '2s' }} />
      </div>
      <div className="absolute top-1/2 right-1/3 opacity-20">
        <Hexagon className="w-3 h-3 text-emerald-400 animate-bounce" style={{ animationDelay: '3s' }} />
      </div>
    </div>
  );

  // Premium floating status panel
  const renderFloatingStatusPanel = () => (
    <div className="fixed top-3 right-3 sm:top-4 sm:right-4 md:top-6 md:right-6 z-40 space-y-1.5 sm:space-y-2 md:space-y-4">
      {/* Session info card */}
      <div className="bg-black/60 backdrop-blur-2xl border border-white/20 rounded-lg sm:rounded-xl md:rounded-2xl p-2 sm:p-3 md:p-4 hover:border-cyan-500/30 transition-all duration-500 group">
        <div className="flex items-center space-x-1.5 sm:space-x-2 md:space-x-3">
          <div className="w-6 h-6 sm:w-8 sm:h-8 md:w-10 md:h-10 rounded-md sm:rounded-lg md:rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
            <Timer className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-white" />
          </div>
          <div>
            <div className="text-xs sm:text-xs md:text-sm font-semibold text-white">
              {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
            </div>
            <div className="text-xs text-gray-400 hidden sm:block">Session Time</div>
          </div>
        </div>
      </div>

      {/* Question counter */}
      <div className="bg-black/60 backdrop-blur-2xl border border-white/20 rounded-lg sm:rounded-xl md:rounded-2xl p-2 sm:p-3 md:p-4 hover:border-purple-500/30 transition-all duration-500 group">
        <div className="flex items-center space-x-1.5 sm:space-x-2 md:space-x-3">
          <div className="w-6 h-6 sm:w-8 sm:h-8 md:w-10 md:h-10 rounded-md sm:rounded-lg md:rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
            <MessageCircle className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-white" />
          </div>
          <div>
            <div className="text-xs sm:text-xs md:text-sm font-semibold text-white">{questionCount}</div>
            <div className="text-xs text-gray-400 hidden sm:block">Questions</div>
          </div>
        </div>
      </div>

      {/* Current state indicator */}
      <div className="bg-black/60 backdrop-blur-2xl border border-white/20 rounded-lg sm:rounded-xl md:rounded-2xl p-2 sm:p-3 md:p-4 hover:border-emerald-500/30 transition-all duration-500 group">
        <div className="flex items-center space-x-1.5 sm:space-x-2 md:space-x-3">
          <div className={`w-6 h-6 sm:w-8 sm:h-8 md:w-10 md:h-10 rounded-md sm:rounded-lg md:rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 ${
            turnState === 'ai' ? 'bg-gradient-to-br from-orange-500 to-red-600' :
            isListening ? 'bg-gradient-to-br from-blue-500 to-cyan-600' :
            isProcessing ? 'bg-gradient-to-br from-purple-500 to-indigo-600' :
            'bg-gradient-to-br from-emerald-500 to-green-600'
          }`}>
            {turnState === 'ai' ? <Volume2 className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-white" /> :
             isListening ? <Mic className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-white" /> :
             isProcessing ? <Brain className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-white animate-pulse" /> :
             <Target className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-white" />}
          </div>
          <div>
            <div className="text-xs sm:text-xs md:text-sm font-semibold text-white">
              {turnState === 'ai' ? 'AI Speaking' :
               isListening ? 'Listening' :
               isProcessing ? 'Processing' :
               'Ready'}
            </div>
            <div className="text-xs text-gray-400 hidden sm:block">Status</div>
          </div>
        </div>
      </div>
    </div>
  );

  // Advanced control panel
  const renderAdvancedControls = () => (
    <div className="fixed bottom-3 left-3 right-3 sm:bottom-4 sm:left-4 sm:right-4 md:bottom-6 md:left-6 md:right-6 z-40">
      <div className="bg-black/70 backdrop-blur-2xl border border-white/20 rounded-xl sm:rounded-2xl md:rounded-3xl p-3 sm:p-4 md:p-6 max-w-4xl mx-auto">
        <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4 md:gap-0">
          {/* Left: Primary controls */}
          <div className="flex items-center space-x-2 sm:space-x-3 md:space-x-4 order-2 sm:order-1">
            <Button
              onClick={handleMicrophoneToggle}
              disabled={isDisabled}
              className={`w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 rounded-lg sm:rounded-xl md:rounded-2xl shadow-lg transition-all duration-300 group focus:outline-none focus:ring-4 focus:ring-cyan-500/50 active:scale-95 min-h-[48px] ${
                isListening 
                  ? 'bg-gradient-to-br from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 shadow-red-500/25'
                  : 'bg-gradient-to-br from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-cyan-500/25'
              }`}
            >
              {isListening ? (
                <MicOff className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-white group-hover:scale-110 transition-transform" />
              ) : (
                <Mic className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-white group-hover:scale-110 transition-transform" />
              )}
            </Button>

            <Button
              onClick={toggleTranscript}
              variant="outline"
              className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-md sm:rounded-lg md:rounded-xl bg-black/40 border-white/20 hover:border-purple-500/40 hover:bg-purple-500/10 transition-all duration-300 group focus:outline-none focus:ring-4 focus:ring-purple-500/50 active:scale-95 min-h-[44px]"
              aria-label={transcriptVisible ? 'Hide transcript' : 'Show transcript'}
            >
              <MessageCircle className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-gray-300 group-hover:text-purple-300 group-hover:scale-110 transition-all" />
            </Button>

            {/* Coach Feedback Button */}
            <div className="relative">
              <Button
                onClick={handleCoachButtonClick}
                variant="outline"
                className={`w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-md sm:rounded-lg md:rounded-xl transition-all duration-300 group relative min-h-[44px] ${
                  Object.values(coachFeedbackStates).some(state => state.isAnalyzing)
                    ? 'bg-yellow-900/30 border-yellow-500/40 hover:bg-yellow-900/50'
                    : 'bg-black/40 border-white/20 hover:border-yellow-500/40 hover:bg-yellow-500/10'
                }`}
              >
                <div className="relative">
                  <Brain className={`w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 transition-all ${
                    Object.values(coachFeedbackStates).some(state => state.isAnalyzing)
                      ? 'text-yellow-300'
                      : 'text-gray-300 group-hover:text-yellow-300 group-hover:scale-110'
                  }`} />
                  
                  {/* Loading spinner overlay when analyzing */}
                  {Object.values(coachFeedbackStates).some(state => state.isAnalyzing) && (
                    <Loader2 className="absolute inset-0 w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 text-yellow-400 animate-spin" />
                  )}
                </div>
              </Button>

              {/* Notification popup */}
              {showCoachNotification && (
                <div 
                  className="absolute -top-10 sm:-top-12 left-1/2 transform -translate-x-1/2 z-50 animate-in fade-in-0 zoom-in-95 duration-500"
                  style={{
                    animation: 'fadeInOut 2s ease-in-out forwards'
                  }}
                >
                  <div className="bg-gradient-to-r from-yellow-900/90 to-orange-900/90 backdrop-blur-md border border-yellow-500/50 rounded-lg px-2 sm:px-3 py-1 sm:py-2 shadow-lg">
                    <p className="text-yellow-200 text-xs sm:text-sm font-medium whitespace-nowrap">
                      Coach feedback ready!
                    </p>
                    {/* Arrow pointer */}
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-yellow-500/50"></div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Center: Voice activity visualization */}
          <div className="flex-1 flex justify-center order-1 sm:order-2 mb-2 sm:mb-0">
            <div className="flex items-center space-x-2">
              {turnState === 'ai' && (
                <div className="flex items-center space-x-2">
                  <span className="text-xs sm:text-sm text-orange-300 font-medium">AI Speaking...</span>
                </div>
              )}
              
              {isListening && (
                <div className="flex items-center space-x-2">
                  <span className="text-xs sm:text-sm text-blue-300 font-medium">Listening...</span>
                </div>
              )}
              
              {isProcessing && (
                <div className="flex items-center space-x-2">
                  <Brain className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400 animate-pulse" />
                  <span className="text-xs sm:text-sm text-purple-300 font-medium">Processing...</span>
                </div>
              )}

              {!isListening && !isProcessing && turnState !== 'ai' && (
                <div className="flex items-center space-x-2 text-gray-400">
                  <Target className="w-4 h-4 sm:w-5 sm:h-5" />
                  <span className="text-xs sm:text-sm font-medium">Ready to listen</span>
                </div>
              )}
            </div>
          </div>

          {/* Right: End Interview Button */}
          <div className="flex items-center order-3">
            <Button
              onClick={onEndInterview}
              variant="outline"
              className="px-3 py-2 sm:px-4 sm:py-2 md:px-6 h-10 sm:h-12 md:h-14 rounded-md sm:rounded-lg md:rounded-xl bg-black/40 border-red-500/30 hover:border-red-500/50 hover:bg-red-500/10 text-red-300 hover:text-red-100 transition-all duration-300 group text-xs sm:text-sm md:text-base focus:outline-none focus:ring-4 focus:ring-red-500/50 active:scale-95 min-h-[44px]"
              aria-label="End interview session"
            >
              <X className="w-3 h-3 sm:w-4 sm:h-4 md:w-5 md:h-5 mr-1 sm:mr-1 md:mr-2 group-hover:scale-110 transition-transform" />
              <span className="hidden xs:inline sm:hidden md:inline">End Interview</span>
              <span className="xs:hidden sm:inline md:hidden">End</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  // Handle modal close and trigger TTS
  const handleInstructionsClose = () => {
    setShowInstructions(false);
    
    setTimeout(() => {
      const introMessage = messages.find(msg => 
        msg.role === 'assistant' && 
        msg.agent === 'interviewer' && 
        typeof msg.content === 'string'
      );
      
      if (introMessage && typeof introMessage.content === 'string') {
        playTextToSpeech(introMessage.content);
      }
    }, 100);
  };

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-screen overflow-hidden"
      onMouseMove={handleMouseMove}
    >
      {/* Advanced immersive background */}
      {renderAdvancedBackground()}
      
      {/* Floating status panels */}
      {renderFloatingStatusPanel()}

      {/* Transcript toggle - premium design */}
      <button
        onClick={toggleTranscript}
        className={`
          fixed top-1/2 -translate-y-1/2 z-30 p-3 md:p-4 
          bg-black/70 backdrop-blur-2xl border border-white/20 
          hover:border-cyan-500/40 hover:bg-cyan-500/10 
          shadow-2xl text-white transition-all duration-500 ease-out
          ${transcriptVisible ? 'left-72 sm:left-80 md:left-96 rounded-r-xl md:rounded-r-2xl' : 'left-0 rounded-r-xl md:rounded-r-2xl'}
          group
        `}
        title={transcriptVisible ? 'Hide Transcript' : 'Show Transcript'}
      >
        <div className="flex items-center space-x-1 md:space-x-2">
          {transcriptVisible ? (
            <ChevronLeft className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform" />
          ) : (
            <ChevronRight className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform" />
          )}
        </div>
      </button>

      {/* Main Voice-First Interface - Enhanced */}
      <div className="relative z-20 h-full">
      <VoiceFirstInterviewPanel
        isListening={isListening}
        isProcessing={isProcessing || isLoading}
        isDisabled={isDisabled}
        voiceActivity={voiceActivityLevel}
        turnState={turnState}
        messages={messages}
        onToggleMicrophone={handleMicrophoneToggle}
        onToggleTranscript={toggleTranscript}
        showMessages={true}
        accumulatedTranscript={accumulatedTranscript}
      />
      </div>

      {/* Advanced control panel */}
      {renderAdvancedControls()}

      {/* Transcript Drawer */}
      <TranscriptDrawer
        isOpen={transcriptVisible}
        messages={messages}
        onClose={toggleTranscript}
        onPlayMessage={playTextToSpeech}
        onSendTextFromTranscript={onSendMessage}
        coachFeedbackStates={coachFeedbackStates}
        latestFeedbackToggled={latestFeedbackToggled}
        latestFeedbackIndex={getLatestFeedbackMessageIndex()}
      />

      {/* Interview Instructions Modal */}
      <InterviewInstructionsModal
        isOpen={showInstructions}
        onClose={handleInstructionsClose}
      />

      {/* Session Warning Dialog */}
      <SessionWarningDialog
        open={showSessionWarning}
        timeRemaining={sessionTimeRemaining}
        onExtend={onExtendSession}
        onEndNow={onSessionTimeout}
      />

      {/* Custom styles for coach notification animation */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes fadeInOut {
            0% { opacity: 0; transform: translateY(10px) translateX(-50%) scale(0.9); }
            20% { opacity: 1; transform: translateY(0) translateX(-50%) scale(1); }
            80% { opacity: 1; transform: translateY(0) translateX(-50%) scale(1); }
            100% { opacity: 0; transform: translateY(-5px) translateX(-50%) scale(0.95); }
          }
        `
      }} />
    </div>
  );
};

export default InterviewSession;
