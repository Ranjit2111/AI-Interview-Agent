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
  
  // Advanced interaction states
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [activeFloatingElement, setActiveFloatingElement] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  
  // Feature Constellation states
  const [activeFeature, setActiveFeature] = useState<string | null>(null);
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);
  const [constellationMode, setConstellationMode] = useState<'overview' | 'spotlight'>('overview');
  
  // Configuration state
  const [jobRole, setJobRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [resumeContent, setResumeContent] = useState('');
  const [style, setStyle] = useState<'formal' | 'casual' | 'aggressive' | 'technical'>('formal');
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [interviewDuration, setInterviewDuration] = useState(10);
  const [company, setCompany] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  
  const heroRef = useRef<HTMLDivElement>(null);
  const configSectionRef = useRef<HTMLDivElement>(null);
  const featuresSectionRef = useRef<HTMLDivElement>(null);
  const constellationRef = useRef<HTMLDivElement>(null);

  // Enhanced mouse tracking for 3D effects
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

  // Auto-cycle floating elements
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveFloatingElement((prev) => (prev + 1) % 3);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

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
        'Adapts to your experience level', 
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
      title: 'Real-time Coach',
      subtitle: 'Silent Performance Analysis',
      description: 'Get instant feedback on your communication patterns, confidence levels, and areas for improvement.',
      features: [
        'Analyzes your speaking patterns',
        'Detects confidence and clarity',
        'Provides actionable feedback'
      ],
      icon: Brain,
      position: { x: 20, y: 25 },
      color: '#8b5cf6',
      gradient: 'from-purple-500 to-pink-600',
      glowColor: 'rgba(139, 92, 246, 0.4)',
    },
    {
      id: 'learning-engine',
      title: 'Smart Learning Engine', 
      subtitle: 'Personalized Growth Path',
      description: 'Receive curated learning resources and practice recommendations based on your performance.',
      features: [
        'Identifies skill gaps automatically',
        'Curated learning resources',
        'Track your progress over time'
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
      description: 'Powered by cutting-edge AI for crystal-clear voice recognition and natural speech synthesis.',
      features: [
        'Industry-leading voice recognition',
        'Natural-sounding AI responses',
        'Real-time audio processing'
      ],
      icon: Mic,
      position: { x: 25, y: 70 },
      color: '#f97316',
      gradient: 'from-orange-500 to-red-600',
      glowColor: 'rgba(249, 115, 22, 0.4)',
    },
    {
      id: 'data-security',
      title: 'Enterprise Security',
      subtitle: 'Your Data Protected',
      description: 'Bank-level encryption and secure cloud storage ensure your interview data remains private and protected.',
      features: [
        'End-to-end encryption',
        'Secure cloud storage', 
        'GDPR compliant data handling'
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
      toast({ title: "Missing Field", description: "Job Role is required.", variant: "destructive" });
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

  // Advanced floating orbs background
  const renderAdvancedBackground = () => (
    <div className="absolute inset-0 overflow-hidden">
      {/* Primary floating orbs with physics */}
      <div 
        className="absolute w-96 h-96 rounded-full opacity-20 blur-3xl transition-all duration-[3000ms] ease-in-out"
        style={{
          background: 'radial-gradient(circle, rgba(34, 211, 238, 0.4) 0%, rgba(168, 85, 247, 0.2) 50%, transparent 100%)',
          transform: `translate(${20 + mousePosition.x * 0.5}px, ${10 + mousePosition.y * 0.3}px) scale(${activeFloatingElement === 0 ? 1.2 : 1})`,
          top: '10%',
          left: '60%',
        }}
      />
      <div 
        className="absolute w-80 h-80 rounded-full opacity-25 blur-2xl transition-all duration-[2500ms] ease-in-out"
        style={{
          background: 'radial-gradient(circle, rgba(168, 85, 247, 0.5) 0%, rgba(236, 72, 153, 0.3) 50%, transparent 100%)',
          transform: `translate(${-mousePosition.x * 0.3}px, ${-mousePosition.y * 0.4}px) scale(${activeFloatingElement === 1 ? 1.3 : 1})`,
          bottom: '20%',
          left: '10%',
        }}
      />
      <div 
        className="absolute w-64 h-64 rounded-full opacity-30 blur-xl transition-all duration-[2000ms] ease-in-out"
        style={{
          background: 'radial-gradient(circle, rgba(34, 197, 94, 0.4) 0%, rgba(34, 211, 238, 0.3) 50%, transparent 100%)',
          transform: `translate(${mousePosition.x * 0.2}px, ${mousePosition.y * 0.5}px) scale(${activeFloatingElement === 2 ? 1.1 : 1})`,
          top: '50%',
          right: '5%',
        }}
      />
      
      {/* Geometric accent shapes */}
      <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-cyan-400 rounded-full animate-pulse opacity-60" />
      <div className="absolute top-3/4 right-1/3 w-3 h-3 bg-purple-400 rotate-45 animate-bounce opacity-40" />
      <div className="absolute bottom-1/3 left-2/3 w-1 h-8 bg-gradient-to-b from-pink-400 to-transparent animate-pulse" />
      
      {/* Dynamic mesh gradient overlay */}
      <div 
        className="absolute inset-0 opacity-30"
        style={{
          background: `
            radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(34, 211, 238, 0.1) 0%, transparent 50%),
            radial-gradient(circle at ${100 - mousePosition.x}% ${100 - mousePosition.y}%, rgba(168, 85, 247, 0.1) 0%, transparent 50%)
          `
        }}
      />
    </div>
  );

  // Revolutionary Hero Section
  const renderHeroSection = () => (
    <div 
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
      ref={heroRef}
      onMouseMove={handleMouseMove}
    >
      {renderAdvancedBackground()}
      
      {/* Centered Hero Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-20">
        <div className="max-w-5xl xl:max-w-6xl 2xl:max-w-7xl mx-auto text-center">
          
          {/* Badge */}
          <div className={`inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-600/20 border border-purple-500/30 backdrop-blur-sm mb-8 transition-all duration-1000 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 -translate-y-8'}`}>
            <Sparkles className="w-4 h-4 text-cyan-300" />
            <span className="text-sm font-semibold text-cyan-300 tracking-wider">Introducing AI Interview System</span>
          </div>

          {/* Main Headline with Modern Typography */}
          <div className={`space-y-6 mb-12 transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 -translate-y-12'}`}>
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold leading-tight">
              <span className="bg-gradient-to-r from-white to-gray-200 bg-clip-text text-transparent">
                Modern AI for the
              </span>
              <br />
              <span className="relative">
                <span className="bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                  next generation
                </span>
                {/* Stylish underline */}
                <div className="absolute bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 transform scale-x-0 animate-[scale-x_1s_ease-out_0.8s_forwards] origin-left"></div>
              </span>
            </h1>
            
            <p className="text-lg sm:text-xl lg:text-2xl text-gray-300 max-w-3xl xl:max-w-4xl mx-auto leading-relaxed font-light">
              Practice with AI-powered agents that provide real-time coaching 
              and personalized learning recommendations.
            </p>
          </div>

          {/* Action Buttons */}
          <div className={`flex flex-col sm:flex-row gap-6 justify-center items-center mb-16 transition-all duration-1000 delay-400 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'}`}>
            <Button
              onClick={scrollToConfig}
              className="w-full sm:w-auto bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white px-8 py-4 rounded-2xl text-lg font-semibold shadow-2xl hover:shadow-purple-500/25 transition-all duration-300 group border-0 min-h-[56px]"
            >
              Get Started
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </Button>
            
            <Button
              onClick={scrollToFeatures}
              variant="outline"
              className="w-full sm:w-auto border-2 border-white/20 bg-black/20 hover:bg-white/10 text-white px-8 py-4 rounded-2xl text-lg font-semibold backdrop-blur-sm hover:border-cyan-500/50 transition-all duration-300 min-h-[56px]"
            >
              Know More
            </Button>
          </div>

          {/* Real Statistics */}
          <div className={`grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8 max-w-2xl xl:max-w-3xl mx-auto transition-all duration-1000 delay-600 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 translate-y-12'}`}>
            <div className="text-center group cursor-default">
              <div className="flex items-center justify-center mb-2">
                <Clock className="w-6 h-6 text-cyan-400 mr-2" />
              </div>
              <div className="text-3xl font-bold text-cyan-400 group-hover:scale-110 transition-transform">24/7</div>
              <div className="text-sm text-gray-400 tracking-wide">Available</div>
            </div>
            
            <div className="text-center group cursor-default">
              <div className="flex items-center justify-center mb-2">
                <Volume2 className="w-6 h-6 text-purple-400 mr-2" />
              </div>
              <div className="text-3xl font-bold text-purple-400 group-hover:scale-110 transition-transform">Voice</div>
              <div className="text-sm text-gray-400 tracking-wide">Enabled</div>
            </div>
            
            <div className="text-center group cursor-default">
              <div className="flex items-center justify-center mb-2">
                <Lightning className="w-6 h-6 text-pink-400 mr-2" />
              </div>
              <div className="text-3xl font-bold text-pink-400 group-hover:scale-110 transition-transform">Instant</div>
              <div className="text-sm text-gray-400 tracking-wide">Feedback</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Configuration Form Section - Completely Redesigned
  const renderConfigurationForm = () => (
    <div ref={configSectionRef} className="py-24 relative overflow-hidden">
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
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-600/20 border border-purple-500/30 backdrop-blur-sm mb-6">
              <Settings className="w-4 h-4 text-cyan-300" />
              <span className="text-sm font-semibold text-cyan-300 tracking-wider">Interview Configuration</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">
                Craft Your Perfect
              </span>
              <br />
              <span className="text-white">Interview Experience</span>
            </h2>
            <p className="text-gray-400 text-xl max-w-3xl xl:max-w-4xl mx-auto leading-relaxed">
              Configure every aspect of your practice session with our intelligent wizard
            </p>
          </div>

          {/* Revolutionary Bento Grid Configuration */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-12">
            
            {/* Job Role Selection - Large Featured Panel */}
            <div className="lg:col-span-8 bg-gradient-to-br from-black/80 via-gray-900/80 to-black/80 backdrop-blur-3xl border border-white/10 rounded-3xl p-6 sm:p-8 shadow-2xl hover:shadow-cyan-500/10 transition-all duration-500 group">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 shadow-lg">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white group-hover:text-cyan-300 transition-colors">Target Role</h3>
                  <p className="text-gray-400">What position are you preparing for?</p>
                </div>
                <span className="ml-auto px-3 py-1 rounded-full bg-red-500/20 text-red-300 text-xs font-medium">Required</span>
              </div>
              
              {/* Popular roles with advanced hover effects */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                {popularRoles.map((role, index) => (
                  <button
                    key={role.title}
                    onClick={() => setJobRole(role.title)}
                    className={`relative p-4 rounded-xl border transition-all duration-500 text-left group/role overflow-hidden ${
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
                    
                    <div className="relative flex items-center space-x-3">
                      <span className="text-2xl transform group-hover/role:scale-110 transition-transform duration-300">{role.icon}</span>
                      <span className="text-sm font-medium group-hover/role:text-white transition-colors">
                        {role.title}
                      </span>
                    </div>
                    
                    {/* Selection indicator */}
                    {jobRole === role.title && (
                      <div className="absolute top-2 right-2">
                        <CheckCircle className="w-5 h-5 text-white animate-pulse" />
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
                  className="bg-black/60 border-white/20 text-white placeholder-gray-400 rounded-xl px-4 py-4 text-lg focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all duration-300 hover:border-white/30"
                />
                {jobRole && !popularRoles.find(r => r.title === jobRole) && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <Sparkles className="w-5 h-5 text-purple-400 animate-pulse" />
                  </div>
                )}
              </div>
            </div>

            {/* Company & Duration - Right Side Panels */}
            <div className="lg:col-span-4 space-y-6">
              
              {/* Company Selection */}
              <div className="bg-gradient-to-br from-purple-900/30 via-black/80 to-purple-900/30 backdrop-blur-3xl border border-purple-500/20 rounded-2xl p-6 shadow-xl hover:shadow-purple-500/10 transition-all duration-500">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 shadow-md">
                    <Building2 className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">Company</h3>
                    <p className="text-xs text-gray-400">Optional context</p>
                  </div>
                </div>
                <Input
                  placeholder="Google, Microsoft, StartupCo..."
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="bg-black/60 border-purple-500/20 text-white placeholder-gray-500 rounded-xl focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300"
                />
              </div>

              {/* Duration with Visual Feedback */}
              <div className="bg-gradient-to-br from-orange-900/30 via-black/80 to-orange-900/30 backdrop-blur-3xl border border-orange-500/20 rounded-2xl p-6 shadow-xl hover:shadow-orange-500/10 transition-all duration-500">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-orange-500 to-red-600 shadow-md">
                    <Clock className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">Duration</h3>
                    <p className="text-xs text-gray-400">{interviewDuration} minutes</p>
                  </div>
                </div>
                
                {/* Premium slider with visual feedback */}
                <div className="space-y-3">
                  <input
                    type="range"
                    min="5"
                    max="30"
                    value={interviewDuration}
                    onChange={(e) => setInterviewDuration(parseInt(e.target.value))}
                    className="w-full h-3 bg-gray-800 rounded-lg appearance-none cursor-pointer slider-premium"
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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
            
            {/* Interview Style Selection */}
            <div className="bg-gradient-to-br from-black/80 via-blue-900/20 to-black/80 backdrop-blur-3xl border border-blue-500/20 rounded-3xl p-8 shadow-2xl hover:shadow-blue-500/10 transition-all duration-500">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 shadow-lg">
                  <MessageSquare className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">Interview Style</h3>
                  <p className="text-gray-400">Choose your preferred interaction mode</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {interviewStyles.map((styleOption) => (
                  <button
                    key={styleOption.value}
                    onClick={() => setStyle(styleOption.value as any)}
                    className={`relative p-7 rounded-xl border text-left transition-all duration-500 overflow-hidden group/style ${
                      style === styleOption.value
                        ? `border-${styleOption.color}-500 bg-${styleOption.color}-500/20 text-white shadow-lg`
                        : 'border-white/10 bg-black/40 text-gray-400 hover:text-white hover:border-white/20'
                    }`}
                  >
                    {/* Advanced hover glow */}
                    <div className={`absolute inset-0 bg-gradient-to-br from-${styleOption.color}-500/10 to-${styleOption.color}-600/10 opacity-0 group-hover/style:opacity-100 transition-opacity duration-500 rounded-xl`}></div>
                    
                    <div className="relative">
                      <div className="text-lg font-bold mb-3">{styleOption.label}</div>
                      <div className="text-sm opacity-80">{styleOption.description}</div>
                      
                      {/* Selection indicator */}
                      {style === styleOption.value && (
                        <div className="absolute top-0 right-0">
                          <div className={`w-3 h-3 rounded-full bg-${styleOption.color}-500 animate-pulse`}></div>
                        </div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty Level with Visual Bars */}
            <div className="bg-gradient-to-br from-black/80 via-gray-900/20 to-black/80 backdrop-blur-3xl border border-gray-500/20 rounded-3xl p-8 shadow-2xl hover:shadow-orange-500/10 transition-all duration-500">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-gray-500 to-gray-600 shadow-lg">
                    <BarChart3 className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">Difficulty Level</h3>
                    <p className="text-gray-400">Adjust challenge complexity</p>
                  </div>
                </div>

                <div className="space-y-4">
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
                        className={`w-full p-6 rounded-xl border text-left transition-all duration-500 flex items-center justify-between hover:shadow-lg ${
                          difficulty === level.value
                            ? `${colorClasses.border} ${colorClasses.bg} text-white scale-105 shadow-lg ${colorClasses.shadow}`
                            : `border-white/10 bg-black/40 text-gray-400 hover:text-white hover:border-white/20 ${colorClasses.hoverShadow}`
                        }`}
                      >
                        <div>
                          <div className="text-lg font-bold">{level.label}</div>
                          <div className="text-sm opacity-80 mt-1">{level.description}</div>
                        </div>
                        
                        {/* Visual difficulty bars */}
                        <div className="flex space-x-2">
                          {[...Array(3)].map((_, i) => (
                            <div
                              key={i}
                              className={`w-3 h-8 rounded-full transition-all duration-300 ${
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
              disabled={!jobRole.trim() || isLoading}
              className="group relative px-12 py-6 bg-gradient-to-r from-cyan-500 via-purple-600 to-pink-500 hover:from-cyan-400 hover:via-purple-500 hover:to-pink-400 text-white font-bold text-xl rounded-2xl shadow-2xl hover:shadow-purple-500/30 transition-all duration-500 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none border-0 overflow-hidden"
            >
              {/* Animated background overlay */}
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-purple-700 to-pink-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              
              <div className="relative flex items-center justify-center space-x-3">
                {isLoading ? (
                  <>
                    <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Initializing AI Agents...</span>
                  </>
                ) : (
                  <>
                    <span>Launch Interview Session</span>
                    <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform duration-300" />
                  </>
                )}
              </div>

              {/* Shimmer effect */}
              <div className="absolute inset-0 -top-px overflow-hidden rounded-2xl">
                <div className="animate-shimmer absolute inset-0 -top-px bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12 transform translate-x-[-100%]"></div>
              </div>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  // Revolutionary Interactive Feature Constellation
  const renderFeatureConstellation = () => {
    const activeFeatureData = featureConstellation.find(f => f.id === activeFeature);
    
    return (
      <div ref={featuresSectionRef} className="relative min-h-screen py-24 overflow-hidden">
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
              className="absolute w-2 h-2 rounded-full opacity-20 animate-pulse"
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
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold mb-6">
              <span className="bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">
                How It Works
              </span>
            </h2>
            <p className="text-2xl text-gray-400 max-w-4xl mx-auto leading-relaxed">
              Discover our comprehensive AI system through an interactive experience
            </p>
          </div>

          {/* Interactive Constellation Container */}
          <div 
            ref={constellationRef}
            className="relative w-full h-[500px] sm:h-[600px] mx-auto"
            onMouseMove={handleMouseMove}
          >
            {/* Central AI Hub Core */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
              <div className="relative">
                {/* Pulsing core orb */}
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-400 via-purple-500 to-pink-400 shadow-2xl animate-pulse">
                  <div className="absolute inset-2 rounded-full bg-gradient-to-br from-cyan-300 via-purple-400 to-pink-300 animate-spin-slow"></div>
                  <div className="absolute inset-4 rounded-full bg-gradient-to-br from-white/20 to-transparent backdrop-blur-sm"></div>
                </div>
                
                {/* Core glow effect */}
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-400/20 via-purple-500/20 to-pink-400/20 blur-xl scale-150 animate-pulse"></div>
                
                {/* Central label */}
                <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                  <span className="text-sm font-semibold text-white/80 px-3 py-1 rounded-full bg-black/30 backdrop-blur-sm">
                    AI Core
                  </span>
                </div>
              </div>
            </div>

            {/* Feature Orbs with Advanced Interactions */}
            {featureConstellation.map((feature, index) => {
              const IconComponent = feature.icon;
              const isHovered = hoveredFeature === feature.id;
              const isActive = activeFeature === feature.id;
              
              return (
                <div
                  key={feature.id}
                  className="absolute cursor-pointer group"
                  style={{
                    left: `${feature.position.x}%`,
                    top: `${feature.position.y}%`,
                    transform: 'translate(-50%, -50%)',
                    zIndex: isActive ? 30 : isHovered ? 25 : 15,
                  }}
                  onMouseEnter={() => setHoveredFeature(feature.id)}
                  onMouseLeave={() => setHoveredFeature(null)}
                  onTouchStart={() => setHoveredFeature(feature.id)}
                  onClick={() => {
                    if (activeFeature === feature.id) {
                      setActiveFeature(null);
                      setConstellationMode('overview');
                    } else {
                      setActiveFeature(feature.id);
                      setConstellationMode('spotlight');
                    }
                  }}
                >
                  {/* Feature orb */}
                  <div 
                    className={`relative transition-all duration-500 ease-out ${
                      isHovered || isActive ? 'scale-125' : 'scale-100'
                    }`}
                  >
                    <div 
                      className={`w-16 h-16 rounded-full shadow-2xl transition-all duration-500 flex items-center justify-center ${
                        isActive ? 'scale-110' : ''
                      }`}
                      style={{
                        background: `linear-gradient(135deg, ${feature.color}, ${feature.color}dd)`,
                        boxShadow: `
                          0 20px 40px -10px ${feature.color}40,
                          0 0 30px ${feature.color}30,
                          inset 0 2px 4px rgba(255, 255, 255, 0.2)
                        `
                      }}
                    >
                      <IconComponent className="w-8 h-8 text-white" />
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
                    <div className={`absolute -bottom-10 left-1/2 transform -translate-x-1/2 whitespace-nowrap transition-all duration-300 ${
                      isHovered || isActive ? 'opacity-100 translate-y-0' : 'opacity-70 translate-y-1'
                    }`}>
                      <span className="text-xs font-semibold text-white px-2 py-1 rounded-full bg-black/40 backdrop-blur-sm">
                        {feature.title}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Feature Spotlight Panel */}
            {activeFeatureData && constellationMode === 'spotlight' && (
              <div className="absolute inset-0 flex items-center justify-center z-40">
                <div 
                  className="w-full max-w-4xl mx-4 p-8 rounded-3xl backdrop-blur-3xl border border-white/20 shadow-2xl transform transition-all duration-500 ease-out"
                  style={{
                    background: `linear-gradient(135deg, ${activeFeatureData.glowColor}, rgba(0, 0, 0, 0.8))`,
                    boxShadow: `0 25px 50px -12px ${activeFeatureData.color}40`
                  }}
                >
                  <div className="flex items-start gap-8">
                    {/* Feature Icon */}
                    <div 
                      className="flex-shrink-0 w-24 h-24 rounded-2xl flex items-center justify-center shadow-lg"
                      style={{ background: `linear-gradient(135deg, ${activeFeatureData.color}, ${activeFeatureData.color}dd)` }}
                    >
                      <activeFeatureData.icon className="w-12 h-12 text-white" />
                    </div>
                    
                    {/* Feature Content */}
                    <div className="flex-1">
                      <h3 className="text-4xl font-bold text-white mb-2">{activeFeatureData.title}</h3>
                      <p className="text-xl font-semibold mb-4" style={{ color: activeFeatureData.color }}>
                        {activeFeatureData.subtitle}
                      </p>
                      <p className="text-gray-300 text-lg leading-relaxed mb-6">
                        {activeFeatureData.description}
                      </p>
                      
                      {/* Features list */}
                      <div className="space-y-3">
                        {activeFeatureData.features.map((feature, idx) => (
                          <div key={idx} className="flex items-center gap-3">
                            <div 
                              className="w-2 h-2 rounded-full flex-shrink-0"
                              style={{ backgroundColor: activeFeatureData.color }}
                            />
                            <span className="text-gray-300">{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {/* Close button */}
                    <button
                      onClick={() => {
                        setActiveFeature(null);
                        setConstellationMode('overview');
                      }}
                      className="text-white/60 hover:text-white transition-colors duration-200 p-2"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Interactive Instructions */}
          <div className="text-center mt-16">
            <p className="text-gray-400 text-lg mb-4">
              {constellationMode === 'overview' 
                ? 'Hover over the floating elements to explore • Click to learn more'
                : 'Click anywhere outside to return to overview'
              }
            </p>
            <div className="flex justify-center items-center gap-4">
              {featureConstellation.map((feature, index) => (
                <div
                  key={feature.id}
                  className={`w-3 h-3 rounded-full transition-all duration-300 ${
                    activeFeature === feature.id
                      ? 'scale-125 shadow-lg'
                      : hoveredFeature === feature.id
                      ? 'scale-110'
                      : 'scale-100'
                  }`}
                  style={{ 
                    backgroundColor: activeFeature === feature.id ? feature.color : feature.color + '60',
                    boxShadow: activeFeature === feature.id ? `0 0 20px ${feature.color}60` : 'none'
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
                <a href="mailto:ranjitnagaraj2131@gmail.com" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-cyan-500/30 hover:shadow-cyan-500/20 transition-all duration-300">
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
        `
      }} />
    </div>
  );
};

export default Index;