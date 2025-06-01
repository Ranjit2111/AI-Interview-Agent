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
  showTranscriptButton?: boolean;
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
  showTranscriptButton = true
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
      className="immersive-interview-panel relative overflow-hidden"
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
      <div className="voice-first-layout">
        
        {/* Minimal Message Display - Positioned at top */}
        {showMessages && (
          <div className="absolute top-0 left-0 right-0 z-20">
            <MinimalMessageDisplay
              lastUserMessage={lastUserMessage}
              lastAIMessage={lastAIMessage}
              isVisible={Boolean(lastUserMessage || lastAIMessage)}
              autoHideTimeout={30000}
              onToggleTranscript={showTranscriptButton ? onToggleTranscript : undefined}
            />
          </div>
        )}

        {/* Central Microphone Button - Main focal point */}
        <div className="flex-1 flex items-center justify-center min-h-screen">
          <CentralMicButton
            isListening={isListening}
            isProcessing={isProcessing}
            isDisabled={isDisabled}
            voiceActivity={voiceActivity}
            turnState={turnState}
            onToggle={onToggleMicrophone}
          />
        </div>

        {/* Status Area - Fixed at bottom */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
          <div className="text-center space-y-4">
            {/* Ambient Audio Visualizer */}
            {(isListening || turnState === 'ai') && (
              <div className="flex items-center space-x-2 opacity-40 mb-4">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div
                    key={i}
                    className={`
                      w-0.5 rounded-full transition-all duration-200
                      ${turnState === 'ai' ? 'bg-orange-400' : 'bg-blue-400'}
                    `}
                    style={{
                      height: `${4 + Math.sin(Date.now() * 0.01 + i * 0.5) * (isListening ? voiceActivity * 8 : 4)}px`,
                      animationDelay: `${i * 0.1}s`
                    }}
                  />
                ))}
              </div>
            )}

            {/* Connection Status */}
            <div className="flex items-center justify-center space-x-2">
              <div 
                className={`
                  w-2 h-2 rounded-full transition-colors duration-300
                  ${isDisabled ? 'bg-red-500 animate-pulse' : 'bg-green-500'}
                `}
              />
              <span className="text-xs text-gray-400 font-medium">
                {isDisabled ? 'Connecting...' : 'Connected'}
              </span>
            </div>

            {/* Session Progress Indicator */}
            {messages.length > 0 && (
              <div className="text-xs text-gray-500">
                {messages.filter(m => m.role === 'user').length} exchanges
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Corner Accent Lights */}
      <div className="absolute top-4 left-4 w-16 h-16">
        <div 
          className="w-full h-full rounded-full opacity-20 blur-xl"
          style={{
            background: turnState === 'ai' 
              ? `radial-gradient(circle, rgba(255, 149, 0, ${ambientIntensity}) 0%, transparent 70%)`
              : `radial-gradient(circle, rgba(0, 122, 255, ${ambientIntensity}) 0%, transparent 70%)`
          }}
        />
      </div>
      
      <div className="absolute top-4 right-4 w-16 h-16">
        <div 
          className="w-full h-full rounded-full opacity-20 blur-xl"
          style={{
            background: turnState === 'ai' 
              ? `radial-gradient(circle, rgba(175, 82, 222, ${ambientIntensity}) 0%, transparent 70%)`
              : `radial-gradient(circle, rgba(0, 122, 255, ${ambientIntensity * 0.7}) 0%, transparent 70%)`
          }}
        />
      </div>

      <div className="absolute bottom-4 left-4 w-12 h-12">
        <div 
          className="w-full h-full rounded-full opacity-15 blur-lg"
          style={{
            background: `radial-gradient(circle, rgba(255, 255, 255, ${ambientIntensity * 0.5}) 0%, transparent 70%)`
          }}
        />
      </div>

      <div className="absolute bottom-4 right-4 w-12 h-12">
        <div 
          className="w-full h-full rounded-full opacity-15 blur-lg"
          style={{
            background: `radial-gradient(circle, rgba(255, 255, 255, ${ambientIntensity * 0.3}) 0%, transparent 70%)`
          }}
        />
      </div>
    </div>
  );
};

export default VoiceFirstInterviewPanel; 