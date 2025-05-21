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
    recommended_resources?: { topic: string; resources: { title: string; url: string; snippet: string }[] }[];
  };
  onStartNewInterview: () => void;
}

const renderTextSection = (title: string, content?: string) => {
  if (!content || content.trim() === "") {
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
      {content.split('\n').map((paragraph, index) => (
        <p key={index} className="text-gray-300 mb-2 whitespace-pre-wrap">{paragraph}</p>
      ))}
    </div>
  );
};

const InterviewResults: React.FC<InterviewResultsProps> = ({
  coachingSummary,
  onStartNewInterview,
}) => {

  const {
    patterns_tendencies,
    strengths,
    weaknesses,
    improvement_focus_areas,
    recommended_resources,
  } = coachingSummary || {};

  return (
    <div className="container mx-auto max-w-4xl p-4 text-gray-100">
      <div className="text-center mb-10">
        <h2 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-2">
          Interview Completed!
        </h2>
        <p className="text-gray-400 text-lg">
          Here's your comprehensive feedback. Use it to shine in your next interview!
        </p>
      </div>

      <Card className="shadow-2xl bg-gray-800/50 border-purple-500/30">
        <CardHeader className="border-b border-purple-500/30">
          <CardTitle className="text-2xl font-semibold text-purple-300">Detailed Coaching Summary</CardTitle>
          <CardDescription className="text-gray-400">
            Actionable insights to improve your interview performance.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-8">
            {renderTextSection("Observed Patterns & Tendencies", patterns_tendencies)}
            {renderTextSection("Strengths", strengths)}
            {renderTextSection("Weaknesses & Areas for Development", weaknesses)}
            {renderTextSection("Key Focus Areas for Improvement", improvement_focus_areas)}

            {recommended_resources && recommended_resources.length > 0 && (
              <div>
                <h3 className="text-xl font-semibold text-purple-400 mb-4">Recommended Resources</h3>
                <Accordion type="single" collapsible className="w-full">
                  {recommended_resources.map((item, index) => (
                    <AccordionItem value={`item-${index}`} key={index} className="border-purple-500/30">
                      <AccordionTrigger className="text-lg text-purple-300 hover:text-purple-200">
                        {item.topic}
                      </AccordionTrigger>
                      <AccordionContent className="pt-2">
                        {item.resources && item.resources.length > 0 ? (
                          <ul className="space-y-3">
                            {item.resources.map((resource, rIndex) => (
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
            )}
          </div>
        </CardContent>
      </Card>

      <div className="mt-10 text-center">
        <Button
          onClick={onStartNewInterview}
          size="lg"
          className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white shadow-lg hover:shadow-purple-500/20 text-lg font-medium btn-ripple"
        >
          Start New Interview
        </Button>
      </div>
    </div>
  );
};

export default InterviewResults;
