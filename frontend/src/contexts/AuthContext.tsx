import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

// Define types
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  getToken: () => string | null;
}

interface User {
  id: string;
  email: string;
  name: string;
  created_at?: string;
}

interface AuthProviderProps {
  children: ReactNode;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: User;
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Storage keys
const ACCESS_TOKEN_KEY = 'ai_interviewer_access_token';
const REFRESH_TOKEN_KEY = 'ai_interviewer_refresh_token';
const USER_KEY = 'ai_interviewer_user';

// API base URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Initialize user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      const storedUser = localStorage.getItem(USER_KEY);
      const storedToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      
      if (storedUser && storedToken) {
        setUser(JSON.parse(storedUser));
        
        // Configure axios with the stored token
        axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        
        // Optionally validate token with backend
        try {
          await axios.get(`${API_URL}/auth/me`);
        } catch (error) {
          // Token is invalid, clear storage
          localStorage.removeItem(ACCESS_TOKEN_KEY);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
          setUser(null);
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      
      setIsLoading(false);
    };
    
    loadUser();
  }, []);
  
  // Register a new user
  const register = async (email: string, password: string, name: string) => {
    setIsLoading(true);
    
    try {
      const response = await axios.post<AuthTokens>(`${API_URL}/auth/register`, {
        email,
        password,
        name
      });
      
      const { access_token, refresh_token, user } = response.data;
      
      // Store tokens and user
      localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      
      // Set user state
      setUser(user);
      
      // Configure axios with the token
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  // Login a user
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    
    try {
      const response = await axios.post<AuthTokens>(`${API_URL}/auth/login`, {
        email,
        password
      });
      
      const { access_token, refresh_token, user } = response.data;
      
      // Store tokens and user
      localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      
      // Set user state
      setUser(user);
      
      // Configure axios with the token
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  // Logout a user
  const logout = async () => {
    setIsLoading(true);
    
    try {
      // Call logout endpoint
      await axios.post(`${API_URL}/auth/logout`);
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local logout even if API call fails
    } finally {
      // Clear storage
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      
      // Clear user state
      setUser(null);
      
      // Remove axios authorization header
      delete axios.defaults.headers.common['Authorization'];
      
      setIsLoading(false);
    }
  };
  
  // Get the current token
  const getToken = (): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  };
  
  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    getToken
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook to use the auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

export default AuthContext; 