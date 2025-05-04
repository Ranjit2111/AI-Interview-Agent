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
  // Extract relevant data from coaching summary
  const getStrengths = () => {
    if (coachingSummary?.sections) {
      // Look for strengths in all sections
      for (const section of coachingSummary.sections) {
        if (section.strengths && section.strengths.length > 0) {
          return section.strengths;
        }
      }
    }
    return null;
  };

  const getImprovements = () => {
    if (coachingSummary?.sections) {
      // Look for improvements in all sections
      for (const section of coachingSummary.sections) {
        if (section.improvements && section.improvements.length > 0) {
          return section.improvements;
        }
      }
    }
    return null;
  };

  const strengths = getStrengths();
  const improvements = getImprovements();
  const summary = coachingSummary?.summary;

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
                  {strengths ? (
                    <ul className="list-disc list-inside space-y-2">
                      {Array.isArray(strengths) ? (
                        strengths.map((strength: string, i: number) => (
                          <li key={i}>{strength}</li>
                        ))
                      ) : (
                        <p>{String(strengths)}</p>
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
                  {improvements ? (
                    <ul className="list-disc list-inside space-y-2">
                      {Array.isArray(improvements) ? (
                        improvements.map((area: string, i: number) => (
                          <li key={i}>{area}</li>
                        ))
                      ) : (
                        <p>{String(improvements)}</p>
                      )}
                    </ul>
                  ) : (
                    <p className="text-gray-500 italic">No improvement data available</p>
                  )}
                </div>
                
                {/* Summary/Overall Assessment */}
                <div>
                  <h3 className="text-xl font-semibold text-interview-secondary mb-3">
                    Recommendations
                  </h3>
                  {summary ? (
                    <p className="text-gray-700">{summary}</p>
                  ) : (
                    <p className="text-gray-500 italic">No recommendations available</p>
                  )}
                </div>
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
                {/* Display Job Role */}
                <div className="col-span-1 md:col-span-2 border rounded-lg p-4">
                  <h4 className="font-medium">Job Role</h4>
                  <p className="text-lg">{skillProfile?.job_role || "[Not Specified]"}</p>
                </div>
                
                {/* Display Assessed Skills */}
                <div className="col-span-1 md:col-span-2 border rounded-lg p-4">
                  <h4 className="font-medium">Assessed Skills</h4>
                  {skillProfile?.assessed_skills && skillProfile.assessed_skills.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                      {skillProfile.assessed_skills.map((skill: any, index: number) => (
                        <div key={index} className="border rounded-lg p-3">
                          <div className="flex justify-between items-center">
                            <h5 className="font-medium">{skill.skill_name}</h5>
                            <Badge className="bg-interview-secondary">
                              {skill.proficiency_level || "Not Assessed"}
                            </Badge>
                          </div>
                          {skill.category && (
                            <p className="text-sm text-gray-500 mt-1">Category: {skill.category}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 italic mt-2">No skill assessment data available</p>
                  )}
                </div>
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

export default InterviewResults;
