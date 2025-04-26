// frontend/src/context/AppContext.js
import React, { createContext, useState, useContext, useMemo, useCallback } from 'react';

// 1. Create Context
const AppContext = createContext();

// 2. Create Provider Component
export const AppProvider = ({ children }) => {
  const [sessionId, setSessionId] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [jobContext, setJobContextState] = useState({ role: '', description: '', resume: null });
  const [feedbackData, setFeedbackData] = useState(null);
  const [isSessionActive, setIsSessionActive] = useState(false);

  // Clear error function
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Add message to history
  const addMessageToHistory = useCallback((message) => {
    // message should be an object like { role: 'user' | 'agent', content: string }
    setConversationHistory(prev => [...prev, message]);
  }, []);

  // Set job context (including resume file object)
  const setJobContext = useCallback((context) => {
    setJobContextState(context);
  }, []);

  // Function to reset session state
  const resetSession = useCallback(() => {
    setSessionId(null);
    setConversationHistory([]);
    setIsLoading(false);
    setError(null);
    setJobContextState({ role: '', description: '', resume: null });
    setFeedbackData(null);
    setIsSessionActive(false);
    console.log("Session state reset");
  }, []);

  // 3. Provide state and update functions value
  const contextValue = useMemo(() => ({
    sessionId,
    setSessionId,
    conversationHistory,
    addMessageToHistory,
    isLoading,
    setIsLoading,
    error,
    setError,
    clearError,
    jobContext,
    setJobContext,
    feedbackData,
    setFeedbackData,
    isSessionActive,
    setIsSessionActive,
    resetSession
  }), [
    sessionId,
    conversationHistory,
    isLoading,
    error,
    jobContext,
    feedbackData,
    isSessionActive,
    addMessageToHistory,
    clearError,
    setJobContext,
    resetSession
  ]);

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// 4. Create Custom Hook for easy consumption
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}; 