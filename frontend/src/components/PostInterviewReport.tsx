import React, { useState, useEffect, useRef } from 'react';
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
  Compass, Map, BookMarked, Telescope, Radar, Layers
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

const PostInterviewReport: React.FC<PostInterviewReportProps> = ({
  perTurnFeedback,
  finalSummary,
  resources,
  onStartNewInterview,
}) => {
  // Enhanced state management
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [searchProgress, setSearchProgress] = useState({ step: 0, currentTopic: '', progress: 0 });
  const [analysisProgress, setAnalysisProgress] = useState({ step: 0, currentArea: '', progress: 0 });
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; vx: number; vy: number; size: number; color: string; life: number }>>([]);
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [expandedFeedback, setExpandedFeedback] = useState<number | null>(null);
  const [visibleCards, setVisibleCards] = useState<Set<string>>(new Set());
  
  const containerRef = useRef<HTMLDivElement>(null);

  // Enhanced mouse tracking for 3D effects
  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    setMousePosition({ x, y });
  };

  // Time tracking for dynamic animations
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 100);
    return () => clearInterval(interval);
  }, []);

  // Advanced particle system for dynamic backgrounds
  useEffect(() => {
    const shouldShowParticles = finalSummary.status === 'loading' || resources.status === 'loading';
    
    if (shouldShowParticles) {
      const particleCount = 15;
      const newParticles = Array.from({ length: particleCount }, (_, i) => ({
        id: Date.now() + i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 2 + 1,
        color: finalSummary.status === 'loading' ? 'blue' : 'green',
        life: 1
      }));
      setParticles(newParticles);
      
      const animationInterval = setInterval(() => {
        setParticles(prev => prev.map(p => ({
          ...p,
          x: (p.x + p.vx + 100) % 100,
          y: (p.y + p.vy + 100) % 100,
          life: Math.max(0, p.life - 0.01)
        })).filter(p => p.life > 0));
      }, 50);
      
      return () => clearInterval(animationInterval);
    } else {
      setParticles([]);
    }
  }, [finalSummary.status, resources.status]);

  // Simulate search progress for enhanced UX
  useEffect(() => {
    if (resources.status === 'loading' && finalSummary.data?.resource_search_topics) {
      const topics = finalSummary.data.resource_search_topics;
      let currentStep = 0;
      
      const progressInterval = setInterval(() => {
        if (currentStep < topics.length) {
          setSearchProgress({
            step: currentStep,
            currentTopic: topics[currentStep] || '',
            progress: ((currentStep + 1) / topics.length) * 100
          });
          currentStep++;
        } else {
          clearInterval(progressInterval);
        }
      }, 2000);
      
      return () => clearInterval(progressInterval);
    }
  }, [resources.status, finalSummary.data?.resource_search_topics]);

  // Simulate analysis progress
  useEffect(() => {
    if (finalSummary.status === 'loading') {
      const analysisAreas = [
        'Analyzing response patterns',
        'Identifying strengths',
        'Evaluating weaknesses',
        'Generating improvement recommendations'
      ];
      let currentStep = 0;
      
      const progressInterval = setInterval(() => {
        if (currentStep < analysisAreas.length) {
          setAnalysisProgress({
            step: currentStep,
            currentArea: analysisAreas[currentStep],
            progress: ((currentStep + 1) / analysisAreas.length) * 100
          });
          currentStep++;
        } else {
          clearInterval(progressInterval);
        }
      }, 1500);
      
      return () => clearInterval(progressInterval);
    }
  }, [finalSummary.status]);

  // Intersection observer for card animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisibleCards(prev => new Set([...prev, entry.target.id]));
          }
        });
      },
      { threshold: 0.1 }
    );

    const cards = document.querySelectorAll('[data-card]');
    cards.forEach(card => observer.observe(card));

    return () => observer.disconnect();
  }, []);

  // Advanced background system
  const renderAdvancedBackground = () => (
    <div className="absolute inset-0 overflow-hidden">
      {/* Dynamic gradient background */}
      <div 
        className="absolute inset-0 transition-all duration-1000 ease-out"
        style={{
          background: `
            radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, 
              rgba(34, 211, 238, 0.08) 0%, 
              rgba(168, 85, 247, 0.05) 30%, 
              transparent 70%),
            radial-gradient(circle at ${100 - mousePosition.x}% ${100 - mousePosition.y}%, 
              rgba(236, 72, 153, 0.06) 0%, 
              rgba(34, 197, 94, 0.04) 40%, 
              transparent 80%),
            linear-gradient(135deg, 
              rgba(0, 0, 0, 0.98) 0%, 
              rgba(15, 23, 42, 0.99) 50%, 
              rgba(0, 0, 0, 0.98) 100%)
          `
        }}
      />

      {/* Floating particles */}
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="absolute w-1 h-1 rounded-full transition-opacity duration-500"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            backgroundColor: particle.color === 'blue' ? '#22D3EE' : '#10B981',
            opacity: particle.life * 0.6,
            transform: `scale(${particle.size})`,
            boxShadow: `0 0 ${particle.size * 3}px currentColor`,
          }}
        />
      ))}

      {/* Geometric accents */}
      <div className="absolute top-1/4 left-1/5 opacity-10">
        <Circle className="w-4 h-4 text-cyan-400 animate-pulse" style={{ animationDelay: '0s' }} />
      </div>
      <div className="absolute top-3/4 right-1/4 opacity-15">
        <Square className="w-3 h-3 text-purple-400 animate-bounce" style={{ animationDelay: '2s' }} />
      </div>
      <div className="absolute bottom-1/3 left-1/3 opacity-20">
        <Triangle className="w-5 h-5 text-pink-400 animate-pulse" style={{ animationDelay: '4s' }} />
      </div>
    </div>
  );

  // Premium loading state with agentic search visualization
  const renderAgenticSearchLoading = () => (
    <div className="space-y-6">
      {/* Search Agent Activity */}
      <div className="bg-black/60 backdrop-blur-2xl border border-emerald-500/30 rounded-3xl p-8 relative overflow-hidden">
        {/* Background animation */}
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-cyan-500/5 animate-pulse" />
        
        <div className="relative z-10 space-y-6">
          {/* Agent Header */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center shadow-xl shadow-emerald-500/20">
                <Search className="w-8 h-8 text-white" />
              </div>
              <div className="absolute -inset-1 rounded-2xl border-2 border-emerald-400/50 animate-ping" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white">AI Search Agent Active</h3>
              <p className="text-emerald-300">Intelligently curating learning resources for your skill gaps</p>
            </div>
          </div>

          {/* Search Progress */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-300">Search Progress</span>
              <span className="text-sm text-emerald-400 font-medium">{Math.round(searchProgress.progress)}%</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full transition-all duration-1000 ease-out relative"
                style={{ width: `${searchProgress.progress}%` }}
              >
                <div className="absolute inset-0 bg-white/20 animate-pulse" />
              </div>
            </div>
          </div>

          {/* Current Search Topic */}
          {searchProgress.currentTopic && (
            <div className="flex items-center space-x-3 p-4 bg-black/40 rounded-2xl border border-emerald-500/20">
              <Globe className="w-5 h-5 text-emerald-400 animate-spin" />
              <div>
                <p className="text-sm text-gray-400">Currently searching for:</p>
                <p className="text-emerald-300 font-medium">{searchProgress.currentTopic}</p>
              </div>
            </div>
          )}

          {/* Search Steps Visualization */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { icon: Telescope, label: 'Analyzing Skills', step: 0 },
              { icon: Database, label: 'Querying Resources', step: 1 },
              { icon: Radar, label: 'Filtering Quality', step: 2 },
              { icon: Target, label: 'Ranking Relevance', step: 3 }
            ].map((item, index) => (
              <div 
                key={index}
                className={`text-center p-4 rounded-xl transition-all duration-500 ${
                  searchProgress.step >= index 
                    ? 'bg-emerald-500/20 border border-emerald-500/40' 
                    : 'bg-gray-800/30 border border-gray-600/30'
                }`}
              >
                <item.icon className={`w-6 h-6 mx-auto mb-2 ${
                  searchProgress.step >= index ? 'text-emerald-400' : 'text-gray-500'
                }`} />
                <p className={`text-xs ${
                  searchProgress.step >= index ? 'text-emerald-300' : 'text-gray-500'
                }`}>
                  {item.label}
                </p>
              </div>
            ))}
          </div>

          {/* Real-time activity feed */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-xs text-gray-400">
              <Activity className="w-3 h-3 animate-pulse" />
              <span>Real-time search activity</span>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex items-center space-x-2 text-emerald-300">
                <div className="w-1 h-1 bg-emerald-400 rounded-full animate-ping" />
                <span>Querying educational platforms for relevant content...</span>
              </div>
              <div className="flex items-center space-x-2 text-cyan-300">
                <div className="w-1 h-1 bg-cyan-400 rounded-full animate-ping" />
                <span>Filtering results by quality and relevance score...</span>
              </div>
              <div className="flex items-center space-x-2 text-blue-300">
                <div className="w-1 h-1 bg-blue-400 rounded-full animate-ping" />
                <span>Analyzing content depth and learning value...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Advanced analysis loading state
  const renderAnalysisLoading = () => (
    <div className="bg-black/60 backdrop-blur-2xl border border-blue-500/30 rounded-3xl p-8 relative overflow-hidden">
      {/* Background animation */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 animate-pulse" />
      
      <div className="relative z-10 space-y-6">
        {/* Agent Header */}
        <div className="flex items-center space-x-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-xl shadow-blue-500/20">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <div className="absolute -inset-1 rounded-2xl border-2 border-blue-400/50 animate-ping" />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">AI Coach Analyzing</h3>
            <p className="text-blue-300">Deep analysis of your interview performance in progress</p>
          </div>
        </div>

        {/* Analysis Progress */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Analysis Progress</span>
            <span className="text-sm text-blue-400 font-medium">{Math.round(analysisProgress.progress)}%</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-1000 ease-out relative"
              style={{ width: `${analysisProgress.progress}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse" />
            </div>
          </div>
        </div>

        {/* Current Analysis Area */}
        {analysisProgress.currentArea && (
          <div className="flex items-center space-x-3 p-4 bg-black/40 rounded-2xl border border-blue-500/20">
            <Eye className="w-5 h-5 text-blue-400 animate-pulse" />
            <div>
              <p className="text-sm text-gray-400">Currently analyzing:</p>
              <p className="text-blue-300 font-medium">{analysisProgress.currentArea}</p>
            </div>
          </div>
        )}

        {/* Analysis modules */}
        <div className="grid grid-cols-2 gap-4">
          {[
            { icon: MessageSquare, label: 'Response Quality', active: analysisProgress.step >= 0 },
            { icon: TrendingUp, label: 'Performance Patterns', active: analysisProgress.step >= 1 },
            { icon: Award, label: 'Strength Recognition', active: analysisProgress.step >= 2 },
            { icon: Target, label: 'Improvement Areas', active: analysisProgress.step >= 3 }
          ].map((item, index) => (
            <div 
              key={index}
              className={`flex items-center space-x-3 p-3 rounded-xl transition-all duration-500 ${
                item.active 
                  ? 'bg-blue-500/20 border border-blue-500/40' 
                  : 'bg-gray-800/30 border border-gray-600/30'
              }`}
            >
              <item.icon className={`w-5 h-5 ${
                item.active ? 'text-blue-400' : 'text-gray-500'
              }`} />
              <span className={`text-sm ${
                item.active ? 'text-blue-300' : 'text-gray-500'
              }`}>
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Enhanced text section with better typography and layout
  const renderTextSection = (title: string, content?: any, icon?: React.ReactNode, gradient?: string) => {
    const textContent = typeof content === 'string' ? content : 
                       content !== null && content !== undefined ? JSON.stringify(content, null, 2) : '';
    
    if (!textContent || textContent.trim() === "") {
      return (
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            {icon}
            <h3 className={`text-xl font-bold ${gradient || 'text-purple-400'}`}>{title}</h3>
          </div>
          <p className="text-gray-400 italic text-sm">No specific {title.toLowerCase()} noted for this section.</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          {icon}
          <h3 className={`text-xl font-bold ${gradient || 'text-purple-400'}`}>{title}</h3>
        </div>
        <div className="space-y-3">
          {textContent.split('\n').map((paragraph, index) => (
            <p key={index} className="text-gray-300 leading-relaxed whitespace-pre-wrap">
              {paragraph}
            </p>
          ))}
        </div>
      </div>
    );
  };

  // Premium resource display with enhanced visuals
  const renderRecommendedResources = (resourcesData?: any[]) => {
    if (!resourcesData || resourcesData.length === 0) {
      return (
        <div className="text-center py-8">
          <BookOpen className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400">No resources available for this session.</p>
        </div>
      );
    }

    // Check format and render accordingly
    const isLegacyFormat = resourcesData.length > 0 && resourcesData[0]?.topic && resourcesData[0]?.resources;
    
    if (isLegacyFormat) {
      return (
        <div className="space-y-6">
          {resourcesData.map((item, index) => (
            <div key={index} className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center">
                  <BookMarked className="w-4 h-4 text-white" />
                </div>
                <h4 className="text-lg font-semibold text-emerald-400">{item.topic}</h4>
              </div>
              
              {item.resources && item.resources.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {item.resources.map((resource: any, rIndex: number) => (
                    <div key={rIndex} className="group bg-black/40 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:border-emerald-500/40 hover:shadow-emerald-500/10 transition-all duration-300">
                      <div className="flex items-start space-x-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                          <ExternalLink className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <a
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-semibold text-white hover:text-emerald-300 transition-colors group block"
                          >
                            {resource.title}
                          </a>
                          <p className="text-sm text-gray-400 mt-2 leading-relaxed">{resource.snippet}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 italic text-sm">No specific resources found for this topic.</p>
              )}
            </div>
          ))}
        </div>
      );
    }

    // New agentic format with enhanced styling
    return (
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center space-x-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            <p className="text-emerald-300 font-medium">AI-Curated Learning Resources</p>
            <Sparkles className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="text-gray-400 text-sm max-w-2xl mx-auto">
            These resources were intelligently selected based on your interview performance, 
            skill gaps, and learning preferences by our advanced AI agent.
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {resourcesData.map((resource: any, index: number) => (
            <div 
              key={index} 
              className="group bg-black/40 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden hover:border-emerald-500/40 hover:shadow-2xl hover:shadow-emerald-500/10 transition-all duration-500"
            >
              {/* Resource header */}
              <div className="p-6 space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                      {resource.resource_type === 'tutorial' ? <Video className="w-6 h-6 text-white" /> :
                       resource.resource_type === 'article' ? <FileText className="w-6 h-6 text-white" /> :
                       resource.resource_type === 'course' ? <GraduationCap className="w-6 h-6 text-white" /> :
                       <BookOpen className="w-6 h-6 text-white" />}
                    </div>
                    {resource.resource_type && (
                      <span className="px-3 py-1 text-xs font-medium bg-emerald-500/20 text-emerald-300 rounded-full border border-emerald-500/30">
                        {resource.resource_type}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group/link"
                  >
                    <h4 className="text-lg font-semibold text-white group-hover/link:text-emerald-300 transition-colors leading-tight">
                      {resource.title}
                    </h4>
                  </a>
                  <p className="text-gray-400 mt-3 text-sm leading-relaxed">{resource.description}</p>
                </div>

                {/* AI reasoning section */}
                {resource.reasoning && (
                  <div className="mt-4 p-4 bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-l-4 border-blue-400/50 rounded-r-xl">
                    <div className="flex items-start space-x-3">
                      <Brain className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-blue-300 font-medium mb-1">AI Recommendation Reasoning:</p>
                        <p className="text-xs text-blue-200 leading-relaxed">{resource.reasoning}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action button */}
                <div className="pt-2">
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-cyan-600 hover:from-emerald-400 hover:to-cyan-500 text-white text-sm font-medium rounded-xl transition-all duration-300 group/btn"
                  >
                    <span>Explore Resource</span>
                    <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Premium error state
  const renderErrorState = (type: 'summary' | 'resources', error: string) => (
    <div className="bg-black/60 backdrop-blur-2xl border border-red-500/30 rounded-2xl p-8 text-center">
      <div className="space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-red-500 to-pink-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8 text-white" />
        </div>
        <div>
          <h3 className="text-xl font-semibold text-red-300 mb-2">Generation Error</h3>
          <p className="text-red-400 text-sm">{error}</p>
        </div>
        <Button
          onClick={() => window.location.reload()}
          variant="outline"
          className="border-red-500/30 text-red-300 hover:bg-red-500/10"
        >
          Try Again
        </Button>
      </div>
    </div>
  );

  // Premium per-turn feedback with enhanced design
  const renderPerTurnFeedback = () => {
    if (!perTurnFeedback || perTurnFeedback.length === 0) {
      return (
        <div className="text-center py-12">
          <MessageSquare className="w-16 h-16 text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-400 mb-2">No Per-Turn Feedback</h3>
          <p className="text-gray-500">No detailed feedback available for this session.</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {perTurnFeedback.map((item, index) => (
          <div 
            key={index} 
            className={`group bg-black/40 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden transition-all duration-500 hover:border-purple-500/40 hover:shadow-purple-500/10 ${
              visibleCards.has(`feedback-${index}`) ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'
            }`}
            id={`feedback-${index}`}
            data-card
          >
            {/* Question header */}
            <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 px-6 py-4 border-b border-white/5">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                    <span className="text-white font-bold text-sm">{index + 1}</span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">Question {index + 1}</p>
                    <h4 className="text-purple-300 font-semibold">{item.question}</h4>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setExpandedFeedback(expandedFeedback === index ? null : index)}
                  className="text-purple-400 hover:text-purple-300"
                >
                  {expandedFeedback === index ? 'Collapse' : 'View Details'}
                </Button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Your answer */}
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded bg-blue-500/20 flex items-center justify-center">
                    <Users className="w-2 h-2 text-blue-400" />
                  </div>
                  <h5 className="text-sm font-medium text-blue-300">Your Response</h5>
                </div>
                <div className={`bg-blue-900/10 border-l-4 border-blue-500/50 rounded-r-xl p-4 ${
                  expandedFeedback === index ? '' : 'line-clamp-3'
                }`}>
                  <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">{item.answer}</p>
                </div>
              </div>

              {/* Coach feedback */}
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded bg-yellow-500/20 flex items-center justify-center">
                    <Brain className="w-2 h-2 text-yellow-400" />
                  </div>
                  <h5 className="text-sm font-medium text-yellow-300">AI Coach Analysis</h5>
                </div>
                <div className={`bg-yellow-900/10 border-l-4 border-yellow-500/50 rounded-r-xl p-4 ${
                  expandedFeedback === index ? '' : 'line-clamp-4'
                }`}>
                  <p className="text-gray-100 text-sm leading-relaxed whitespace-pre-wrap">{item.feedback}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div 
      ref={containerRef}
      className="min-h-screen relative overflow-hidden"
      onMouseMove={handleMouseMove}
    >
      {/* Advanced background */}
      {renderAdvancedBackground()}
      
      <div className="relative z-10 flex flex-col min-h-screen p-4 md:p-8">
        <div className="w-full max-w-7xl mx-auto space-y-8">
          
          {/* Premium header */}
          <div className="text-center space-y-4 py-8">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center shadow-xl">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-400 bg-clip-text text-transparent">
              Interview Analysis Report
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
              Comprehensive AI-powered analysis of your interview performance with personalized recommendations
            </p>
          </div>

          {/* Bento Grid Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left Column - Per-turn feedback (spans 2 columns on large screens) */}
            <div className="lg:col-span-2 space-y-8">
              
              {/* Turn-by-Turn Feedback */}
              <div 
                className={`bg-black/60 backdrop-blur-2xl border border-purple-500/30 rounded-3xl shadow-2xl transition-all duration-700 ${
                  visibleCards.has('feedback-section') ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'
                }`}
                id="feedback-section"
                data-card
              >
                <div className="p-8">
                  <div className="flex items-center space-x-4 mb-8">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-xl">
                      <MessageSquare className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-white">Detailed Feedback</h2>
                      <p className="text-purple-300">Turn-by-turn analysis of your interview responses</p>
                    </div>
                  </div>
                  
                  {renderPerTurnFeedback()}
                </div>
              </div>

              {/* Final Summary */}
              <div 
                className={`bg-black/60 backdrop-blur-2xl border border-blue-500/30 rounded-3xl shadow-2xl transition-all duration-700 ${
                  visibleCards.has('summary-section') ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'
                }`}
                id="summary-section"
                data-card
              >
                <div className="p-8">
                  <div className="flex items-center space-x-4 mb-8">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-xl">
                      {finalSummary.status === 'completed' ? (
                        <CheckCircle className="w-6 h-6 text-white" />
                      ) : finalSummary.status === 'error' ? (
                        <AlertCircle className="w-6 h-6 text-white" />
                      ) : (
                        <Brain className="w-6 h-6 text-white" />
                      )}
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-white">Performance Analysis</h2>
                      <p className="text-blue-300">Comprehensive evaluation by our AI coach</p>
                    </div>
                  </div>

                  {finalSummary.status === 'loading' && renderAnalysisLoading()}
                  {finalSummary.status === 'error' && renderErrorState('summary', finalSummary.error || 'Unknown error')}
                  {finalSummary.status === 'completed' && finalSummary.data && (
                    <div className="space-y-8">
                      {renderTextSection(
                        "Observed Patterns & Tendencies", 
                        finalSummary.data.patterns_tendencies,
                        <TrendingUp className="w-6 h-6 text-orange-400" />,
                        "bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent"
                      )}
                      {renderTextSection(
                        "Key Strengths", 
                        finalSummary.data.strengths,
                        <Award className="w-6 h-6 text-emerald-400" />,
                        "bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent"
                      )}
                      {renderTextSection(
                        "Areas for Development", 
                        finalSummary.data.weaknesses,
                        <Target className="w-6 h-6 text-amber-400" />,
                        "bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent"
                      )}
                      {renderTextSection(
                        "Focus Areas for Improvement", 
                        finalSummary.data.improvement_focus_areas,
                        <Lightbulb className="w-6 h-6 text-purple-400" />,
                        "bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent"
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column - Resources and CTA */}
            <div className="space-y-8">
              
              {/* Learning Resources */}
              <div 
                className={`bg-black/60 backdrop-blur-2xl border border-emerald-500/30 rounded-3xl shadow-2xl transition-all duration-700 ${
                  visibleCards.has('resources-section') ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'
                }`}
                id="resources-section"
                data-card
              >
                <div className="p-8">
                  <div className="flex items-center space-x-4 mb-8">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center shadow-xl">
                      {resources.status === 'completed' ? (
                        <CheckCircle className="w-6 h-6 text-white" />
                      ) : resources.status === 'error' ? (
                        <AlertCircle className="w-6 h-6 text-white" />
                      ) : (
                        <Search className="w-6 h-6 text-white" />
                      )}
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-white">Learning Resources</h2>
                      <p className="text-emerald-300 text-sm">AI-curated materials for your growth</p>
                    </div>
                  </div>

                  {resources.status === 'loading' && renderAgenticSearchLoading()}
                  {resources.status === 'error' && renderErrorState('resources', resources.error || 'Unknown error')}
                  {resources.status === 'completed' && resources.data && renderRecommendedResources(resources.data)}
                </div>
              </div>

              {/* Action Card */}
              <div 
                className={`bg-black/60 backdrop-blur-2xl border border-cyan-500/30 rounded-3xl shadow-2xl p-8 text-center transition-all duration-700 ${
                  visibleCards.has('cta-section') ? 'opacity-100 transform-none' : 'opacity-0 translate-y-8'
                }`}
                id="cta-section"
                data-card
              >
                <div className="space-y-6">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center mx-auto shadow-xl">
                    <Zap className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-2">Ready for Your Next Challenge?</h3>
                    <p className="text-gray-400">Apply what you've learned and practice again to improve further.</p>
                  </div>
                  <Button
                    onClick={onStartNewInterview}
                    size="lg"
                    className="w-full bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white shadow-lg hover:shadow-cyan-500/20 text-lg font-semibold py-4 rounded-xl transition-all duration-300 group"
                  >
                    <span>Start New Interview</span>
                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PostInterviewReport; 