import { useState } from 'react';
import { useAppContext } from '../src/context/AppContext';
import { postJson } from '../src/services/api'; // Use postJson now as we send config data, not FormData

export default function SetupForm() {
  // Global context
  const {
    isLoading, 
    setIsLoading, 
    setError, 
    clearError,
    setSessionId, 
    setJobContext, 
    setIsSessionActive,
    addMessageToHistory // Need to add initial agent message
  } = useAppContext();

  // Local state for form inputs
  const [jobRole, setJobRoleLocal] = useState('');
  const [jobDescription, setJobDescriptionLocal] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jobRole.trim()) {
      setError('Job Role is required.');
      return;
    }
    
    clearError();
    setIsLoading(true);
    setIsSessionActive(false); // Reset session active status
    setSessionId(null); // Reset session ID

    // Construct the InterviewConfig object for the backend
    const interviewConfig = {
      job_role: jobRole,
      job_description: jobDescription || null, // Send null if empty
      // resume_content: null, // Cannot handle resume file upload with this endpoint
      // Add other potential InterviewConfig fields if needed, with defaults
      interview_style: "formal", // Use lowercase value expected by backend Enum
      question_count: 5,        // Example default
      difficulty_level: "medium", // Example default
      // user_id: null // Let backend handle user ID if applicable
    };

    try {
      // Call the correct endpoint with postJson
      const response = await postJson('/api/interview/start', interviewConfig);
      
      if (response && response.session_id) {
        // Update global context
        setJobContext({ role: jobRole, description: jobDescription, resume: null }); // Resume is null now
        setSessionId(response.session_id);
        setIsSessionActive(true);
        console.log("Session started with ID:", response.session_id);

        // Handle initial message from agent
        if (response.initial_message && response.initial_message.content) {
            addMessageToHistory({ 
                role: response.initial_message.role || 'agent', 
                content: response.initial_message.content 
            });
        }

        console.log("Setup successful, initial message added (if any).");
        // TODO: Implement scrolling to interview section
        // This might involve calling a function passed via props or context
        // Example: props.onSessionStart(); 
      } else {
        // Handle cases where response might be missing session_id
        throw new Error(response?.detail || 'Failed to start session. Invalid response from server.');
      }

    } catch (error) {
      console.error("Error starting interview session:", error);
      setError(error.message || 'Failed to start interview session. Check network or server.');
      setIsSessionActive(false); // Ensure session is marked inactive on error
      setSessionId(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container-custom">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12 slide-up">
          <h2 className="text-3xl font-bold mb-4">Interview Setup</h2>
          <p className="text-shaga-secondary">Configure your interview parameters</p>
        </div>
        
        <form onSubmit={handleSubmit} className="card p-6 slide-up animation-delay-200">
          <div className="space-y-6">
            {/* Job Role Input */}
            <div>
              <label htmlFor="jobRole" className="block text-sm font-medium text-shaga-secondary mb-1">
                Job Role <span className="text-accent-yellow">*</span>
              </label>
              <input 
                id="jobRole"
                type="text" 
                value={jobRole} 
                onChange={(e) => setJobRoleLocal(e.target.value)} 
                placeholder="e.g. Software Engineer, Product Manager" 
                className="input-field" 
                required
                disabled={isLoading}
              />
            </div>
            
            {/* Job Description Input */}
            <div>
              <label htmlFor="jobDescription" className="block text-sm font-medium text-shaga-secondary mb-1">
                Job Description (Optional)
              </label>
              <textarea 
                id="jobDescription"
                value={jobDescription} 
                onChange={(e) => setJobDescriptionLocal(e.target.value)} 
                placeholder="Paste the job description here..." 
                className="input-field min-h-[120px]"
                rows={4}
                disabled={isLoading}
              />
            </div>
            
            {/* Resume Upload Input - REMOVED */}
            {/* 
            <div>
              <label htmlFor="resume" className="block text-sm font-medium text-shaga-secondary mb-1">
                Upload Resume (PDF or DOCX, Optional)
              </label>
              <input 
                id="resume"
                type="file" 
                onChange={handleFileChange} 
                accept=".pdf, .docx, application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document" 
                className="file-input"
                disabled={isLoading}
              />
              {fileName && (
                <p className="mt-2 text-sm text-accent-yellow">
                  Selected file: {fileName}
                </p>
              )}
            </div>
            */}
            
            {/* Submit Button */}
            <div className="pt-4">
              <button 
                type="submit" 
                className="btn-accent w-full"
                disabled={isLoading || !jobRole.trim()}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    {/* Simple SVG Spinner */}
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Starting Session...
                  </span>
                ) : (
                  'Start Interview Session'
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
} 