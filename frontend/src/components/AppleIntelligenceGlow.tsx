import React, { useEffect, useRef } from 'react';

interface AppleIntelligenceGlowProps {
  isActive: boolean;
  mode: 'user' | 'ai' | 'idle';
  voiceActivity?: number; // 0-1 for voice volume
  className?: string;
  children?: React.ReactNode;
}

const AppleIntelligenceGlow: React.FC<AppleIntelligenceGlowProps> = ({
  isActive,
  mode,
  voiceActivity = 0,
  className = '',
  children
}) => {
  const glowRef = useRef<HTMLDivElement>(null);
  const rippleRef = useRef<HTMLDivElement>(null);

  // Update glow intensity based on voice activity
  useEffect(() => {
    if (!glowRef.current) return;

    const intensity = Math.max(0.3, voiceActivity);
    const scale = 1 + (voiceActivity * 0.3);
    
    if (mode === 'user' && isActive) {
      glowRef.current.style.setProperty('--glow-opacity', intensity.toString());
      glowRef.current.style.setProperty('--glow-scale', scale.toString());
    } else if (mode === 'ai' && isActive) {
      glowRef.current.style.setProperty('--glow-opacity', intensity.toString());
      glowRef.current.style.setProperty('--glow-scale', scale.toString());
    }
  }, [voiceActivity, isActive, mode]);

  // Create ripple effect on activation
  useEffect(() => {
    if (isActive && rippleRef.current) {
      const ripple = rippleRef.current;
      ripple.style.animation = 'none';
      // Force reflow
      ripple.offsetHeight;
      ripple.style.animation = 'apple-ripple 1.5s ease-out';
    }
  }, [isActive]);

  const getGlowClass = () => {
    if (!isActive && mode === 'idle') return 'glow-breathing';
    if (mode === 'user' && isActive) return 'apple-glow-user';
    if (mode === 'ai' && isActive) return 'apple-glow-ai';
    return '';
  };

  const getGlowColors = () => {
    switch (mode) {
      case 'user':
        return {
          primary: 'rgba(0, 122, 255, 0.4)',
          secondary: 'rgba(0, 122, 255, 0.2)',
          tertiary: 'rgba(0, 122, 255, 0.1)'
        };
      case 'ai':
        return {
          primary: 'rgba(255, 149, 0, 0.4)',
          secondary: 'rgba(175, 82, 222, 0.3)',
          tertiary: 'rgba(255, 149, 0, 0.1)'
        };
      default:
        return {
          primary: 'rgba(255, 255, 255, 0.1)',
          secondary: 'rgba(255, 255, 255, 0.05)',
          tertiary: 'rgba(255, 255, 255, 0.02)'
        };
    }
  };

  const colors = getGlowColors();

  return (
    <div 
      ref={glowRef}
      className={`relative ${getGlowClass()} ${className}`}
      style={{
        '--glow-opacity': isActive ? '0.6' : '0.3',
        '--glow-scale': isActive ? '1.1' : '1',
      } as React.CSSProperties}
    >
      {/* Primary Glow Layer */}
      <div 
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(circle at center, ${colors.primary} 0%, transparent 70%)`,
          transform: `scale(var(--glow-scale, 1))`,
          opacity: `var(--glow-opacity, 0.3)`,
          transition: 'all 0.3s ease-out',
          filter: 'blur(8px)',
        }}
      />
      
      {/* Secondary Glow Layer */}
      <div 
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(circle at center, ${colors.secondary} 0%, transparent 60%)`,
          transform: `scale(calc(var(--glow-scale, 1) * 1.3))`,
          opacity: `calc(var(--glow-opacity, 0.3) * 0.7)`,
          transition: 'all 0.3s ease-out',
          filter: 'blur(16px)',
        }}
      />
      
      {/* Tertiary Glow Layer */}
      <div 
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(circle at center, ${colors.tertiary} 0%, transparent 50%)`,
          transform: `scale(calc(var(--glow-scale, 1) * 1.6))`,
          opacity: `calc(var(--glow-opacity, 0.3) * 0.5)`,
          transition: 'all 0.3s ease-out',
          filter: 'blur(24px)',
        }}
      />

      {/* Ripple Effect */}
      {isActive && (
        <div 
          ref={rippleRef}
          className="absolute inset-0 rounded-full pointer-events-none"
          style={{
            background: `radial-gradient(circle at center, ${colors.primary} 0%, transparent 70%)`,
            opacity: '0',
          }}
        />
      )}

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>

      {/* Ambient Particles for Enhanced Effect */}
      {isActive && voiceActivity > 0.5 && (
        <>
          <div 
            className="particle-effect"
            style={{
              top: '20%',
              left: '20%',
              animationDelay: '0s',
            }}
          />
          <div 
            className="particle-effect"
            style={{
              top: '30%',
              right: '25%',
              animationDelay: '1s',
            }}
          />
          <div 
            className="particle-effect"
            style={{
              bottom: '25%',
              left: '30%',
              animationDelay: '2s',
            }}
          />
          <div 
            className="particle-effect"
            style={{
              bottom: '20%',
              right: '20%',
              animationDelay: '3s',
            }}
          />
        </>
      )}
    </div>
  );
};

export default AppleIntelligenceGlow; 