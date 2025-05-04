import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Loader } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import VoiceRecorder from './VoiceRecorder';
import AudioPlayer from './AudioPlayer';
import { Message } from '@/hooks/useInterviewSession';

interface InterviewSessionProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onEndInterview: () => void;
  onVoiceSelect: (voiceId: string | null) => void;
}

const InterviewSession: React.FC<InterviewSessionProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onEndInterview,
  onVoiceSelect,
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTranscriptionComplete = (text: string) => {
    console.log("handleTranscriptionComplete called with text:", text);
    setInput(text);
    console.log("Input state updated to:", text);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-black/50 backdrop-blur-lg z-10 shadow-lg">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-medium bg-gradient-to-r from-cyan-300 to-purple-400 bg-clip-text text-transparent">Interview Session</h2>
          {isLoading && (
            <div className="text-sm text-gray-400 flex items-center">
              <span className="relative flex h-2 w-2 me-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
              </span>
              Thinking...
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <AudioPlayer onVoiceSelect={onVoiceSelect} />
          <Button
            variant="outline"
            className="text-red-400 border-red-800/30 hover:bg-red-900/20 hover:text-red-300 hover:border-red-500/30 transition-all duration-300 hover:shadow-red-500/20"
            onClick={onEndInterview}
            disabled={isLoading}
          >
            End Interview
          </Button>
        </div>
      </div>

      {/* Background elements */}
      <div className="absolute inset-0 pointer-events-none z-0 opacity-20">
        <div className="absolute h-48 w-48 bg-purple-500/10 rounded-full blur-3xl top-[20%] right-[25%] animate-float"></div>
        <div className="absolute h-64 w-64 bg-cyan-500/10 rounded-full blur-3xl bottom-[30%] left-[15%] animate-float animation-delay-2000"></div>
      </div>

      {/* Messages area */}
      <ScrollArea className="flex-1 p-4 bg-gradient-to-b from-black/40 to-gray-900/20 relative z-10">
        <div className="space-y-4 max-w-3xl mx-auto">
          {messages.map((message, index) => (
            <Card
              key={index}
              className={`p-4 transition-all duration-500 backdrop-blur-md border shadow-lg perspective-card ${
                message.role === 'user'
                  ? 'ml-auto bg-black/30 border-white/5 hover:border-purple-500/20 max-w-[80%] animate-slide-in-right'
                  : 'bg-black/40 border-white/10 hover:border-cyan-500/20 max-w-[80%] animate-fade-in'
              }`}
            >
              <div className={`text-sm font-medium mb-1 ${message.role === 'user' ? 'text-purple-400' : 'text-cyan-400'}`}>
                {message.role === 'user' ? 'You' : 'Interviewer'}
              </div>
              <div className="whitespace-pre-wrap text-gray-100">{message.content}</div>
            </Card>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input area */}
      <div className="p-4 border-t border-white/10 bg-black/60 backdrop-blur-lg shadow-[0_-4px_20px_rgba(0,0,0,0.2)] relative z-10">
        <div className="flex items-end gap-3 max-w-3xl mx-auto">
          <div className="flex-1 relative group">
            <Textarea
              placeholder="Type your answer here..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={isLoading}
              className="min-h-[50px] bg-gray-900/70 border-gray-700/70 text-gray-100 focus:border-interview-secondary shadow-sm rounded-lg resize-none hover:border-gray-600 focus:shadow-[0_0_15px_rgba(168,85,247,0.2)]"
            />
            <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-cyan-500/20 to-purple-600/20 -z-10 opacity-0 group-focus-within:opacity-100 blur-xl transition-opacity"></div>
          </div>
          <VoiceRecorder
            onTranscriptionComplete={handleTranscriptionComplete}
            isDisabled={isLoading}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 shadow-lg hover:shadow-purple-500/20 transition-all duration-300"
          >
            {isLoading ? <Loader className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default InterviewSession;
