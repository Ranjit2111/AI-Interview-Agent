import { useEffect } from 'react';
import { useAppContext } from '../src/context/AppContext';
import { getJson } from '../src/services/api'; // Use getJson

export default function FeedbackDisplay() {
  const {
    sessionId, 
    isLoading, 
    setIsLoading, 
    error, 
    setError, 
    clearError,
    feedbackData, // This will now hold the SkillProfile structure
    setFeedbackData, 
    isSessionActive, 
    jobContext // Get job role for display
  } = useAppContext();

  // Function to fetch skill profile
  const fetchSkillProfile = async () => {
    if (!sessionId) {
      setFeedbackData(null);
      return;
    }

    console.log(`Fetching skill profile for session: ${sessionId}`);
    clearError();
    setIsLoading(true);
    setFeedbackData(null); 

    try {
      // Call the correct endpoint: /api/interview/skill-profile?session_id=...
      const endpoint = `/api/interview/skill-profile?session_id=${encodeURIComponent(sessionId)}`;
      const response = await getJson(endpoint);
      
      // Expects SkillProfile format: { job_role: str, assessed_skills: List[Dict] }
      if (response && Array.isArray(response.assessed_skills)) {
        setFeedbackData(response); 
        console.log("Skill profile data received:", response);
      } else {
        // Handle cases where response is empty or not in expected format
        console.warn("Received unexpected skill profile format or empty data:", response);
        // Set feedbackData to an empty state or specific structure to indicate no skills found
        setFeedbackData({ job_role: jobContext?.role || 'N/A', assessed_skills: [] }); 
        // Optionally set an error: setError("Could not retrieve valid skill profile data.");
      }

    } catch (error) {
      console.error("Error fetching skill profile:", error);
      setError(error.message || 'Failed to fetch skill profile. Check network or server.');
      setFeedbackData(null); 
    } finally {
      setIsLoading(false);
    }
  };

  // Render individual skill assessment 
  const renderSkillAssessment = (skill, index) => {
    // Determine color based on score (example logic)
    const score = skill.score || 0; // Assuming score is 0-1
    let colorClass = 'bg-gray-500';
    if (score >= 0.8) colorClass = 'bg-accent-green';
    else if (score >= 0.6) colorClass = 'bg-accent-yellow';
    else if (score >= 0.4) colorClass = 'bg-orange-500';
    else colorClass = 'bg-red-600';

    const percentage = Math.max(0, Math.min(100, score * 100));

    return (
      <div key={index} className="p-4 bg-dark-600 rounded-md">
        <h4 className="text-md font-semibold text-shaga-primary mb-2">{skill.skill_name || `Skill ${index + 1}`}</h4>
        <div className="w-full bg-dark-400 rounded-full h-3 mb-1">
          <div 
            className={`${colorClass} h-3 rounded-full transition-all duration-500 ease-out`} 
            style={{ width: `${percentage}%` }}
            title={`${percentage.toFixed(0)}%`}
          ></div>
        </div>
        <p className="text-sm text-shaga-secondary mt-2">{skill.assessment || "No assessment details available."}</p>
        {/* TODO: Add button/link to fetch resources for this skill? */}
        {/* <button className="text-xs text-accent-blue hover:underline mt-1">Find resources</button> */}
      </div>
    );
  };

  return (
    <div className="container-custom">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12 slide-up">
          <h2 className="text-3xl font-bold mb-4">Interview Feedback</h2>
          <p className="text-shaga-secondary">Review your skill assessment based on the interview</p>
        </div>

        {/* Button to manually fetch feedback */}
        {sessionId && (
             <div className="text-center mb-8">
                <button 
                    onClick={fetchSkillProfile} // Changed function name
                    className="btn-outline"
                    disabled={isLoading}
                >
                    {isLoading ? 'Loading Skill Profile...' : 'Get Skill Profile'} 
                </button>
             </div>
        )}
        
        {isLoading && !feedbackData && (
            <div className="card p-6 text-center slide-up animation-delay-200">
                <p className="text-shaga-secondary">Loading skill assessment...</p>
            </div>
        )}

        {!isLoading && feedbackData ? (
          <div className="card p-6 slide-up animation-delay-200">
            <h3 className="text-lg font-medium text-accent-yellow mb-4">
                Skill Assessment for: {feedbackData.job_role || jobContext?.role || 'Selected Role'}
            </h3>
            
            {feedbackData.assessed_skills && feedbackData.assessed_skills.length > 0 ? (
              <div className="space-y-4">
                {feedbackData.assessed_skills.map(renderSkillAssessment)}
              </div>
            ) : (
              <p className="text-shaga-secondary text-center py-4">No specific skills assessed or assessment data available for this session.</p>
            )}
            
            {/* Optionally display summary if it comes with skill profile? */}
            {/* {feedbackData.summary && (...) } */}
          </div>
        ) : !isLoading && (
          <div className="card p-6 text-center slide-up animation-delay-200">
            <p className="text-shaga-secondary mb-4">No skill assessment available. Complete an interview and click 'Get Skill Profile'.</p>
          </div>
        )}
      </div>
    </div>
  );
} 