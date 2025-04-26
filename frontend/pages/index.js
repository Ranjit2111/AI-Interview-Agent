import { useRef, useEffect, useState } from 'react';
import Head from 'next/head';
import dynamic from 'next/dynamic';

// Import the context hook
import { useAppContext } from '../src/context/AppContext';

// Import the new components
import SetupForm from '../components/SetupForm';
import InterviewChatWindow from '../components/InterviewChatWindow';
import FeedbackDisplay from '../components/FeedbackDisplay';

// Placeholder import for Feedback component
// import FeedbackDisplay from '../components/FeedbackDisplay';

// Set default to localhost if not specified in environment variables
// IMPORTANT: This ensures we ALWAYS use localhost for this local project
const BACKEND_URL = "http://localhost:8000";
console.log("Using backend URL:", BACKEND_URL);

// Dynamically import client-only components with no SSR
// These might be moved into the specific components that use them later
const DynamicCameraView = dynamic(
  () => import('../components/CameraView'),
  { ssr: false }
);

// Removed: DynamicSpeechInput, DynamicSpeechOutput as they will be in InterviewChatWindow

export default function Home() {
  // --- State Management ---
  // Access global state and functions via context hook
  const { error, clearError } = useAppContext(); // Example: Accessing error state

  // Local UI state (remains in this component)
  const [activeSection, setActiveSection] = useState('home'); // For navbar highlighting
  const [navbarVisible, setNavbarVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isClient, setIsClient] = useState(false); // For handling client-side only rendering

  // --- Refs ---
  const sectionsRef = useRef({}); // For scrolling to sections
  // Removed: audioRef, mediaRecorderRef, audioChunksRef (will move to relevant components)

  // --- Effects ---
  // Set isClient to true when component mounts (important for dynamic imports)
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Handle scroll events for navbar visibility and active section highlighting
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
      let currentSection = 'home';
      Object.entries(sectionsRef.current).forEach(([key, section]) => {
        if (section) {
          const rect = section.getBoundingClientRect();
          // Adjust threshold as needed
          if (rect.top <= window.innerHeight / 2 && rect.bottom >= window.innerHeight / 2) {
            currentSection = key;
          }
        }
      });
      setActiveSection(currentSection);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  // --- Helper Functions ---
  // Scroll to a specific section
  const scrollToSection = (sectionId) => {
    sectionsRef.current[sectionId]?.scrollIntoView({ behavior: 'smooth' });
  };

  // Removed: handleSubmitContext, handleSubmitInterview, handleAudioSubmit, 
  // startRecording, stopRecording, handleFileChange, handleSpeechInput
  // These will be moved to the respective components (SetupForm, InterviewChatWindow etc.)

  // --- Render ---
  return (
    <div className="min-h-screen bg-dark-900 text-shaga-primary">
      <Head>
        <title>AI Interview Coach | Advanced Interview Training</title>
        <meta name="description" content="AI-powered interview coaching with real-time feedback and analysis" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Navbar (remains here as it controls scrolling) */}
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

      {/* Global Error Display (Example) */}
      {error && (
        <div className="fixed top-20 right-5 bg-red-600 text-white p-4 rounded-lg shadow-lg z-50">
          <p>Error: {error}</p>
          <button onClick={clearError} className="ml-4 text-sm underline">Dismiss</button>
        </div>
      )}

      {/* Hero Section (remains mostly here) */}
      <section 
        ref={el => sectionsRef.current.home = el}
        className="section min-h-screen flex items-center relative overflow-hidden"
        style={{ paddingTop: '80px' }} // Adjust for navbar height
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
            {/* Camera View might also move later, but keep for now */}
            <div className="camera-container fade-in animation-delay-200">
              {isClient ? <DynamicCameraView /> : 
                <div className="w-full h-full flex items-center justify-center bg-dark-800">
                  <p className="text-shaga-secondary">Camera loading...</p>
                </div>
              }
              {/* Decorative elements for camera view */}
              <div className="absolute inset-0 border border-accent-yellow pointer-events-none"></div>
              <div className="absolute top-4 left-4 flex items-center">
                <div className="w-2 h-2 rounded-full bg-accent-green mr-2 animate-pulse"></div>
                <span className="text-xs text-shaga-secondary uppercase tracking-wider">Live Camera</span>
              </div>
              <div className="absolute bottom-4 left-4 text-xs text-shaga-secondary uppercase tracking-wider">Compatible with<br />all devices</div>
              <div className="absolute bottom-4 right-4 text-xs text-shaga-secondary uppercase tracking-wider">AI·COACH</div>
            </div>
          </div>
        </div>
        
        {/* Parallax background elements */}
        {/* Consider moving these styles to CSS for cleaner code */}
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

      {/* Setup Section - Now uses SetupForm component */}
      <section 
        ref={el => sectionsRef.current.setup = el}
        className="section bg-dark-800 py-16 md:py-24" // Added padding
      >
        <SetupForm /> 
      </section>

      {/* Interview Section - Now uses InterviewChatWindow component */}
      <section 
        id="interview" 
        ref={el => sectionsRef.current.interview = el}
        className="section min-h-screen flex flex-col items-center justify-center py-12"
      >
        <InterviewChatWindow />
      </section>

      {/* Feedback Section - Now uses FeedbackDisplay component */}
      <section 
        ref={el => sectionsRef.current.feedback = el}
        className="section bg-dark-800 py-16 md:py-24" // Added padding
      >
        <FeedbackDisplay />
      </section>

      {/* Footer (remains here) */}
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
