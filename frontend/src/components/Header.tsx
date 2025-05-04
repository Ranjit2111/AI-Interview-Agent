
import React from 'react';
import { Button } from '@/components/ui/button';
import { Sparkles, Zap, Bot, BarChart3, Code, Github } from 'lucide-react';

interface HeaderProps {
  onReset?: () => void;
  showReset?: boolean;
}

const Header: React.FC<HeaderProps> = ({ onReset, showReset = false }) => {
  return (
    <header className="relative z-10 bg-black/40 backdrop-blur-lg border-b border-white/10 py-4 shadow-lg">
      <div className="container mx-auto flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute -inset-0.5 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 opacity-70 blur-sm animate-pulse-slow"></div>
            <div className="relative p-1 rounded-full bg-gradient-to-br from-cyan-400 via-purple-500 to-pink-500">
              <div className="w-10 h-10 flex items-center justify-center rounded-full bg-black">
                <Sparkles className="h-5 w-5 text-transparent bg-clip-text bg-gradient-to-br from-cyan-300 to-purple-400" />
              </div>
            </div>
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent font-display tracking-tight">AI Interviewer</h1>
        </div>
        
        {/* Visual elements for top right area */}
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-4">
            <div className="glass-effect rounded-xl px-4 py-3 flex items-center gap-2 hover:border-purple-500/30 transition-all duration-300 group">
              <Bot className="text-cyan-400 h-5 w-5 group-hover:text-cyan-300 transition-colors" />
              <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">AI Assistant</span>
            </div>
            
            <div className="glass-effect rounded-xl px-4 py-3 flex items-center gap-2 hover:border-cyan-500/30 transition-all duration-300 group">
              <Zap className="text-purple-400 h-5 w-5 group-hover:text-purple-300 transition-colors" />
              <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">Real-time Feedback</span>
            </div>
            
            <div className="glass-effect rounded-xl px-4 py-3 flex items-center gap-2 hover:border-pink-500/30 transition-all duration-300 group">
              <BarChart3 className="text-pink-400 h-5 w-5 group-hover:text-pink-300 transition-colors" />
              <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">Skill Analytics</span>
            </div>
          </div>
          
          {/* Add animated stats for the top right */}
          <div className="hidden md:block glass-effect rounded-xl px-4 py-2 border border-purple-500/20">
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent animate-pulse-slow">
                  500+
                </div>
                <div className="text-xs text-gray-400">Questions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent animate-pulse-slow animation-delay-500">
                  24/7
                </div>
                <div className="text-xs text-gray-400">Support</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-pink-400 to-cyan-400 bg-clip-text text-transparent animate-pulse-slow animation-delay-1000">
                  99%
                </div>
                <div className="text-xs text-gray-400">Success Rate</div>
              </div>
            </div>
          </div>
        </div>
        
        <div>
          {showReset && (
            <Button 
              variant="outline" 
              onClick={onReset}
              className="border-white/10 bg-black/20 hover:bg-white/10 hover:border-purple-500/50 hover:shadow-[0_0_15px_rgba(168,85,247,0.35)] transition-all duration-300 font-medium"
            >
              New Interview
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
