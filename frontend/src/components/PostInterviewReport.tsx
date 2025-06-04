import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ExternalLink, Brain, Search, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { PerTurnFeedbackItem } from '../services/api';

interface PostInterviewReportProps {
  perTurnFeedback: PerTurnFeedbackItem[];
  finalSummary: {
    status: 'loading' | 'completed' | 'error';
    data?: {
      patterns_tendencies?: string;
      strengths?: string;
      weaknesses?: string;
      improvement_focus_areas?: string;
      resource_search_topics?: string[];
      recommended_resources?: any[];
    };
    error?: string;
  };
  resources: {
    status: 'loading' | 'completed' | 'error';
    data?: any[];
    error?: string;
  };
  onStartNewInterview: () => void;
}

const PostInterviewReport: React.FC<PostInterviewReportProps> = ({
  perTurnFeedback,
  finalSummary,
  resources,
  onStartNewInterview,
}) => {
  // Loading state animations
  const [dotsCount, setDotsCount] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => {
      setDotsCount(prev => (prev % 3) + 1);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const renderTextSection = (title: string, content?: any) => {
    const textContent = typeof content === 'string' ? content : 
                       content !== null && content !== undefined ? JSON.stringify(content, null, 2) : '';
    
    if (!textContent || textContent.trim() === "") {
      return (
        <div>
          <h3 className="text-xl font-semibold text-purple-400 mb-3">{title}</h3>
          <p className="text-gray-400 italic">No specific {title.toLowerCase()} noted for this section.</p>
        </div>
      );
    }
    return (
      <div>
        <h3 className="text-xl font-semibold text-purple-400 mb-3">{title}</h3>
        {textContent.split('\n').map((paragraph, index) => (
          <p key={index} className="text-gray-300 mb-2 whitespace-pre-wrap">{paragraph}</p>
        ))}
      </div>
    );
  };

  const renderRecommendedResources = (resourcesData?: any[]) => {
    if (!resourcesData || resourcesData.length === 0) {
      return null;
    }

    // Check if this is the legacy format (with topic and resources)
    const isLegacyFormat = resourcesData.length > 0 && resourcesData[0]?.topic && resourcesData[0]?.resources;
    
    if (isLegacyFormat) {
      // Legacy format: [{ topic: string, resources: [{title, url, snippet}] }]
      return (
        <div>
          <h3 className="text-xl font-semibold text-purple-400 mb-4">Recommended Resources</h3>
          <Accordion type="single" collapsible className="w-full">
            {resourcesData.map((item, index) => (
              <AccordionItem value={`item-${index}`} key={index} className="border-purple-500/30">
                <AccordionTrigger className="text-lg text-purple-300 hover:text-purple-200">
                  {item.topic}
                </AccordionTrigger>
                <AccordionContent className="pt-2">
                  {item.resources && item.resources.length > 0 ? (
                    <ul className="space-y-3">
                      {item.resources.map((resource: any, rIndex: number) => (
                        <li key={rIndex} className="p-3 bg-gray-700/50 rounded-md hover:bg-gray-700/80 transition-colors">
                          <a
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-cyan-400 hover:text-cyan-300 group"
                          >
                            {resource.title}
                            <ExternalLink className="inline-block ml-2 h-4 w-4 opacity-70 group-hover:opacity-100" />
                          </a>
                          <p className="text-sm text-gray-400 mt-1">{resource.snippet}</p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-400 italic">No specific resources found for this topic.</p>
                  )}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      );
    } else {
      // New agentic format: flat list of resources with title, url, description, resource_type
      return (
        <div>
          <h3 className="text-xl font-semibold text-purple-400 mb-4">Recommended Learning Resources</h3>
          <p className="text-gray-400 mb-4 text-sm">
            These resources were intelligently selected based on your interview performance and skill gaps.
          </p>
          <ul className="space-y-3">
            {resourcesData.map((resource: any, index: number) => (
              <li key={index} className="p-4 bg-gray-700/50 rounded-md hover:bg-gray-700/80 transition-colors border border-purple-500/20">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-cyan-400 hover:text-cyan-300 group text-lg"
                    >
                      {resource.title}
                      <ExternalLink className="inline-block ml-2 h-4 w-4 opacity-70 group-hover:opacity-100" />
                    </a>
                    {resource.resource_type && (
                      <span className="ml-2 px-2 py-1 text-xs bg-purple-500/20 text-purple-300 rounded-full">
                        {resource.resource_type}
                      </span>
                    )}
                    <p className="text-sm text-gray-400 mt-2">{resource.description}</p>
                    {resource.reasoning && (
                      <div className="mt-2 p-2 bg-blue-900/20 border-l-2 border-blue-400/50 rounded-r">
                        <p className="text-xs text-blue-300 font-medium mb-1">Why this resource was recommended:</p>
                        <p className="text-xs text-blue-200">{resource.reasoning}</p>
                      </div>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      );
    }
  };

  const renderLoadingState = (type: 'summary' | 'resources') => {
    const icons = {
      summary: <Brain className="w-5 h-5 text-blue-400" />,
      resources: <Search className="w-5 h-5 text-green-400" />
    };

    const messages = {
      summary: `Coach is analyzing your performance to prepare a summary${'.'.repeat(dotsCount)}`,
      resources: `Looking for personalized learning resources${'.'.repeat(dotsCount)}`
    };

    const colors = {
      summary: 'border-blue-500/30 bg-blue-900/20',
      resources: 'border-green-500/30 bg-green-900/20'
    };

    return (
      <Card className={`${colors[type]} transition-all duration-300`}>
        <CardContent className="p-6">
          <div className="flex items-center space-x-3">
            <div className="relative">
              {icons[type]}
              <Loader2 className="absolute inset-0 w-5 h-5 text-yellow-400 animate-spin" />
            </div>
            <div>
              <p className="text-gray-200 font-medium">{messages[type]}</p>
              <p className="text-gray-400 text-sm mt-1">
                {type === 'summary' ? 'Multiple AI agents are working behind the scenes' : 'Searching online resources for your skill gaps'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderErrorState = (type: 'summary' | 'resources', error: string) => {
    return (
      <Card className="border-red-500/30 bg-red-900/20">
        <CardContent className="p-6">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div>
              <p className="text-red-300 font-medium">Error generating {type}</p>
              <p className="text-red-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="flex flex-col h-full p-4 md:p-8 bg-gradient-to-br from-gray-900 via-purple-900/30 to-gray-900">
      <div className="w-full max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-2">
            Post Interview Report
          </h1>
          <p className="text-gray-400 text-lg">
            Your comprehensive interview analysis and personalized recommendations
          </p>
        </div>

        {/* Turn-wise Feedback Section - Always Available Immediately */}
        <Card className="bg-black/70 border-purple-500/30 shadow-2xl shadow-purple-500/10 backdrop-blur-lg">
          <CardHeader className="border-b border-purple-500/20">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <CardTitle className="text-2xl font-bold text-purple-300">
                Turn-by-Turn Feedback
              </CardTitle>
            </div>
            <CardDescription className="text-gray-400">
              Detailed feedback for each of your answers during the interview.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {(!perTurnFeedback || perTurnFeedback.length === 0) ? (
              <div className="p-6 text-center">
                <p className="text-gray-400">No per-turn feedback available for this session.</p>
              </div>
            ) : (
              <ScrollArea className="h-[400px]">
                <div className="p-6 space-y-6">
                  {perTurnFeedback.map((item, index) => (
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
            )}
          </CardContent>
        </Card>

        {/* Final Summary Section - Progressive Loading */}
        <Card className="bg-black/70 border-purple-500/30 shadow-2xl shadow-purple-500/10 backdrop-blur-lg">
          <CardHeader className="border-b border-purple-500/20">
            <div className="flex items-center space-x-2">
              {finalSummary.status === 'completed' ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : finalSummary.status === 'error' ? (
                <AlertCircle className="w-5 h-5 text-red-400" />
              ) : (
                <Brain className="w-5 h-5 text-blue-400" />
              )}
              <CardTitle className="text-2xl font-bold text-purple-300">
                Detailed Coaching Summary
              </CardTitle>
            </div>
            <CardDescription className="text-gray-400">
              Comprehensive analysis of your interview performance and improvement areas.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            {finalSummary.status === 'loading' && renderLoadingState('summary')}
            {finalSummary.status === 'error' && renderErrorState('summary', finalSummary.error || 'Unknown error')}
            {finalSummary.status === 'completed' && finalSummary.data && (
              <div className="space-y-8">
                {renderTextSection("Observed Patterns & Tendencies", finalSummary.data.patterns_tendencies)}
                {renderTextSection("Strengths", finalSummary.data.strengths)}
                {renderTextSection("Weaknesses & Areas for Development", finalSummary.data.weaknesses)}
                {renderTextSection("Key Focus Areas for Improvement", finalSummary.data.improvement_focus_areas)}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Resources Section - Progressive Loading */}
        <Card className="bg-black/70 border-purple-500/30 shadow-2xl shadow-purple-500/10 backdrop-blur-lg">
          <CardHeader className="border-b border-purple-500/20">
            <div className="flex items-center space-x-2">
              {resources.status === 'completed' ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : resources.status === 'error' ? (
                <AlertCircle className="w-5 h-5 text-red-400" />
              ) : (
                <Search className="w-5 h-5 text-green-400" />
              )}
              <CardTitle className="text-2xl font-bold text-purple-300">
                Personalized Learning Resources
              </CardTitle>
            </div>
            <CardDescription className="text-gray-400">
              Curated resources to help you improve in identified skill areas.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            {resources.status === 'loading' && renderLoadingState('resources')}
            {resources.status === 'error' && renderErrorState('resources', resources.error || 'Unknown error')}
            {resources.status === 'completed' && resources.data && (
              <div>
                {renderRecommendedResources(resources.data)}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Action Button */}
        <div className="text-center">
          <Button
            onClick={onStartNewInterview}
            size="lg"
            className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white shadow-lg hover:shadow-purple-500/20 text-lg font-medium"
          >
            Start New Interview
          </Button>
        </div>
      </div>
    </div>
  );
};

export default PostInterviewReport; 