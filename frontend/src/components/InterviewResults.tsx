import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ExternalLink } from 'lucide-react';

interface InterviewResultsProps {
  coachingSummary: {
    patterns_tendencies?: string;
    strengths?: string;
    weaknesses?: string;
    improvement_focus_areas?: string;
    resource_search_topics?: string[];
    recommended_resources?: any[]; // Can be legacy format or new agentic format
  };
  onStartNewInterview: () => void;
}

const renderTextSection = (title: string, content?: any) => {
  // Convert content to string if it's not already a string
  const textContent = typeof content === 'string' ? content : 
                     content !== null && content !== undefined ? JSON.stringify(content, null, 2) : '';
  
  if (!textContent || textContent.trim() === "") {
    return (
      <div>
        <h3 className="text-lg sm:text-xl lg:text-2xl font-semibold text-purple-400 mb-2 sm:mb-3">{title}</h3>
        <p className="text-gray-400 italic text-sm sm:text-base">No specific {title.toLowerCase()} noted for this section.</p>
      </div>
    );
  }
  return (
    <div>
      <h3 className="text-lg sm:text-xl lg:text-2xl font-semibold text-purple-400 mb-2 sm:mb-3">{title}</h3>
      {textContent.split('\n').map((paragraph, index) => (
        <p key={index} className="text-gray-300 mb-2 whitespace-pre-wrap text-sm sm:text-base leading-relaxed">{paragraph}</p>
      ))}
    </div>
  );
};

