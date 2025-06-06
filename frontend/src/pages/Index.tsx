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
  ChevronDown, Sparkles, Zap, BarChart3, Bot, Github, Linkedin, Twitter, Mail, 
  Save, History, Award, Users, BriefcaseBusiness, Building2, FileText, UploadCloud, 
  Settings, ArrowRight, Play, Star, TrendingUp, Target, CheckCircle, ArrowUpRight, 
  BookOpen, Headphones, Brain, Search, ChevronRight, Clock, Volume2, MessageSquare,
  Zap as Lightning 
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
  const [currentCapabilityCard, setCurrentCapabilityCard] = useState(0);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  
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
  const capabilitiesRef = useRef<HTMLDivElement>(null);

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
  const scrollToCapabilities = () => {
    capabilitiesRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToConfig = () => {
    configSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Capability cards data
  const capabilityCards = [
    {
      id: 'interview-agent',
      title: 'AI Interview Agent',
      subtitle: 'Intelligent Conversation Partner',
      description: 'Our advanced AI interviewer adapts to your responses in real-time, asking follow-up questions and providing a natural interview experience.',
      features: [
        'Voice-enabled conversation with natural speech processing',
        'Dynamic question generation based on your role and experience',
        'Real-time adaptation to your answers and speaking style',
        'Multiple interview styles: Technical, Behavioral, Case Study'
      ],
      icon: Bot,
      gradient: 'from-cyan-500 to-blue-600',
      accentColor: 'cyan'
    },
    {
      id: 'coach-agent',
      title: 'Background Coach Analysis',
      subtitle: 'Real-time Performance Monitoring',
      description: 'While you interview, our coach agent silently analyzes your responses, identifying strengths and areas for improvement.',
      features: [
        'Continuous analysis of communication patterns',
        'Real-time detection of filler words and hesitations',
        'Assessment of technical accuracy and depth',
        'Evaluation of storytelling and structure quality'
      ],
      icon: Brain,
      gradient: 'from-purple-500 to-pink-600',
      accentColor: 'purple'
    },
    {
      id: 'recommendations',
      title: 'Smart Resource Engine',
      subtitle: 'Personalized Learning Paths',
      description: 'After your interview, get curated learning resources based on identified skill gaps, powered by intelligent search algorithms.',
      features: [
        'Automated skill gap analysis from your performance',
        'Curated learning resources via Serper Dev search',
        'Personalized improvement recommendations',
        'Track progress across multiple interview sessions'
      ],
      icon: Search,
      gradient: 'from-emerald-500 to-teal-600',
      accentColor: 'emerald'
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
    { value: 'medium', label: 'Intermediate', description: 'Standard interview complexity', bars: 2, color: 'yellow' },
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
      <div className="container mx-auto px-4 relative z-20">
        <div className="max-w-5xl mx-auto text-center">
          
          {/* Badge */}
          <div className={`inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-600/20 border border-purple-500/30 backdrop-blur-sm mb-8 transition-all duration-1000 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 -translate-y-8'}`}>
            <Sparkles className="w-4 h-4 text-cyan-300" />
            <span className="text-sm font-semibold text-cyan-300 tracking-wider">Introducing AI Interview System</span>
          </div>

          {/* Main Headline with Modern Typography */}
          <div className={`space-y-6 mb-12 transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 -translate-y-12'}`}>
            <h1 className="text-5xl lg:text-7xl font-bold leading-tight">
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
            
            <p className="text-xl lg:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed font-light">
              Practice with AI-powered agents that provide real-time coaching 
              and personalized learning recommendations.
            </p>
          </div>

          {/* Action Buttons */}
          <div className={`flex flex-col sm:flex-row gap-6 justify-center items-center mb-16 transition-all duration-1000 delay-400 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'}`}>
            <Button
              onClick={scrollToConfig}
              className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white px-8 py-4 rounded-2xl text-lg font-semibold shadow-2xl hover:shadow-purple-500/25 transition-all duration-300 group border-0"
            >
              Get Started
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </Button>
            
            <Button
              onClick={scrollToCapabilities}
              variant="outline"
              className="border-2 border-white/20 bg-black/20 hover:bg-white/10 text-white px-8 py-4 rounded-2xl text-lg font-semibold backdrop-blur-sm hover:border-cyan-500/50 transition-all duration-300"
            >
              Know More
            </Button>
          </div>

          {/* Real Statistics */}
          <div className={`grid grid-cols-3 gap-8 max-w-2xl mx-auto transition-all duration-1000 delay-600 ${isVisible ? 'opacity-100 transform-none' : 'opacity-0 translate-y-12'}`}>
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

  // Horizontal Scrolling Capability Cards
  const renderCapabilityCards = () => (
    <div ref={capabilitiesRef} className="py-24 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-black via-gray-900/50 to-black"></div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-cyan-300 via-purple-400 to-pink-300 bg-clip-text text-transparent">
              How It Works
            </span>
          </h2>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Discover the three powerful AI agents working together to deliver your personalized interview experience
          </p>
        </div>

        {/* Horizontal Scrolling Cards Container */}
        <div className="relative">
          <div className="flex gap-8 overflow-x-auto pb-8 snap-x snap-mandatory scrollbar-hide">
            {capabilityCards.map((card, index) => {
              const IconComponent = card.icon;
              return (
                <div
                  key={card.id}
                  className="flex-none w-96 snap-center"
                >
                  <div className="bg-black/60 backdrop-blur-2xl border border-white/20 rounded-3xl p-8 h-full hover:border-purple-500/40 transition-all duration-500 group hover:scale-105">
                    <div className="space-y-6">
                      {/* Icon */}
                      <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${card.gradient} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                        <IconComponent className="w-8 h-8 text-white" />
                      </div>

                      {/* Header */}
                      <div>
                        <h3 className="text-2xl font-bold text-white mb-2">{card.title}</h3>
                        <p className={`text-${card.accentColor}-400 font-medium mb-4`}>{card.subtitle}</p>
                        <p className="text-gray-300 leading-relaxed">{card.description}</p>
                      </div>

                      {/* Features */}
                      <div className="space-y-3">
                        {card.features.map((feature, idx) => (
                          <div key={idx} className="flex items-start gap-3">
                            <div className={`w-2 h-2 rounded-full bg-${card.accentColor}-400 mt-2 flex-shrink-0`}></div>
                            <span className="text-gray-400 text-sm leading-relaxed">{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Scroll Indicator */}
          <div className="flex justify-center mt-8 gap-2">
            {capabilityCards.map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  index === currentCapabilityCard ? 'bg-purple-500 w-8' : 'bg-gray-600'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Configuration Form Section
  const renderConfigurationForm = () => (
    <div ref={configSectionRef} className="py-24 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-black via-purple-900/10 to-black"></div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-cyan-300 to-purple-400 bg-clip-text text-transparent">
                Start Your Practice Session
              </span>
            </h2>
            <p className="text-gray-400 text-lg">Configure your personalized interview experience</p>
          </div>

          <div className="bg-black/60 backdrop-blur-2xl border border-white/20 rounded-3xl p-8 shadow-2xl">
            <div className="space-y-8">
              {/* Job Role Selection */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
                  <Target className="w-4 h-4 text-cyan-400" />
                  <span>Job Role</span>
                  <span className="text-red-400">*</span>
                </div>
                
                {/* Popular roles grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                  {popularRoles.map((role) => (
                    <button
                      key={role.title}
                      onClick={() => setJobRole(role.title)}
                      className={`p-4 rounded-xl border transition-all duration-300 text-left group ${
                        jobRole === role.title 
                          ? `border-gradient bg-gradient-to-r ${role.gradient} border-transparent text-white shadow-lg` 
                          : 'border-white/10 bg-black/30 hover:border-white/20 text-gray-300'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-xl">{role.icon}</span>
                        <span className="text-sm font-medium group-hover:text-white transition-colors">
                          {role.title}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
                
                {/* Custom role input */}
                <Input
                  placeholder="Or enter a custom role..."
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  className="bg-black/50 border-white/10 text-white placeholder-gray-500 rounded-xl focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all duration-300"
                />
              </div>

              {/* Company (Optional) */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
                  <Building2 className="w-4 h-4 text-purple-400" />
                  <span>Company Name</span>
                  <span className="text-xs text-gray-500">(Optional)</span>
                </div>
                <Input
                  placeholder="e.g., Google, Microsoft, StartupCo..."
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="bg-black/50 border-white/10 text-white placeholder-gray-500 rounded-xl focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300"
                />
              </div>

              {/* Advanced Settings Toggle */}
              <button
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                className="flex items-center justify-between w-full p-4 rounded-xl border border-white/10 bg-black/30 hover:bg-black/50 transition-all duration-300"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
                  <Settings className="w-4 h-4" />
                  <span>Advanced Options</span>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-300 ${showAdvancedOptions ? 'rotate-180' : ''}`} />
              </button>

              {/* Advanced Options Panel */}
              {showAdvancedOptions && (
                <div className="space-y-6 p-6 rounded-xl bg-black/30 border border-white/5">
                  {/* Interview Style */}
                  <div className="space-y-3">
                    <label className="text-sm font-medium text-gray-300">Interview Style</label>
                    <div className="grid grid-cols-2 gap-3">
                      {interviewStyles.map((styleOption) => (
                        <button
                          key={styleOption.value}
                          onClick={() => setStyle(styleOption.value as any)}
                          className={`p-4 rounded-lg border text-left transition-all duration-300 ${
                            style === styleOption.value
                              ? `border-${styleOption.color}-500 bg-${styleOption.color}-500/10 text-white`
                              : 'border-white/10 bg-black/30 text-gray-400 hover:text-white'
                          }`}
                        >
                          <div className="text-sm font-medium">{styleOption.label}</div>
                          <div className="text-xs opacity-70 mt-1">{styleOption.description}</div>
                        </button>
                      ))}
                    </div>
                  </div>
        
                  {/* Difficulty Level */}
                  <div className="space-y-3">
                    <label className="text-sm font-medium text-gray-300">Difficulty Level</label>
                    <div className="space-y-3">
                      {difficultyLevels.map((level) => (
                        <button
                          key={level.value}
                          onClick={() => setDifficulty(level.value as any)}
                          className={`w-full p-4 rounded-lg border text-left transition-all duration-300 flex items-center justify-between ${
                            difficulty === level.value
                              ? `border-${level.color}-500 bg-${level.color}-500/10 text-white`
                              : 'border-white/10 bg-black/30 text-gray-400 hover:text-white'
                          }`}
                        >
                          <div>
                            <div className="text-sm font-medium">{level.label}</div>
                            <div className="text-xs opacity-70 mt-1">{level.description}</div>
                          </div>
                          <div className="flex space-x-1">
                            {[...Array(3)].map((_, i) => (
                              <div
                                key={i}
                                className={`w-2 h-5 rounded-full ${
                                  i < level.bars 
                                    ? `bg-${level.color}-500` 
                                    : 'bg-gray-600'
                                }`}
                              />
                            ))}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
          
                  {/* Duration Slider */}
                  <div className="space-y-3">
                    <label className="text-sm font-medium text-gray-300">
                      Interview Duration: {interviewDuration} minutes
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="30"
                      value={interviewDuration}
                      onChange={(e) => setInterviewDuration(parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>5 min</span>
                      <span>Quick practice</span>
                      <span>30 min</span>
                    </div>
                  </div>
          
                  {/* Resume Upload */}
                  <div className="space-y-3">
                    <label className="text-sm font-medium text-gray-300">Resume (Optional)</label>
                    <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:border-purple-500/50 transition-all duration-300">
                      <UploadCloud className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                      <p className="text-sm text-gray-400 mb-3">
                        Drag & drop your resume or click to browse
                      </p>
                      <input
                        type="file"
                        accept=".txt,.pdf,.docx"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="resume-upload"
                      />
                      <label
                        htmlFor="resume-upload"
                        className="text-xs text-purple-400 hover:text-purple-300 cursor-pointer font-medium"
                      >
                        Supports TXT, PDF, DOCX
                      </label>
                    </div>
                    {resumeContent && (
                      <div className="text-xs text-green-400 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        Resume content loaded successfully
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Launch Button */}
              <Button
                onClick={handleStartInterview}
                disabled={!jobRole.trim() || isLoading}
                className="w-full py-4 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-purple-500/25 transition-all duration-300 group disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Preparing Interview...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-2">
                    <Play className="w-5 h-5 group-hover:scale-110 transition-transform" />
                    <span>Start Interview Practice</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </div>
                )}
              </Button>

              <p className="text-xs text-gray-500 text-center">
                No account required • Free forever • Instant feedback
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Render footer
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
                <a href="https://github.com/your-username/ai-interviewer" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-cyan-500/30 hover:shadow-cyan-500/20 transition-all duration-300">
                  <Github className="h-5 w-5 text-gray-300 hover:text-cyan-400" />
                </a>
                <a href="https://twitter.com/your-username" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-purple-500/30 hover:shadow-purple-500/20 transition-all duration-300">
                  <Twitter className="h-5 w-5 text-gray-300 hover:text-purple-400" />
                </a>
                <a href="https://linkedin.com/in/your-username" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-pink-500/30 hover:shadow-pink-500/20 transition-all duration-300">
                  <Linkedin className="h-5 w-5 text-gray-300 hover:text-pink-400" />
                </a>
                <a href="mailto:contact@example.com" target="_blank" rel="noopener noreferrer" className="bg-black/40 backdrop-blur-xl border border-white/10 p-3 rounded-full hover:border-cyan-500/30 hover:shadow-cyan-500/20 transition-all duration-300">
                  <Mail className="h-5 w-5 text-gray-300 hover:text-cyan-400" />
                </a>
              </div>
              
              <div className="text-center text-sm text-gray-500">
                <p>© 2023 AI Interviewer. All rights reserved.</p>
                <p className="mt-1">
                  <a href="#" className="text-gray-400 hover:text-gray-300 transition-colors">Privacy Policy</a>
                  <span className="mx-2">·</span>
                  <a href="#" className="text-gray-400 hover:text-gray-300 transition-colors">Terms of Service</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </footer>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-black text-gray-100 relative overflow-hidden">
      {state !== 'interviewing' && (
        <Header 
          showReset={state === 'completed'} 
          onReset={actions.resetInterview}
        />
      )}
      
      <main className="flex-1 flex flex-col">
        {state === 'configuring' && (
          <>
            {renderHeroSection()}
            {renderCapabilityCards()}
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

      {/* Custom styles for enhanced animations */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes scale-x {
            from { transform: scaleX(0); }
            to { transform: scaleX(1); }
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
        `
      }} />
    </div>
  );
};

export default Index;
