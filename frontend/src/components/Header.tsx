import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Sparkles, Zap, Bot, BarChart3, Code, Github, LogOut, User, UserPlus, LogIn } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import AuthModal from './AuthModal';

interface HeaderProps {
  onReset?: () => void;
  showReset?: boolean;
}

const Header: React.FC<HeaderProps> = ({ onReset, showReset = false }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
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
    navigate('/');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      <header className="relative z-10 bg-black/40 backdrop-blur-lg py-4 shadow-lg">
        <div className="container mx-auto flex items-center justify-between px-4">
          {/* Logo and Title */}
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
          
          {/* Right side container with social links and auth */}
          <div className="flex items-center gap-6">
            {/* Social Links */}
            <div className="flex items-center space-x-3">
              <a 
                href="https://github.com/Ranjit2111" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="p-2 rounded-full bg-black/30 hover:bg-white/10 border border-white/10 hover:border-cyan-500/30 transition-all duration-300 hover:shadow-cyan-500/20 group"
              >
                <Github className="h-4 w-4 text-gray-400 group-hover:text-cyan-400 transition-colors" />
              </a>
              <a 
                href="https://www.linkedin.com/in/ranjit-n/" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="p-2 rounded-full bg-black/30 hover:bg-white/10 border border-white/10 hover:border-blue-500/30 transition-all duration-300 hover:shadow-blue-500/20 group"
              >
                <svg className="h-4 w-4 text-gray-400 group-hover:text-blue-400 transition-colors" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
              </a>
            </div>
            
            {/* Authentication Section */}
            <div className="flex items-center gap-4">
              {/* User info and logout */}
              {user ? (
                <div className="flex items-center gap-3">
                  <div className="glass-effect rounded-xl px-3 py-2 flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-300">{user.name || user.email}</span>
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
                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleSignInClick}
                    className="flex items-center space-x-2 px-6 py-3 text-gray-300 hover:text-white bg-black/30 hover:bg-white/10 backdrop-blur-sm border border-white/10 hover:border-cyan-500/30 rounded-xl transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10"
                  >
                    <LogIn size={16} />
                    <span className="font-medium">Sign In</span>
                  </button>
                  <button
                    onClick={handleSignUpClick}
                    className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white rounded-xl font-medium shadow-lg hover:shadow-purple-500/25 transition-all duration-300 backdrop-blur-sm border border-purple-500/20 hover:scale-105"
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