const renderRecommendedResources = (resources?: any[]) => {
  if (!resources || resources.length === 0) {
    return null;
  }

  // Check if this is the legacy format (with topic and resources)
  const isLegacyFormat = resources.length > 0 && resources[0]?.topic && resources[0]?.resources;
  
  if (isLegacyFormat) {
    // Legacy format: [{ topic: string, resources: [{title, url, snippet}] }]
    return (
      <div>
        <h3 className="text-lg sm:text-xl lg:text-2xl font-semibold text-purple-400 mb-3 sm:mb-4">Recommended Resources</h3>
        <Accordion type="single" collapsible className="w-full">
          {resources.map((item, index) => (
            <AccordionItem value={`item-${index}`} key={index} className="border-purple-500/30">
              <AccordionTrigger className="text-base sm:text-lg text-purple-300 hover:text-purple-200 px-2 sm:px-0">
                {item.topic}
              </AccordionTrigger>
              <AccordionContent className="pt-2">
                {item.resources && item.resources.length > 0 ? (
                  <ul className="space-y-3">
                    {item.resources.map((resource: any, rIndex: number) => (
                      <li key={rIndex} className="p-3 sm:p-4 bg-gray-700/50 rounded-md hover:bg-gray-700/80 transition-colors">
                        <a
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-cyan-400 hover:text-cyan-300 group text-sm sm:text-base"
                        >
                          {resource.title}
                          <ExternalLink className="inline-block ml-2 h-3 w-3 sm:h-4 sm:w-4 opacity-70 group-hover:opacity-100" />
                        </a>
                        <p className="text-xs sm:text-sm text-gray-400 mt-1">{resource.snippet}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-400 italic text-sm sm:text-base">No specific resources found for this topic.</p>
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
        <h3 className="text-lg sm:text-xl lg:text-2xl font-semibold text-purple-400 mb-3 sm:mb-4">Recommended Learning Resources</h3>
        <p className="text-gray-400 mb-3 sm:mb-4 text-xs sm:text-sm">
          These resources were intelligently selected based on your interview performance and skill gaps.
        </p>
        <ul className="space-y-3 sm:space-y-4">
          {resources.map((resource: any, index: number) => (
            <li key={index} className="p-3 sm:p-4 bg-gray-700/50 rounded-md hover:bg-gray-700/80 transition-colors border border-purple-500/20">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium text-cyan-400 hover:text-cyan-300 group text-sm sm:text-base lg:text-lg"
                  >
                    {resource.title}
                    <ExternalLink className="inline-block ml-2 h-3 w-3 sm:h-4 sm:w-4 opacity-70 group-hover:opacity-100" />
                  </a>
                  {resource.resource_type && (
                    <span className="ml-2 px-2 py-1 text-xs bg-purple-500/20 text-purple-300 rounded-full">
                      {resource.resource_type}
                    </span>
                  )}
                  <p className="text-xs sm:text-sm text-gray-400 mt-2">{resource.description}</p>
                  {resource.reasoning && (
                    <div className="mt-2 p-2 bg-blue-900/20 border-l-2 border-blue-400/50 rounded-r">
                      <p className="text-xs font-medium mb-1 text-blue-300">Why this resource was recommended:</p>
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

const InterviewResults: React.FC<InterviewResultsProps> = ({
  coachingSummary,
  onStartNewInterview,
}) => {
  console.log('🎯 InterviewResults component rendering');
  console.log('🎯 coachingSummary received:', coachingSummary);
  console.log('🎯 coachingSummary type:', typeof coachingSummary);
  
  // Add detailed logging for resources
  console.log('🎯 Raw recommended_resources:', coachingSummary?.recommended_resources);
  console.log('🎯 recommended_resources type:', typeof coachingSummary?.recommended_resources);
  console.log('🎯 recommended_resources is array:', Array.isArray(coachingSummary?.recommended_resources));
  console.log('🎯 recommended_resources length:', coachingSummary?.recommended_resources?.length);
  
  if (coachingSummary?.recommended_resources && coachingSummary.recommended_resources.length > 0) {
    console.log('🎯 First resource item:', coachingSummary.recommended_resources[0]);
    console.log('🎯 All resource items:');
    coachingSummary.recommended_resources.forEach((resource, index) => {
      console.log(`🎯 Resource ${index}:`, resource);
    });
  }
  
  // Add error boundary check
  if (!coachingSummary) {
    console.log('🎯 InterviewResults: coachingSummary is null/undefined');
    return (
      <div className="container mx-auto max-w-4xl p-4 text-gray-100">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-400 mb-4">Error: No Coaching Summary Available</h2>
          <p className="text-gray-400 mb-4">The coaching summary data is missing or corrupted.</p>
          <Button onClick={onStartNewInterview}>Start New Interview</Button>
        </div>
      </div>
    );
  }

  const {
    patterns_tendencies,
    strengths,
    weaknesses,
    improvement_focus_areas,
    recommended_resources,
  } = coachingSummary || {};

  return (
    <div className="container mx-auto max-w-2xl sm:max-w-3xl lg:max-w-4xl xl:max-w-5xl p-3 sm:p-4 lg:p-6 text-gray-100">
      <div className="text-center mb-8 sm:mb-10 lg:mb-12">
        <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-3 sm:mb-4">
          Interview Completed!
        </h2>
        <p className="text-gray-400 text-base sm:text-lg lg:text-xl px-4 sm:px-0">
          Here's your comprehensive feedback. Use it to shine in your next interview!
        </p>
      </div>

      <Card className="shadow-2xl bg-gray-800/50 border-purple-500/30 rounded-lg sm:rounded-xl lg:rounded-2xl">
        <CardHeader className="border-b border-purple-500/30 p-4 sm:p-6">
          <CardTitle className="text-lg sm:text-xl lg:text-2xl font-semibold text-purple-300">Detailed Coaching Summary</CardTitle>
          <CardDescription className="text-gray-400 text-sm sm:text-base">
            Actionable insights to improve your interview performance.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 lg:p-8">
          <div className="space-y-6 sm:space-y-8">
            {renderTextSection("Observed Patterns & Tendencies", patterns_tendencies)}
            {renderTextSection("Strengths", strengths)}
            {renderTextSection("Weaknesses & Areas for Development", weaknesses)}
            {renderTextSection("Key Focus Areas for Improvement", improvement_focus_areas)}

            {renderRecommendedResources(recommended_resources)}
          </div>
        </CardContent>
      </Card>

      <div className="mt-8 sm:mt-10 lg:mt-12 text-center">
        <Button
          onClick={onStartNewInterview}
          size="lg"
          className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white shadow-lg hover:shadow-purple-500/20 text-base sm:text-lg font-medium btn-ripple px-6 sm:px-8 py-3 sm:py-4 rounded-lg sm:rounded-xl min-h-[48px] transition-all duration-300 hover:scale-105"
        >
          Start New Interview
        </Button>
      </div>
    </div>
  );
};

export default InterviewResults;
