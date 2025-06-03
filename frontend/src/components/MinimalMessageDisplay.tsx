import React, { useEffect, useState } from 'react';
import { User, Bot } from 'lucide-react';

interface MinimalMessageDisplayProps {
  lastUserMessage?: string;
  lastAIMessage?: string;
  isVisible: boolean;
  autoHideTimeout?: number;
  onToggleTranscript?: () => void;
}

const MinimalMessageDisplay: React.FC<MinimalMessageDisplayProps> = ({
  lastUserMessage,
  lastAIMessage,
  isVisible,
  autoHideTimeout = 8000, // Reduced from 30 seconds to 8 seconds
  onToggleTranscript
}) => {
  const [shouldShow, setShouldShow] = useState(isVisible);
  const [hideTimer, setHideTimer] = useState<NodeJS.Timeout | null>(null);

  // Handle auto-hide functionality
  useEffect(() => {
    if (isVisible && autoHideTimeout > 0) {
      // Clear existing timer
      if (hideTimer) {
        clearTimeout(hideTimer);
      }

      // Set new timer
      const timer = setTimeout(() => {
        setShouldShow(false);
      }, autoHideTimeout);

      setHideTimer(timer);
      setShouldShow(true);

      return () => {
        if (timer) clearTimeout(timer);
      };
    } else {
      setShouldShow(isVisible);
    }
  }, [isVisible, autoHideTimeout, lastUserMessage, lastAIMessage]);

  // Handle manual show/hide
  useEffect(() => {
    setShouldShow(isVisible);
  }, [isVisible]);

  const handleMouseEnter = () => {
    // Pause auto-hide on hover
    if (hideTimer) {
      clearTimeout(hideTimer);
      setHideTimer(null);
    }
  };

  const handleMouseLeave = () => {
    // Resume auto-hide on mouse leave
    if (autoHideTimeout > 0 && isVisible) {
      const timer = setTimeout(() => {
        setShouldShow(false);
      }, 3000); // Shorter timeout after hover (3 seconds)
      setHideTimer(timer);
    }
  };

  if (!lastUserMessage && !lastAIMessage) {
    return null;
  }

  return (
    <div 
      className={`
        minimal-text-overlay
        transition-all duration-500 ease-out
        ${shouldShow ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}
      `}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* User Message */}
        {lastUserMessage && (
          <div className="floating-message-user animate-fade-in">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-blue-500/20 border border-blue-400/30 flex items-center justify-center">
                  <User className="w-4 h-4 text-blue-300" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-blue-100 leading-relaxed">
                  {lastUserMessage}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* AI Message */}
        {lastAIMessage && (
          <div className="floating-message-ai animate-fade-in animation-delay-200">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500/20 to-purple-500/20 border border-orange-400/30 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-orange-300" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-orange-100 leading-relaxed">
                  {lastAIMessage}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Fade Overlay Indicator */}
      {shouldShow && autoHideTimeout > 0 && (
        <div className="absolute top-0 right-0 mt-2 mr-2">
          <div className="w-2 h-2 bg-gray-400/50 rounded-full animate-pulse" />
        </div>
      )}
    </div>
  );
};

export default MinimalMessageDisplay; 