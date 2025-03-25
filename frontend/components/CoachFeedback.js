import { useEffect, useRef } from 'react';

// Component for displaying feedback from the coach agent
const CoachFeedback = ({ 
  feedback = [], 
  transcript = [],
  isLoading = false 
}) => {
  const feedbackEndRef = useRef(null);

  // Scroll to bottom when new feedback arrives
  useEffect(() => {
    scrollToBottom();
  }, [feedback]);

  const scrollToBottom = () => {
    feedbackEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Render a feedback item with highlighted transcript parts if applicable
  const renderFeedbackItem = (item, index) => {
    const { text, timestamp, highlightedParts = [], category = 'general' } = item;
    
    // Category determines the color scheme
    const getCategoryStyles = (category) => {
      switch (category.toLowerCase()) {
        case 'positive':
          return 'border-green-500 bg-green-50 dark:bg-green-900/20';
        case 'improvement':
          return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
        case 'critical':
          return 'border-red-500 bg-red-50 dark:bg-red-900/20';
        default:
          return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20';
      }
    };

    const categoryStyles = getCategoryStyles(category);
    
    return (
      <div 
        key={index} 
        className={`p-4 mb-4 rounded-lg border-l-4 ${categoryStyles} transition-all duration-300 hover:shadow-md`}
      >
        <div className="mb-2 font-medium">
          {category.charAt(0).toUpperCase() + category.slice(1)} Feedback 
          {timestamp && (
            <span className="text-xs text-gray-500 ml-2">
              {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>
        
        <div className="mb-3">{text}</div>
        
        {/* Display highlighted parts from the transcript if any */}
        {highlightedParts.length > 0 && (
          <div className="mt-2 bg-gray-100 dark:bg-gray-800 p-3 rounded text-sm">
            <div className="text-xs text-gray-500 mb-1">Referenced conversation:</div>
            {highlightedParts.map((part, pidx) => {
              // Find the transcript part
              const transcriptPart = transcript.find(t => t.id === part.transcriptId);
              if (!transcriptPart) return null;
              
              return (
                <div key={pidx} className="mb-2 last:mb-0">
                  <div className="font-medium text-xs mb-1">
                    {transcriptPart.speaker === 'user' ? 'You' : 'Interviewer'}:
                  </div>
                  <div className="pl-2 border-l-2 border-gray-300">
                    {part.text || transcriptPart.text}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      <h3 className="text-lg font-semibold mb-4 sticky top-0 bg-white dark:bg-gray-900 py-2 z-10 border-b border-gray-200 dark:border-gray-700">
        Coach Feedback
      </h3>
      
      <div className="flex-1 overflow-y-auto">
        {feedback.length === 0 && !isLoading ? (
          <div className="text-gray-500 text-center py-8">
            <p>No feedback yet. The coach will provide feedback as your interview progresses.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {feedback.map((item, index) => renderFeedbackItem(item, index))}
          </div>
        )}
        
        {isLoading && (
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg animate-pulse flex space-x-4">
            <div className="flex-1 space-y-4 py-1">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={feedbackEndRef} />
      </div>
    </div>
  );
};

export default CoachFeedback; 