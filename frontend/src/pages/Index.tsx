import React, { useState, useRef, useEffect } from 'react';
import { useInterviewSession } from '@/hooks/useInterviewSession';
import Header from '@/components/Header';
import InterviewConfig from '@/components/InterviewConfig';
import InterviewSession from '@/components/InterviewSession';
import InterviewResults from '@/components/InterviewResults';
import PerTurnFeedbackReview from '@/components/PerTurnFeedbackReview';
import PostInterviewReport from '@/components/PostInterviewReport';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Sparkles, Zap, BarChart3, Bot, Github, Linkedin, Twitter, Mail, 
  Save, History, Award, Users, BriefcaseBusiness, Building2, FileText, UploadCloud, 
  Settings, ArrowRight, Star, TrendingUp, Target, CheckCircle, ArrowUpRight, 
  BookOpen, Headphones, Brain, Search, ChevronRight, Clock, Volume2, MessageSquare,
  Zap as Lightning, Mic, Shield, Database
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import AuthModal from '@/components/AuthModal';
import { InterviewStartRequest, api } from '@/services/api';
import { useToast } from "@/hooks/use-toast";

const Index = () => {
  const { 
    state,
    messages,
    isLoading,
    results,
    postInterviewState,
    selectedVoice,
    coachFeedbackStates,
    sessionId,
    actions
  } = useInterviewSession();
  
  const { user } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('register');
  const { toast } = useToast();
  
  // Animation and interaction states
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isVisible, setIsVisible] = useState(false);
  
  // Feature Constellation states
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);
  
  // Configuration state
  const [jobRole, setJobRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [resumeContent, setResumeContent] = useState('');
  const [style, setStyle] = useState<'formal' | 'casual' | 'aggressive' | 'technical'>('formal');
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [interviewDuration, setInterviewDuration] = useState(10);
  const [company, setCompany] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [showRequiredError, setShowRequiredError] = useState(false);
  
  const heroRef = useRef<HTMLDivElement>(null);
  const configSectionRef = useRef<HTMLDivElement>(null);
  const jobRoleSectionRef = useRef<HTMLDivElement>(null);
  const featuresSectionRef = useRef<HTMLDivElement>(null);
  const constellationRef = useRef<HTMLDivElement>(null);

  // Mouse tracking for feature constellation interactions
  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    setMousePosition({ x, y });
  };

  // Advanced visibility tracking
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



  // Clear required error when user starts typing job role
  useEffect(() => {
    if (jobRole.trim() && showRequiredError) {
      setShowRequiredError(false);
    }
  }, [jobRole, showRequiredError]);

  // Scroll handlers
  const scrollToFeatures = () => {
    featuresSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToConfig = () => {
    configSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Feature Constellation Data - Interactive floating elements
  const featureConstellation = [
    {
      id: 'interview-agent',
      title: 'AI Interview Agent',
      subtitle: 'Your Personal Interviewer',
      description: 'Experience natural conversations with an AI that adapts to your responses and asks thoughtful follow-up questions.',
      features: [
        'Natural voice conversations',
        'Adapts to the JD and your resume', 
        'Multiple interview styles available'
      ],
      icon: Bot,
      position: { x: 75, y: 30 }, // Percentage positions for responsive layout
      color: '#06b6d4',
      gradient: 'from-cyan-500 to-blue-600',
      glowColor: 'rgba(6, 182, 212, 0.4)',
    },
    {
      id: 'coach-agent', 
      title: 'Real-time Coach Agent',
      subtitle: 'Background Performance Analysis',
      description: 'Get instant feedback on your communication patterns, confidence levels, and areas for improvement.',
      features: [
        'Analyzes your responses',
        'Detects clarity and answer relevance',
        'Provides actionable feedback to improve'
      ],
      icon: Brain,
      position: { x: 20, y: 25 },
      color: '#8b5cf6',
      gradient: 'from-purple-500 to-pink-600',
      glowColor: 'rgba(139, 92, 246, 0.4)',
    },
    {
      id: 'learning-engine',
      title: 'Resource Search Engine', 
      subtitle: 'Personalized Resource Search',
      description: 'Receive curated learning resources and practice recommendations based on your performance.',
      features: [
        'Identifies skill gaps',
        'Search for resources based on your performance',
        'Curated learning resources'
      ],
      icon: Search,
      position: { x: 75, y: 75 },
      color: '#10b981',
      gradient: 'from-emerald-500 to-teal-600',
      glowColor: 'rgba(16, 185, 129, 0.4)',
    },
    {
      id: 'speech-processing',
      title: 'Speech Processing',
      subtitle: 'Advanced Voice Technology', 
      description: 'Powered by cutting-edge STT & TTS for crystal-clear voice recognition and natural speech synthesis.',
      features: [
        "Deepgram's real-time streaming STT",
        'Natural sounding AI responses via Amazon Polly TTS',
        'Websockets for real-time communication'
      ],
      icon: Mic,
      position: { x: 25, y: 70 },
      color: '#f97316',
      gradient: 'from-orange-500 to-red-600',
      glowColor: 'rgba(249, 115, 22, 0.4)',
    },
    {
      id: 'data-security',
      title: 'Database',
      subtitle: 'Your Session Data Protected',
      description: 'Bank-level encryption and secure cloud storage ensure your interview data remains private and protected.',
      features: [
        'End-to-end encryption',
        'Secure data storage in Supabase', 
        'RLS for data access control'
      ],
      icon: Shield,
      position: { x: 50, y: 85 },
      color: '#22c55e',
      gradient: 'from-green-500 to-emerald-600',
      glowColor: 'rgba(34, 197, 94, 0.4)',
    }
  ];

  // Popular job roles for quick selection
  const popularRoles = [
    { title: 'Software Engineer', icon: '💻', gradient: 'from-blue-500 to-cyan-500' },
    { title: 'Product Manager', icon: '📊', gradient: 'from-purple-500 to-pink-500' },
    { title: 'Data Scientist', icon: '📈', gradient: 'from-green-500 to-teal-500' },
    { title: 'UX Designer', icon: '🎨', gradient: 'from-orange-500 to-red-500' },
    { title: 'Marketing Manager', icon: '📢', gradient: 'from-indigo-500 to-purple-500' },
    { title: 'Sales Representative', icon: '💼', gradient: 'from-yellow-500 to-orange-500' }
  ];

  // Interview style configurations
  const interviewStyles = [
    { value: 'formal', label: 'Professional', description: 'Traditional corporate interview style', color: 'blue' },
    { value: 'casual', label: 'Conversational', description: 'Relaxed and friendly approach', color: 'green' },
    { value: 'technical', label: 'Technical Deep-dive', description: 'Focus on technical skills and problem-solving', color: 'purple' },
    { value: 'aggressive', label: 'Challenging', description: 'High-pressure scenario simulation', color: 'red' }
  ];

  // Difficulty levels with visual indicators
  const difficultyLevels = [
    { value: 'easy', label: 'Beginner', description: 'Basic questions, gentle pace', bars: 1, color: 'green' },
    { value: 'medium', label: 'Intermediate', description: 'Standard interview complexity', bars: 2, color: 'orange' },
    { value: 'hard', label: 'Advanced', description: 'Complex scenarios and follow-ups', bars: 3, color: 'red' }
  ];

  // File upload handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validTypes = [
      'text/plain',
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    if (!validTypes.includes(file.type)) {
      toast({
        title: "Unsupported File Type",
        description: "Please upload a .txt, .pdf, or .docx file.",
        variant: "destructive",
      });
      return;
    }

    if (file.type === 'text/plain') {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setResumeContent(event.target.result as string);
          toast({ title: "Success", description: "Resume content loaded successfully." });
        }
      };
      reader.readAsText(file);
    } else {
      setIsUploading(true);
      try {
        const response = await api.uploadResumeFile(file);
        if (response.resume_text) {
          setResumeContent(response.resume_text);
          toast({
            title: "Resume Processed",
            description: `${response.filename} content extracted successfully.`,
          });
        }
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : "Failed to upload resume.";
        toast({
          title: "Upload Error",
          description: errorMsg,
          variant: "destructive",
        });
      } finally {
        setIsUploading(false);
      }
    }
    e.target.value = '';
  };

  // Start interview handler
  const handleStartInterview = () => {
    if (!jobRole.trim()) {
      // Show visual error state
      setShowRequiredError(true);
      
      // Scroll to job role section with smooth animation
      setTimeout(() => {
        jobRoleSectionRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
      }, 100);
      
      // Show helpful toast message
      toast({ 
        title: "Required Field Missing", 
        description: "Please enter a job role to start your interview practice.", 
        variant: "destructive" 
      });
      
      // Clear error state after a few seconds
      setTimeout(() => {
        setShowRequiredError(false);
      }, 5000);
      
      return;
    }
    
    const config: InterviewStartRequest = {
      job_role: jobRole,
      job_description: jobDescription || undefined,
      resume_content: resumeContent || undefined,
      style,
      difficulty,
      company_name: company || undefined,
      interview_duration_minutes: interviewDuration,
      use_time_based_interview: true,
    };
    
    actions.startInterview(config);
  };

  // Hero background with image and light effects
  const renderHeroBackground = () => (
    <div className="absolute inset-0 overflow-hidden">
      {/* Hero gradient background image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('/hero-gradient.jpg')"
        }}
      />
      
      {/* Slightly lighter overlay for balanced brightness */}
      <div className="absolute inset-0 bg-black/30" />
      
      {/* Subtle light beam effects */}
      <div className="absolute inset-0">
        {/* Central light beam */}
      <div 
          className="absolute top-0 left-1/2 transform -translate-x-1/2 w-1 h-full opacity-25"
        style={{
            background: 'linear-gradient(to bottom, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0.15) 50%, transparent 100%)',
            filter: 'blur(2px)'
          }}
        />
        
        {/* Side light accents */}
      <div 
          className="absolute top-1/4 left-1/4 w-px h-32 opacity-18 rotate-12"
        style={{
            background: 'linear-gradient(to bottom, rgba(255, 255, 255, 0.5), transparent)',
            filter: 'blur(1px)'
        }}
      />
        <div 
          className="absolute top-1/3 right-1/4 w-px h-24 opacity-18 -rotate-12"
        style={{
            background: 'linear-gradient(to bottom, rgba(255, 255, 255, 0.5), transparent)',
            filter: 'blur(1px)'
        }}
      />
      </div>
    </div>
  );

  // Stunning Hero Section with Modern Typography
  const renderHeroSection = () => (
    <div 
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
      ref={heroRef}
    >
      {renderHeroBackground()}
      
      {/* Centered Hero Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-20">
        <div className="max-w-6xl mx-auto text-center">
          
          {/* Refined Badge */}
          <div className={`inline-flex items-center gap-2 sm:gap-3 px-4 sm:px-8 py-3 sm:py-4 rounded-full bg-black/30 backdrop-blur-md border border-white/10 mb-8 sm:mb-12 transition-all duration-1000 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 -translate-y-8'}`}>
            <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-gray-300" />
            <span className="text-xs sm:text-sm font-medium text-gray-300 tracking-wide">AI Interview System</span>
          </div>

          {/* Main Headline with Responsive Typography */}
          <div className={`space-y-4 sm:space-y-8 mb-8 sm:mb-12 transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 -translate-y-12'}`}>
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-7xl xl:text-8xl font-black leading-tight tracking-tight">
              <div className="text-white/95 mb-2 sm:mb-3">
                Master Your
              </div>
              <div className="text-white/95">
                Interview Skills
              </div>
            </h1>
            
            <p className="text-base sm:text-lg lg:text-2xl text-gray-300 max-w-full sm:max-w-4xl mx-auto leading-relaxed font-normal px-4 sm:px-0">
              Practice with intelligent AI agents that simulate real interviews
              <br className="hidden sm:block" />
              and provide personalized coaching feedback
            </p>
          </div>

          {/* Action Buttons with Mobile Optimization */}
          <div className={`flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-center mb-12 sm:mb-16 px-4 sm:px-0 transition-all duration-1000 delay-400 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'}`}>
            <Button
              onClick={scrollToConfig}
              className="w-full sm:w-auto bg-white/90 hover:bg-white/90 text-gray-900 px-6 sm:px-8 py-3 sm:py-4 rounded-xl text-base sm:text-lg font-bold shadow-lg hover:shadow-white/10 transition-all duration-300 group border-0 min-h-[48px] sm:min-h-[56px] hover:scale-105"
            >
              Get Started
              <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </Button>
            
            <Button
              variant="outline"
              onClick={scrollToFeatures}
              className="w-full sm:w-auto border-2 border-white/20 bg-black/20 hover:bg-white/10 text-gray-200 hover:text-white px-6 sm:px-8 py-3 sm:py-4 rounded-xl text-base sm:text-lg font-semibold backdrop-blur-sm hover:border-white/40 transition-all duration-300 min-h-[48px] sm:min-h-[56px] hover:scale-105"
            >
              Learn More
            </Button>
          </div>

          {/* Scroll indicator - hidden on mobile */}
          <div className={`hidden sm:block transition-all duration-1000 delay-600 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'}`}>
            <div className="flex items-center justify-center space-x-2 text-gray-400">
              <span className="text-sm font-medium tracking-wider">Scroll to explore features</span>
              </div>
            </div>
              </div>
      </div>
    </div>
  );

  // Configuration Form Section - Completely Redesigned
  const renderConfigurationForm = () => (
    <div ref={configSectionRef} className="py-16 sm:py-24 relative overflow-hidden">
      {/* Advanced Multi-layer Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-950 to-black"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-purple-900/10 via-transparent to-cyan-900/10"></div>
        
        {/* Dynamic floating particles */}
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-cyan-400 rounded-full opacity-30 animate-pulse"
            style={{
              left: `${20 + (i * 12) % 60}%`,
              top: `${15 + (i * 17) % 70}%`,
              animationDelay: `${i * 0.7}s`,
              animationDuration: `${2 + (i % 3)}s`
            }}
          />
        ))}
      </div>
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl 2xl:max-w-none mx-auto">
          {/* Section Header */}
          <div className="text-center mb-12 sm:mb-16">
            <div className="inline-flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-600/20 border border-purple-500/30 backdrop-blur-sm mb-4 sm:mb-6">
              <Settings className="w-3 h-3 sm:w-4 sm:h-4 text-cyan-300" />
              <span className="text-xs sm:text-sm font-semibold text-cyan-300 tracking-wider">Interview Configuration</span>
            </div>
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold mb-4 sm:mb-6">
              <span className="bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">
                Craft Your Perfect
              </span>
              <br />
              <span className="text-white">Interview Experience</span>
            </h2>
            <p className="text-gray-400 text-base sm:text-xl max-w-3xl xl:max-w-4xl mx-auto leading-relaxed px-4 sm:px-0">
              Configure every aspect of your practice session with our intelligent wizard
            </p>
          </div>

          {/* Revolutionary Bento Grid Configuration */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6 mb-8 sm:mb-12">
            
            {/* Job Role Selection - Large Featured Panel */}
            <div 
              ref={jobRoleSectionRef}
              className={`lg:col-span-8 bg-gradient-to-br from-black/80 via-gray-900/80 to-black/80 backdrop-blur-3xl border rounded-2xl sm:rounded-3xl p-4 sm:p-6 lg:p-8 shadow-2xl transition-all duration-500 group ${
                showRequiredError 
                  ? 'border-red-500/60 shadow-red-500/20' 
                  : 'border-white/10 hover:shadow-cyan-500/10'
              }`}
            >
              <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
                <div className={`p-2 sm:p-3 rounded-xl shadow-lg transition-all duration-300 ${
                  showRequiredError 
                    ? 'bg-gradient-to-br from-red-500 to-red-600' 
                    : 'bg-gradient-to-br from-cyan-500 to-purple-600'
                }`}>
                  <Target className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className={`text-lg sm:text-2xl font-bold transition-colors ${
                    showRequiredError 
                      ? 'text-red-300' 
                      : 'text-white group-hover:text-cyan-300'
                  }`}>
                    Target Role
                  </h3>
                  <p className="text-gray-400 text-sm sm:text-base">What position are you preparing for?</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 sm:px-4 py-1 sm:py-2 rounded-full font-medium text-xs sm:text-sm transition-all duration-300 ${
                    showRequiredError 
                      ? 'bg-red-500/30 text-red-200' 
                      : 'bg-red-500/20 text-red-300'
                  }`}>
                    Required
                  </span>
                </div>
              </div>
              
              {/* Popular roles with mobile optimization */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
                {popularRoles.map((role, index) => (
                  <button
                    key={role.title}
                    onClick={() => setJobRole(role.title)}
                    className={`relative p-3 sm:p-4 rounded-xl border transition-all duration-500 text-left group/role overflow-hidden ${
                      jobRole === role.title 
                        ? `border-cyan-500 bg-gradient-to-r ${role.gradient} text-white shadow-lg scale-105 z-10` 
                        : 'border-white/10 bg-black/40 hover:border-white/20 text-gray-300 hover:scale-105'
                    }`}
                    style={{
                      animationDelay: `${index * 0.1}s`
                    }}
                  >
                    {/* Hover glow effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 opacity-0 group-hover/role:opacity-100 transition-opacity duration-500 rounded-xl"></div>
                    
                    <div className="relative flex items-center space-x-2 sm:space-x-3">
                      <span className="text-xl sm:text-2xl transform group-hover/role:scale-110 transition-transform duration-300">{role.icon}</span>
                      <span className="text-xs sm:text-sm font-medium group-hover/role:text-white transition-colors">
                        {role.title}
                      </span>
                    </div>
                    
                    {/* Selection indicator */}
                    {jobRole === role.title && (
                      <div className="absolute top-2 right-2">
                        <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
              
              {/* Custom role input with premium styling */}
              <div className="relative">
                <Input
                  placeholder="Or describe your custom role ..."
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  className={`bg-black/60 text-white placeholder-gray-400 rounded-xl px-3 sm:px-4 py-3 sm:py-4 text-base sm:text-lg transition-all duration-300 ${
                    showRequiredError && !jobRole.trim()
                      ? 'border-red-500/60 focus:border-red-500'
                      : 'border-white/20 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 hover:border-white/30'
                  }`}
                />
                {jobRole && !popularRoles.find(r => r.title === jobRole) && (
                  <div className="absolute right-2 sm:right-3 top-1/2 transform -translate-y-1/2">
                    <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400" />
                  </div>
                )}
              </div>
            </div>

            {/* Company & Duration - Right Side Panels */}
            <div className="lg:col-span-4 space-y-4 sm:space-y-6">
              
              {/* Company Selection */}
              <div className="bg-gradient-to-br from-purple-900/30 via-black/80 to-purple-900/30 backdrop-blur-3xl border border-purple-500/20 rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-xl hover:shadow-purple-500/10 transition-all duration-500">
                <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                  <div className="p-1.5 sm:p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 shadow-md">
                    <Building2 className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-white">Company</h3>
                    <p className="text-xs text-gray-400">Optional context</p>
                  </div>
                </div>
                <Input
                  placeholder="Google, Microsoft, StartupCo..."
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="bg-black/60 border-purple-500/20 text-white placeholder-gray-500 rounded-xl focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300 text-sm sm:text-base"
                />
              </div>

              {/* Duration with Visual Feedback */}
              <div className="bg-gradient-to-br from-orange-900/30 via-black/80 to-orange-900/30 backdrop-blur-3xl border border-orange-500/20 rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-xl hover:shadow-orange-500/10 transition-all duration-500">
                <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                  <div className="p-1.5 sm:p-2 rounded-lg bg-gradient-to-br from-orange-500 to-red-600 shadow-md">
                    <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-white">Duration</h3>
                    <p className="text-xs text-gray-400">{interviewDuration} minutes</p>
                  </div>
                </div>
                
                {/* Premium slider with visual feedback */}
                <div className="space-y-2 sm:space-y-3">
                  <input
                    type="range"
                    min="5"
                    max="30"
                    value={interviewDuration}
                    onChange={(e) => setInterviewDuration(parseInt(e.target.value))}
                    className="w-full h-2 sm:h-3 bg-gray-800 rounded-lg appearance-none cursor-pointer slider-premium"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span className={interviewDuration <= 10 ? 'text-green-400' : 'text-gray-500'}>5 min • Quick</span>
                    <span className={interviewDuration > 10 && interviewDuration <= 20 ? 'text-yellow-400' : 'text-gray-500'}>15 min • Standard</span>
                    <span className={interviewDuration > 20 ? 'text-red-400' : 'text-gray-500'}>30 min • Deep</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Interview Style & Difficulty - Full Width Advanced Panels */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-8 sm:mb-12">
            
            {/* Interview Style Selection */}
            <div className="bg-gradient-to-br from-black/80 via-blue-900/20 to-black/80 backdrop-blur-3xl border border-blue-500/20 rounded-2xl sm:rounded-3xl p-4 sm:p-6 lg:p-8 shadow-2xl hover:shadow-blue-500/10 transition-all duration-500">
              <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
                <div className="p-2 sm:p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 shadow-lg">
                  <MessageSquare className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg sm:text-2xl font-bold text-white">Interview Style</h3>
                  <p className="text-gray-400 text-sm sm:text-base">Choose your preferred interaction mode</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-5">
                {interviewStyles.map((styleOption) => (
                  <button
                    key={styleOption.value}
                    onClick={() => setStyle(styleOption.value as any)}
                    className={`relative p-4 sm:p-7 rounded-xl border text-left transition-all duration-500 overflow-hidden group/style ${
                      style === styleOption.value
                        ? `border-${styleOption.color}-500 bg-${styleOption.color}-500/20 text-white shadow-lg`
                        : 'border-white/10 bg-black/40 text-gray-400 hover:text-white hover:border-white/20'
                    }`}
                  >
                    {/* Advanced hover glow */}
                    <div className={`absolute inset-0 bg-gradient-to-br from-${styleOption.color}-500/10 to-${styleOption.color}-600/10 opacity-0 group-hover/style:opacity-100 transition-opacity duration-500 rounded-xl`}></div>
                    
                    <div className="relative">
                      <div className="text-base sm:text-lg font-bold mb-2 sm:mb-3">{styleOption.label}</div>
                      <div className="text-xs sm:text-sm opacity-80">{styleOption.description}</div>
                      
                      {/* Selection indicator */}
                      {style === styleOption.value && (
                        <div className="absolute top-0 right-0">
                          <div className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-${styleOption.color}-500 animate-pulse`}></div>
                        </div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty Level with Visual Bars */}
            <div className="bg-gradient-to-br from-black/80 via-gray-900/20 to-black/80 backdrop-blur-3xl border border-gray-500/20 rounded-2xl sm:rounded-3xl p-4 sm:p-6 lg:p-8 shadow-2xl hover:shadow-orange-500/10 transition-all duration-500">
                <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
                  <div className="p-2 sm:p-3 rounded-xl bg-gradient-to-br from-gray-500 to-gray-600 shadow-md">
                    <BarChart3 className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-white">Difficulty Level</h3>
                    <p className="text-gray-400 text-sm sm:text-base">Adjust challenge complexity</p>
                  </div>
                </div>

                <div className="space-y-2 sm:space-y-3">
                  {difficultyLevels.map((level) => {
                    // Function to get the correct color classes
                    const getColorClasses = (color) => {
                      switch(color) {
                        case 'green':
                          return {
                            border: 'border-green-500',
                            bg: 'bg-green-500/20',
                            shadow: 'shadow-green-500/20',
                            hoverShadow: 'hover:shadow-green-500/10',
                            barBg: 'bg-green-500'
                          };
                        case 'orange':
                          return {
                            border: 'border-orange-500',
                            bg: 'bg-orange-500/20',
                            shadow: 'shadow-orange-500/20',
                            hoverShadow: 'hover:shadow-orange-500/10',
                            barBg: 'bg-orange-500'
                          };
                        case 'red':
                          return {
                            border: 'border-red-500',
                            bg: 'bg-red-500/20',
                            shadow: 'shadow-red-500/20',
                            hoverShadow: 'hover:shadow-red-500/10',
                            barBg: 'bg-red-500'
                          };
                        default:
                          return {
                            border: 'border-gray-500',
                            bg: 'bg-gray-500/20',
                            shadow: 'shadow-gray-500/20',
                            hoverShadow: 'hover:shadow-gray-500/10',
                            barBg: 'bg-gray-500'
                          };
                      }
                    };

                    const colorClasses = getColorClasses(level.color);

                    return (
                      <button
                        key={level.value}
                        onClick={() => setDifficulty(level.value as any)}
                        className={`w-full p-4 sm:p-6 rounded-xl border text-left transition-all duration-500 flex items-center justify-between hover:shadow-lg ${
                          difficulty === level.value
                            ? `${colorClasses.border} ${colorClasses.bg} text-white scale-105 shadow-lg ${colorClasses.shadow}`
                            : `border-white/10 bg-black/40 text-gray-400 hover:text-white hover:border-white/20 ${colorClasses.hoverShadow}`
                        }`}
                      >
                        <div>
                          <div className="text-base sm:text-lg font-bold">{level.label}</div>
                          <div className="text-xs sm:text-sm opacity-80 mt-1">{level.description}</div>
                        </div>
                        
                        {/* Visual difficulty bars */}
                        <div className="flex space-x-2">
                          {[...Array(3)].map((_, i) => (
                            <div
                              key={i}
                              className={`w-2 h-6 rounded-full transition-all duration-300 ${
                                i < level.bars 
                                  ? `${colorClasses.barBg} shadow-lg` 
                                  : 'bg-gray-700'
                              }`}
                            />
                          ))}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
          </div>

          {/* Resume Upload - Full Width Premium Panel */}
          <div className="bg-gradient-to-br from-black/80 via-purple-900/20 to-black/80 backdrop-blur-3xl border border-purple-500/20 rounded-3xl p-8 shadow-2xl hover:shadow-purple-500/10 transition-all duration-500 mb-12">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Resume Analysis</h3>
                <p className="text-gray-400">Upload your resume for personalized questions (Optional)</p>
              </div>
            </div>
            
            <div className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-500 ${
              resumeContent 
                ? 'border-green-500/50 bg-green-500/10' 
                : 'border-purple-500/30 hover:border-purple-500/60 bg-purple-500/5 hover:bg-purple-500/10'
            }`}>
              {resumeContent ? (
                <div className="space-y-4">
                  <CheckCircle className="w-12 h-12 text-green-400 mx-auto animate-pulse" />
                  <p className="text-green-300 font-medium">Resume content loaded successfully!</p>
                  <p className="text-gray-400 text-sm">AI will use this to create personalized interview questions</p>
                  <button
                    onClick={() => setResumeContent('')}
                    className="text-purple-400 hover:text-purple-300 text-sm font-medium transition-colors"
                  >
                    Upload different resume
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <UploadCloud className="w-12 h-12 text-purple-400 mx-auto group-hover:scale-110 transition-transform duration-300" />
                  <div>
                    <p className="text-white font-medium mb-2">
                      Drag & drop your resume or click to browse
                    </p>
                    <p className="text-gray-400 text-sm">
                      Supports PDF, DOCX, and TXT formats
                    </p>
                  </div>
                  <input
                    type="file"
                    accept=".txt,.pdf,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="resume-upload"
                    disabled={isUploading}
                  />
                  <label
                    htmlFor="resume-upload"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-400 hover:to-pink-500 text-white font-medium rounded-xl cursor-pointer transition-all duration-300 shadow-lg hover:shadow-purple-500/25"
                  >
                    {isUploading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <UploadCloud className="w-4 h-4" />
                        Choose File
                      </>
                    )}
                  </label>
                </div>
              )}
            </div>
          </div>

          {/* Launch Button - Premium Call to Action */}
          <div className="text-center">
            <Button
              onClick={handleStartInterview}
              disabled={isLoading}
              className={`group relative px-12 py-6 font-bold text-xl rounded-2xl shadow-2xl transition-all duration-500 transform border-0 overflow-hidden ${
                !jobRole.trim()
                  ? 'bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-500 hover:to-gray-600 text-gray-300 cursor-pointer hover:shadow-gray-500/20 hover:scale-105'
                  : 'bg-gradient-to-r from-cyan-500 via-purple-600 to-pink-500 hover:from-cyan-400 hover:via-purple-500 hover:to-pink-400 text-white hover:shadow-purple-500/30 hover:scale-105'
              } ${isLoading ? 'opacity-50 cursor-not-allowed transform-none' : ''}`}
            >
              {/* Animated background overlay - only show when job role is selected */}
              {jobRole.trim() && (
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-purple-700 to-pink-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              )}
              
              <div className="relative flex items-center justify-center space-x-3">
                {isLoading ? (
                  <>
                    <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Initializing AI Agents...</span>
                  </>
                ) : !jobRole.trim() ? (
                  <>
                    <span>Start Interview Session</span>
                    <ArrowRight className="w-6 h-6" />
                  </>
                ) : (
                  <>
                    <span>Start Interview Session</span>
                    <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform duration-300" />
                  </>
                )}
              </div>

              {/* Shimmer effect */}
              <div className="absolute inset-0 -top-px overflow-hidden rounded-2xl">
                <div className="animate-shimmer absolute inset-0 -top-px bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12 transform translate-x-[-100%]"></div>
              </div>
            </Button>
            
            {/* Helpful message when job role is missing */}
            {!jobRole.trim() && (
              <p className="mt-4 text-gray-400 text-sm">
                💡 Choose a job role above to start your personalized interview practice
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  // Revolutionary Interactive Feature Constellation
  const renderFeatureConstellation = () => {
    const hoveredFeatureData = featureConstellation.find(f => f.id === hoveredFeature);
    
    return (
      <div ref={featuresSectionRef} className="relative min-h-screen py-16 sm:py-24 overflow-hidden">
        {/* Advanced Multi-layer Background */}
        <div className="absolute inset-0">
          {/* Primary gradient base */}
          <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-950 to-black"></div>
          
          {/* Dynamic mesh gradient overlay */}
          <div 
            className="absolute inset-0 opacity-30"
            style={{
              background: `
                radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(6, 182, 212, 0.15) 0%, transparent 50%),
                radial-gradient(circle at ${100 - mousePosition.x}% ${100 - mousePosition.y}%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
                conic-gradient(from 0deg at 50% 50%, rgba(16, 185, 129, 0.1), rgba(249, 115, 22, 0.1), rgba(34, 197, 94, 0.1), rgba(6, 182, 212, 0.1))
              `
            }}
          />
          
          {/* Floating particle orbs */}
          {[...Array(12)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full opacity-20 animate-pulse"
              style={{
                background: `radial-gradient(circle, ${featureConstellation[i % featureConstellation.length].color}, transparent)`,
                left: `${15 + (i * 7) % 80}%`,
                top: `${10 + (i * 11) % 80}%`,
                animationDelay: `${i * 0.5}s`,
                animationDuration: `${3 + (i % 3)}s`
              }}
            />
          ))}
        </div>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          {/* Section Header */}
          <div className="text-center mb-8 sm:mb-12 lg:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl 2xl:text-7xl font-bold mb-4 sm:mb-6">
              <span className="bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">
                How It Works
              </span>
            </h2>
            <p className="text-lg sm:text-xl lg:text-2xl text-gray-400 max-w-4xl mx-auto leading-relaxed px-4 sm:px-0">
              Discover our comprehensive AI system through an interactive experience
            </p>
          </div>

          {/* Interactive Constellation Container */}
          <div 
            ref={constellationRef}
            className="relative w-full h-[400px] sm:h-[500px] lg:h-[600px] mx-auto"
            onMouseMove={handleMouseMove}
          >
            {/* Central AI Hub Core */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
              <div className="relative">
                {/* Pulsing core orb */}
                <div className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 rounded-full bg-gradient-to-br from-cyan-400 via-purple-500 to-pink-400 shadow-2xl animate-pulse">
                  <div className="absolute inset-1 sm:inset-2 rounded-full bg-gradient-to-br from-cyan-300 via-purple-400 to-pink-300 animate-spin-slow"></div>
                  <div className="absolute inset-2 sm:inset-4 rounded-full bg-gradient-to-br from-white/20 to-transparent backdrop-blur-sm"></div>
                </div>
                
                {/* Core glow effect */}
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-400/20 via-purple-500/20 to-pink-400/20 blur-xl scale-150 animate-pulse"></div>
                
                {/* Central label */}
                <div className="absolute -bottom-6 sm:-bottom-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                  <span className="text-xs sm:text-sm font-semibold text-white/80 px-2 sm:px-3 py-1 rounded-full bg-black/40 backdrop-blur-sm">
                    AI Core
                  </span>
                </div>
              </div>
            </div>

            {/* Feature Orbs with Mobile-Optimized Hover Interactions */}
            {featureConstellation.map((feature, index) => {
              const IconComponent = feature.icon;
              const isHovered = hoveredFeature === feature.id;
              
              return (
                <div
                  key={feature.id}
                  className="absolute group"
                  style={{
                    left: `${feature.position.x}%`,
                    top: `${feature.position.y}%`,
                    transform: 'translate(-50%, -50%)',
                    zIndex: isHovered ? 25 : 15,
                  }}
                  onMouseEnter={() => setHoveredFeature(feature.id)}
                  onMouseLeave={() => setHoveredFeature(null)}
                  onClick={() => {
                    // Toggle feature on mobile touch
                    if (window.innerWidth < 768) {
                      setHoveredFeature(isHovered ? null : feature.id);
                    }
                  }}
                >
                  {/* Feature orb */}
                  <div 
                    className={`relative transition-all duration-500 ease-out ${
                      isHovered ? 'scale-125' : 'scale-100'
                    }`}
                  >
                    <div 
                      className="w-10 h-10 sm:w-12 sm:h-12 lg:w-16 lg:h-16 rounded-full shadow-2xl transition-all duration-500 flex items-center justify-center cursor-pointer"
                      style={{
                        background: `linear-gradient(135deg, ${feature.color}, ${feature.color}dd)`,
                        boxShadow: `
                          0 20px 40px -10px ${feature.color}40,
                          0 0 30px ${feature.color}30,
                          inset 0 2px 4px rgba(255, 255, 255, 0.2)
                        `
                      }}
                    >
                      <IconComponent className="w-5 h-5 sm:w-6 sm:h-6 lg:w-8 lg:h-8 text-white" />
                    </div>
                    
                    {/* Floating animation */}
                    <div 
                      className="absolute inset-0 rounded-full opacity-40 animate-ping"
                      style={{ 
                        background: `radial-gradient(circle, ${feature.glowColor}, transparent)`,
                        animationDuration: `${2 + index * 0.3}s`
                      }}
                    />
                    
                    {/* Feature label */}
                    <div className={`absolute -bottom-8 sm:-bottom-10 left-1/2 transform -translate-x-1/2 whitespace-nowrap transition-all duration-300 ${
                      isHovered ? 'opacity-100 translate-y-0' : 'opacity-70 translate-y-1'
                    }`}>
                      <span className="text-xs font-semibold text-white px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full bg-black/40 backdrop-blur-sm">
                        {feature.title}
                      </span>
                    </div>
                  </div>

                  {/* Mobile-Optimized Hover Card */}
                  {isHovered && (
                <div 
                      className="absolute z-30 pointer-events-none"
                  style={{
                        left: feature.position.x > 50 ? '-260px' : '60px', // Smaller cards for mobile
                        top: '50%',
                        transform: 'translateY(-50%)'
                      }}
                    >
                    <div 
                        className="w-64 sm:w-80 p-4 sm:p-5 rounded-xl sm:rounded-2xl backdrop-blur-2xl border border-white/20 shadow-2xl transform transition-all duration-300 ease-out opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100"
                        style={{
                          background: `linear-gradient(135deg, ${feature.glowColor}, rgba(0, 0, 0, 0.9))`,
                          boxShadow: `0 20px 40px -10px ${feature.color}30`
                        }}
                    >
                        {/* Focused Header */}
                        <div className="mb-3 sm:mb-4">
                          <p className="text-base sm:text-lg font-semibold text-white mb-1 sm:mb-2" style={{ color: feature.color }}>
                            {feature.subtitle}
                      </p>
                          <p className="text-gray-300 text-xs sm:text-sm leading-relaxed">
                            {feature.description}
                      </p>
                        </div>
                      
                        {/* Enhanced Features List */}
                        <div className="space-y-2 sm:space-y-3">
                          <h5 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Key Capabilities</h5>
                          {feature.features.map((feat, idx) => (
                            <div key={idx} className="flex items-start gap-2 sm:gap-3 text-xs sm:text-sm">
                            <div 
                                className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full flex-shrink-0 mt-1.5 sm:mt-2"
                                style={{ backgroundColor: feature.color }}
                            />
                              <span className="text-gray-300 leading-relaxed">{feat}</span>
                          </div>
                        ))}
                    </div>
                    
                        {/* Optional: Add a subtle gradient accent */}
                        <div 
                          className="absolute top-0 left-0 right-0 h-0.5 sm:h-1 rounded-t-xl sm:rounded-t-2xl"
                          style={{ background: `linear-gradient(90deg, ${feature.color}, ${feature.color}80)` }}
                        />
                </div>
              </div>
            )}
                </div>
              );
            })}


          </div>

          {/* Interactive Instructions */}
          <div className="text-center mt-12 sm:mt-16">
            <p className="text-gray-400 text-base sm:text-lg mb-3 sm:mb-4 px-4 sm:px-0">
              <span className="hidden sm:inline">Hover over</span>
              <span className="sm:hidden">Tap</span> the floating elements to explore our AI system features
            </p>
            <div className="flex justify-center items-center gap-2 sm:gap-4">
              {featureConstellation.map((feature, index) => (
                <div
                  key={feature.id}
                  className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full transition-all duration-300 ${
                    hoveredFeature === feature.id
                      ? 'scale-125 shadow-lg'
                      : 'scale-100'
                  }`}
                  style={{ 
                    backgroundColor: hoveredFeature === feature.id ? feature.color : feature.color + '60',
                    boxShadow: hoveredFeature === feature.id ? `0 0 20px ${feature.color}60` : 'none'
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render footer
  const renderFooter = () => {
    if (state !== 'configuring') return null;
    
    return (
      <footer className="py-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-black/0 to-purple-900/5 z-0"></div>
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-5xl xl:max-w-6xl mx-auto">
            <div className="flex flex-col items-center justify-center">
              <div className="flex items-center mb-4">
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
              
              <p className="text-gray-400 text-center mb-4 max-w-md">
                Enhance your interview skills with our AI-powered simulator. Practice, get feedback, and improve.
              </p>
              
              <div className="flex justify-center space-x-4 mb-6">
                <a href="https://github.com/Ranjit2111/AI-Interview-Agent" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-cyan-500/30 hover:shadow-cyan-500/20 transition-all duration-300">
                  <Github className="h-5 w-5 text-gray-300 hover:text-cyan-400" />
                </a>
                <a href="https://x.com/Ranjit_AI" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-purple-500/30 hover:shadow-purple-500/20 transition-all duration-300">
                  <Twitter className="h-5 w-5 text-gray-300 hover:text-purple-400" />
                </a>
                <a href="https://www.linkedin.com/in/ranjit-n/" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-pink-500/30 hover:shadow-pink-500/20 transition-all duration-300">
                  <Linkedin className="h-5 w-5 text-gray-300 hover:text-pink-400" />
                </a>
                <a href="mailto:ranjitn.dev@gmail.com" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-cyan-500/30 hover:shadow-cyan-500/20 transition-all duration-300">
                  <Mail className="h-5 w-5 text-gray-300 hover:text-cyan-400" />
                </a>
              </div>
              
              <div className="text-center text-sm text-gray-500">
                <p>© 2025 AI Interviewer. All rights reserved.</p>
              </div>
            </div>
          </div>
        </div>
      </footer>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-black text-gray-100 relative overflow-hidden">
      {state !== 'interviewing' && state !== 'post_interview' && (
        <Header 
          showReset={state === 'completed'} 
          onReset={actions.resetInterview}
        />
      )}
      
      <main className="flex-1 flex flex-col">
        {state === 'configuring' && (
          <>
            {renderHeroSection()}
            {renderFeatureConstellation()}
            {renderConfigurationForm()}
            {renderFooter()}
          </>
        )}
        
        {state === 'interviewing' && (
          <InterviewSession 
            messages={messages}
            isLoading={isLoading}
            onSendMessage={actions.sendMessage}
            onEndInterview={actions.endInterview}
            onVoiceSelect={actions.setSelectedVoice}
            coachFeedbackStates={coachFeedbackStates}
            sessionId={sessionId}
          />
        )}

        {state === 'post_interview' && postInterviewState && (
          <PostInterviewReport 
            perTurnFeedback={postInterviewState.perTurnFeedback}
            finalSummary={postInterviewState.finalSummary}
            resources={postInterviewState.resources}
            onStartNewInterview={actions.resetInterview}
            onGoHome={actions.resetInterview}
          />
        )}
        
        {state === 'completed' && results?.coachingSummary && (
          <InterviewResults 
            coachingSummary={results.coachingSummary} 
            onStartNewInterview={actions.resetInterview} 
          />
        )}
      </main>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />

      {/* Enhanced Custom Styles for Advanced Animations */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes scale-x {
            from { transform: scaleX(0); }
            to { transform: scaleX(1); }
          }
          
          @keyframes spin-slow {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          
          @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
          }
          
          @keyframes pulse-glow {
            0%, 100% { opacity: 0.4; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.1); }
          }
          
          @keyframes constellation-orbit {
            0% { transform: rotate(0deg) translateX(50px) rotate(0deg); }
            100% { transform: rotate(360deg) translateX(50px) rotate(-360deg); }
          }
          
          .animate-spin-slow {
            animation: spin-slow 8s linear infinite;
          }
          
          .animate-float {
            animation: float 3s ease-in-out infinite;
          }
          
          .animate-pulse-glow {
            animation: pulse-glow 2s ease-in-out infinite;
          }
          
          .animate-constellation-orbit {
            animation: constellation-orbit 20s linear infinite;
          }
          
          .scrollbar-hide {
            -ms-overflow-style: none;
            scrollbar-width: none;
          }
          
          .scrollbar-hide::-webkit-scrollbar {
            display: none;
          }
          
          .slider::-webkit-slider-thumb {
            appearance: none;
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: linear-gradient(45deg, #06b6d4, #8b5cf6);
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
          }
          
          .slider::-moz-range-thumb {
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: linear-gradient(45deg, #06b6d4, #8b5cf6);
            cursor: pointer;
            border: none;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
          }
          
          /* Premium slider for duration */
          .slider-premium::-webkit-slider-thumb {
            appearance: none;
            height: 24px;
            width: 24px;
            border-radius: 50%;
            background: linear-gradient(45deg, #f97316, #ef4444);
            cursor: pointer;
            box-shadow: 0 6px 16px rgba(249, 115, 22, 0.5);
            border: 2px solid white;
            transition: all 0.3s ease;
          }
          
          .slider-premium::-webkit-slider-thumb:hover {
            transform: scale(1.2);
            box-shadow: 0 8px 20px rgba(249, 115, 22, 0.7);
          }
          
          .slider-premium::-moz-range-thumb {
            height: 24px;
            width: 24px;
            border-radius: 50%;
            background: linear-gradient(45deg, #f97316, #ef4444);
            cursor: pointer;
            border: 2px solid white;
            box-shadow: 0 6px 16px rgba(249, 115, 22, 0.5);
            transition: all 0.3s ease;
          }
          
          .slider-premium::-moz-range-thumb:hover {
            transform: scale(1.2);
            box-shadow: 0 8px 20px rgba(249, 115, 22, 0.7);
          }
          
          /* Shimmer animation for launch button */
          @keyframes shimmer {
            0% { transform: translateX(-100%) skewX(-12deg); }
            100% { transform: translateX(200%) skewX(-12deg); }
          }
          
          .animate-shimmer {
            animation: shimmer 2s ease-in-out infinite;
          }
          

          
          /* Gentle shake animation for invalid submission */
          @keyframes gentle-shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
          }
          
          .animate-gentle-shake {
            animation: gentle-shake 0.5s ease-in-out;
          }
          
          /* Enhanced hero typography effects */
          @keyframes hero-text-glow {
            0%, 100% { text-shadow: 0 0 20px rgba(255, 255, 255, 0.1); }
            50% { text-shadow: 0 0 30px rgba(255, 255, 255, 0.2), 0 0 40px rgba(255, 255, 255, 0.1); }
          }
          
          .hero-title {
            animation: hero-text-glow 4s ease-in-out infinite;
          }
          
          /* Better text rendering */
          .hero-text {
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
          }
        `
      }} />
    </div>
  );
};

export default Index;