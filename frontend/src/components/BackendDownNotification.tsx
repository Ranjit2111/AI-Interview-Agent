import React from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Github, Linkedin, Mail, ExternalLink, X } from 'lucide-react';

interface BackendDownNotificationProps {
  isOpen: boolean;
  onClose: () => void;
}

const BackendDownNotification: React.FC<BackendDownNotificationProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      {/* Backdrop with blur effect */}
      <div className="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={onClose} />
      
      {/* Modal Content */}
      <div className="relative w-full max-w-lg sm:max-w-xl lg:max-w-2xl mx-auto">
        <div className="bg-gradient-to-br from-black/90 via-red-900/20 to-black/90 backdrop-blur-3xl border border-red-500/30 rounded-2xl sm:rounded-3xl p-6 sm:p-8 shadow-2xl">
          
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-all duration-300"
          >
            <X className="w-5 h-5 text-gray-300" />
          </button>
          
          {/* Header with warning icon */}
          <div className="flex items-center gap-3 sm:gap-4 mb-6">
            <div className="p-3 sm:p-4 rounded-xl bg-gradient-to-br from-red-500 to-orange-600 shadow-lg">
              <AlertTriangle className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-white">Backend Service Unavailable</h2>
              <p className="text-gray-400 text-sm sm:text-base">Service temporarily offline</p>
            </div>
          </div>

          {/* Main message */}
          <div className="space-y-4 sm:space-y-6 mb-6 sm:mb-8">
            <div className="bg-black/40 rounded-xl p-4 sm:p-6 border border-red-500/20">
              <p className="text-gray-300 text-sm sm:text-base leading-relaxed">
                Hi, I'm <span className="text-white font-semibold">Ranjit</span>, the developer of this AI Interviewer Agent. 
                I've temporarily shut down the backend service to save on hosting costs. The backend runs on Azure, 
                which incurs charges, so I keep it offline when not actively demonstrating the project.
              </p>
            </div>

            <div className="bg-black/40 rounded-xl p-4 sm:p-6 border border-purple-500/20">
              <h4 className="text-white font-semibold mb-3 text-sm sm:text-base">📧 Want to try the full experience?</h4>
              <p className="text-gray-300 text-sm sm:text-base leading-relaxed">
                Reach out to me and I'll be happy to spin up the backend for a demo! You can also run the entire 
                project locally by following the setup instructions on GitHub.
              </p>
            </div>
          </div>

          {/* Contact buttons */}
          <div className="space-y-4">
            <h4 className="text-white font-semibold text-sm sm:text-base">Get in touch:</h4>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Email */}
              <a
                href="mailto:ranjitn.dev@gmail.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 rounded-xl bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 text-cyan-300 hover:text-white hover:border-cyan-400/50 transition-all duration-300 group"
              >
                <Mail className="w-4 h-4 sm:w-5 sm:h-5" />
                <span className="text-xs sm:text-sm font-medium">Email</span>
                <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4 ml-auto group-hover:translate-x-1 transition-transform" />
              </a>

              {/* LinkedIn */}
              <a
                href="https://www.linkedin.com/in/ranjit-n/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 rounded-xl bg-gradient-to-r from-blue-500/20 to-indigo-600/20 border border-blue-500/30 text-blue-300 hover:text-white hover:border-blue-400/50 transition-all duration-300 group"
              >
                <Linkedin className="w-4 h-4 sm:w-5 sm:h-5" />
                <span className="text-xs sm:text-sm font-medium">LinkedIn</span>
                <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4 ml-auto group-hover:translate-x-1 transition-transform" />
              </a>

              {/* GitHub */}
              <a
                href="https://github.com/Ranjit2111/AI-Interview-Agent"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 rounded-xl bg-gradient-to-r from-purple-500/20 to-pink-600/20 border border-purple-500/30 text-purple-300 hover:text-white hover:border-purple-400/50 transition-all duration-300 group"
              >
                <Github className="w-4 h-4 sm:w-5 sm:h-5" />
                <span className="text-xs sm:text-sm font-medium">GitHub</span>
                <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4 ml-auto group-hover:translate-x-1 transition-transform" />
              </a>
            </div>

            {/* Local setup call-to-action */}
            <div className="bg-gradient-to-r from-green-500/10 to-emerald-600/10 border border-green-500/20 rounded-xl p-4 sm:p-5">
              <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
                <Github className="w-4 h-4 sm:w-5 sm:h-5 text-green-400" />
                <h4 className="text-green-300 font-semibold text-sm sm:text-base">Run Locally</h4>
              </div>
              <p className="text-gray-300 text-xs sm:text-sm leading-relaxed mb-3 sm:mb-4">
                Want to explore the full AI Interviewer Agent right now? You can run the complete project locally 
                with your own API keys following the detailed setup guide on GitHub.
              </p>
              <a
                href="https://github.com/Ranjit2111/AI-Interview-Agent#-getting-started"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-green-400 hover:text-green-300 text-xs sm:text-sm font-medium transition-colors"
              >
                View setup instructions
                <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4" />
              </a>
            </div>
          </div>

          {/* Close button */}
          <div className="mt-6 sm:mt-8 text-center">
            <Button
              onClick={onClose}
              className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-500 hover:to-gray-600 text-white px-6 sm:px-8 py-2 sm:py-3 rounded-xl font-medium border-0"
            >
              Continue Browsing
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackendDownNotification; 