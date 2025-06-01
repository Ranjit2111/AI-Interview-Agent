import React, { useEffect, useRef, useState } from 'react';
import { X, Copy, Volume2, User, Bot, Download } from 'lucide-react';
import { Message } from '../hooks/useInterviewSession';

interface TranscriptDrawerProps {
  isOpen: boolean;
  messages: Message[];
  onClose: () => void;
  onPlayMessage?: (message: string) => void;
}

const TranscriptDrawer: React.FC<TranscriptDrawerProps> = ({
  isOpen,
  messages,
  onClose,
  onPlayMessage
}) => {
  const drawerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

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

  const handleCopyMessage = async (content: string | any, messageId: string) => {
    try {
      const textContent = getContentAsString(content);
      await navigator.clipboard.writeText(textContent);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error('Failed to copy message:', error);
    }
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

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Drawer */}
      <div 
        ref={drawerRef}
        className={`
          transcript-drawer
          ${isOpen ? 'open' : ''}
        `}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 px-6 py-4 border-b border-white/10 backdrop-blur-xl bg-black/80">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Interview Transcript</h2>
              <p className="text-sm text-gray-400 mt-1">
                {messages.filter(m => m.role === 'user').length} exchanges • {messages.length} total messages
              </p>
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
              const isCopied = copiedMessageId === messageId;
              const contentText = getContentAsString(message.content);

              return (
                <div
                  key={messageId}
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
                        <span className="text-xs text-gray-500">
                          {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : 'Now'}
                        </span>
                      </div>
                      
                      <p className={`text-sm leading-relaxed ${styling.text}`}>
                        {contentText}
                      </p>

                      {/* Message Actions */}
                      <div className="flex items-center space-x-2 mt-3">
                        {/* Copy Button */}
                        <button
                          onClick={() => handleCopyMessage(message.content, messageId)}
                          className="
                            flex items-center space-x-1 px-2 py-1 
                            bg-white/5 hover:bg-white/10 
                            border border-white/10 hover:border-white/20
                            rounded-md text-xs 
                            transition-all duration-200
                            group
                          "
                        >
                          <Copy className="w-3 h-3" />
                          <span>{isCopied ? 'Copied!' : 'Copy'}</span>
                        </button>

                        {/* Play Audio Button (if TTS available) */}
                        {onPlayMessage && message.role === 'assistant' && message.agent !== 'coach' && (
                          <button
                            onClick={() => onPlayMessage(contentText)}
                            className="
                              flex items-center space-x-1 px-2 py-1 
                              bg-white/5 hover:bg-white/10 
                              border border-white/10 hover:border-white/20
                              rounded-md text-xs 
                              transition-all duration-200
                              group
                            "
                          >
                            <Volume2 className="w-3 h-3" />
                            <span>Play</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 px-6 py-3 border-t border-white/10 backdrop-blur-xl bg-black/80">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Scroll to navigate • Press ESC to close</span>
            <span>{new Date().toLocaleString()}</span>
          </div>
        </div>
      </div>
    </>
  );
};

export default TranscriptDrawer; 