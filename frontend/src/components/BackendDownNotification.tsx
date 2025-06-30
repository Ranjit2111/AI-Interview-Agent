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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4">
      {/* Backdrop with blur effect */}
      <div className="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={onClose} />
      
      {/* Modal Content */}
      <div className="relative w-full max-w-md sm:max-w-lg lg:max-w-xl mx-auto max-h-[90vh] overflow-y-auto">
        <div className="bg-gradient-to-br from-black/90 via-red-900/20 to-black/90 backdrop-blur-3xl border border-red-500/30 rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-2xl">
          
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-3 right-3 p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-all duration-300"
          >
            <X className="w-4 h-4 text-gray-300" />
          </button>
          
          {/* Header with warning icon */}
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-lg bg-gradient-to-br from-red-500 to-orange-600 shadow-lg">
              <AlertTriangle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white">Backend Service Unavailable</h2>
              <p className="text-gray-400 text-xs sm:text-sm">Service temporarily offline</p>
            </div>
          </div>

          {/* Main message - condensed */}
          <div className="space-y-3 mb-5">
            <div className="bg-black/40 rounded-lg p-3 sm:p-4 border border-red-500/20">
              <p className="text-gray-300 text-xs sm:text-sm leading-relaxed">
                Hi, I'm <span className="text-white font-semibold">Ranjit</span>, the developer of this AI Interviewer Agent. 
                I've temporarily shut down the backend service to save on hosting costs. The backend runs on Azure, 
                which incurs charges, so I keep it offline when not actively showcasing my project.
              </p>
            </div>

            <div className="bg-black/40 rounded-lg p-3 sm:p-4 border border-purple-500/20">
              <h4 className="text-white font-semibold mb-2 text-xs sm:text-sm">📧 Want to try the full experience?</h4>
              <p className="text-gray-300 text-xs sm:text-sm leading-relaxed">
                Reach out to me and I'll be happy to spin up the backend for a demo! You can also run the entire 
                project locally by following the setup instructions on GitHub.
              </p>
            </div>
          </div>

          {/* Contact buttons - more compact */}
          <div className="space-y-3">
            <h4 className="text-white font-semibold text-xs sm:text-sm">Get in touch:</h4>
            
            <div className="grid grid-cols-2 gap-3">
              {/* Email */}
              <a
                href="mailto:ranjitn.dev@gmail.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 text-cyan-300 hover:text-white hover:border-cyan-400/50 transition-all duration-300 group"
              >
                <Mail className="w-4 h-4" />
                <span className="text-xs font-medium">Email</span>
              </a>

              {/* LinkedIn */}
              <a
                href="https://www.linkedin.com/in/ranjit-n/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-gradient-to-r from-blue-500/20 to-indigo-600/20 border border-blue-500/30 text-blue-300 hover:text-white hover:border-blue-400/50 transition-all duration-300 group"
              >
                <Linkedin className="w-4 h-4" />
                <span className="text-xs font-medium">LinkedIn</span>
              </a>
            </div>

            {/* Local setup call-to-action - condensed */}
            <div className="bg-gradient-to-r from-green-500/10 to-emerald-600/10 border border-green-500/20 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Github className="w-4 h-4 text-green-400" />
                <h4 className="text-green-300 font-semibold text-xs sm:text-sm">Run Locally</h4>
              </div>
              <p className="text-gray-300 text-xs leading-relaxed mb-2.5">
                Want to explore the full AI Interviewer Agent right now? You can run the complete project locally 
                with your own API keys following the detailed setup guide on GitHub.
              </p>
              <a
                href="https://github.com/Ranjit2111/AI-Interview-Agent/blob/main/setup_guide.md"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-green-400 hover:text-green-300 text-xs font-medium transition-colors"
              >
                View setup instructions
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* Close button */}
          <div className="mt-4 text-center">
            <Button
              onClick={onClose}
              className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-500 hover:to-gray-600 text-white px-5 py-2 rounded-lg font-medium border-0 text-sm"
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