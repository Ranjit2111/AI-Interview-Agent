import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'register';
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, initialMode = 'login' }) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);

  // Sync mode with initialMode prop when it changes
  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="relative w-full max-w-md mx-4">
        <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl border border-white border-opacity-20 shadow-2xl">
          <div className="flex items-center justify-between p-6 border-b border-white border-opacity-20">
            <h2 className="text-2xl font-bold text-white">
              {mode === 'login' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-300 hover:text-white hover:bg-white hover:bg-opacity-10 rounded-lg transition-all duration-200"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-6">
            {mode === 'login' ? (
              <LoginForm onSuccess={onClose} />
            ) : (
              <RegisterForm onSuccess={onClose} />
            )}

            <div className="mt-6 text-center">
              <p className="text-gray-300">
                {mode === 'login' ? "Don't have an account?" : "Already have an account?"}
                <button
                  onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
                  className="ml-2 text-blue-400 hover:text-blue-300 font-medium transition-colors duration-200"
                >
                  {mode === 'login' ? 'Sign up' : 'Sign in'}
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthModal; 