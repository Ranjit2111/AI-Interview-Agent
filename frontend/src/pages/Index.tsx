import React, { useState, useRef, useEffect } from 'react';
import { useInterviewSession } from '@/hooks/useInterviewSession';
import Header from '@/components/Header';
import InterviewConfig from '@/components/InterviewConfig';
import InterviewSession from '@/components/InterviewSession';
import InterviewResults from '@/components/InterviewResults';
import PerTurnFeedbackReview from '@/components/PerTurnFeedbackReview';
import { Button } from '@/components/ui/button';
import { ChevronDown, Sparkles, Zap, BarChart3, Bot, Github, Linkedin, Twitter, Mail, Save, History, Award, Users } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import AuthModal from '@/components/AuthModal';

const Index = () => {
  const { 
    state,
    messages,
    isLoading,
    results,
    selectedVoice,
    actions
  } = useInterviewSession();
  
  // Add debugging logs
  console.log('🎯 Index render - Current state:', state);
  console.log('🎯 Index render - Results:', results);
  console.log('🎯 Index render - Results type:', typeof results);
  if (results) {
    console.log('🎯 Index render - coachingSummary:', results.coachingSummary);
    console.log('🎯 Index render - coachingSummary type:', typeof results.coachingSummary);
    console.log('🎯 Index render - perTurnFeedback:', results.perTurnFeedback);
  }
  
  // Move hook calls to top level to fix React hooks violation
  const { user } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('register');
  
  const configSectionRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  
  // Track mouse position for parallax effect
  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    setMousePosition({
      x: (event.clientX / window.innerWidth) * 30,
      y: (event.clientY / window.innerHeight) * 30,
    });
  };

  const scrollToConfig = () => {
    configSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Animation for elements that should appear when in view
  const [isVisible, setIsVisible] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);
  
  // Debug effect for tracking completed state
  useEffect(() => {
    if (state === 'completed' && results?.coachingSummary) {
      console.log('🎯 Rendering InterviewResults with coachingSummary:', results.coachingSummary);
    }
  }, [state, results?.coachingSummary]);
  
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      });
    }, { threshold: 0.1 });
    
    if (heroRef.current) {
      observer.observe(heroRef.current);
    }
    
    return () => {
      if (heroRef.current) {
        observer.unobserve(heroRef.current);
      }
    };
  }, []);

  // Render animated blobs for background
  const renderBlobs = () => {
    return (
      <>
        <div className="animated-blob w-[25vw] h-[25vw] top-[0%] left-[20%] mix-blend-multiply"></div>
        <div className="animated-blob w-[35vw] h-[35vw] bottom-[0%] right-[25%] mix-blend-multiply animation-delay-2000"></div>
        <div className="animated-blob w-[30vw] h-[30vw] bottom-[10%] left-[5%] mix-blend-multiply animation-delay-4000"></div>
      </>
    );
  };

  // Render footer with social links
  const renderFooter = () => {
    if (state !== 'configuring') return null;
    
    return (
      <footer className="py-12 border-t border-white/10 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-black/0 to-purple-900/5 z-0"></div>
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-5xl mx-auto">
            <div className="flex flex-col items-center justify-center">
              <div className="flex items-center mb-6">
                <div className="relative">
                  <div className="absolute -inset-0.5 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 opacity-70 blur-sm"></div>
                  <div className="relative p-1 rounded-full bg-gradient-to-br from-cyan-400 via-purple-500 to-pink-500">
                    <div className="w-8 h-8 flex items-center justify-center rounded-full bg-black">
                      <Sparkles className="h-4 w-4 text-transparent bg-clip-text bg-gradient-to-br from-cyan-300 to-purple-400" />
                    </div>
                  </div>
                </div>
                <h3 className="ml-2 text-xl font-bold bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">AI Interviewer</h3>
              </div>
              
              <p className="text-gray-400 text-center mb-6 max-w-md">
                Enhance your interview skills with our AI-powered simulator. Practice, get feedback, and improve.
              </p>
              
              <div className="flex justify-center space-x-4 mb-8">
                <a href="https://github.com/your-username/ai-interviewer" target="_blank" rel="noopener noreferrer" className="glass-effect p-3 rounded-full hover:border-cyan-500/30 hover:shadow-cyan-500/20 transition-all duration-300">
                  <Github className="h-5 w-5 text-gray-300 hover:text-cyan-400" />
                </a>
                <a href="https://twitter.com/your-username" target="_blank" rel="noopener noreferrer" className="glass-effect p-3 rounded-full hover:border-purple-500/30 hover:shadow-purple-500/20 transition-all duration-300">
                  <Twitter className="h-5 w-5 text-gray-300 hover:text-purple-400" />
                </a>
                <a href="https://linkedin.com/in/your-username" target="_blank" rel="noopener noreferrer" className="glass-effect p-3 rounded-full hover:border-pink-500/30 hover:shadow-pink-500/20 transition-all duration-300">
                  <Linkedin className="h-5 w-5 text-gray-300 hover:text-pink-400" />
                </a>
                <a href="mailto:contact@example.com" target="_blank" rel="noopener noreferrer" className="glass-effect p-3 rounded-full hover:border-cyan-500/30 hover:shadow-cyan-500/20 transition-all duration-300">
                  <Mail className="h-5 w-5 text-gray-300 hover:text-cyan-400" />
                </a>
              </div>
              
              <div className="text-center text-sm text-gray-500">
                <p>© 2023 AI Interviewer. All rights reserved.</p>
                <p className="mt-1">
                  <a href="#" className="text-gray-400 hover:text-gray-300 underline-animation">Privacy Policy</a>
                  <span className="mx-2">·</span>
                  <a href="#" className="text-gray-400 hover:text-gray-300 underline-animation">Terms of Service</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </footer>
    );
  };

  // Render signup benefits section
  const renderSignupBenefits = () => {
    if (user || state !== 'configuring') return null;

    const handleSignUpClick = () => {
      setAuthModalMode('register');
      setIsAuthModalOpen(true);
    };

    const handleSignInClick = () => {
      setAuthModalMode('login');
      setIsAuthModalOpen(true);
    };

    return (
      <>
        <section className="py-20 border-t border-white/10 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-900/10 to-cyan-900/10"></div>
          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              <div className="mb-8">
                <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">
                  Want to Save Your Progress?
                </h2>
                <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                  Create a free account to unlock powerful features and track your interview improvements over time.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                <div className="glass-effect p-6 rounded-xl hover:border-cyan-500/20 hover:shadow-cyan-500/10 transition-all duration-300">
                  <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Save className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-200 mb-3">Save Your Sessions</h3>
                  <p className="text-gray-400">
                    Keep track of all your practice sessions and never lose your progress. Resume where you left off.
                  </p>
                </div>

                <div className="glass-effect p-6 rounded-xl hover:border-purple-500/20 hover:shadow-purple-500/10 transition-all duration-300">
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <History className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-200 mb-3">View History</h3>
                  <p className="text-gray-400">
                    Access your complete interview history and see how you've improved over time with detailed analytics.
                  </p>
                </div>

                <div className="glass-effect p-6 rounded-xl hover:border-pink-500/20 hover:shadow-pink-500/10 transition-all duration-300">
                  <div className="w-12 h-12 bg-gradient-to-r from-pink-500 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Award className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-200 mb-3">Performance Tracking</h3>
                  <p className="text-gray-400">
                    Get detailed insights into your strengths and areas for improvement with comprehensive feedback reports.
                  </p>
                </div>
              </div>

              <div className="glass-effect p-8 rounded-2xl bg-gradient-to-r from-cyan-500/10 to-purple-600/10 border border-cyan-500/20">
                <h3 className="text-2xl font-bold mb-4 text-white">Ready to Level Up Your Interview Game?</h3>
                <p className="text-gray-300 mb-6 max-w-2xl mx-auto">
                  Join thousands of professionals who've improved their interview skills with our AI-powered platform. 
                  It's <strong>completely free</strong> and takes less than 30 seconds to get started.
                </p>
                
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <Button 
                    onClick={handleSignUpClick}
                    size="lg"
                    className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white shadow-lg hover:shadow-purple-500/20 text-lg group font-medium btn-ripple"
                  >
                    <Users className="mr-2 h-5 w-5" />
                    Create Free Account
                    <Sparkles className="ml-2 h-5 w-5 group-hover:animate-pulse-slow" />
                  </Button>
                  
                  <span className="text-gray-400">or</span>
                  
                  <Button 
                    onClick={handleSignInClick}
                    variant="outline"
                    size="lg"
                    className="border-white/10 bg-black/20 hover:bg-white/10 text-gray-300 hover:text-white hover:border-cyan-500/30 text-lg font-medium"
                  >
                    Sign In
                  </Button>
                </div>
                
                <p className="text-sm text-gray-500 mt-4">
                  No credit card required • Free forever • Start practicing immediately
                </p>
              </div>
            </div>
          </div>
        </section>

        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          initialMode={authModalMode}
        />
      </>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-black text-gray-100 relative overflow-hidden">
      <Header 
        showReset={state === 'interviewing' || state === 'completed'} 
        onReset={actions.resetInterview}
      />
      
      <main className="flex-1 flex flex-col">
        {state === 'configuring' && (
          <>
            <div 
              className="relative h-[90vh] overflow-hidden flex items-center"
              ref={heroRef}
              onMouseMove={handleMouseMove}
            >
              {renderBlobs()}
              
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(30,20,60,0.5),rgba(0,0,0,0.8))] z-10"></div>
              
              <div className="absolute inset-0 z-5">
                <div className="absolute w-full h-full">
                  {/* Grid pattern overlay */}
                  <div 
                    className="absolute inset-0 opacity-10"
                    style={{ 
                      backgroundImage: 'linear-gradient(#22d3ee 1px, transparent 1px), linear-gradient(90deg, #22d3ee 1px, transparent 1px)', 
                      backgroundSize: '40px 40px',
                      backgroundPosition: `${mousePosition.x}px ${mousePosition.y}px`,
                      transition: 'background-position 0.1s ease-out'
                    }}
                  ></div>
                </div>
              </div>
              
              <div className="container mx-auto px-4 relative z-20">
                <div className="max-w-3xl">
                  <div className={`mb-8 transition-all duration-700 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 -translate-y-8'}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-3 py-1 text-xs rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-600/20 border border-purple-500/20 backdrop-blur-sm text-cyan-300 font-semibold tracking-wider">
                        AI-POWERED PRACTICE
                      </span>
                    </div>
                    <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">
                      Master Your <br />Interview Skills
                    </h1>
                    <p className="text-xl md:text-2xl mb-8 text-gray-400 max-w-2xl leading-relaxed">
                      Enhance your interview technique with our AI-powered simulator. Get real-time feedback and track your improvement.
                    </p>
                  </div>
                  
                  <div className={`flex flex-col sm:flex-row gap-4 transition-all duration-700 delay-300 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'}`}>
                    <Button 
                      onClick={scrollToConfig}
                      size="lg"
                      className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white shadow-lg hover:shadow-purple-500/20 text-lg group font-medium btn-ripple"
                    >
                      Start Practicing
                      <Zap className="ml-2 h-5 w-5 group-hover:animate-pulse-slow" />
                    </Button>
                    
                    <Button 
                      variant="outline"
                      size="lg"
                      className="border-white/10 bg-black/20 hover:bg-white/10 text-gray-300 hover:text-white hover:border-purple-500/30 text-lg font-medium"
                    >
                      Learn More
                      <ChevronDown className="ml-2 h-5 w-5 group-hover:translate-y-1 transition-transform" />
                    </Button>
                  </div>
                  
                  <div className={`mt-16 grid grid-cols-1 sm:grid-cols-3 gap-6 transition-all duration-700 delay-500 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'}`}>
                    <div className="glass-effect p-5 rounded-xl hover:border-cyan-500/20 hover:shadow-cyan-500/10 transition-all duration-300 halo-glow perspective-card">
                      <Bot className="text-cyan-400 mb-3 h-6 w-6" />
                      <h3 className="font-bold text-lg text-gray-200">AI Interviewer</h3>
                      <p className="text-gray-400 text-sm mt-2">Practice with our advanced AI that adapts to your responses</p>
                    </div>
                    
                    <div className="glass-effect p-5 rounded-xl hover:border-purple-500/20 hover:shadow-purple-500/10 transition-all duration-300 halo-glow perspective-card">
                      <Sparkles className="text-purple-400 mb-3 h-6 w-6" />
                      <h3 className="font-bold text-lg text-gray-200">Real-time Feedback</h3>
                      <p className="text-gray-400 text-sm mt-2">Get immediate insights on your performance and areas for improvement</p>
                    </div>
                    
                    <div className="glass-effect p-5 rounded-xl hover:border-pink-500/20 hover:shadow-pink-500/10 transition-all duration-300 halo-glow perspective-card">
                      <BarChart3 className="text-pink-400 mb-3 h-6 w-6" />
                      <h3 className="font-bold text-lg text-gray-200">In-depth Feedback</h3>
                      <p className="text-gray-400 text-sm mt-2">Receive comprehensive analysis of your performance and targeted advice.</p>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Adjusted position of the bouncing arrow to be below the grid cards */}
              <div className="absolute bottom-10 left-0 right-0 flex justify-center animate-bounce z-20 pointer-events-none mt-12">
                <ChevronDown className="h-8 w-8 text-gray-400" />
              </div>
              
              {/* Animated shapes */}
              <div className="absolute h-32 w-32 bg-purple-500/5 rounded-full blur-3xl top-[30%] right-[20%] animate-float"></div>
              <div className="absolute h-48 w-48 bg-cyan-500/5 rounded-full blur-3xl bottom-[20%] left-[15%] animate-float animation-delay-2000"></div>
            </div>
            
            <div 
              id="config-section" 
              className="container mx-auto py-20 px-4" 
              ref={configSectionRef}
            >
              <div className="max-w-3xl mx-auto glass-card rounded-xl shadow-2xl p-8 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-purple-600/5 z-0"></div>
                <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent text-center relative z-10">
                  Configure Your Interview
                </h2>
                <div className="relative z-10">
                  <InterviewConfig 
                    onSubmit={actions.startInterview}
                    isLoading={isLoading}
                  />
                </div>
              </div>
            </div>
            
            {renderFooter()}
            {renderSignupBenefits()}
          </>
        )}
        
        {state === 'interviewing' && (
          <InterviewSession 
            messages={messages}
            isLoading={isLoading}
            onSendMessage={actions.sendMessage}
            onEndInterview={actions.endInterview}
            onVoiceSelect={actions.setSelectedVoice}
          />
        )}

        {state === 'reviewing_feedback' && results?.perTurnFeedback && (
          <PerTurnFeedbackReview 
            feedbackItems={results.perTurnFeedback}
            onProceedToSummary={actions.proceedToFinalSummary}
          />
        )}
        
        {state === 'completed' && results?.coachingSummary && (
          <InterviewResults 
            coachingSummary={results.coachingSummary} 
            onStartNewInterview={actions.resetInterview} 
          />
        )}
      </main>
    </div>
  );
};

export default Index;
