import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Loader, Bot, User, Brain, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import VoiceInputToggle from './VoiceInputToggle';
import AudioPlayer from './AudioPlayer';
import CoachFeedbackDisplay from './CoachFeedbackDisplay';
import RealTimeCoachFeedback from './RealTimeCoachFeedback';
import { Message, CoachFeedbackState } from '@/hooks/useInterviewSession';

interface InterviewSessionProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onEndInterview: () => void;
  onVoiceSelect: (voiceId: string | null) => void;
  coachFeedbackStates: CoachFeedbackState;
}

const InterviewSession: React.FC<InterviewSessionProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onEndInterview,
  onVoiceSelect,
  coachFeedbackStates,
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
    
    // Append the new transcription to existing input, with proper spacing
    setInput(prevInput => {
      const trimmedText = text.trim();
      if (!trimmedText) return prevInput;
      
      const currentText = prevInput.trim();
      if (currentText === '') {
        // If input is empty, just use the new text
        return trimmedText;
      } else {
        // Append with a space separator
        return currentText + ' ' + trimmedText;
      }
    });
    
    console.log("Input state updated by appending:", text);
  };

  const handleClearInput = () => {
    setInput('');
  };

  const getAgentDisplayName = (message: Message) => {
    if (message.role === 'user') return 'You';
    if (message.agent === 'coach') return 'Coach';
    return 'Interviewer';
  };

  const getAgentIcon = (message: Message) => {
    if (message.role === 'user') return <User className="h-5 w-5 mr-2" />;
    if (message.agent === 'coach') return <Brain className="h-5 w-5 mr-2" />;
    return <Bot className="h-5 w-5 mr-2" />;
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
          {messages.map((message, index) => {
            const isUser = message.role === 'user';
            const isCoach = message.agent === 'coach';
            
            let cardClasses = 'p-4 transition-all duration-500 backdrop-blur-md border shadow-lg perspective-card max-w-[80%]';
            let nameColor = 'text-cyan-400';
            let icon = <Bot className="h-5 w-5 mr-2 flex-shrink-0" />;

            if (isUser) {
              cardClasses += ' ml-auto bg-black/30 border-white/5 hover:border-purple-500/20 animate-slide-in-right';
              nameColor = 'text-purple-400';
              icon = <User className="h-5 w-5 mr-2 flex-shrink-0" />;
            } else if (isCoach) {
              cardClasses += ' bg-black/30 border-yellow-500/30 hover:border-yellow-400/40 animate-fade-in';
              nameColor = 'text-yellow-400';
              icon = <Brain className="h-5 w-5 mr-2 flex-shrink-0" />;
            } else {
              cardClasses += ' bg-black/40 border-white/10 hover:border-cyan-500/20 animate-fade-in';
            }

            return (
              <div key={index}>
                <Card className={cardClasses}>
                  <div className={`flex items-center text-sm font-medium mb-2 ${nameColor}`}>
                    {icon}
                    {getAgentDisplayName(message)}
                  </div>
                  {isCoach && typeof message.content === 'object' ? (
                    <CoachFeedbackDisplay feedback={message.content as any} />
                  ) : (
                    <div className="whitespace-pre-wrap text-gray-100">
                      {typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}
                    </div>
                  )}
                </Card>
                
                {/* Real-time coach feedback for user messages */}
                {isUser && (
                  <RealTimeCoachFeedback
                    isAnalyzing={coachFeedbackStates[index]?.isAnalyzing || false}
                    feedback={coachFeedbackStates[index]?.feedback}
                    userMessageIndex={index}
                  />
                )}
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input area */}
      <div className="p-4 border-t border-white/10 bg-black/60 backdrop-blur-lg shadow-[0_-4px_20px_rgba(0,0,0,0.2)] relative z-10">
        <div className="flex flex-col gap-3 max-w-3xl mx-auto">
          <div className="flex items-end gap-3 w-full">
            <div className="flex-1 relative group">
              <Textarea
                placeholder="Type your answer here..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={isLoading}
                className="min-h-[50px] bg-gray-900/70 border-gray-700/70 text-gray-100 focus:border-interview-secondary shadow-sm rounded-lg resize-none hover:border-gray-600 focus:shadow-[0_0_15px_rgba(168,85,247,0.2)] pr-10"
              />
              {/* Clear button - only show when there's text */}
              {input.trim() && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearInput}
                  className="absolute top-2 right-2 h-6 w-6 p-0 text-gray-400 hover:text-gray-200 hover:bg-gray-700/50"
                  title="Clear text"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
              <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-cyan-500/20 to-purple-600/20 -z-10 opacity-0 group-focus-within:opacity-100 blur-xl transition-opacity"></div>
            </div>
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 shadow-lg hover:shadow-purple-500/20 transition-all duration-300"
            >
              {isLoading ? <Loader className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
          <VoiceInputToggle
            onTranscriptionComplete={handleTranscriptionComplete}
            isDisabled={isLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default InterviewSession;
