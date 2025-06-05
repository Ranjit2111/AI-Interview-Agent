import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import VoiceFirstInterviewPanel from './VoiceFirstInterviewPanel';
import TranscriptDrawer from './TranscriptDrawer';
import OffScreenCoachFeedback from './OffScreenCoachFeedback';
import InterviewInstructionsModal from './InterviewInstructionsModal';
import { useVoiceFirstInterview } from '../hooks/useVoiceFirstInterview';
import { Message, CoachFeedbackState } from '@/hooks/useInterviewSession';
import { 
  X, ChevronLeft, ChevronRight, Mic, MicOff, Brain, Activity, 
  MessageCircle, Timer, Sparkles, Zap, Eye, Volume2, VolumeX,
  Settings, BarChart3, Target, ArrowRight, Circle, Square,
  Triangle, Hexagon, Play, Pause, RotateCcw, FastForward
} from 'lucide-react';

interface InterviewSessionProps {
  sessionId?: string;
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
  // Enhanced state management
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [showInstructions, setShowInstructions] = useState(true);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [ambientIntensity, setAmbientIntensity] = useState(0.4);
  const [isFullscreen, setIsFullscreen] = useState(true);
  const [showAdvancedControls, setShowAdvancedControls] = useState(false);
  const [sessionStartTime] = useState(Date.now());
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; vx: number; vy: number; size: number; color: string; life: number }>>([]);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const defaultVoiceSetRef = useRef(false);

  // Initialize voice-first interview system
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
      setSelectedVoice('Matthew');
      onVoiceSelect('Matthew');
      defaultVoiceSetRef.current = true;
    }
  }, []);

  // Enhanced microphone toggle
  const handleMicrophoneToggle = async () => {
    if (isListening) {
      toggleMicrophone();
    } else {
      toggleMicrophone();
    }
  };

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
    <div className="fixed top-6 left-6 z-40 space-y-4">
      {/* Session info card */}
      <div className="bg-black/60 backdrop-blur-2xl border border-white/20 rounded-2xl p-4 hover:border-cyan-500/30 transition-all duration-500 group">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
            <Timer className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">
              {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
            </div>
            <div className="text-xs text-gray-400">Session Time</div>
          </div>
        </div>
      </div>

      {/* Question counter */}
      <div className="bg-black/60 backdrop-blur-2xl border border-white/20 rounded-2xl p-4 hover:border-purple-500/30 transition-all duration-500 group">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
            <MessageCircle className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">{questionCount}</div>
            <div className="text-xs text-gray-400">Questions</div>
          </div>
        </div>
      </div>

      {/* Current state indicator */}
      <div className="bg-black/60 backdrop-blur-2xl border border-white/20 rounded-2xl p-4 hover:border-emerald-500/30 transition-all duration-500 group">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 ${
            turnState === 'ai' ? 'bg-gradient-to-br from-orange-500 to-red-600' :
            isListening ? 'bg-gradient-to-br from-blue-500 to-cyan-600' :
            isProcessing ? 'bg-gradient-to-br from-purple-500 to-indigo-600' :
            'bg-gradient-to-br from-emerald-500 to-teal-600'
          }`}>
            {turnState === 'ai' ? <Volume2 className="w-5 h-5 text-white" /> :
             isListening ? <Mic className="w-5 h-5 text-white" /> :
             isProcessing ? <Brain className="w-5 h-5 text-white animate-pulse" /> :
             <Target className="w-5 h-5 text-white" />}
          </div>
          <div>
            <div className="text-sm font-semibold text-white">
              {turnState === 'ai' ? 'AI Speaking' :
               isListening ? 'Listening' :
               isProcessing ? 'Processing' :
               'Ready'}
            </div>
            <div className="text-xs text-gray-400">Status</div>
          </div>
        </div>
      </div>
    </div>
  );

  // Advanced control panel
  const renderAdvancedControls = () => (
    <div className="fixed bottom-6 left-6 right-6 z-40">
      <div className="bg-black/70 backdrop-blur-2xl border border-white/20 rounded-3xl p-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          {/* Left: Primary controls */}
          <div className="flex items-center space-x-4">
            <Button
              onClick={handleMicrophoneToggle}
              disabled={isDisabled}
              className={`w-16 h-16 rounded-2xl shadow-lg transition-all duration-300 group ${
                isListening 
                  ? 'bg-gradient-to-br from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 shadow-red-500/25' 
                  : 'bg-gradient-to-br from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-cyan-500/25'
              }`}
            >
              {isListening ? (
                <MicOff className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
              ) : (
                <Mic className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
              )}
            </Button>

            <Button
              onClick={toggleTranscript}
              variant="outline"
              className="w-14 h-14 rounded-xl bg-black/40 border-white/20 hover:border-purple-500/40 hover:bg-purple-500/10 transition-all duration-300 group"
            >
              <MessageCircle className="w-5 h-5 text-gray-300 group-hover:text-purple-300 group-hover:scale-110 transition-all" />
            </Button>

            <Button
              onClick={toggleCoachFeedback}
              variant="outline"
              className="w-14 h-14 rounded-xl bg-black/40 border-white/20 hover:border-emerald-500/40 hover:bg-emerald-500/10 transition-all duration-300 group"
            >
              <Brain className="w-5 h-5 text-gray-300 group-hover:text-emerald-300 group-hover:scale-110 transition-all" />
            </Button>
          </div>

          {/* Center: Voice activity visualization */}
          <div className="flex-1 flex justify-center">
            <div className="flex items-center space-x-2">
              {turnState === 'ai' && (
                <div className="flex items-center space-x-1">
                  <Volume2 className="w-5 h-5 text-orange-400" />
                  <div className="flex space-x-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className="w-1 h-8 bg-gradient-to-t from-orange-600 to-orange-400 rounded-full animate-pulse"
                        style={{ animationDelay: `${i * 0.1}s` }}
                      />
                    ))}
                  </div>
                  <span className="text-sm text-orange-300 font-medium ml-2">AI Speaking</span>
                </div>
              )}
              
              {isListening && (
                <div className="flex items-center space-x-1">
                  <Mic className="w-5 h-5 text-cyan-400" />
                  <div className="flex space-x-1">
                    {[...Array(7)].map((_, i) => (
                      <div
                        key={i}
                        className="w-1 bg-gradient-to-t from-cyan-600 to-cyan-400 rounded-full transition-all duration-150"
                        style={{ 
                          height: `${20 + (voiceActivityLevel || 0) * 20 + Math.sin(Date.now() / 200 + i) * 10}px`,
                          animationDelay: `${i * 0.1}s` 
                        }}
                      />
                    ))}
                  </div>
                  <span className="text-sm text-cyan-300 font-medium ml-2">Listening</span>
                </div>
              )}
              
              {isProcessing && (
                <div className="flex items-center space-x-2">
                  <Brain className="w-5 h-5 text-purple-400 animate-pulse" />
                  <div className="flex space-x-1">
                    {[...Array(3)].map((_, i) => (
                      <div
                        key={i}
                        className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 0.2}s` }}
                      />
                    ))}
                  </div>
                  <span className="text-sm text-purple-300 font-medium">Processing</span>
                </div>
              )}

              {!isListening && !isProcessing && turnState !== 'ai' && (
                <div className="flex items-center space-x-2 text-gray-400">
                  <Target className="w-5 h-5" />
                  <span className="text-sm font-medium">Ready to listen</span>
                </div>
              )}
            </div>
          </div>

          {/* Right: Secondary controls */}
          <div className="flex items-center space-x-4">
            <Button
              onClick={() => setShowAdvancedControls(!showAdvancedControls)}
              variant="outline"
              className="w-14 h-14 rounded-xl bg-black/40 border-white/20 hover:border-gray-400 hover:bg-gray-500/10 transition-all duration-300 group"
            >
              <Settings className="w-5 h-5 text-gray-300 group-hover:text-gray-100 group-hover:rotate-90 transition-all duration-300" />
            </Button>

            <Button
              onClick={onEndInterview}
              variant="outline"
              className="px-6 h-14 rounded-xl bg-black/40 border-red-500/30 hover:border-red-500/50 hover:bg-red-500/10 text-red-300 hover:text-red-100 transition-all duration-300 group"
            >
              <X className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
              End Interview
            </Button>
          </div>
        </div>

        {/* Expanded controls */}
        {showAdvancedControls && (
          <div className="mt-6 pt-6 border-t border-white/10">
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{questionCount}</div>
                <div className="text-sm text-gray-400">Questions Asked</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{responseCount}</div>
                <div className="text-sm text-gray-400">Responses Given</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">
                  {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
                </div>
                <div className="text-sm text-gray-400">Session Duration</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">
                  {messages.filter(m => m.role === 'assistant' && m.agent === 'coach').length}
                </div>
                <div className="text-sm text-gray-400">Coach Tips</div>
              </div>
            </div>
          </div>
        )}
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
          fixed top-1/2 -translate-y-1/2 z-30 p-4 
          bg-black/70 backdrop-blur-2xl border border-white/20 
          hover:border-cyan-500/40 hover:bg-cyan-500/10 
          shadow-2xl text-white transition-all duration-500 ease-out
          ${transcriptVisible ? 'left-80 md:left-96 rounded-r-2xl' : 'left-0 rounded-r-2xl'}
          group
        `}
        title={transcriptVisible ? 'Hide Transcript' : 'Show Transcript'}
      >
        <div className="flex items-center space-x-2">
          {transcriptVisible ? (
            <ChevronLeft className="w-6 h-6 group-hover:scale-110 transition-transform" />
          ) : (
            <ChevronRight className="w-6 h-6 group-hover:scale-110 transition-transform" />
          )}
          {!transcriptVisible && (
            <MessageCircle className="w-5 h-5 opacity-70 group-hover:opacity-100 transition-opacity" />
          )}
        </div>
      </button>

      {/* Main Voice-First Interface - Enhanced */}
      <div className="relative z-20 h-full">
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
        onClose={handleInstructionsClose}
      />
    </div>
  );
};

export default InterviewSession;
