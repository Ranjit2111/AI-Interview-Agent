import React, { useEffect, useRef, useState } from 'react';
import { X, Volume2, User, Bot, Download, Brain, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { Message, CoachFeedbackState } from '../hooks/useInterviewSession';

interface TranscriptDrawerProps {
  isOpen: boolean;
  messages: Message[];
  onClose: () => void;
  onPlayMessage?: (message: string) => void;
  onSendTextFromTranscript: (message: string) => void;
  coachFeedbackStates: CoachFeedbackState;
}

const TranscriptDrawer: React.FC<TranscriptDrawerProps> = ({
  isOpen,
  messages,
  onClose,
  onPlayMessage,
  onSendTextFromTranscript,
  coachFeedbackStates
}) => {
  const drawerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [newMessage, setNewMessage] = useState('');
  const [expandedCoachFeedback, setExpandedCoachFeedback] = useState<Set<number>>(new Set());

  // Handle escape key press
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isOpen && contentRef.current) {
      const scrollToBottom = () => {
        contentRef.current?.scrollTo({
          top: contentRef.current.scrollHeight,
          behavior: 'smooth'
        });
      };
      
      // Delay to ensure content is rendered
      setTimeout(scrollToBottom, 100);
    }
  }, [messages, isOpen]);

  // Helper to convert content to string
  const getContentAsString = (content: string | any): string => {
    if (typeof content === 'string') {
      return content;
    }
    // If it's an object, try to extract meaningful text
    if (content && typeof content === 'object') {
      return JSON.stringify(content, null, 2);
    }
    return String(content);
  };

  const handleDownloadTranscript = () => {
    const transcript = messages
      .map((message, index) => {
        const role = message.role === 'user' ? 'User' : 'AI Interviewer';
        const timestamp = new Date(message.timestamp || Date.now()).toLocaleString();
        const content = getContentAsString(message.content);
        return `[${timestamp}] ${role}: ${content}`;
      })
      .join('\n\n');

    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview-transcript-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getMessageIcon = (role: string) => {
    if (role === 'user') {
      return <User className="w-4 h-4 text-blue-300" />;
    }
    return <Bot className="w-4 h-4 text-orange-300" />;
  };

  const getMessageStyling = (role: string) => {
    if (role === 'user') {
      return {
        container: 'bg-gradient-to-r from-blue-900/20 to-blue-800/30 border-blue-500/30',
        text: 'text-blue-100',
        avatar: 'bg-blue-500/20 border-blue-400/30'
      };
    }
    return {
      container: 'bg-gradient-to-r from-orange-900/20 to-purple-900/20 border-orange-500/30',
      text: 'text-orange-100',
      avatar: 'bg-gradient-to-br from-orange-500/20 to-purple-500/20 border-orange-400/30'
    };
  };

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      onSendTextFromTranscript(newMessage.trim());
      setNewMessage('');
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  // Toggle coach feedback for a specific message
  const toggleCoachFeedback = (messageIndex: number) => {
    setExpandedCoachFeedback(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageIndex)) {
        newSet.delete(messageIndex);
      } else {
        newSet.add(messageIndex);
      }
      return newSet;
    });
  };

  // Get coach feedback for a message
  const getCoachFeedback = (messageIndex: number) => {
    return coachFeedbackStates[messageIndex];
  };

  // if (!isOpen) return null; // Keep the component in DOM for transitions, control visibility via transform

  return (
    <>
      {/* Backdrop - REMOVED for side panel style */}
      {/* 
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300"
        onClick={onClose}
      />
      */}

      {/* Drawer - MODIFIED for left slide-out panel */}
      <div 
        ref={drawerRef}
        className={`
          fixed inset-y-0 left-0 z-30 w-80 md:w-96 
          bg-gray-900/95 shadow-xl flex flex-col 
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 px-4 sm:px-6 py-4 border-b border-white/10 bg-gray-900/80 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Interview Transcript</h2>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Download Button */}
              <button
                onClick={handleDownloadTranscript}
                className="
                  p-2 rounded-lg 
                  bg-white/5 hover:bg-white/10 
                  border border-white/10 hover:border-white/20
                  transition-all duration-200
                  group
                "
                title="Download Transcript"
              >
                <Download className="w-4 h-4 text-gray-300 group-hover:text-white" />
              </button>

              {/* Close Button */}
              <button
                onClick={onClose}
                className="
                  p-2 rounded-lg 
                  bg-white/5 hover:bg-white/10 
                  border border-white/10 hover:border-white/20
                  transition-all duration-200
                  group
                "
              >
                <X className="w-4 h-4 text-gray-300 group-hover:text-white" />
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div 
          ref={contentRef}
          className="flex-1 overflow-y-auto px-6 py-4 space-y-4"
        >
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-700/50 flex items-center justify-center">
                  <Bot className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-400 text-sm">No messages yet</p>
                <p className="text-gray-500 text-xs mt-2">Start speaking to begin the interview</p>
              </div>
            </div>
          ) : (
            messages.map((message, index) => {
              const messageId = `${message.role}-${index}`;
              const styling = getMessageStyling(message.role);
              const contentText = getContentAsString(message.content);

              return (
                <div key={messageId}>
                  <div
                    className={`
                      backdrop-blur-md border shadow-lg
                      rounded-xl p-4 transition-all duration-300 hover:shadow-xl
                      ${styling.container}
                    `}
                  >
                    <div className="flex items-start space-x-3">
                      {/* Avatar */}
                      <div className={`
                        w-8 h-8 rounded-full border flex items-center justify-center flex-shrink-0
                        ${styling.avatar}
                      `}>
                        {getMessageIcon(message.role)}
                      </div>

                      {/* Message Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-gray-300">
                            {message.role === 'user' ? 'You' : 'AI Interviewer'}
                          </span>
                        </div>
                        
                        <p className={`text-sm leading-relaxed ${styling.text}`}>
                          {contentText}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Coach Feedback Section (only for user messages) */}
                  {message.role === 'user' && (
                    <>
                      {/* Coach Feedback Toggle Button */}
                      <div className="mt-2 ml-2">
                        {(() => {
                          const feedbackState = getCoachFeedback(index);
                          const hasAnalysis = feedbackState?.isAnalyzing;
                          const hasFeedback = feedbackState?.feedback;
                          const isExpanded = expandedCoachFeedback.has(index);

                          // Don't show button if no analysis and no feedback
                          if (!hasAnalysis && !hasFeedback) return null;

                          return (
                            <button
                              onClick={() => toggleCoachFeedback(index)}
                              className={`
                                flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium
                                transition-all duration-300 group
                                ${hasAnalysis 
                                  ? 'bg-yellow-900/30 border border-yellow-500/40 text-yellow-300 hover:bg-yellow-900/50' 
                                  : hasFeedback 
                                    ? 'bg-gradient-to-r from-yellow-900/20 to-orange-900/20 border border-yellow-500/30 text-yellow-300 hover:border-yellow-500/50 hover:bg-yellow-900/30'
                                    : 'bg-gray-800/30 border border-gray-600/30 text-gray-400'
                                }
                              `}
                            >
                              <div className="flex items-center space-x-2">
                                {hasAnalysis ? (
                                  <>
                                    <div className="relative">
                                      <Brain className="w-4 h-4" />
                                      <Loader2 className="absolute inset-0 w-4 h-4 animate-spin" />
                                    </div>
                                    <span>Coach is analyzing...</span>
                                  </>
                                ) : hasFeedback ? (
                                  <>
                                    <Brain className="w-4 h-4" />
                                    <span>View coach feedback</span>
                                  </>
                                ) : (
                                  <>
                                    <Brain className="w-4 h-4" />
                                    <span>No feedback yet</span>
                                  </>
                                )}
                              </div>
                              {!hasAnalysis && (
                                isExpanded ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                              )}
                            </button>
                          );
                        })()}
                      </div>

                      {/* Coach Feedback Content */}
                      {expandedCoachFeedback.has(index) && (() => {
                        const feedbackState = getCoachFeedback(index);
                        if (!feedbackState?.feedback) return null;

                        return (
                          <div className="mt-3 ml-2">
                            <div className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 backdrop-blur-md border border-yellow-500/30 rounded-xl p-4">
                              <div className="flex items-start space-x-3">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border border-yellow-400/30 flex items-center justify-center flex-shrink-0">
                                  <Brain className="w-4 h-4 text-yellow-300" />
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs font-medium text-yellow-300">AI Coach Feedback</span>
                                  </div>
                                  <p className="text-sm leading-relaxed text-yellow-100">
                                    {feedbackState.feedback}
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })()}
                    </>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer - MODIFIED to include text input */}
        <div className="sticky bottom-0 px-4 sm:px-6 py-3 border-t border-white/10 bg-gray-900/80 backdrop-blur-md">
          <div className="flex items-center space-x-2">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              rows={1}
              className="flex-1 p-2 bg-gray-800/60 border border-gray-600/70 rounded-lg text-sm text-white placeholder-gray-400 resize-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all"
            />
            <button
              onClick={handleSendMessage}
              disabled={!newMessage.trim()}
              className="p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg disabled:opacity-50 transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default TranscriptDrawer; 