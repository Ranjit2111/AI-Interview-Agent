import { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import dynamic from 'next/dynamic';

// Set default to localhost if not specified in environment variables
// IMPORTANT: This ensures we ALWAYS use localhost for this local project
const BACKEND_URL = "http://localhost:8000";
console.log("Using backend URL:", BACKEND_URL);

// Dynamically import a client-only component with no SSR
const DynamicCameraView = dynamic(
  () => import('../components/CameraView'),
  { ssr: false }
);

export default function Home() {
  const [userInput, setUserInput] = useState('');
  const [response, setResponse] = useState('');
  const [jobRole, setJobRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [resume, setResume] = useState(null);
  const [audioFeedback, setAudioFeedback] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('home');
  const [fileName, setFileName] = useState('');
  const [navbarVisible, setNavbarVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isClient, setIsClient] = useState(false);
  
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const sectionsRef = useRef({});

  // Set isClient to true when component mounts
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Handle scroll events for parallax and navbar visibility
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
      
      // Handle active section
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

  const handleSubmitContext = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    const formData = new FormData();
    formData.append('job_role', jobRole);
    formData.append('job_description', jobDescription);
    if (resume) {
      formData.append('resume_file', resume);
    }

    try {
      const res = await fetch(`${BACKEND_URL}/submit-context`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        console.error("Error submitting job context:", res.statusText);
        alert(`Error submitting job context: ${res.statusText}`);
      } else {
        // Scroll to interview section
        sectionsRef.current.interview?.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (error) {
      console.error("Error submitting job context:", error);
      alert(`Network error: ${error.message}. Make sure the backend server is running.`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitInterview = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const res = await fetch(`${BACKEND_URL}/generate-interview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_input: userInput, job_role: jobRole, job_description: jobDescription }),
      });

      if (!res.ok) {
        console.error("Error generating interview:", res.statusText);
        alert(`Error generating interview: ${res.statusText}`);
        return;
      }

      const data = await res.json();
      setResponse(data.generated_text);
    } catch (error) {
      console.error("Error generating interview:", error);
      alert(`Network error: ${error.message}. Make sure the backend server is running.`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAudioSubmit = async (audioBlob) => {
    setIsLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob);

      const res = await fetch(`${BACKEND_URL}/process-audio`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        console.error("Error processing audio:", res.statusText);
        alert(`Error processing audio: ${res.statusText}`);
        return;
      }

      const data = await res.json();
      setAudioFeedback(`${BACKEND_URL}${data.audio_url}`);
    } catch (error) {
      console.error("Error processing audio:", error);
      alert(`Network error: ${error.message}. Make sure the backend server is running.`);
    } finally {
      setIsLoading(false);
    }
  };

  const startRecording = async () => {
    if (isRecording) return;

    setIsRecording(true);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await handleAudioSubmit(audioBlob);
      };

      mediaRecorderRef.current.start();
    } catch (error) {
      console.error("Error starting recording:", error);
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (!isRecording) return;

    mediaRecorderRef.current.stop();
    setIsRecording(false);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setResume(file);
      setFileName(file.name);
    }
  };

  const scrollToSection = (sectionId) => {
    sectionsRef.current[sectionId]?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen">
      <Head>
        <title>AI Interview Coach | Advanced Interview Training</title>
        <meta name="description" content="AI-powered interview coaching with real-time feedback and analysis" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Navbar */}
      <nav className={`navbar ${navbarVisible ? 'navbar-visible' : 'navbar-hidden'}`}>
        <div className="container-custom py-4 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-xl font-bold tracking-wider text-accent-yellow">:AI·COACH</h1>
            <div className="hidden md:flex space-x-6">
              <button 
                onClick={() => scrollToSection('home')} 
                className={`nav-link ${activeSection === 'home' ? 'nav-link-active' : ''}`}
              >
                :HOME
              </button>
              <button 
                onClick={() => scrollToSection('setup')} 
                className={`nav-link ${activeSection === 'setup' ? 'nav-link-active' : ''}`}
              >
                :SETUP
              </button>
              <button 
                onClick={() => scrollToSection('interview')} 
                className={`nav-link ${activeSection === 'interview' ? 'nav-link-active' : ''}`}
              >
                :INTERVIEW
              </button>
              <button 
                onClick={() => scrollToSection('feedback')} 
                className={`nav-link ${activeSection === 'feedback' ? 'nav-link-active' : ''}`}
              >
                :FEEDBACK
              </button>
            </div>
          </div>
          <div>
            <span className="text-xs text-shaga-muted tracking-widest">©AI·COACH</span>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section 
        ref={el => sectionsRef.current.home = el}
        className="section min-h-screen flex items-center relative overflow-hidden"
        style={{ paddingTop: '80px' }}
      >
        <div className="container-custom relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="fade-in">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
                <span className="text-accent-yellow">AI</span> Interview
                <br />Coach
              </h1>
              <p className="text-shaga-secondary text-lg mb-8 max-w-lg">
                Advanced interview training powered by AI. Practice with real-time feedback and analysis to ace your next interview.
              </p>
              <div className="flex flex-wrap gap-4">
                <button 
                  onClick={() => scrollToSection('setup')} 
                  className="btn-accent"
                >
                  Start Training
                </button>
                <button 
                  onClick={() => scrollToSection('feedback')} 
                  className="btn-outline"
                >
                  View Feedback
                </button>
              </div>
            </div>
            <div className="camera-container fade-in animation-delay-200">
              {isClient ? <DynamicCameraView /> : 
                <div className="w-full h-full flex items-center justify-center bg-dark-800">
                  <p className="text-shaga-secondary">Camera loading...</p>
                </div>
              }
              <div className="absolute inset-0 border border-accent-yellow pointer-events-none"></div>
              <div className="absolute top-4 left-4 flex items-center">
                <div className="w-2 h-2 rounded-full bg-accent-green mr-2 animate-pulse"></div>
                <span className="text-xs text-shaga-secondary uppercase tracking-wider">Live Camera</span>
              </div>
              <div className="absolute bottom-4 left-4">
                <div className="text-xs text-shaga-secondary uppercase tracking-wider">
                  Compatible with<br />all devices
                </div>
              </div>
              <div className="absolute bottom-4 right-4">
                <div className="text-xs text-shaga-secondary uppercase tracking-wider">
                  AI·COACH
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Parallax background elements */}
        <div 
          className="parallax-layer" 
          style={{ 
            transform: `translateY(${typeof window !== 'undefined' ? window.scrollY * 0.1 : 0}px)`,
            backgroundImage: 'radial-gradient(circle at 20% 30%, rgba(255, 204, 0, 0.05) 0%, transparent 50%)'
          }}
        ></div>
        <div 
          className="parallax-layer" 
          style={{ 
            transform: `translateY(${typeof window !== 'undefined' ? window.scrollY * 0.2 : 0}px)`,
            backgroundImage: 'radial-gradient(circle at 80% 70%, rgba(0, 204, 255, 0.05) 0%, transparent 50%)'
          }}
        ></div>
      </section>

      {/* Setup Section */}
      <section 
        ref={el => sectionsRef.current.setup = el}
        className="section bg-dark-800"
      >
        <div className="container-custom">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-12 slide-up">
              <h2 className="text-3xl font-bold mb-4">Interview Setup</h2>
              <p className="text-shaga-secondary">Configure your interview parameters</p>
            </div>
            
            <form onSubmit={handleSubmitContext} className="card p-6 slide-up animation-delay-200">
              <div className="space-y-6">
                <div>
                  <label htmlFor="jobRole" className="block text-sm font-medium text-shaga-secondary mb-1">
                    Job Role <span className="text-accent-yellow">*</span>
                  </label>
                  <input 
                    id="jobRole"
                    type="text" 
                    value={jobRole} 
                    onChange={(e) => setJobRole(e.target.value)} 
                    placeholder="e.g. Software Engineer, Product Manager" 
                    className="input-field" 
                    required
                  />
                </div>
                
                <div>
                  <label htmlFor="jobDescription" className="block text-sm font-medium text-shaga-secondary mb-1">
                    Job Description
                  </label>
                  <textarea 
                    id="jobDescription"
                    value={jobDescription} 
                    onChange={(e) => setJobDescription(e.target.value)} 
                    placeholder="Paste the job description here..." 
                    className="input-field min-h-[120px]"
                    rows={4}
                  />
                </div>
                
                <div>
                  <label htmlFor="resume" className="block text-sm font-medium text-shaga-secondary mb-1">
                    Upload Resume (PDF or DOCX)
                  </label>
                  <input 
                    id="resume"
                    type="file" 
                    onChange={handleFileChange} 
                    accept="application/pdf, .docx" 
                    className="file-input"
                  />
                  {fileName && (
                    <p className="mt-2 text-sm text-accent-yellow">
                      Selected file: {fileName}
                    </p>
                  )}
                </div>
                
                <div className="pt-4">
                  <button 
                    type="submit" 
                    className="btn-accent w-full"
                    disabled={isLoading || !jobRole}
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </span>
                    ) : (
                      'Start Interview'
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* Interview Section */}
      <section 
        ref={el => sectionsRef.current.interview = el}
        className="section"
      >
        <div className="container-custom">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            <div>
              <div className="slide-up">
                <h2 className="text-3xl font-bold mb-6">Interview Session</h2>
                <div className="camera-container mb-6">
                  {isClient ? <DynamicCameraView /> : 
                    <div className="w-full h-full flex items-center justify-center bg-dark-800">
                      <p className="text-shaga-secondary">Camera loading...</p>
                    </div>
                  }
                  <div className="absolute inset-0 border border-accent-yellow pointer-events-none"></div>
                  <div className="absolute top-4 left-4 flex items-center">
                    <div className="w-2 h-2 rounded-full bg-accent-green mr-2 animate-pulse"></div>
                    <span className="text-xs text-shaga-secondary uppercase tracking-wider">Live Camera</span>
                  </div>
                  {isRecording && (
                    <div className="absolute top-4 right-4 flex items-center">
                      <div className="w-2 h-2 rounded-full bg-red-500 mr-2 animate-pulse"></div>
                      <span className="text-xs text-red-400 uppercase tracking-wider">Recording</span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex gap-4 mb-8 slide-up animation-delay-200">
                <button 
                  onClick={isRecording ? stopRecording : startRecording} 
                  className={`flex-1 ${isRecording ? 'btn-primary border-red-500 text-red-400' : 'btn-primary'}`}
                >
                  {isRecording ? 'Stop Recording' : 'Start Recording'}
                </button>
                <button 
                  onClick={() => scrollToSection('feedback')} 
                  className="btn-outline"
                >
                  View Feedback
                </button>
              </div>
              
              {audioFeedback && (
                <div className="card p-4 slide-up animation-delay-300">
                  <h3 className="text-lg font-medium text-shaga-primary mb-2">Audio Feedback:</h3>
                  <audio ref={audioRef} controls src={audioFeedback} className="w-full mt-2" />
                </div>
              )}
            </div>
            
            <div className="space-y-6">
              {response && (
                <div className="card p-6 bg-dark-700 border-l-2 border-l-accent-yellow slide-up">
                  <h3 className="text-lg font-medium text-accent-yellow mb-2">Interviewer Question:</h3>
                  <p className="text-shaga-primary">{response}</p>
                </div>
              )}
              
              <form onSubmit={handleSubmitInterview} className="card p-6 slide-up animation-delay-200">
                <div className="space-y-4">
                  <div>
                    <label htmlFor="userInput" className="block text-sm font-medium text-shaga-secondary mb-1">
                      Your Answer
                    </label>
                    <textarea 
                      id="userInput"
                      value={userInput} 
                      onChange={(e) => setUserInput(e.target.value)} 
                      placeholder="Type your answer here..." 
                      className="input-field min-h-[120px]"
                      rows={4}
                    />
                  </div>
                  
                  <button 
                    type="submit" 
                    className="btn-accent w-full"
                    disabled={isLoading || !userInput}
                  >
                    {isLoading && !isRecording ? (
                      <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </span>
                    ) : (
                      'Submit Answer'
                    )}
                  </button>
                </div>
              </form>
              
              <div className="card p-6 slide-up animation-delay-300">
                <h3 className="text-lg font-medium text-shaga-primary mb-4">Interview Stats</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-accent-yellow mb-1">
                      {response ? '1' : '0'}
                    </div>
                    <div className="text-xs text-shaga-muted uppercase tracking-wider">
                      Questions
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-accent-yellow mb-1">
                      {userInput ? '1' : '0'}
                    </div>
                    <div className="text-xs text-shaga-muted uppercase tracking-wider">
                      Answers
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feedback Section */}
      <section 
        ref={el => sectionsRef.current.feedback = el}
        className="section bg-dark-800"
      >
        <div className="container-custom">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-12 slide-up">
              <h2 className="text-3xl font-bold mb-4">Interview Feedback</h2>
              <p className="text-shaga-secondary">Review your performance and get AI-powered insights</p>
            </div>
            
            {audioFeedback ? (
              <div className="card p-6 slide-up animation-delay-200">
                <h3 className="text-lg font-medium text-accent-yellow mb-4">Audio Analysis</h3>
                <audio ref={audioRef} controls src={audioFeedback} className="w-full mb-6" />
                <div className="space-y-4">
                  <div className="p-4 bg-dark-600 rounded-md">
                    <h4 className="text-sm font-medium text-shaga-secondary mb-2">Confidence Score</h4>
                    <div className="w-full bg-dark-400 rounded-full h-2.5">
                      <div className="bg-accent-yellow h-2.5 rounded-full" style={{ width: '85%' }}></div>
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-shaga-muted">0%</span>
                      <span className="text-xs text-shaga-muted">100%</span>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-dark-600 rounded-md">
                    <h4 className="text-sm font-medium text-shaga-secondary mb-2">Clarity of Speech</h4>
                    <div className="w-full bg-dark-400 rounded-full h-2.5">
                      <div className="bg-accent-green h-2.5 rounded-full" style={{ width: '75%' }}></div>
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-shaga-muted">0%</span>
                      <span className="text-xs text-shaga-muted">100%</span>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-dark-600 rounded-md">
                    <h4 className="text-sm font-medium text-shaga-secondary mb-2">Content Relevance</h4>
                    <div className="w-full bg-dark-400 rounded-full h-2.5">
                      <div className="bg-accent-blue h-2.5 rounded-full" style={{ width: '90%' }}></div>
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-shaga-muted">0%</span>
                      <span className="text-xs text-shaga-muted">100%</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="card p-6 text-center slide-up animation-delay-200">
                <p className="text-shaga-secondary mb-4">No feedback available yet. Complete an interview session to get feedback.</p>
                <button 
                  onClick={() => scrollToSection('interview')} 
                  className="btn-accent"
                >
                  Go to Interview
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-dark-900 border-t border-dark-700">
        <div className="container-custom">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <h1 className="text-xl font-bold tracking-wider text-accent-yellow">:AI·COACH</h1>
            </div>
            <div className="flex space-x-6">
              <button onClick={() => scrollToSection('home')} className="nav-link">:HOME</button>
              <button onClick={() => scrollToSection('setup')} className="nav-link">:SETUP</button>
              <button onClick={() => scrollToSection('interview')} className="nav-link">:INTERVIEW</button>
              <button onClick={() => scrollToSection('feedback')} className="nav-link">:FEEDBACK</button>
            </div>
            <div className="mt-4 md:mt-0">
              <span className="text-xs text-shaga-muted tracking-widest">© {new Date().getFullYear()} AI·COACH</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
