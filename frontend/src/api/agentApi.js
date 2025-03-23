import axios from 'axios';

// Base API URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Start a new interview session
 * @param {Object} config - Interview configuration
 * @returns {Promise<Object>} Session information
 */
export const startInterview = async (config) => {
  try {
    const response = await apiClient.post('/api/interview/start', config);
    return response.data;
  } catch (error) {
    console.error('Error starting interview:', error);
    throw error;
  }
};

/**
 * Send a message to the interview agent
 * @param {string} message - User message
 * @param {string} sessionId - Session identifier
 * @param {string} userId - Optional user identifier
 * @returns {Promise<Object>} Agent response
 */
export const sendMessage = async (message, sessionId, userId = null) => {
  try {
    const response = await apiClient.post('/api/interview/send', {
      message,
      session_id: sessionId,
      user_id: userId,
    });
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

/**
 * End an interview session
 * @param {string} sessionId - Session identifier
 * @param {string} userId - Optional user identifier
 * @returns {Promise<Object>} End confirmation
 */
export const endInterview = async (sessionId, userId = null) => {
  try {
    const response = await apiClient.post('/api/interview/end', {
      message: '',
      session_id: sessionId,
      user_id: userId,
    });
    return response.data;
  } catch (error) {
    console.error('Error ending interview:', error);
    throw error;
  }
};

/**
 * Get information about an interview session
 * @param {string} sessionId - Session identifier
 * @returns {Promise<Object>} Session information
 */
export const getSessionInfo = async (sessionId) => {
  try {
    const response = await apiClient.get(`/api/interview/info?session_id=${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting session info:', error);
    throw error;
  }
};

/**
 * List active interview sessions
 * @param {string} userId - Optional user identifier to filter by
 * @returns {Promise<Array>} List of active sessions
 */
export const listSessions = async (userId = null) => {
  try {
    const url = userId ? `/api/interview/sessions?user_id=${userId}` : '/api/interview/sessions';
    const response = await apiClient.get(url);
    return response.data;
  } catch (error) {
    console.error('Error listing sessions:', error);
    throw error;
  }
};

/**
 * Get metrics for an interview session
 * @param {string} sessionId - Session identifier
 * @returns {Promise<Object>} Session metrics
 */
export const getSessionMetrics = async (sessionId) => {
  try {
    const response = await apiClient.get(`/api/interview/metrics?session_id=${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting session metrics:', error);
    throw error;
  }
};

/**
 * Get conversation history for a session
 * @param {string} sessionId - Session identifier
 * @returns {Promise<Array>} Conversation history
 */
export const getConversationHistory = async (sessionId) => {
  try {
    const response = await apiClient.get(`/api/interview/history?session_id=${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting conversation history:', error);
    throw error;
  }
}; 