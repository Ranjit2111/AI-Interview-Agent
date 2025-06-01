import React, { useState, useEffect } from 'react';
import { Brain, ChevronDown, ChevronUp, Loader } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface RealTimeCoachFeedbackProps {
  isAnalyzing: boolean;
  feedback?: string;
  userMessageIndex: number;
}

const RealTimeCoachFeedback: React.FC<RealTimeCoachFeedbackProps> = ({
  isAnalyzing,
  feedback,
  userMessageIndex,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showPulse, setShowPulse] = useState(false);

  // Auto-expand when feedback arrives, with a slight delay for effect
  useEffect(() => {
    if (feedback && !isAnalyzing) {
      const timer = setTimeout(() => {
        setShowPulse(true);
        // Auto-expand on first feedback for better UX
        if (!isExpanded) {
          setIsExpanded(true);
        }
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [feedback, isAnalyzing]);

  // Reset pulse effect after showing
  useEffect(() => {
    if (showPulse) {
      const timer = setTimeout(() => setShowPulse(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [showPulse]);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  // If no feedback and not analyzing, don't render anything
  if (!isAnalyzing && !feedback) {
    return null;
  }

  return (
    <div className="mt-2 max-w-[80%]">
      <Card 
        className={`
          bg-gradient-to-r from-blue-900/20 to-purple-900/20 
          border-blue-500/30 backdrop-blur-md shadow-lg 
          transition-all duration-500 
          ${showPulse ? 'shadow-blue-500/30 border-blue-400/50' : ''}
          ${isAnalyzing ? 'animate-pulse' : ''}
        `}
      >
        {/* Coach Status Header */}
        <div className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="relative">
                <Brain className={`h-4 w-4 text-blue-400 ${isAnalyzing ? 'animate-pulse' : ''}`} />
                {isAnalyzing && (
                  <div className="absolute -inset-1">
                    <div className="w-6 h-6 border-2 border-blue-400/30 rounded-full animate-spin border-t-blue-400"></div>
                  </div>
                )}
              </div>
              
              <span className="text-sm font-medium text-blue-400">
                {isAnalyzing ? 'Coach is analyzing your response...' : 'Coach Feedback'}
              </span>
              
              {isAnalyzing && (
                <div className="flex space-x-1">
                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              )}
            </div>

            {/* Toggle button - only show when feedback is available */}
            {feedback && !isAnalyzing && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleToggle}
                className="h-6 px-2 text-blue-400 hover:text-blue-300 hover:bg-blue-900/20"
              >
                <span className="text-xs mr-1">
                  {isExpanded ? 'Hide' : 'Show'} Feedback
                </span>
                {isExpanded ? (
                  <ChevronUp className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>

          {/* Processing indicator */}
          {isAnalyzing && (
            <div className="mt-2 flex items-center gap-2 text-xs text-blue-300/80">
              <Loader className="h-3 w-3 animate-spin" />
              <span>Analyzing answer quality, relevance, and coaching points...</span>
            </div>
          )}
        </div>

        {/* Feedback Content - Expandable */}
        {feedback && isExpanded && (
          <div 
            className={`
              border-t border-blue-500/20 p-3 pt-3
              animate-in slide-in-from-top-2 duration-300
              ${showPulse ? 'bg-blue-900/10' : ''}
            `}
          >
            <div className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
              {feedback}
            </div>
            
            {/* Subtle coaching attribution */}
            <div className="mt-2 pt-2 border-t border-blue-500/10">
              <div className="flex items-center gap-1 text-xs text-blue-400/70">
                <Brain className="h-3 w-3" />
                <span>AI Interview Coach • Real-time Analysis</span>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default RealTimeCoachFeedback; 