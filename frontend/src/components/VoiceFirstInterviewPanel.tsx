import React, { useEffect, useRef, useState } from 'react';
import CentralMicButton from './CentralMicButton';
import MinimalMessageDisplay from './MinimalMessageDisplay';
import { Message } from '../hooks/useInterviewSession';

interface VoiceFirstInterviewPanelProps {
  // Voice state
  isListening: boolean;
  isProcessing: boolean;
  isDisabled: boolean;
  voiceActivity?: number;
  turnState: 'user' | 'ai' | 'idle';
  
  // Messages
  messages: Message[];
  
  // Actions
  onToggleMicrophone: () => void;
  onToggleTranscript: () => void;
  
  // Display preferences
  showMessages?: boolean;
  accumulatedTranscript?: string;
}

const VoiceFirstInterviewPanel: React.FC<VoiceFirstInterviewPanelProps> = ({
  isListening,
  isProcessing,
  isDisabled,
  voiceActivity = 0,
  turnState,
  messages,
  onToggleMicrophone,
  onToggleTranscript,
  showMessages = true,
  accumulatedTranscript
}) => {
  const panelRef = useRef<HTMLDivElement>(null);
  const [ambientIntensity, setAmbientIntensity] = useState(0.3);
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; delay: number }>>([]);

  // Get last messages for minimal display
  const getLastMessages = () => {
    const userMessages = messages.filter(m => m.role === 'user');
    const aiMessages = messages.filter(m => m.role === 'assistant' && m.agent === 'interviewer');
    
    const lastUserMessage = userMessages[userMessages.length - 1]?.content;
    const lastAIMessage = aiMessages[aiMessages.length - 1]?.content;
    
    // Ensure we return strings for display
    return { 
      lastUserMessage: typeof lastUserMessage === 'string' ? lastUserMessage : '',
      lastAIMessage: typeof lastAIMessage === 'string' ? lastAIMessage : ''
    };
  };

  // Update ambient intensity based on voice activity and turn state
  useEffect(() => {
    if (turnState === 'ai') {
      setAmbientIntensity(0.6);
    } else if (isListening && voiceActivity > 0) {
      setAmbientIntensity(0.4 + voiceActivity * 0.4);
    } else if (isListening) {
      setAmbientIntensity(0.5);
    } else {
      setAmbientIntensity(0.3);
    }
  }, [isListening, voiceActivity, turnState]);

  // Generate ambient particles
  useEffect(() => {
    if (isListening || turnState === 'ai') {
      const newParticles = Array.from({ length: 8 }, (_, i) => ({
        id: Date.now() + i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        delay: Math.random() * 4
      }));
      setParticles(newParticles);
    } else {
      setParticles([]);
    }
  }, [isListening, turnState]);

  // Dynamic background gradient based on state
  const getBackgroundGradient = () => {
    if (turnState === 'ai') {
      return `
        radial-gradient(circle at 20% 20%, rgba(255, 149, 0, ${ambientIntensity * 0.08}) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(175, 82, 222, ${ambientIntensity * 0.06}) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(255, 149, 0, ${ambientIntensity * 0.04}) 0%, transparent 50%)
      `;
    } else if (isListening) {
      return `
        radial-gradient(circle at 30% 30%, rgba(0, 122, 255, ${ambientIntensity * 0.08}) 0%, transparent 50%),
        radial-gradient(circle at 70% 70%, rgba(0, 122, 255, ${ambientIntensity * 0.06}) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(0, 122, 255, ${ambientIntensity * 0.04}) 0%, transparent 50%)
      `;
    } else {
      return `
        radial-gradient(circle at 20% 20%, rgba(0, 122, 255, 0.02) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(255, 149, 0, 0.02) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(175, 82, 222, 0.01) 0%, transparent 50%)
      `;
    }
  };

  const { lastUserMessage, lastAIMessage } = getLastMessages();

  return (
    <div 
      ref={panelRef}
      className="immersive-interview-panel relative overflow-hidden min-h-screen flex flex-col"
      style={{
        backgroundImage: getBackgroundGradient(),
        transition: 'all 0.8s ease-out'
      }}
    >
      {/* Ambient Lighting Effects */}
      <div className="absolute inset-0 ambient-lighting opacity-50" />
      
      {/* Dynamic Border Glow */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          border: `1px solid rgba(255, 255, 255, ${0.05 + ambientIntensity * 0.1})`,
          boxShadow: `
            inset 0 0 60px rgba(0, 122, 255, ${ambientIntensity * 0.1}),
            inset 0 0 120px rgba(255, 149, 0, ${ambientIntensity * 0.05}),
            0 0 60px rgba(0, 0, 0, 0.8)
          `,
          transition: 'all 0.8s ease-out'
        }}
      />

      {/* Floating Particles */}
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="particle-effect"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            animationDelay: `${particle.delay}s`,
            opacity: ambientIntensity * 0.6
          }}
        />
      ))}

      {/* Main Content Layout */}
      <div className="voice-first-layout h-full min-h-screen flex flex-col">

        {/* Central Microphone Button - Main focal point */}
        <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center w-full max-w-xl sm:max-w-2xl">
            <CentralMicButton
              isListening={isListening}
              isProcessing={isProcessing}
              isDisabled={isDisabled}
              voiceActivity={voiceActivity}
              turnState={turnState}
              onToggle={onToggleMicrophone}
            />
          </div>
        </div>

        {/* User Transcript Display */}
        {accumulatedTranscript && accumulatedTranscript.trim() && (
          <div className="
            accumulated-transcript absolute left-1/2 bottom-6 sm:bottom-8 transform -translate-x-1/2
            mx-3 sm:mx-4 lg:mx-6 xl:mx-8 px-3 sm:px-4 lg:px-6 py-2.5 sm:py-3 lg:py-4 
            bg-gray-900/40 backdrop-blur-sm 
            border border-blue-500/20 
            rounded-lg sm:rounded-xl shadow-lg
            max-w-xl sm:max-w-2xl w-[calc(100%-2rem)] sm:w-auto
            transition-all duration-300
          ">
            <div className="flex items-start space-x-2 sm:space-x-3">
              <div className="
                w-5 h-5 sm:w-6 sm:h-6 lg:w-8 lg:h-8 rounded-full 
                bg-blue-500/20 border border-blue-400/30
                flex items-center justify-center flex-shrink-0 mt-0.5
              ">
                <span className="text-blue-300 text-xs sm:text-xs lg:text-sm font-medium">You</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white/90 text-sm sm:text-base lg:text-lg leading-relaxed break-words">
                  {accumulatedTranscript}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Corner Accent Lights */}
      <div className="absolute top-3 left-3 sm:top-4 sm:left-4 w-12 h-12 sm:w-16 sm:h-16">
        <div 
          className="w-full h-full rounded-full opacity-20 blur-xl"
          style={{
            background: turnState === 'ai' 
              ? 'radial-gradient(circle, rgba(255, 149, 0, 0.6), transparent)'
              : 'radial-gradient(circle, rgba(0, 122, 255, 0.6), transparent)',
          }}
        />
      </div>
      <div className="absolute bottom-3 right-3 sm:bottom-4 sm:right-4 w-12 h-12 sm:w-16 sm:h-16">
        <div 
          className="w-full h-full rounded-full opacity-15 blur-xl"
          style={{
            background: isListening 
              ? 'radial-gradient(circle, rgba(0, 122, 255, 0.5), transparent)'
              : 'radial-gradient(circle, rgba(175, 82, 222, 0.5), transparent)',
          }}
        />
      </div>
    </div>
  );
};

export default VoiceFirstInterviewPanel; 