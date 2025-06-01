import type { Config } from "tailwindcss";

export default {
	darkMode: ["class"],
	content: [
		"./pages/**/*.{ts,tsx}",
		"./components/**/*.{ts,tsx}",
		"./app/**/*.{ts,tsx}",
		"./src/**/*.{ts,tsx}",
	],
	prefix: "",
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px'
			}
		},
		extend: {
			colors: {
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				sidebar: {
					DEFAULT: 'hsl(var(--sidebar-background))',
					foreground: 'hsl(var(--sidebar-foreground))',
					primary: 'hsl(var(--sidebar-primary))',
					'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
					accent: 'hsl(var(--sidebar-accent))',
					'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
					border: 'hsl(var(--sidebar-border))',
					ring: 'hsl(var(--sidebar-ring))'
				},
				interview: {
					'primary': '#22d3ee',
					'secondary': '#a855f7',
					'accent': '#f0abfc',
					'user': '#374151',
					'ai': '#1e40af',
				},
				// Apple Intelligence Color Scheme
				apple: {
					'blue': '#007AFF',
					'orange': '#FF9500',
					'purple': '#AF52DE',
					'dark': '#1C1C1E',
					'light-gray': '#F2F2F7',
					'gray': '#48484A',
					'yellow': '#FFD60A',
				}
			},
			fontFamily: {
				'sans': ['"Inter"', 'sans-serif'],
				'mono': ['"JetBrains Mono"', 'monospace'],
				'display': ['"Inter"', 'system-ui', 'sans-serif'],
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			keyframes: {
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				},
				'pulse-slow': {
					'0%, 100%': { opacity: '1' },
					'50%': { opacity: '0.7' },
				},
				'wave': {
					'0%': { transform: 'scale(1)', opacity: '1' },
					'100%': { transform: 'scale(1.5)', opacity: '0' },
				},
				'fade-in': {
					'0%': { opacity: '0', transform: 'translateY(10px)' },
					'100%': { opacity: '1', transform: 'translateY(0)' }
				},
				'slide-in-right': {
					'0%': { opacity: '0', transform: 'translateX(20px)' },
					'100%': { opacity: '1', transform: 'translateX(0)' }
				},
				'scale-in': {
					'0%': { transform: 'scale(0.95)', opacity: '0' },
					'100%': { transform: 'scale(1)', opacity: '1' }
				},
				'glow': {
					'0%, 100%': { boxShadow: '0 0 5px rgba(139, 92, 246, 0.5)' },
					'50%': { boxShadow: '0 0 20px rgba(139, 92, 246, 0.8)' }
				},
				'float': {
					'0%, 100%': { transform: 'translateY(0)' },
					'50%': { transform: 'translateY(-10px)' }
				},
				'gradient-shift': {
					'0%': { backgroundPosition: '0% 50%' },
					'50%': { backgroundPosition: '100% 50%' },
					'100%': { backgroundPosition: '0% 50%' }
				},
				'pulse-ring': {
					'0%': { transform: 'scale(0.8)', opacity: '0' },
					'50%': { transform: 'scale(1)', opacity: '0.5' },
					'100%': { transform: 'scale(1.5)', opacity: '0' }
				},
				'blob': {
					'0%, 100%': { borderRadius: '60% 40% 30% 70%/60% 30% 70% 40%' },
					'25%': { borderRadius: '30% 60% 70% 40%/50% 60% 30% 60%' },
					'50%': { borderRadius: '40% 60% 60% 40%/60% 40% 60% 50%' },
					'75%': { borderRadius: '40% 60% 70% 30%/40% 40% 60% 50%' }
				},
				// Apple Intelligence Animations
				'apple-glow-user': {
					'0%, 100%': { 
						boxShadow: '0 0 20px rgba(0, 122, 255, 0.3), 0 0 40px rgba(0, 122, 255, 0.2), 0 0 80px rgba(0, 122, 255, 0.1)' 
					},
					'50%': { 
						boxShadow: '0 0 30px rgba(0, 122, 255, 0.6), 0 0 60px rgba(0, 122, 255, 0.4), 0 0 120px rgba(0, 122, 255, 0.2)' 
					}
				},
				'apple-glow-ai': {
					'0%, 100%': { 
						boxShadow: '0 0 20px rgba(255, 149, 0, 0.3), 0 0 40px rgba(175, 82, 222, 0.2), 0 0 80px rgba(255, 149, 0, 0.1)' 
					},
					'50%': { 
						boxShadow: '0 0 30px rgba(255, 149, 0, 0.6), 0 0 60px rgba(175, 82, 222, 0.4), 0 0 120px rgba(255, 149, 0, 0.2)' 
					}
				},
				'apple-ripple': {
					'0%': { 
						transform: 'scale(0)', 
						opacity: '1' 
					},
					'100%': { 
						transform: 'scale(4)', 
						opacity: '0' 
					}
				},
				'voice-wave': {
					'0%, 100%': { height: '4px' },
					'50%': { height: '20px' }
				},
				'breathing': {
					'0%, 100%': { 
						transform: 'scale(1)',
						opacity: '0.8'
					},
					'50%': { 
						transform: 'scale(1.05)',
						opacity: '1'
					}
				},
				'mic-pulse': {
					'0%': { 
						transform: 'scale(1)',
						boxShadow: '0 0 0 0 rgba(0, 122, 255, 0.7)'
					},
					'70%': {
						transform: 'scale(1.05)',
						boxShadow: '0 0 0 10px rgba(0, 122, 255, 0)'
					},
					'100%': {
						transform: 'scale(1)',
						boxShadow: '0 0 0 0 rgba(0, 122, 255, 0)'
					}
				},
				'slide-up': {
					'0%': { 
						transform: 'translateY(100%)',
						opacity: '0'
					},
					'100%': { 
						transform: 'translateY(0)',
						opacity: '1'
					}
				},
				'slide-right': {
					'0%': { 
						transform: 'translateX(100%)',
						opacity: '0'
					},
					'100%': { 
						transform: 'translateX(0)',
						opacity: '1'
					}
				},
				'ambient-glow': {
					'0%, 100%': { opacity: '0.3' },
					'50%': { opacity: '0.6' }
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'pulse-slow': 'pulse-slow 3s ease-in-out infinite',
				'wave': 'wave 1.5s linear infinite',
				'fade-in': 'fade-in 0.6s ease-out forwards',
				'slide-in-right': 'slide-in-right 0.5s ease-out',
				'scale-in': 'scale-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
				'glow': 'glow 2s infinite',
				'float': 'float 6s ease-in-out infinite',
				'gradient-shift': 'gradient-shift 8s ease infinite',
				'pulse-ring': 'pulse-ring 2s cubic-bezier(0.455, 0.03, 0.515, 0.955) infinite',
				'blob': 'blob 10s ease-in-out infinite',
				// Apple Intelligence Animations
				'apple-glow-user': 'apple-glow-user 2s ease-in-out infinite',
				'apple-glow-ai': 'apple-glow-ai 2s ease-in-out infinite',
				'apple-ripple': 'apple-ripple 1.5s ease-out',
				'voice-wave': 'voice-wave 1.2s ease-in-out infinite',
				'breathing': 'breathing 3s ease-in-out infinite',
				'mic-pulse': 'mic-pulse 2s infinite',
				'slide-up': 'slide-up 0.3s ease-out',
				'slide-right': 'slide-right 0.3s ease-out',
				'ambient-glow': 'ambient-glow 4s ease-in-out infinite'
			},
			backgroundSize: {
				'200%': '200% 200%',
				'300%': '300% 300%'
			},
			backdropBlur: {
				'xs': '2px',
			},
			boxShadow: {
				'apple-glow-user': '0 0 20px rgba(0, 122, 255, 0.3), 0 0 40px rgba(0, 122, 255, 0.2)',
				'apple-glow-ai': '0 0 20px rgba(255, 149, 0, 0.3), 0 0 40px rgba(175, 82, 222, 0.2)',
				'immersive': '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.05)',
				'glass': '0 8px 32px rgba(0, 0, 0, 0.37)',
			}
		}
	},
	plugins: [require("tailwindcss-animate")],
} satisfies Config;
