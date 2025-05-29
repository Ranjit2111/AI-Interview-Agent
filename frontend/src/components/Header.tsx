import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Sparkles, Zap, Bot, BarChart3, Code, Github, LogOut, User, UserPlus, LogIn } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import AuthModal from './AuthModal';

interface HeaderProps {
  onReset?: () => void;
  showReset?: boolean;
}

const Header: React.FC<HeaderProps> = ({ onReset, showReset = false }) => {
  const { user, logout } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

  const handleSignInClick = () => {
    setAuthModalMode('login');
    setIsAuthModalOpen(true);
  };

  const handleSignUpClick = () => {
    setAuthModalMode('register');
    setIsAuthModalOpen(true);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleTitleClick = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      <header className="relative z-10 bg-black/40 backdrop-blur-lg border-b border-white/10 py-4 shadow-lg">
        <div className="container mx-auto flex items-center justify-between px-4">
          <div className="flex items-center gap-3 cursor-pointer hover:scale-105 transition-transform duration-200" onClick={handleTitleClick}>
            <div className="relative">
              <div className="absolute -inset-0.5 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 opacity-70 blur-sm animate-pulse-slow"></div>
              <div className="relative p-1 rounded-full bg-gradient-to-br from-cyan-400 via-purple-500 to-pink-500">
                <div className="w-10 h-10 flex items-center justify-center rounded-full bg-black">
                  <Sparkles className="h-5 w-5 text-transparent bg-clip-text bg-gradient-to-br from-cyan-300 to-purple-400" />
                </div>
              </div>
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent font-display tracking-tight hover:from-cyan-200 hover:via-purple-300 hover:to-pink-200 transition-all duration-200">AI Interviewer</h1>
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
          
          <div className="flex items-center gap-4">
            {/* User info and logout */}
            {user ? (
              <div className="flex items-center gap-3">
                <div className="glass-effect rounded-xl px-3 py-2 flex items-center gap-2">
                  <User className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-300">{user.email}</span>
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleLogout}
                  className="border-white/10 bg-black/20 hover:bg-red-900/20 hover:border-red-500/50 text-gray-300 hover:text-red-300 transition-all duration-300"
                >
                  <LogOut className="h-4 w-4 mr-1" />
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleSignInClick}
                  className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-white hover:bg-opacity-10 rounded-lg transition-all duration-200"
                >
                  <LogIn size={16} />
                  <span>Sign In</span>
                </button>
                <button
                  onClick={handleSignUpClick}
                  className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg transition-all duration-200"
                >
                  <UserPlus size={16} />
                  <span>Sign Up</span>
                </button>
              </div>
            )}
            
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

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />
    </>
  );
};

export default Header;
