const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

console.log('API Service using Backend URL:', BACKEND_URL);

/**
 * Handles basic error checking for fetch responses.
 * Throws an error with backend message if response is not ok.
 * @param {Response} response - The fetch response object.
 * @returns {Promise<Response>} - The response object if ok.
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    let errorMsg = `HTTP error! status: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMsg = errorData.detail || errorData.message || errorMsg;
    } catch (e) {
      // Ignore if response body is not JSON
    }
    console.error('API Error:', errorMsg);
    throw new Error(errorMsg);
  }
  return response;
};

/**
 * Performs a GET request and returns the JSON response.
 * @param {string} endpoint - The API endpoint (e.g., '/api/health').
 * @param {object} [options] - Optional fetch options.
 * @returns {Promise<any>} - The JSON response data.
 */
export const getJson = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    await handleResponse(response);
    return await response.json();
  } catch (error) {
    console.error(`GET request to ${endpoint} failed:`, error);
    throw error; // Re-throw the error for components to handle
  }
};

/**
 * Performs a POST request with JSON data.
 * @param {string} endpoint - The API endpoint.
 * @param {object} data - The data to send as JSON.
 * @param {object} [options] - Optional fetch options.
 * @returns {Promise<any>} - The JSON response data.
 */
export const postJson = async (endpoint, data, options = {}) => {
  try {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(data),
      ...options,
    });
    await handleResponse(response);
    // Handle cases where backend might return empty response (e.g., 204 No Content)
    if (response.status === 204) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error(`POST JSON request to ${endpoint} failed:`, error);
    throw error;
  }
};

/**
 * Performs a POST request with FormData (e.g., for file uploads).
 * @param {string} endpoint - The API endpoint.
 * @param {FormData} formData - The FormData object to send.
 * @param {object} [options] - Optional fetch options.
 * @returns {Promise<any>} - The JSON response data.
 */
export const postFormData = async (endpoint, formData, options = {}) => {
  try {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: 'POST',
      // Note: Don't set Content-Type header for FormData, 
      // the browser sets it automatically with the correct boundary.
      headers: {
        'Accept': 'application/json',
        ...options.headers,
      },
      body: formData,
      ...options,
    });
    await handleResponse(response);
    if (response.status === 204) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error(`POST FormData request to ${endpoint} failed:`, error);
    throw error;
  }
};

// Example usage (can be removed later):
// export const getHealth = () => getJson('/api/health');
// export const startSession = (data) => postJson('/api/agents/session/start', data);
// export const sendMessage = (sessionId, data) => postJson(`/api/agents/session/${sessionId}/chat`, data);
// export const uploadResume = (sessionId, formData) => postFormData(`/api/agents/session/${sessionId}/resume`, formData); 