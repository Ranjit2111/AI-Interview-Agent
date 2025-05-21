import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { PerTurnFeedbackItem } from '../services/api'; // Assuming api.ts is in ../services

interface PerTurnFeedbackReviewProps {
  feedbackItems: PerTurnFeedbackItem[];
  onProceedToSummary: () => void;
}

const PerTurnFeedbackReview: React.FC<PerTurnFeedbackReviewProps> = ({ feedbackItems, onProceedToSummary }) => {
  if (!feedbackItems || feedbackItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <p className="text-lg text-gray-400 mb-4">No per-turn feedback available for this session.</p>
        <Button onClick={onProceedToSummary}>View Final Summary</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full p-4 md:p-8 bg-gradient-to-br from-gray-900 via-purple-900/30 to-gray-900">
      <Card className="w-full max-w-4xl mx-auto bg-black/70 border-purple-500/30 shadow-2xl shadow-purple-500/10 backdrop-blur-lg">
        <CardHeader className="text-center border-b border-purple-500/20 pb-4">
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
            Review Your Answers
          </CardTitle>
          <CardDescription className="text-gray-400">
            Here's a breakdown of the feedback for each of your answers during the interview.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-280px)] md:h-[calc(100vh-300px)]">
            <div className="p-6 space-y-6">
              {feedbackItems.map((item, index) => (
                <Card key={index} className="bg-gray-800/50 border-gray-700/50 overflow-hidden transition-all hover:shadow-lg hover:border-purple-400/50">
                  <CardHeader className="bg-gray-700/30 p-4">
                    <p className="text-xs text-gray-400 mb-1">Question {index + 1}</p>
                    <CardTitle className="text-md font-semibold text-purple-300">{item.question}</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 space-y-3">
                    <div>
                      <h4 className="text-sm font-medium text-gray-400 mb-1">Your Answer:</h4>
                      <p className="text-sm text-gray-200 bg-black/30 p-3 rounded-md whitespace-pre-wrap">{item.answer}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-yellow-400 mb-1">Coach's Feedback:</h4>
                      <p className="text-sm text-gray-100 bg-black/30 p-3 rounded-md whitespace-pre-wrap">{item.feedback}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
      <div className="mt-6 text-center">
        <Button 
          onClick={onProceedToSummary} 
          className="bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white font-semibold py-3 px-8 rounded-lg shadow-lg hover:shadow-pink-500/30 transition-all duration-300 text-lg"
        >
          View Final Summary & Recommendations
        </Button>
      </div>
    </div>
  );
};

export default PerTurnFeedbackReview; 