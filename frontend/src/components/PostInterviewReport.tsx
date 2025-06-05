import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { 
  ExternalLink, Brain, Search, Loader2, CheckCircle, AlertCircle, 
  Globe, BookOpen, Video, FileText, GraduationCap, Target, 
  TrendingUp, Award, Lightbulb, Zap, Star, ArrowRight, 
  Circle, Square, Triangle, Hexagon, Activity, Eye, Database,
  Code, Users, MessageSquare, BarChart3, Timer, Sparkles,
  Compass, Map, BookMarked, Telescope, Radar, Layers, Play,
  Filter, Cpu, Network, Scan, Bot, ChevronDown, ChevronUp,
  Clock, Mic, Volume2, Heart, Waves, Atom, Orbit
} from 'lucide-react';
import { PerTurnFeedbackItem } from '../services/api';

interface PostInterviewReportProps {
  perTurnFeedback: PerTurnFeedbackItem[];
  finalSummary: {
    status: 'loading' | 'completed' | 'error';
    data?: {
      patterns_tendencies?: string;
      strengths?: string;
      weaknesses?: string;
      improvement_focus_areas?: string;
      resource_search_topics?: string[];
      recommended_resources?: any[];
    };
    error?: string;
  };
  resources: {
    status: 'loading' | 'completed' | 'error';
    data?: any[];
    error?: string;
  };
  onStartNewInterview: () => void;
}

// Advanced particle system for immersive backgrounds
interface Particle {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  life: number;
  pulsation: number;
  rotation: number;
  rotationSpeed: number;
}

// Enhanced floating orb system
interface FloatingOrb {
  id: number;
  x: number;
  y: number;
  size: number;
  color: string;
  opacity: number;
  speed: number;
  direction: number;
  pulse: number;
}

