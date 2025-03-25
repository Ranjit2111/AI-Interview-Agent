import { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import dynamic from 'next/dynamic';
import Link from 'next/link';

// Dynamic imports for client-only components
const DynamicCameraView = dynamic(() => import('../components/CameraView'), { ssr: false });
const DynamicSpeechInput = dynamic(() => import('../components/SpeechInput'), { ssr: false });
const DynamicSpeechOutput = dynamic(() => import('../components/SpeechOutput'), { ssr: false });
const DynamicChatWindow = dynamic(() => import('../components/ChatWindow'), { ssr: false });
const DynamicUserContextForm = dynamic(() => import('../components/UserContextForm'), { ssr: false });
const DynamicCoachFeedback = dynamic(() => import('../components/CoachFeedback'), { ssr: false });
const DynamicTranscriptManager = dynamic(() => import('../components/TranscriptManager'), { ssr: false });

// Set default to localhost if not specified in environment variables
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Home() {
  // App state
  const [activeSection, setActiveSection] = useState('user-context');
  const [navbarVisible, setNavbarVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isClient, setIsClient] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  
  // Session state
  const [sessionId, setSessionId] = useState(null);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Interview state
  const [messages, setMessages] = useState([]);
  const [isMessageLoading, setIsMessageLoading] = useState(false);
  
  // Media settings
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [microphoneEnabled, setMicrophoneEnabled] = useState(false);
  const [speakerEnabled, setSpeakerEnabled] = useState(true);
  
  // Coach feedback
  const [feedback, setFeedback] = useState([]);
  const [transcript, setTranscript] = useState([]);
  
  // Skill assessment
  const [skills, setSkills] = useState([]);
  const [selectedSkill, setSelectedSkill] = useState(null);
  
  // Refs for section scrolling
  const sectionsRef = useRef({});

  // Set isClient to true when component mounts
  useEffect(() => {
    setIsClient(true);
    
    // Check user preference for dark mode
    if (typeof window !== 'undefined') {
      const savedDarkMode = localStorage.getItem('darkMode') === 'true';
      setDarkMode(savedDarkMode);
      if (savedDarkMode) {
        document.documentElement.classList.add('dark');
      }
    }
  }, []);

  // Handle scroll events for navbar visibility and active section
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // Handle navbar visibility
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        setNavbarVisible(false);
      } else {
        setNavbarVisible(true);
      }
      
      setLastScrollY(currentScrollY);
      
      // Handle active section based on scroll position
      Object.entries(sectionsRef.current).forEach(([key, section]) => {
        if (section) {
          const rect = section.getBoundingClientRect();
          if (rect.top <= 200 && rect.bottom >= 200) {
            setActiveSection(key);
          }
        }
      });
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  // Toggle dark mode
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (typeof window !== 'undefined') {
      localStorage.setItem('darkMode', (!darkMode).toString());
      if (!darkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
  };

  // Scroll to a specific section
  const scrollToSection = (sectionId) => {
    sectionsRef.current[sectionId]?.scrollIntoView({ behavior: 'smooth' });
    setActiveSection(sectionId);
  };

  // Start a new interview session with context data
  const handleStartSession = async (contextData) => {
    setIsLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/sessions/start`, {
        method: 'POST',
        body: contextData, // FormData object with job title, description, resume, etc.
      });
      
      if (!response.ok) {
        throw new Error(`Failed to start session: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSessionId(data.sessionId);
      setIsSessionActive(true);
      
      // Add initial system message
      setMessages([{
        type: 'system',
        text: 'Interview session started. The interviewer will begin shortly.',
        timestamp: new Date().toISOString()
      }]);
      
      // Scroll to interview section
      scrollToSection('interview');
      
    } catch (error) {
      console.error('Error starting interview session:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Send a message to the interviewer
  const handleSendMessage = async (messageText) => {
    if (!sessionId || !messageText.trim()) return;
    
    // Add user message to the chat
    const userMessage = {
      type: 'user',
      text: messageText,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsMessageLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/sessions/${sessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageText }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Add interviewer message to the chat
      const interviewerMessage = {
        type: 'interviewer',
        text: data.response,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, interviewerMessage]);
      
      // Update transcript for coach to analyze
      setTranscript(prev => [...prev, 
        { id: userMessage.timestamp, speaker: 'user', text: userMessage.text },
        { id: interviewerMessage.timestamp, speaker: 'interviewer', text: interviewerMessage.text }
      ]);
      
      // Check for new feedback from coach
      if (data.feedback) {
        setFeedback(prev => [...prev, ...data.feedback]);
      }
      
      // Update skills assessment if provided
      if (data.skills) {
        setSkills(data.skills);
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message to chat
      setMessages(prev => [...prev, {
        type: 'system',
        text: `Error: ${error.message}. Please try again.`,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsMessageLoading(false);
    }
  };

  // Speech input handler
  const handleSpeechInput = (transcript) => {
    if (transcript.trim()) {
      handleSendMessage(transcript);
    }
  };

  // Handle microphone toggle
  const handleMicrophoneToggle = (isEnabled) => {
    setMicrophoneEnabled(isEnabled);
  };

  // End the current interview session
  const handleEndSession = async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/sessions/${sessionId}/end`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to end session: ${response.statusText}`);
      }
      
      // Add system message about session ending
      setMessages(prev => [...prev, {
        type: 'system',
        text: 'Interview session ended. You can view your feedback and skill assessment below.',
        timestamp: new Date().toISOString()
      }]);
      
      setIsSessionActive(false);
      
      // Scroll to feedback section
      scrollToSection('feedback');
      
    } catch (error) {
      console.error('Error ending session:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Select a skill to view details
  const handleSkillSelect = (skill) => {
    setSelectedSkill(skill);
    scrollToSection('skills');
  };

  return (
    <div className={`min-h-screen flex flex-col ${darkMode ? 'dark' : ''}`}>
      <Head>
        <title>AI Interview Agent</title>
        <meta name="description" content="Practice job interviews with AI coaching and skill assessment" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Navigation Bar */}
      <header className={`bg-white dark:bg-gray-900 shadow-md transition-all duration-300 ease-in-out fixed w-full z-50 ${navbarVisible ? 'translate-y-0' : '-translate-y-full'}`}>
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center">
            <span className="text-xl font-bold text-gray-900 dark:text-white">AI Interview Agent</span>
          </div>
          
          <nav className="hidden md:flex items-center space-x-6">
            <button
              onClick={() => scrollToSection('user-context')}
              className={`px-3 py-2 rounded-md transition-colors ${activeSection === 'user-context' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
            >
              Job Context
            </button>
            
            <button
              onClick={() => scrollToSection('interview')}
              className={`px-3 py-2 rounded-md transition-colors ${activeSection === 'interview' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
              disabled={!isSessionActive && !sessionId}
            >
              Interview
            </button>
            
            <button
              onClick={() => scrollToSection('feedback')}
              className={`px-3 py-2 rounded-md transition-colors ${activeSection === 'feedback' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
              disabled={!sessionId}
            >
              Coach Feedback
            </button>
            
            <button
              onClick={() => scrollToSection('skills')}
              className={`px-3 py-2 rounded-md transition-colors ${activeSection === 'skills' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
              disabled={!sessionId}
            >
              Skill Assessment
            </button>
            
            <button
              onClick={() => scrollToSection('transcript')}
              className={`px-3 py-2 rounded-md transition-colors ${activeSection === 'transcript' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
              disabled={!sessionId}
            >
              Transcript
            </button>
          </nav>
          
          <div className="flex items-center">
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-full text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none"
              aria-label="Toggle dark mode"
            >
              {darkMode ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow pt-16 bg-gray-50 dark:bg-gray-900">
        {/* User Context Section */}
      <section 
          id="user-context-section" 
          className="min-h-screen py-16 px-4"
          ref={el => sectionsRef.current['user-context'] = el}
        >
          <div className="container mx-auto max-w-4xl">
            <h1 className="text-3xl font-bold text-center mb-12 text-gray-900 dark:text-white">
              Prepare for Your Interview
              </h1>
            
            {isClient && (
              <DynamicUserContextForm 
                onSubmit={handleStartSession} 
                isLoading={isLoading}
              />
            )}
          </div>
        </section>
        
        {/* Interview Section */}
        <section 
          id="interview-section" 
          className="min-h-screen py-16 px-4 bg-gray-100 dark:bg-gray-800"
          ref={el => sectionsRef.current['interview'] = el}
        >
          <div className="container mx-auto max-w-5xl">
            <h2 className="text-2xl font-bold mb-8 text-gray-900 dark:text-white">
              Interview Session
            </h2>
            
            {!sessionId ? (
              <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md p-8 text-center">
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  Please set up your job details first before starting the interview.
                </p>
                <button 
                  onClick={() => scrollToSection('user-context')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Go to Job Setup
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[70vh]">
                {/* Camera View */}
                <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md overflow-hidden lg:col-span-1">
                  <div className="h-full flex flex-col">
                    <div className="p-3 border-b border-gray-200 dark:border-gray-600 flex justify-between items-center">
                      <h3 className="font-medium text-gray-900 dark:text-white">Camera</h3>
                    </div>
                    <div className="flex-grow relative">
                      {isClient && (
                        <DynamicCameraView autoStart={false} />
                      )}
                    </div>
                    <div className="p-3 border-t border-gray-200 dark:border-gray-600 flex justify-center items-center space-x-4">
                      {isClient && (
                        <DynamicSpeechInput
                          onSpeechResult={handleSpeechInput}
                          onListeningChange={handleMicrophoneToggle}
                          autoStart={false}
                        />
                      )}
              </div>
            </div>
                </div>
                
                {/* Chat Window */}
                <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md overflow-hidden lg:col-span-2">
                  <div className="h-full">
                    {isClient && (
                      <DynamicChatWindow
                        messages={messages}
                        onSendMessage={handleSendMessage}
                        isLoading={isMessageLoading}
                      />
                    )}
              </div>
                </div>
              </div>
            )}
            
            {/* Interview Controls */}
            {sessionId && (
              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleEndSession}
                  disabled={isLoading || !isSessionActive}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  End Interview
                </button>
              </div>
            )}
          </div>
        </section>
        
        {/* Coach Feedback Section */}
      <section 
          id="feedback-section" 
          className="min-h-screen py-16 px-4"
          ref={el => sectionsRef.current['feedback'] = el}
        >
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-2xl font-bold mb-8 text-gray-900 dark:text-white">
              Coach Feedback
            </h2>
            
            {!sessionId ? (
              <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md p-8 text-center">
                <p className="text-gray-600 dark:text-gray-300">
                  Complete an interview session to receive coach feedback.
                </p>
                </div>
            ) : (
              <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md p-6 h-[70vh]">
                {isClient && (
                  <DynamicCoachFeedback
                    feedback={feedback}
                    transcript={transcript}
                    isLoading={false}
                  />
                )}
              </div>
            )}
        </div>
      </section>

        {/* Skill Assessment Section */}
      <section 
          id="skills-section" 
          className="min-h-screen py-16 px-4 bg-gray-100 dark:bg-gray-800"
          ref={el => sectionsRef.current['skills'] = el}
        >
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-2xl font-bold mb-8 text-gray-900 dark:text-white">
              Skill Assessment
            </h2>
            
            {!sessionId ? (
              <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md p-8 text-center">
                <p className="text-gray-600 dark:text-gray-300">
                  Complete an interview session to receive skill assessments.
                </p>
              </div>
            ) : skills.length === 0 ? (
              <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md p-8 text-center">
                <p className="text-gray-600 dark:text-gray-300">
                  No skill assessments available yet. Continue with the interview to receive feedback.
                </p>
                  </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {skills.map((skill, index) => (
                  <div 
                    key={index}
                    className="bg-white dark:bg-gray-700 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => handleSkillSelect(skill)}
                  >
                    <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">{skill.name}</h3>
                    <div className="mb-3">
                      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5">
                        <div 
                          className="bg-blue-600 h-2.5 rounded-full" 
                          style={{ width: `${(skill.proficiency / 5) * 100}%` }}
                        ></div>
                      </div>
                      <div className="flex justify-between mt-1 text-sm text-gray-600 dark:text-gray-400">
                        <span>Beginner</span>
                        <span>Expert</span>
              </div>
                    </div>
                    <p className="text-gray-600 dark:text-gray-300 text-sm line-clamp-3">{skill.summary}</p>
                  </div>
                ))}
              </div>
            )}
            
            {/* Selected Skill Details */}
            {selectedSkill && (
              <div className="mt-8 bg-white dark:bg-gray-700 rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white">{selectedSkill.name}</h3>
                  <button
                    onClick={() => setSelectedSkill(null)}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
            </div>
            
                <div className="mb-4">
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5 mb-1">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full" 
                      style={{ width: `${(selectedSkill.proficiency / 5) * 100}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                    <span>Level: {selectedSkill.proficiency}/5</span>
                    <span>{selectedSkill.proficiency < 3 ? 'Needs Improvement' : selectedSkill.proficiency < 4 ? 'Competent' : 'Excellent'}</span>
                    </div>
                  </div>
                  
                <div className="mb-6">
                  <h4 className="font-medium mb-2 text-gray-800 dark:text-gray-200">Assessment</h4>
                  <p className="text-gray-600 dark:text-gray-300">{selectedSkill.assessment}</p>
                    </div>
                
                {selectedSkill.resources && selectedSkill.resources.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2 text-gray-800 dark:text-gray-200">Learning Resources</h4>
                    <ul className="space-y-2">
                      {selectedSkill.resources.map((resource, index) => (
                        <li key={index} className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                          <a 
                            href={resource.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 dark:text-blue-400 hover:underline flex items-start"
                          >
                            <svg className="w-5 h-5 mr-2 text-gray-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                            </svg>
                            <div>
                              <span className="font-medium">{resource.title}</span>
                              <p className="text-sm text-gray-600 dark:text-gray-400">{resource.description}</p>
                    </div>
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
                </div>
        </section>
        
        {/* Transcript Section */}
        <section 
          id="transcript-section" 
          className="min-h-screen py-16 px-4"
          ref={el => sectionsRef.current['transcript'] = el}
        >
          <div className="container mx-auto max-w-5xl">
            <h2 className="text-2xl font-bold mb-8 text-gray-900 dark:text-white">
              Interview Transcript
            </h2>
            
            {!sessionId ? (
              <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md p-8 text-center">
                <p className="text-gray-600 dark:text-gray-300">
                  Complete an interview session to access and manage transcripts.
                </p>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-700 rounded-lg shadow-md overflow-hidden">
                {isClient && (
                  <DynamicTranscriptManager />
                )}
              </div>
            )}
        </div>
      </section>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 py-6">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <p className="text-gray-600 dark:text-gray-400">
                © {new Date().getFullYear()} AI Interview Agent. All rights reserved.
              </p>
            </div>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                Privacy Policy
              </a>
              <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                Terms of Service
              </a>
              <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
