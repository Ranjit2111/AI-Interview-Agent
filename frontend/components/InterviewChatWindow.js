import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { useAppContext } from '../src/context/AppContext';
import { postJson } from '../src/services/api'; // Use postJson

// Dynamically import client-only components
const DynamicCameraView = dynamic(() => import('./CameraView'), { ssr: false });
// Remove dynamic imports for speech components as they are no longer used
// const DynamicSpeechInput = dynamic(() => import('./SpeechInput'), { ssr: false });
// const DynamicSpeechOutput = dynamic(() => import('./SpeechOutput'), { ssr: false });

export default function InterviewChatWindow() {
  // Global context
  const {
    sessionId,
    isLoading,
    setIsLoading,
    error,
    setError,
    clearError,
    conversationHistory,
    addMessageToHistory,
    isSessionActive
  } = useAppContext();

  // Local state
  const [userInput, setUserInput] = useState('');
  // Remove speech-related state
  // const [useSpeechInput, setUseSpeechInput] = useState(false);
  // const [useSpeechOutput, setUseSpeechOutput] = useState(false);
  // const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Scroll to bottom of chat history when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversationHistory]);

  // Remove speech input handler
  // const handleSpeechInput = (transcript) => {
  //   if (transcript.trim() && !isLoading) {
  //     setUserInput(transcript);
  //     handleSubmit(transcript);
  //   }
  // };

  const handleSubmit = async (inputText) => {
    const textToSubmit = (typeof inputText === 'string' ? inputText : userInput).trim();

    if (!isSessionActive || !sessionId) {
      setError("Interview session is not active. Please start a new session.");
      return;
    }
    if (!textToSubmit) {
      setError("Please enter a response.");
      return;
    }

    clearError();
    setIsLoading(true);
    addMessageToHistory({ role: 'user', content: textToSubmit });
    setUserInput(''); // Clear input field immediately

    // Construct the UserMessage object for the backend
    const userMessage = {
        message: textToSubmit,
        session_id: sessionId,
        // user_id: userIdFromContext // Pass if available and required by backend
    };

    try {
      // Call the correct endpoint with postJson and the correct body structure
      const response = await postJson('/api/interview/send', userMessage);

      // Handle AgentResponse format
      if (response && response.content) {
        addMessageToHistory({
            role: response.role || 'agent', // Use role from response
            content: response.content
            // Add other fields from AgentResponse if needed (e.g., agent name)
        });
      } else {
        throw new Error(response?.detail || 'Invalid response from agent.');
      }

    } catch (error) {
      console.error("Error sending message:", error);
      setError(error.message || 'Failed to send message. Check network or server.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle form submission via button or Enter key
  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSubmit(userInput);
  };

  return (
    <div className="w-full max-w-4xl bg-dark-800 rounded-lg shadow-xl p-6">
      <h2 className="text-2xl font-bold mb-6 text-center text-shaga-primary">Interview Session</h2>
      {!isSessionActive ? (
        <div className="text-center p-8 bg-dark-700 rounded-lg">
          <p className="text-shaga-secondary mb-4">No active interview session.</p>
          <p className="text-shaga-secondary">Please go to the Setup section to start.</p>
          {/* Optional: Add a button to scroll back to setup */}
        </div>
      ) : (
        <div className="flex flex-col md:flex-row gap-6">
          {/* Video feed column */}
          <div className="w-full md:w-1/3">
             <div className="h-64 md:h-auto bg-dark-700 rounded-lg overflow-hidden relative border border-dark-600">
              {isClient ? <DynamicCameraView /> :
                <div className="absolute inset-0 flex items-center justify-center">
                    <p className="text-shaga-secondary\">Loading Camera...</p>
                </div>
              }
              {/* Simple overlay/label */}
              <div className="absolute top-2 left-2 bg-black bg-opacity-50 px-2 py-1 rounded text-xs text-accent-green\">LIVE</div>
            </div>
          </div>

          {/* Interview content column */}
          <div className="w-full md:w-2/3 flex flex-col">
            {/* Response/Chat History Area */}
            <div className="flex-grow mb-6 bg-dark-700 rounded-lg p-4 overflow-y-auto max-h-80 md:max-h-96 min-h-[200px]">
              {conversationHistory.length === 0 && !isLoading && (
                  <p className="text-shaga-muted italic text-center py-4\">The interview will begin shortly...</p>
              )}
              {conversationHistory.map((msg, index) => (
                <div key={index} className={`mb-4 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                  <span className={`inline-block px-4 py-2 rounded-lg ${msg.role === 'user' ? 'bg-accent-blue text-white' : 'bg-dark-600 text-shaga-primary'}`}>
                    {msg.content}
                  </span>
                  {/* Remove SpeechOutput rendering */}
                  {/* {msg.role === 'agent' && isClient && useSpeechOutput && (
                    <div className="mt-2 text-left">
                       <DynamicSpeechOutput
                          text={msg.content}
                          onPlay={() => setIsAudioPlaying(true)}
                          onEnd={() => setIsAudioPlaying(false)}
                          // backendUrl={BACKEND_URL} // Pass backend URL if needed by component
                        />
                    </div>
                  )} */}
                </div>
              ))}
              {isLoading && conversationHistory.length > 0 && (
                  <div className="text-left">
                      <span className="inline-block px-4 py-2 rounded-lg bg-dark-600 text-shaga-muted italic">
                          Agent is typing...
                      </span>
                  </div>
              )}
              {/* Invisible element to scroll to */}
              <div ref={chatEndRef} />
            </div>

            {/* Input area with speech options */}
            <div className="bg-dark-700 rounded-lg p-4">
              <form onSubmit={handleFormSubmit} className="space-y-4">
                {/* Remove Speech Toggles */}
                {/* <div className="flex items-center justify-start space-x-4 mb-2"> ... toggles removed ... </div> */}

                {/* Always show Text Input */}
                <textarea
                  className="input-field w-full"
                  rows="3"
                  placeholder="Type your response here..."
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  disabled={isLoading /* Remove || isAudioPlaying */}
                ></textarea>

                {/* Always show Submit Button */}
                <button
                  type="submit"
                  className="btn-accent w-full md:w-auto"
                  disabled={isLoading || !userInput.trim() /* Remove || isAudioPlaying */}
                >
                  {isLoading ? 'Processing...' : 'Send Response'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 