import React, { useRef, useEffect, useState } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import AppleIntelligenceGlow from './AppleIntelligenceGlow';

interface CentralMicButtonProps {
  isListening: boolean;
  isProcessing: boolean;
  isDisabled: boolean;
  voiceActivity?: number; // 0-1 for voice volume
  turnState: 'user' | 'ai' | 'idle';
  onToggle: () => void;
}

const CentralMicButton: React.FC<CentralMicButtonProps> = ({
  isListening,
  isProcessing,
  isDisabled,
  voiceActivity = 0,
  turnState,
  onToggle
}) => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [isPressed, setIsPressed] = useState(false);

  // Handle button press animations
  const handleMouseDown = () => {
    setIsPressed(true);
  };

  const handleMouseUp = () => {
    setIsPressed(false);
  };

  // Voice activity visualization
  useEffect(() => {
    if (!buttonRef.current) return;

    if (isListening && voiceActivity > 0) {
      const intensity = Math.min(1, voiceActivity * 1.2);
      buttonRef.current.style.setProperty('--voice-intensity', intensity.toString());
    } else {
      buttonRef.current.style.setProperty('--voice-intensity', '0');
    }
  }, [voiceActivity, isListening]);

  const getButtonState = () => {
    if (isDisabled) return 'disabled';
    if (isProcessing) return 'processing';
    if (isListening) return 'listening';
    return 'idle';
  };

  const getGlowMode = (): 'user' | 'ai' | 'idle' => {
    if (isDisabled) return 'idle';
    if (turnState === 'ai') return 'ai';
    if (isListening || turnState === 'user') return 'user';
    return 'idle';
  };

  const getIconComponent = () => {
    if (isProcessing) {
      return <Loader2 className="w-8 h-8 text-white animate-spin" />;
    }
    
    if (isListening) {
      return <MicOff className="w-8 h-8 text-white" />;
    }
    
    return <Mic className="w-8 h-8 text-white" />;
  };

  const buttonState = getButtonState();
  const glowMode = getGlowMode();

  return (
    <div className="relative flex flex-col items-center">
      {/* Main Button with Glow */}
      <AppleIntelligenceGlow
        isActive={isListening || turnState === 'ai'}
        mode={glowMode}
        voiceActivity={voiceActivity}
      >
        <button
          ref={buttonRef}
          onClick={onToggle}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          disabled={isDisabled}
          className={`
            central-mic-button
            ${buttonState === 'listening' ? 'listening' : ''}
            ${buttonState === 'processing' ? 'processing' : ''}
            ${buttonState === 'disabled' ? 'disabled' : ''}
            ${isPressed ? 'scale-95' : ''}
          `}
          style={{
            '--voice-intensity': '0',
            transform: `scale(${isPressed ? '0.95' : '1'}) scale(calc(1 + var(--voice-intensity, 0) * 0.1))`,
            background: 'transparent',
            border: 'none',
          } as React.CSSProperties}
        >
          {/* Icon */}
          <div className="relative z-10 flex items-center justify-center">
            {getIconComponent()}
          </div>
        </button>
      </AppleIntelligenceGlow>

      {/* Voice Activity Waveform */}
      {isListening && voiceActivity > 0.1 && (
        <div className="voice-activity-wave mt-6 text-blue-400">
          <div className="wave-bar" style={{ height: `${4 + voiceActivity * 16}px` }} />
          <div className="wave-bar" style={{ height: `${4 + voiceActivity * 12}px` }} />
          <div className="wave-bar" style={{ height: `${4 + voiceActivity * 20}px` }} />
          <div className="wave-bar" style={{ height: `${4 + voiceActivity * 14}px` }} />
          <div className="wave-bar" style={{ height: `${4 + voiceActivity * 18}px` }} />
          <div className="wave-bar" style={{ height: `${4 + voiceActivity * 10}px` }} />
          <div className="wave-bar" style={{ height: `${4 + voiceActivity * 16}px` }} />
        </div>
      )}

      {/* AI Speaking Indicator */}
      {turnState === 'ai' && (
        <div className="mt-6 flex items-center space-x-2 text-orange-400">
          <div className="voice-activity-wave">
            <div className="wave-bar animate-voice-wave" />
            <div className="wave-bar animate-voice-wave animation-delay-100" />
            <div className="wave-bar animate-voice-wave animation-delay-200" />
            <div className="wave-bar animate-voice-wave animation-delay-300" />
            <div className="wave-bar animate-voice-wave animation-delay-400" />
          </div>
          <span className="text-sm font-medium ml-3">AI Speaking...</span>
        </div>
      )}

      {/* Status Text */}
      <div className="mt-4 text-center">
        {buttonState === 'listening' && (
          <p className="text-sm text-blue-300 font-medium">
            Listening... Tap to stop
          </p>
        )}
        {buttonState === 'processing' && (
          <p className="text-sm text-gray-300 font-medium">
            Processing...
          </p>
        )}
        {buttonState === 'idle' && !isDisabled && (
          <p className="text-sm text-gray-400 font-medium">
            Tap to speak
          </p>
        )}
        {buttonState === 'disabled' && (
          <p className="text-sm text-gray-500 font-medium">
            Please wait...
          </p>
        )}
      </div>
    </div>
  );
};

export default CentralMicButton; 