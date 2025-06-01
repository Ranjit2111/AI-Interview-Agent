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
  autoHideTimeout = 30000, // 30 seconds
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
      }, 5000); // Shorter timeout after hover
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

        {/* Transcript Access Button */}
        {onToggleTranscript && (
          <div className="flex justify-center mt-8">
            <button
              onClick={onToggleTranscript}
              className="
                group relative px-4 py-2 
                bg-white/5 hover:bg-white/10 
                border border-white/10 hover:border-white/20
                rounded-full 
                backdrop-blur-sm
                transition-all duration-300
                text-xs font-medium text-gray-300 hover:text-white
              "
            >
              <span className="relative z-10 flex items-center space-x-2">
                <span>View Full Transcript</span>
                <svg 
                  className="w-3 h-3 transition-transform duration-200 group-hover:translate-y-0.5" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </span>
              
              {/* Hover Effect */}
              <div className="
                absolute inset-0 rounded-full 
                bg-gradient-to-r from-blue-500/10 to-purple-500/10 
                opacity-0 group-hover:opacity-100 
                transition-opacity duration-300
              " />
            </button>
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