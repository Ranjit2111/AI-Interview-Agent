import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Mic, Headphones, CheckCircle } from 'lucide-react';

interface InterviewInstructionsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const InterviewInstructionsModal: React.FC<InterviewInstructionsModalProps> = ({
  isOpen,
  onClose
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="max-w-md w-full mx-4">
        <Card className="bg-gray-900/95 border-cyan-500/30 shadow-xl shadow-cyan-500/10 backdrop-blur-lg">
          <CardHeader className="text-center border-b border-cyan-500/20 pb-4">
            <CardTitle className="text-xl font-bold bg-gradient-to-r from-cyan-300 to-purple-400 bg-clip-text text-transparent">
              Interview Instructions
            </CardTitle>
          </CardHeader>
          
          <CardContent className="p-6 space-y-6">
            {/* Instruction 1 */}
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-400/30 flex items-center justify-center flex-shrink-0 mt-1">
                <Mic className="w-4 h-4 text-cyan-300" />
              </div>
              <div>
                <h3 className="font-semibold text-cyan-300 mb-1">How to Talk</h3>
                <p className="text-gray-300 text-sm leading-relaxed">
                  Click the mic to talk and click it again once you are finished talking.
                </p>
              </div>
            </div>

            {/* Instruction 2 */}
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-full bg-purple-500/20 border border-purple-400/30 flex items-center justify-center flex-shrink-0 mt-1">
                <Headphones className="w-4 h-4 text-purple-300" />
              </div>
              <div>
                <h3 className="font-semibold text-purple-300 mb-1">Best Performance</h3>
                <p className="text-gray-300 text-sm leading-relaxed">
                  Use earphones and speak loudly and clearly for best performance.
                </p>
              </div>
            </div>

            {/* Got it button */}
            <div className="pt-4">
              <Button 
                onClick={onClose}
                className="w-full bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-medium"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Got it! Start Interview
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InterviewInstructionsModal; 