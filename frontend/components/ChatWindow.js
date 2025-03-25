import { useEffect, useRef, useState } from 'react';

// Message types
const MESSAGE_TYPES = {
  USER: 'user',
  INTERVIEWER: 'interviewer',
  SYSTEM: 'system'
};

const ChatWindow = ({ 
  messages = [], 
  onSendMessage,
  isLoading = false
}) => {
  const messagesEndRef = useRef(null);
  const [inputMessage, setInputMessage] = useState('');

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (inputMessage.trim() === '') return;
    
    onSendMessage(inputMessage);
    setInputMessage('');
  };

  // Function to render message with correct styling based on sender
  const renderMessage = (message, index) => {
    const { type, text, timestamp } = message;
    
    const isUser = type === MESSAGE_TYPES.USER;
    const isInterviewer = type === MESSAGE_TYPES.INTERVIEWER;
    const isSystem = type === MESSAGE_TYPES.SYSTEM;
    
    // Style classes based on message type
    const containerClasses = `flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`;
    const messageClasses = `max-w-[70%] p-3 rounded-lg ${
      isUser 
        ? 'bg-blue-600 text-white rounded-br-none' 
        : isInterviewer 
          ? 'bg-gray-700 text-white rounded-bl-none' 
          : 'bg-gray-200 text-gray-800 italic text-sm'
    }`;
    
    return (
      <div key={index} className={containerClasses}>
        <div className="flex flex-col">
          <div className={messageClasses}>
            {text}
          </div>
          {timestamp && (
            <span className="text-xs text-gray-500 mt-1 mx-1">
              {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages container */}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-100 dark:bg-gray-800">
        {messages.length === 0 ? (
          <div className="flex justify-center items-center h-full text-gray-500">
            <p>No messages yet. Start your interview!</p>
          </div>
        ) : (
          messages.map((message, index) => renderMessage(message, index))
        )}
        
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-700 text-white p-3 rounded-lg rounded-bl-none flex items-center">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            className="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={inputMessage.trim() === '' || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatWindow; 