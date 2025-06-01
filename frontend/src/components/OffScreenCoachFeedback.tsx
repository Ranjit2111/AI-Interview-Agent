import React, { useState, useEffect } from 'react';
import { X, MessageSquare, ChevronRight, Lightbulb } from 'lucide-react';
import { CoachFeedbackState } from '../hooks/useInterviewSession';

interface OffScreenCoachFeedbackProps {
  coachFeedbackStates: CoachFeedbackState;
  messages: any[];
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
}

const OffScreenCoachFeedback: React.FC<OffScreenCoachFeedbackProps> = ({
  coachFeedbackStates,
  messages,
  isOpen,
  onToggle,
  onClose
}) => {
  const [hasNewFeedback, setHasNewFeedback] = useState(false);

  // Check for new feedback and update indicator
  useEffect(() => {
    const feedbackEntries = Object.entries(coachFeedbackStates);
    const hasUnreadFeedback = feedbackEntries.some(([_, state]) => 
      state.feedback && !state.isAnalyzing
    );
    setHasNewFeedback(hasUnreadFeedback && !isOpen);
  }, [coachFeedbackStates, isOpen]);

  // Get feedback for user messages
  const getUserMessageFeedback = () => {
    const userMessages = messages
      .map((msg, index) => ({ msg, index }))
      .filter(({ msg }) => msg.role === 'user');

    return userMessages.map(({ msg, index }, userMsgNumber) => {
      const feedbackState = coachFeedbackStates[index];
      return {
        messageIndex: index,
        userMessageNumber: userMsgNumber + 1,
        content: msg.content,
        feedback: feedbackState?.feedback,
        isAnalyzing: feedbackState?.isAnalyzing || false,
        timestamp: msg.timestamp
      };
    });
  };

  const feedbackItems = getUserMessageFeedback();
  const analysisCount = feedbackItems.filter(item => item.isAnalyzing).length;
  const completedCount = feedbackItems.filter(item => item.feedback).length;

  return (
    <>
      {/* Floating Indicator */}
      {!isOpen && (
        <div className="fixed top-1/2 right-4 transform -translate-y-1/2 z-40">
          <button
            onClick={onToggle}
            className="
              group relative
              w-12 h-12 rounded-full
              bg-gradient-to-br from-yellow-900/80 to-yellow-800/90
              border border-yellow-500/30
              backdrop-blur-xl
              shadow-lg shadow-yellow-500/20
              transition-all duration-300
              hover:scale-110 hover:shadow-yellow-500/40
              animate-breathing
            "
          >
            {/* Pulsing Ring for New Feedback */}
            {hasNewFeedback && (
              <div className="absolute -inset-1 rounded-full border-2 border-yellow-400/50 animate-pulse" />
            )}

            {/* Icon */}
            <div className="flex items-center justify-center h-full">
              {analysisCount > 0 ? (
                <div className="relative">
                  <Lightbulb className="w-5 h-5 text-yellow-300" />
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full text-xs text-black font-bold flex items-center justify-center animate-pulse">
                    {analysisCount}
                  </div>
                </div>
              ) : (
                <MessageSquare className="w-5 h-5 text-yellow-300" />
              )}
            </div>

            {/* Tooltip */}
            <div className="
              absolute right-full mr-3 top-1/2 transform -translate-y-1/2
              bg-black/90 text-white text-xs px-2 py-1 rounded
              opacity-0 group-hover:opacity-100 transition-opacity duration-200
              whitespace-nowrap
            ">
              {completedCount > 0 ? `${completedCount} feedback available` : 'Coach feedback'}
            </div>
          </button>
        </div>
      )}

      {/* Slide Panel */}
      <div 
        className={`
          coach-slide-panel
          ${isOpen ? 'open' : ''}
        `}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 px-6 py-4 border-b border-yellow-500/20 backdrop-blur-xl bg-gradient-to-r from-yellow-900/40 to-yellow-800/40">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-yellow-100 flex items-center">
                <Lightbulb className="w-5 h-5 mr-2 text-yellow-300" />
                Coach Feedback
              </h3>
              <p className="text-sm text-yellow-200/80 mt-1">
                {completedCount} of {feedbackItems.length} responses analyzed
              </p>
            </div>
            
            <button
              onClick={onClose}
              className="
                p-2 rounded-lg 
                bg-yellow-500/10 hover:bg-yellow-500/20 
                border border-yellow-500/20 hover:border-yellow-500/30
                transition-all duration-200
                group
              "
            >
              <X className="w-4 h-4 text-yellow-300 group-hover:text-yellow-100" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {feedbackItems.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-yellow-700/20 flex items-center justify-center">
                  <MessageSquare className="w-8 h-8 text-yellow-400" />
                </div>
                <p className="text-yellow-200 text-sm">No responses yet</p>
                <p className="text-yellow-300/60 text-xs mt-2">Start answering questions to get feedback</p>
              </div>
            </div>
          ) : (
            feedbackItems.map((item) => (
              <div
                key={item.messageIndex}
                className="
                  backdrop-blur-md border shadow-lg
                  rounded-xl p-4 transition-all duration-300 hover:shadow-xl
                  bg-gradient-to-r from-yellow-900/20 to-yellow-800/30 border-yellow-500/30
                "
              >
                {/* Response Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-blue-500/20 border border-blue-400/30 flex items-center justify-center">
                      <span className="text-xs font-medium text-blue-300">
                        {item.userMessageNumber}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-yellow-100">
                      Your Response
                    </span>
                  </div>
                  <span className="text-xs text-yellow-300/60">
                    {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : 'Now'}
                  </span>
                </div>

                {/* User Message Preview */}
                <div className="mb-3 p-3 bg-blue-900/20 border border-blue-500/20 rounded-lg">
                  <p className="text-sm text-blue-100 line-clamp-2">
                    {typeof item.content === 'string' ? item.content : JSON.stringify(item.content)}
                  </p>
                </div>

                {/* Feedback Content */}
                {item.isAnalyzing ? (
                  <div className="flex items-center space-x-3 p-3 bg-yellow-900/20 border border-yellow-500/20 rounded-lg">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce animation-delay-100" />
                      <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce animation-delay-200" />
                    </div>
                    <span className="text-sm text-yellow-200">
                      Analyzing your response...
                    </span>
                  </div>
                ) : item.feedback ? (
                  <div className="p-3 bg-yellow-900/20 border border-yellow-500/20 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <Lightbulb className="w-4 h-4 text-yellow-300 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-medium text-yellow-100 mb-1">Coach Analysis</h4>
                        <p className="text-sm text-yellow-200 leading-relaxed">
                          {item.feedback}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-gray-900/20 border border-gray-500/20 rounded-lg">
                    <p className="text-sm text-gray-400 italic">
                      Waiting for analysis...
                    </p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 px-6 py-3 border-t border-yellow-500/20 backdrop-blur-xl bg-gradient-to-r from-yellow-900/40 to-yellow-800/40">
          <div className="flex items-center justify-between text-xs text-yellow-200/80">
            <span>Real-time feedback • Updates automatically</span>
            {analysisCount > 0 && (
              <span className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                <span>Analyzing {analysisCount} response{analysisCount > 1 ? 's' : ''}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Backdrop (when open) */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-30 transition-opacity duration-300"
          onClick={onClose}
        />
      )}
    </>
  );
};

export default OffScreenCoachFeedback; 