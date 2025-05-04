
import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

interface InterviewResultsProps {
  coachingSummary: any;
  skillProfile: any;
  onStartNewInterview: () => void;
}

const InterviewResults: React.FC<InterviewResultsProps> = ({
  coachingSummary,
  skillProfile,
  onStartNewInterview,
}) => {
  return (
    <div className="container mx-auto max-w-4xl p-4">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-interview-primary mb-2">Interview Complete</h2>
        <p className="text-gray-600">
          Here's your feedback and skill assessment
        </p>
      </div>

      <Tabs defaultValue="coaching">
        <div className="flex justify-center mb-6">
          <TabsList>
            <TabsTrigger value="coaching">Coaching Feedback</TabsTrigger>
            <TabsTrigger value="skills">Skills Assessment</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="coaching">
          <Card className="shadow-lg">
            <CardHeader className="bg-interview-primary text-white">
              <CardTitle>Coaching Summary</CardTitle>
              <CardDescription className="text-gray-100">
                Actionable feedback to improve your interview performance
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                {/* Strengths */}
                <div>
                  <h3 className="text-xl font-semibold text-interview-secondary mb-3">Strengths</h3>
                  {coachingSummary?.strengths ? (
                    <ul className="list-disc list-inside space-y-2">
                      {Array.isArray(coachingSummary.strengths) ? (
                        coachingSummary.strengths.map((strength: string, i: number) => (
                          <li key={i}>{strength}</li>
                        ))
                      ) : (
                        <p>{String(coachingSummary.strengths)}</p>
                      )}
                    </ul>
                  ) : (
                    <p className="text-gray-500 italic">No strengths data available</p>
                  )}
                </div>
                
                {/* Areas for Improvement */}
                <div>
                  <h3 className="text-xl font-semibold text-interview-secondary mb-3">
                    Areas for Improvement
                  </h3>
                  {coachingSummary?.areas_for_improvement ? (
                    <ul className="list-disc list-inside space-y-2">
                      {Array.isArray(coachingSummary.areas_for_improvement) ? (
                        coachingSummary.areas_for_improvement.map((area: string, i: number) => (
                          <li key={i}>{area}</li>
                        ))
                      ) : (
                        <p>{String(coachingSummary.areas_for_improvement)}</p>
                      )}
                    </ul>
                  ) : (
                    <p className="text-gray-500 italic">No improvement data available</p>
                  )}
                </div>
                
                {/* Recommendations */}
                <div>
                  <h3 className="text-xl font-semibold text-interview-secondary mb-3">
                    Recommendations
                  </h3>
                  {coachingSummary?.recommendations ? (
                    <ul className="list-disc list-inside space-y-2">
                      {Array.isArray(coachingSummary.recommendations) ? (
                        coachingSummary.recommendations.map((rec: string, i: number) => (
                          <li key={i}>{rec}</li>
                        ))
                      ) : (
                        <p>{String(coachingSummary.recommendations)}</p>
                      )}
                    </ul>
                  ) : (
                    <p className="text-gray-500 italic">No recommendations available</p>
                  )}
                </div>
                
                {/* Overall Assessment */}
                {coachingSummary?.overall_assessment && (
                  <div>
                    <h3 className="text-xl font-semibold text-interview-secondary mb-3">
                      Overall Assessment
                    </h3>
                    <p className="text-gray-700">{coachingSummary.overall_assessment}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="skills">
          <Card className="shadow-lg">
            <CardHeader className="bg-interview-primary text-white">
              <CardTitle>Skills Assessment</CardTitle>
              <CardDescription className="text-gray-100">
                Evaluation of your key interview skills and competencies
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {skillProfile && typeof skillProfile === 'object' ? (
                  Object.entries(skillProfile).map(([skill, rating]: [string, any]) => (
                    <div key={skill} className="border rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium capitalize">
                          {skill.replace(/_/g, ' ')}
                        </h4>
                        {typeof rating === 'number' ? (
                          <SkillBadge score={rating} />
                        ) : (
                          <Badge>{String(rating)}</Badge>
                        )}
                      </div>
                      {typeof rating === 'number' && (
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div
                            className="bg-interview-secondary h-2.5 rounded-full"
                            style={{ width: `${Math.min(100, Math.max(0, rating * 10))}%` }}
                          ></div>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 italic col-span-2 text-center">
                    No skill assessment data available
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-8 text-center">
        <Button 
          onClick={onStartNewInterview}
          className="bg-interview-secondary hover:bg-interview-secondary/90"
          size="lg"
        >
          Start New Interview
        </Button>
      </div>
    </div>
  );
};

// Helper component for skill ratings
const SkillBadge = ({ score }: { score: number }) => {
  let color = '';
  let label = '';
  
  if (score >= 9) {
    color = 'bg-green-500';
    label = 'Excellent';
  } else if (score >= 7) {
    color = 'bg-green-400';
    label = 'Good';
  } else if (score >= 5) {
    color = 'bg-yellow-400';
    label = 'Average';
  } else if (score >= 3) {
    color = 'bg-orange-400';
    label = 'Fair';
  } else {
    color = 'bg-red-500';
    label = 'Needs Improvement';
  }
  
  return (
    <Badge className={`${color} hover:${color}`}>
      {label} ({score}/10)
    </Badge>
  );
};

export default InterviewResults;