const PostInterviewReport: React.FC<PostInterviewReportProps> = ({
  perTurnFeedback,
  finalSummary,
  resources,
  onStartNewInterview,
}) => {
  // Advanced state management
  const [currentView, setCurrentView] = useState<'overview' | 'analysis' | 'resources'>('overview');
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });
  const [scrollY, setScrollY] = useState(0);
  const [isIntersecting, setIsIntersecting] = useState<Record<string, boolean>>({});
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [particles, setParticles] = useState<Particle[]>([]);
  const [floatingOrbs, setFloatingOrbs] = useState<FloatingOrb[]>([]);
  const [currentTime, setCurrentTime] = useState(Date.now());
  
  // Analysis progress state
  const [analysisProgress, setAnalysisProgress] = useState({
    phase: 0,
    currentStep: '',
    progress: 0,
    details: []
  });
  
  // Search progress state
  const [searchProgress, setSearchProgress] = useState({
    phase: 0,
    currentQuery: '',
    foundResources: 0,
    totalQueries: 0,
    currentActivity: '',
    progress: 0
  });
  
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentSection, setCurrentSection] = useState(0);

  // Enhanced mouse tracking with smoothing
  const handleMouseMove = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    setMousePosition({ x, y });
  }, []);

  // Advanced scroll tracking
  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
      
      // Determine current section based on scroll position
      const sections = ['overview', 'analysis', 'resources'];
      const sectionHeight = window.innerHeight;
      const newSection = Math.floor(window.scrollY / sectionHeight);
      setCurrentSection(Math.min(newSection, sections.length - 1));
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Dynamic particle system
  useEffect(() => {
    const createParticles = () => {
      const count = finalSummary.status === 'loading' || resources.status === 'loading' ? 20 : 8;
      return Array.from({ length: count }, (_, i) => ({
        id: Date.now() + i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 3 + 1,
        color: finalSummary.status === 'loading' ? 'blue' : resources.status === 'loading' ? 'green' : 'purple',
        life: 1,
        pulsation: Math.random() * Math.PI * 2,
        rotation: 0,
        rotationSpeed: (Math.random() - 0.5) * 0.1
      }));
    };

    setParticles(createParticles());

    const animationLoop = setInterval(() => {
      setParticles(prev => prev.map(p => ({
        ...p,
        x: (p.x + p.vx + 100) % 100,
        y: (p.y + p.vy + 100) % 100,
        pulsation: p.pulsation + 0.1,
        rotation: p.rotation + p.rotationSpeed,
        life: Math.max(0, p.life - 0.005)
      })).filter(p => p.life > 0));
    }, 50);

    return () => clearInterval(animationLoop);
  }, [finalSummary.status, resources.status]);

  // Floating orbs system
  useEffect(() => {
    const createOrbs = () => {
      return Array.from({ length: 5 }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 200 + 100,
        color: ['cyan', 'purple', 'pink', 'blue', 'green'][i],
        opacity: Math.random() * 0.3 + 0.1,
        speed: Math.random() * 0.5 + 0.2,
        direction: Math.random() * Math.PI * 2,
        pulse: Math.random() * Math.PI * 2
      }));
    };

    setFloatingOrbs(createOrbs());

    const orbAnimation = setInterval(() => {
      setFloatingOrbs(prev => prev.map(orb => ({
        ...orb,
        x: (orb.x + Math.cos(orb.direction) * orb.speed + 100) % 100,
        y: (orb.y + Math.sin(orb.direction) * orb.speed + 100) % 100,
        pulse: orb.pulse + 0.05,
        direction: orb.direction + 0.01
      })));
    }, 100);

    return () => clearInterval(orbAnimation);
  }, []);

  // Time tracking for animations
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 100);
    return () => clearInterval(interval);
  }, []);

  // Enhanced analysis progress simulation
  useEffect(() => {
    if (finalSummary.status === 'loading') {
      const analysisSteps = [
        { step: 'Initializing AI Coach', details: 'Loading conversation context and user profile' },
        { step: 'Processing Responses', details: 'Analyzing linguistic patterns and content quality' },
        { step: 'Identifying Strengths', details: 'Recognizing strong performance areas' },
        { step: 'Evaluating Weaknesses', details: 'Detecting improvement opportunities' },
        { step: 'Generating Insights', details: 'Creating personalized recommendations' }
      ];

      let currentPhase = 0;
      const progressInterval = setInterval(() => {
        if (currentPhase < analysisSteps.length) {
          setAnalysisProgress({
            phase: currentPhase,
            currentStep: analysisSteps[currentPhase].step,
            progress: ((currentPhase + 1) / analysisSteps.length) * 100,
            details: [analysisSteps[currentPhase].details]
          });
          currentPhase++;
        } else {
          clearInterval(progressInterval);
        }
      }, 2000);

      return () => clearInterval(progressInterval);
    }
  }, [finalSummary.status]);

  // Enhanced search progress simulation
  useEffect(() => {
    if (resources.status === 'loading' && finalSummary.data?.resource_search_topics) {
      const topics = finalSummary.data.resource_search_topics;
      const searchActivities = [
        'Initializing search agents',
        'Querying educational platforms',
        'Filtering by quality metrics',
        'Analyzing content relevance',
        'Ranking by learning value',
        'Finalizing recommendations'
      ];

      let queryIndex = 0;
      let activityIndex = 0;
      let resourceCount = 0;

      const searchInterval = setInterval(() => {
        if (queryIndex < topics.length) {
          setSearchProgress({
            phase: Math.floor((queryIndex / topics.length) * searchActivities.length),
            currentQuery: topics[queryIndex],
            foundResources: resourceCount,
            totalQueries: topics.length,
            currentActivity: searchActivities[activityIndex % searchActivities.length],
            progress: ((queryIndex + 1) / topics.length) * 100
          });
          
          queryIndex++;
          activityIndex++;
          resourceCount += Math.floor(Math.random() * 3) + 2;
        } else {
          clearInterval(searchInterval);
        }
      }, 1500);

      return () => clearInterval(searchInterval);
    }
  }, [resources.status, finalSummary.data?.resource_search_topics]);

  // Revolutionary background system with multiple layers
  const renderAdvancedBackground = () => (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Base gradient that responds to mouse */}
      <div 
        className="absolute inset-0 transition-all duration-1000 ease-out"
        style={{
          background: `
            radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, 
              rgba(6, 182, 212, 0.15) 0%, 
              rgba(168, 85, 247, 0.1) 25%, 
              rgba(236, 72, 153, 0.08) 50%, 
              transparent 75%),
            radial-gradient(circle at ${100 - mousePosition.x}% ${100 - mousePosition.y}%, 
              rgba(34, 197, 94, 0.12) 0%, 
              rgba(249, 115, 22, 0.08) 30%, 
              transparent 60%),
            linear-gradient(135deg, 
              #0a0a0a 0%, 
              #0f172a 25%, 
              #1e293b 50%, 
              #0f172a 75%, 
              #0a0a0a 100%)
          `
        }}
      />

      {/* Floating orbs */}
      {floatingOrbs.map((orb) => (
        <div
          key={orb.id}
          className="absolute rounded-full blur-3xl"
          style={{
            left: `${orb.x}%`,
            top: `${orb.y}%`,
            width: `${orb.size}px`,
            height: `${orb.size}px`,
            background: `radial-gradient(circle, 
              ${orb.color === 'cyan' ? 'rgba(6, 182, 212, 0.3)' :
                orb.color === 'purple' ? 'rgba(168, 85, 247, 0.3)' :
                orb.color === 'pink' ? 'rgba(236, 72, 153, 0.3)' :
                orb.color === 'blue' ? 'rgba(59, 130, 246, 0.3)' :
                'rgba(34, 197, 94, 0.3)'} 0%, 
              transparent 70%)`,
            opacity: orb.opacity * (0.5 + 0.5 * Math.sin(orb.pulse)),
            transform: `translate(-50%, -50%) scale(${0.8 + 0.2 * Math.sin(orb.pulse * 1.2)})`
          }}
        />
      ))}

      {/* Dynamic particles */}
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="absolute"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            background: particle.color === 'blue' ? '#3b82f6' : 
                       particle.color === 'green' ? '#10b981' : '#a855f7',
            borderRadius: '50%',
            opacity: particle.life * (0.4 + 0.6 * Math.sin(particle.pulsation)),
            boxShadow: `0 0 ${particle.size * 2}px currentColor`,
            transform: `rotate(${particle.rotation}rad) scale(${0.5 + 0.5 * Math.sin(particle.pulsation * 2)})`
          }}
        />
      ))}

      {/* Parallax geometric shapes */}
      <div 
        className="absolute inset-0"
        style={{ transform: `translateY(${scrollY * 0.1}px)` }}
      >
        <Circle className="absolute top-1/4 left-1/6 w-6 h-6 text-cyan-400/20 animate-pulse" />
        <Square className="absolute top-1/3 right-1/4 w-4 h-4 text-purple-400/20 animate-bounce" />
        <Triangle className="absolute bottom-1/3 left-1/3 w-5 h-5 text-pink-400/20 animate-pulse" />
        <Hexagon className="absolute bottom-1/4 right-1/6 w-7 h-7 text-blue-400/20 animate-bounce" />
      </div>
    </div>
  );

  // Premium loading state for analysis
  const renderAnalysisLoading = () => (
    <div className="relative">
      {/* Main analysis card */}
      <div className="bg-black/40 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 relative overflow-hidden">
        {/* Animated background */}
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            background: `
              linear-gradient(45deg, 
                rgba(59, 130, 246, 0.1) 0%, 
                rgba(168, 85, 247, 0.1) 50%, 
                rgba(236, 72, 153, 0.1) 100%)
            `,
            animation: 'shimmer 3s ease-in-out infinite'
          }}
        />
        
        <div className="relative z-10 space-y-8">
          {/* AI Brain Header */}
          <div className="text-center space-y-4">
            <div className="relative mx-auto w-20 h-20">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 via-purple-600 to-pink-500 flex items-center justify-center shadow-2xl shadow-blue-500/30">
                <Brain className="w-10 h-10 text-white animate-pulse" />
              </div>
              <div className="absolute -inset-2 rounded-full border-2 border-blue-400/30 animate-ping" />
              <div className="absolute -inset-4 rounded-full border border-purple-400/20 animate-pulse" />
            </div>
            <div>
              <h3 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-pink-400 bg-clip-text text-transparent">
                AI Coach Analyzing
              </h3>
              <p className="text-blue-300/80 text-lg">Deep analysis of your interview performance</p>
            </div>
          </div>

          {/* Current step */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center space-x-3 px-6 py-3 bg-black/40 rounded-2xl border border-blue-500/20">
              <Activity className="w-5 h-5 text-blue-400 animate-spin" />
              <span className="text-blue-300 font-medium">{analysisProgress.currentStep}</span>
            </div>
            
            {/* Progress bar */}
            <div className="w-full max-w-md mx-auto">
              <div className="flex justify-between text-sm text-gray-400 mb-2">
                <span>Progress</span>
                <span>{Math.round(analysisProgress.progress)}%</span>
              </div>
              <div className="w-full bg-gray-800/50 rounded-full h-3 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full transition-all duration-1000 ease-out relative"
                  style={{ width: `${analysisProgress.progress}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse" />
                </div>
              </div>
            </div>
          </div>

          {/* Analysis modules */}
          <div className="grid grid-cols-2 gap-4">
            {[
              { icon: MessageSquare, label: 'Response Analysis', active: analysisProgress.phase >= 0 },
              { icon: TrendingUp, label: 'Pattern Recognition', active: analysisProgress.phase >= 1 },
              { icon: Award, label: 'Strength Identification', active: analysisProgress.phase >= 2 },
              { icon: Target, label: 'Improvement Areas', active: analysisProgress.phase >= 3 }
            ].map((module, index) => (
              <div 
                key={index}
                className={`flex items-center space-x-3 p-4 rounded-xl transition-all duration-500 ${
                  module.active 
                    ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/40' 
                    : 'bg-gray-800/20 border border-gray-600/20'
                }`}
              >
                <module.icon className={`w-6 h-6 ${
                  module.active ? 'text-blue-400' : 'text-gray-500'
                }`} />
                <span className={`text-sm font-medium ${
                  module.active ? 'text-blue-300' : 'text-gray-500'
                }`}>
                  {module.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Premium loading state for search
  const renderSearchLoading = () => (
    <div className="relative">
      {/* Main search card */}
      <div className="bg-black/40 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 relative overflow-hidden">
        {/* Animated background */}
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            background: `
              linear-gradient(45deg, 
                rgba(34, 197, 94, 0.1) 0%, 
                rgba(6, 182, 212, 0.1) 50%, 
                rgba(59, 130, 246, 0.1) 100%)
            `,
            animation: 'shimmer 2s ease-in-out infinite reverse'
          }}
        />
        
        <div className="relative z-10 space-y-8">
          {/* Search Agent Header */}
          <div className="text-center space-y-4">
            <div className="relative mx-auto w-20 h-20">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-500 via-cyan-600 to-blue-500 flex items-center justify-center shadow-2xl shadow-emerald-500/30">
                <Search className="w-10 h-10 text-white animate-bounce" />
              </div>
              <div className="absolute -inset-2 rounded-full border-2 border-emerald-400/30 animate-ping" />
              <div className="absolute -inset-4 rounded-full border border-cyan-400/20 animate-pulse" />
            </div>
            <div>
              <h3 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 via-cyan-500 to-blue-400 bg-clip-text text-transparent">
                AI Search Agent Active
              </h3>
              <p className="text-emerald-300/80 text-lg">Curating personalized learning resources</p>
            </div>
          </div>

          {/* Current search query */}
          {searchProgress.currentQuery && (
            <div className="text-center space-y-3">
              <div className="inline-flex items-center space-x-3 px-6 py-3 bg-black/40 rounded-2xl border border-emerald-500/20">
                <Globe className="w-5 h-5 text-emerald-400 animate-spin" />
                <span className="text-emerald-300 font-medium">Searching: {searchProgress.currentQuery}</span>
              </div>
              <p className="text-gray-400 text-sm">{searchProgress.currentActivity}</p>
            </div>
          )}

          {/* Search statistics */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="space-y-2">
              <div className="text-2xl font-bold text-emerald-400">{searchProgress.foundResources}</div>
              <div className="text-xs text-gray-400">Resources Found</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-cyan-400">{searchProgress.totalQueries}</div>
              <div className="text-xs text-gray-400">Topics Searched</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-blue-400">{Math.round(searchProgress.progress)}%</div>
              <div className="text-xs text-gray-400">Complete</div>
            </div>
          </div>

          {/* Search phases */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { icon: Telescope, label: 'Query Formation', phase: 0 },
              { icon: Database, label: 'Platform Search', phase: 1 },
              { icon: Filter, label: 'Quality Filter', phase: 2 },
              { icon: Radar, label: 'Relevance Ranking', phase: 3 }
            ].map((item, index) => (
              <div 
                key={index}
                className={`flex items-center space-x-3 p-3 rounded-xl transition-all duration-500 ${
                  searchProgress.phase >= item.phase
                    ? 'bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border border-emerald-500/40' 
                    : 'bg-gray-800/20 border border-gray-600/20'
                }`}
              >
                <item.icon className={`w-5 h-5 ${
                  searchProgress.phase >= item.phase ? 'text-emerald-400' : 'text-gray-500'
                }`} />
                <span className={`text-sm font-medium ${
                  searchProgress.phase >= item.phase ? 'text-emerald-300' : 'text-gray-500'
                }`}>
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Rest of component implementation continues...
  return (
    <div 
      ref={containerRef}
      className="min-h-screen relative"
      onMouseMove={handleMouseMove}
    >
      {/* Advanced background system */}
      {renderAdvancedBackground()}
      
      {/* Main content with revolutionary layout */}
      <div className="relative z-10 min-h-screen">
        
        {/* Hero section with dynamic navigation */}
        <section className="min-h-screen flex flex-col justify-center items-center px-4 md:px-8 relative">
          <div className="text-center space-y-8 max-w-4xl">
            {/* Animated header */}
            <div 
              className="space-y-6"
              style={{
                transform: `translateY(${scrollY * 0.1}px)`,
                opacity: Math.max(0, 1 - scrollY / 500)
              }}
            >
              <div className="flex items-center justify-center space-x-4 mb-8">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 via-purple-600 to-pink-500 flex items-center justify-center shadow-2xl">
                  <BarChart3 className="w-8 h-8 text-white" />
                </div>
              </div>
              
              <h1 className="text-6xl md:text-7xl font-bold leading-tight">
                <span className="bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-400 bg-clip-text text-transparent">
                  Interview Analysis
                </span>
              </h1>
              
              <p className="text-xl md:text-2xl text-gray-300 leading-relaxed max-w-3xl mx-auto">
                Comprehensive AI-powered insights into your interview performance 
                with personalized learning recommendations
              </p>
            </div>

            {/* Dynamic section navigation */}
            <div className="flex justify-center space-x-6">
              {[
                { id: 'analysis', label: 'Performance Analysis', icon: Brain, status: finalSummary.status },
                { id: 'resources', label: 'Learning Resources', icon: Search, status: resources.status },
                { id: 'feedback', label: 'Detailed Feedback', icon: MessageSquare, status: 'completed' as const }
              ].map((section) => (
                <button
                  key={section.id}
                  onClick={() => {
                    const element = document.getElementById(section.id);
                    element?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="group flex flex-col items-center space-y-3 p-6 bg-black/30 backdrop-blur-xl border border-white/10 rounded-2xl hover:border-white/20 transition-all duration-300 hover:scale-105"
                >
                  <div className="relative">
                    <section.icon className="w-8 h-8 text-white group-hover:text-cyan-400 transition-colors" />
                    {section.status === 'loading' && (
                      <div className="absolute -inset-2 rounded-full border-2 border-cyan-400/50 animate-ping" />
                    )}
                  </div>
                  <span className="text-white font-medium group-hover:text-cyan-400 transition-colors">
                    {section.label}
                  </span>
                  <div className={`w-2 h-2 rounded-full ${
                    section.status === 'completed' ? 'bg-green-400' :
                    section.status === 'loading' ? 'bg-yellow-400 animate-pulse' :
                    'bg-red-400'
                  }`} />
                </button>
              ))}
            </div>
          </div>

          {/* Scroll indicator */}
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
            <ChevronDown className="w-6 h-6 text-white/60" />
          </div>
        </section>

        {/* Analysis section */}
        <section id="analysis" className="min-h-screen flex items-center px-4 md:px-8 py-16">
          <div className="w-full max-w-6xl mx-auto">
            {finalSummary.status === 'loading' && renderAnalysisLoading()}
            {finalSummary.status === 'completed' && finalSummary.data && (
              <div className="space-y-8">
                <h2 className="text-4xl font-bold text-center bg-gradient-to-r from-blue-400 via-purple-500 to-pink-400 bg-clip-text text-transparent mb-12">
                  Performance Analysis
                </h2>
                
                {/* Analysis results grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Patterns & Tendencies */}
                  <div className="bg-black/40 backdrop-blur-2xl border border-white/10 rounded-3xl p-8">
                    <div className="flex items-center space-x-4 mb-6">
                      <TrendingUp className="w-8 h-8 text-orange-400" />
                      <h3 className="text-2xl font-bold text-white">Observed Patterns</h3>
                    </div>
                    <p className="text-gray-300 leading-relaxed">
                      {finalSummary.data.patterns_tendencies || 'No specific patterns identified.'}
                    </p>
                  </div>

                  {/* Strengths */}
                  <div className="bg-black/40 backdrop-blur-2xl border border-white/10 rounded-3xl p-8">
                    <div className="flex items-center space-x-4 mb-6">
                      <Award className="w-8 h-8 text-emerald-400" />
                      <h3 className="text-2xl font-bold text-white">Key Strengths</h3>
                    </div>
                    <p className="text-gray-300 leading-relaxed">
                      {finalSummary.data.strengths || 'No specific strengths identified.'}
                    </p>
                  </div>

                  {/* Areas for Development */}
                  <div className="bg-black/40 backdrop-blur-2xl border border-white/10 rounded-3xl p-8">
                    <div className="flex items-center space-x-4 mb-6">
                      <Target className="w-8 h-8 text-amber-400" />
                      <h3 className="text-2xl font-bold text-white">Development Areas</h3>
                    </div>
                    <p className="text-gray-300 leading-relaxed">
                      {finalSummary.data.weaknesses || 'No specific weaknesses identified.'}
                    </p>
                  </div>

                  {/* Improvement Focus */}
                  <div className="bg-black/40 backdrop-blur-2xl border border-white/10 rounded-3xl p-8">
                    <div className="flex items-center space-x-4 mb-6">
                      <Lightbulb className="w-8 h-8 text-purple-400" />
                      <h3 className="text-2xl font-bold text-white">Focus Areas</h3>
                    </div>
                    <p className="text-gray-300 leading-relaxed">
                      {finalSummary.data.improvement_focus_areas || 'No specific focus areas identified.'}
                    </p>
                  </div>
                </div>
              </div>
            )}
            {finalSummary.status === 'error' && (
              <div className="text-center space-y-6">
                <AlertCircle className="w-16 h-16 text-red-400 mx-auto" />
                <h3 className="text-2xl font-bold text-red-400">Analysis Error</h3>
                <p className="text-red-300">{finalSummary.error}</p>
              </div>
            )}
          </div>
        </section>

        {/* Resources section */}
        <section id="resources" className="min-h-screen flex items-center px-4 md:px-8 py-16">
          <div className="w-full max-w-6xl mx-auto">
            {resources.status === 'loading' && renderSearchLoading()}
            {resources.status === 'completed' && resources.data && (
              <div className="space-y-8">
                <h2 className="text-4xl font-bold text-center bg-gradient-to-r from-emerald-400 via-cyan-500 to-blue-400 bg-clip-text text-transparent mb-12">
                  Learning Resources
                </h2>
                
                {/* Resources grid - simplified and cleaner */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {resources.data.map((resource: any, index: number) => (
                    <div 
                      key={index}
                      className="group bg-black/40 backdrop-blur-2xl border border-white/10 rounded-2xl overflow-hidden hover:border-emerald-500/40 hover:scale-105 transition-all duration-300"
                    >
                      <div className="p-6 space-y-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center">
                            {resource.resource_type === 'video' ? <Video className="w-5 h-5 text-white" /> :
                             resource.resource_type === 'course' ? <GraduationCap className="w-5 h-5 text-white" /> :
                             <FileText className="w-5 h-5 text-white" />}
                          </div>
                          {resource.resource_type && (
                            <span className="px-2 py-1 text-xs bg-emerald-500/20 text-emerald-300 rounded-lg">
                              {resource.resource_type}
                            </span>
                          )}
                        </div>
                        
                        <h4 className="text-lg font-semibold text-white group-hover:text-emerald-300 transition-colors line-clamp-2">
                          {resource.title}
                        </h4>
                        
                        <p className="text-gray-400 text-sm line-clamp-3 leading-relaxed">
                          {resource.description}
                        </p>
                        
                        {resource.reasoning && (
                          <div className="p-3 bg-blue-900/20 border-l-2 border-blue-400/50 rounded-r-lg">
                            <p className="text-xs text-blue-200 leading-relaxed">
                              <strong>AI Reasoning:</strong> {resource.reasoning}
                            </p>
                          </div>
                        )}
                        
                        <a
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-2 text-emerald-400 hover:text-emerald-300 font-medium text-sm group-hover:translate-x-1 transition-all duration-300"
                        >
                          <span>Explore Resource</span>
                          <ArrowRight className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {resources.status === 'error' && (
              <div className="text-center space-y-6">
                <AlertCircle className="w-16 h-16 text-red-400 mx-auto" />
                <h3 className="text-2xl font-bold text-red-400">Search Error</h3>
                <p className="text-red-300">{resources.error}</p>
              </div>
            )}
          </div>
        </section>

        {/* Feedback section */}
        <section id="feedback" className="min-h-screen flex items-center px-4 md:px-8 py-16">
          <div className="w-full max-w-4xl mx-auto">
            <h2 className="text-4xl font-bold text-center bg-gradient-to-r from-purple-400 via-pink-500 to-red-400 bg-clip-text text-transparent mb-12">
              Detailed Feedback
            </h2>
            
            {perTurnFeedback && perTurnFeedback.length > 0 ? (
              <div className="space-y-6">
                {perTurnFeedback.map((item, index) => (
                  <div 
                    key={index}
                    className="bg-black/40 backdrop-blur-2xl border border-white/10 rounded-2xl overflow-hidden"
                  >
                    <div className="p-6 space-y-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">{index + 1}</span>
                        </div>
                        <h4 className="text-lg font-semibold text-white">Question {index + 1}</h4>
                      </div>
                      
                      <div className="space-y-4">
                        <div>
                          <h5 className="text-purple-300 font-medium mb-2">Question:</h5>
                          <p className="text-gray-300 leading-relaxed">{item.question}</p>
                        </div>
                        
                        <div>
                          <h5 className="text-blue-300 font-medium mb-2">Your Response:</h5>
                          <div className="bg-blue-900/10 border-l-4 border-blue-500/50 rounded-r-xl p-4">
                            <p className="text-gray-200 leading-relaxed">{item.answer}</p>
                          </div>
                        </div>
                        
                        <div>
                          <h5 className="text-yellow-300 font-medium mb-2">AI Coach Feedback:</h5>
                          <div className="bg-yellow-900/10 border-l-4 border-yellow-500/50 rounded-r-xl p-4">
                            <p className="text-gray-100 leading-relaxed">{item.feedback}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center space-y-6">
                <MessageSquare className="w-16 h-16 text-gray-500 mx-auto" />
                <h3 className="text-2xl font-bold text-gray-400">No Detailed Feedback</h3>
                <p className="text-gray-500">No turn-by-turn feedback available for this session.</p>
              </div>
            )}
          </div>
        </section>

        {/* Call to action section */}
        <section className="py-16 px-4 md:px-8">
          <div className="max-w-2xl mx-auto text-center space-y-8">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500 via-purple-600 to-pink-500 flex items-center justify-center mx-auto shadow-2xl">
              <Zap className="w-10 h-10 text-white" />
            </div>
            
            <h3 className="text-3xl font-bold text-white">Ready for Your Next Challenge?</h3>
            <p className="text-xl text-gray-400 leading-relaxed">
              Apply what you've learned and practice again to improve further.
            </p>
            
            <Button
              onClick={onStartNewInterview}
              size="lg"
              className="bg-gradient-to-r from-cyan-500 via-purple-600 to-pink-500 hover:from-cyan-400 hover:via-purple-500 hover:to-pink-400 text-white text-lg font-semibold px-8 py-4 rounded-2xl shadow-2xl hover:shadow-cyan-500/20 transition-all duration-300 group"
            >
              <span>Start New Interview</span>
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </Button>
          </div>
        </section>
      </div>

      {/* Custom styles */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes shimmer {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
          }
          
          .line-clamp-2 {
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
          
          .line-clamp-3 {
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
        `
      }} />
    </div>
  );
};

export default PostInterviewReport; 