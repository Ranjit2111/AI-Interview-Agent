import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';

/**
 * TranscriptManager component for managing interview transcripts
 * Features:
 * - List transcripts with filtering/search
 * - View individual transcripts
 * - Export/import transcripts
 * - Search across transcripts by content
 */
const TranscriptManager = () => {
  // State variables
  const [transcripts, setTranscripts] = useState([]);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [exportFormat, setExportFormat] = useState('json');
  const [viewMode, setViewMode] = useState('list'); // 'list', 'detail', 'search'

  // Pagination constants
  const PAGE_SIZE = 10;

  // API URL
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Fetch transcripts from API
  const fetchTranscripts = useCallback(async (reset = false) => {
    try {
      setIsLoading(true);
      setError(null);

      // Reset page if needed
      const currentPage = reset ? 0 : page;
      if (reset) {
        setPage(0);
        setTranscripts([]);
      }

      // Build query parameters
      const params = new URLSearchParams({
        limit: PAGE_SIZE,
        offset: currentPage * PAGE_SIZE,
      });

      // Add selected tags to query
      if (selectedTags.length > 0) {
        selectedTags.forEach(tag => params.append('tags', tag));
      }

      // Fetch data
      const response = await fetch(`${API_URL}/api/transcripts?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Error fetching transcripts: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Update state
      setTranscripts(prev => reset ? data.transcripts : [...prev, ...data.transcripts]);
      setHasMore(data.transcripts.length === PAGE_SIZE);
      
    } catch (err) {
      setError(err.message);
      console.error("Failed to fetch transcripts:", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL, page, selectedTags]);

  // Fetch transcript tags
  const fetchTags = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/transcripts/tags`);
      
      if (!response.ok) {
        throw new Error(`Error fetching tags: ${response.statusText}`);
      }

      const data = await response.json();
      setTags(data);
      
    } catch (err) {
      console.error("Failed to fetch tags:", err);
      // Non-critical, don't set error
    }
  }, [API_URL]);

  // Fetch a specific transcript
  const fetchTranscript = useCallback(async (id) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/transcripts/${id}`);
      
      if (!response.ok) {
        throw new Error(`Error fetching transcript: ${response.statusText}`);
      }

      const data = await response.json();
      setSelectedTranscript(data);
      setViewMode('detail');
      
    } catch (err) {
      setError(err.message);
      console.error("Failed to fetch transcript:", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  // Search transcripts
  const searchTranscripts = useCallback(async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      setIsSearching(true);
      setError(null);

      // Build query parameters
      const params = new URLSearchParams({
        query: query,
      });

      // Add selected tags to query
      if (selectedTags.length > 0) {
        selectedTags.forEach(tag => params.append('tags', tag));
      }

      // Perform search
      const response = await fetch(`${API_URL}/api/transcripts/search?${params.toString()}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`Error searching transcripts: ${response.statusText}`);
      }

      const data = await response.json();
      setSearchResults(data);
      setViewMode('search');
      
    } catch (err) {
      setError(err.message);
      console.error("Failed to search transcripts:", err);
    } finally {
      setIsSearching(false);
    }
  }, [API_URL, selectedTags]);

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce((query) => {
      searchTranscripts(query);
    }, 500),
    [searchTranscripts]
  );

  // Handle search input change
  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    debouncedSearch(query);
  };

  // Handle tag selection
  const handleTagSelect = (tagName) => {
    setSelectedTags(prev => {
      if (prev.includes(tagName)) {
        return prev.filter(t => t !== tagName);
      } else {
        return [...prev, tagName];
      }
    });
  };

  // Export transcript
  const exportTranscript = async (id) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/transcripts/${id}/export?format=${exportFormat}`);
      
      if (!response.ok) {
        throw new Error(`Error exporting transcript: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Create download link
      const blob = new Blob([data.content], { 
        type: exportFormat === 'json' ? 'application/json' : 
              exportFormat === 'csv' ? 'text/csv' : 
              exportFormat === 'markdown' ? 'text/markdown' : 
              exportFormat === 'pdf' ? 'application/pdf' :
              exportFormat === 'docx' ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' :
              'text/plain' 
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);
      
      // Success notification
      showNotification('Transcript exported successfully!', 'success');
      
    } catch (err) {
      setError(err.message);
      console.error("Failed to export transcript:", err);
      showNotification(`Export failed: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Show notification
  const [notification, setNotification] = useState({ message: '', type: '', visible: false });
  
  const showNotification = (message, type = 'info') => {
    setNotification({ message, type, visible: true });
    setTimeout(() => {
      setNotification(prev => ({ ...prev, visible: false }));
    }, 3000);
  };

  // Import transcript
  const importTranscript = async (file) => {
    try {
      setIsLoading(true);
      setError(null);

      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Determine format from file extension
      const fileName = file.name.toLowerCase();
      let format = 'json';
      
      if (fileName.endsWith('.json')) {
        format = 'json';
      } else if (fileName.endsWith('.csv')) {
        format = 'csv';
      } else if (fileName.endsWith('.md')) {
        format = 'markdown';
      } else if (fileName.endsWith('.txt')) {
        format = 'text';
      }
      
      // Send request
      const response = await fetch(`${API_URL}/api/transcripts/import?format=${format}`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Error importing transcript: ${response.statusText}`);
      }

      // Refresh transcript list
      fetchTranscripts(true);
      
    } catch (err) {
      setError(err.message);
      console.error("Failed to import transcript:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle file upload for import
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      importTranscript(file);
    }
  };

  // Load more transcripts
  const loadMore = () => {
    setPage(prev => prev + 1);
  };

  // Initial data load
  useEffect(() => {
    fetchTranscripts();
    fetchTags();
  }, [fetchTranscripts, fetchTags]);

  // Refresh when selected tags change
  useEffect(() => {
    fetchTranscripts(true);
  }, [selectedTags, fetchTranscripts]);

  // Render transcript list view
  const renderTranscriptList = () => (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Interview Transcripts</h2>
      
      {transcripts.length === 0 && !isLoading ? (
        <p className="text-gray-500">No transcripts found. Start an interview or import transcripts.</p>
      ) : (
        <div className="space-y-4">
          {transcripts.map(transcript => (
            <div 
              key={transcript.id}
              className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition"
              onClick={() => fetchTranscript(transcript.id)}
            >
              <h3 className="font-medium">{transcript.title}</h3>
              <div className="flex flex-wrap gap-2 mt-2">
                {transcript.tags.map(tag => (
                  <span 
                    key={tag.id}
                    className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800"
                    style={{ backgroundColor: tag.color || '#e6f2ff' }}
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {new Date(transcript.created_at).toLocaleDateString()}
              </p>
              {transcript.summary && (
                <p className="text-sm text-gray-700 mt-2 line-clamp-2">
                  {transcript.summary}
                </p>
              )}
            </div>
          ))}
          
          {hasMore && (
            <button
              className="w-full py-2 border rounded-lg hover:bg-gray-50 transition"
              onClick={loadMore}
              disabled={isLoading}
            >
              {isLoading ? 'Loading...' : 'Load More'}
            </button>
          )}
        </div>
      )}
    </div>
  );

  // Render transcript detail view
  const renderTranscriptDetail = () => {
    if (!selectedTranscript) return null;
    
    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">{selectedTranscript.title || 'Interview Transcript'}</h2>
          <button
            onClick={() => setViewMode('list')}
            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Back to List
          </button>
        </div>
        
        <div className="mb-3 text-sm text-gray-600 dark:text-gray-400">
          <span>Date: {new Date(selectedTranscript.timestamp).toLocaleString()}</span>
          {selectedTranscript.duration && (
            <span className="ml-4">Duration: {formatDuration(selectedTranscript.duration)}</span>
          )}
        </div>
        
        {selectedTranscript.tags && selectedTranscript.tags.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-2">
            {selectedTranscript.tags.map(tag => (
              <span key={tag} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                {tag}
              </span>
            ))}
          </div>
        )}
        
        {selectedTranscript.summary && (
          <div className="mb-6 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
            <h3 className="font-medium mb-2">Summary</h3>
            <p className="text-gray-700 dark:text-gray-300">{selectedTranscript.summary}</p>
          </div>
        )}
        
        <div className="mb-6">
          <h3 className="font-medium mb-2">Transcript</h3>
          <div className="max-h-96 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
            {renderMessages(selectedTranscript.messages)}
          </div>
        </div>
        
        {selectedTranscript.feedback && (
          <div className="mb-6">
            <h3 className="font-medium mb-2">Feedback</h3>
            <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
              {selectedTranscript.feedback}
            </div>
          </div>
        )}
        
        {renderExportOptions()}
      </div>
    );
  };

  // Render search results
  const renderSearchResults = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Search Results</h2>
        <button
          className="text-blue-600 hover:underline"
          onClick={() => {
            setViewMode('list');
            setSearchQuery('');
            setSearchResults([]);
          }}
        >
          &larr; Back to List
        </button>
      </div>
      
      {searchResults.length === 0 ? (
        <p className="text-gray-500">No results found. Try a different search term.</p>
      ) : (
        <div className="space-y-4">
          {searchResults.map((result, index) => (
            <div 
              key={index}
              className="p-4 border rounded-lg hover:bg-gray-50 transition"
              onClick={() => fetchTranscript(result.transcript_id)}
            >
              <h3 className="font-medium">{result.title}</h3>
              <div className="mt-2 p-3 bg-yellow-50 rounded text-sm">
                <div dangerouslySetInnerHTML={{ 
                  __html: highlightSearchTerm(result.content, searchQuery) 
                }} />
              </div>
              <div className="flex justify-between mt-2 text-sm text-gray-500">
                <span>Relevance: {Math.round(result.relevance_score * 100)}%</span>
                <span>{result.created_at ? new Date(result.created_at).toLocaleDateString() : ''}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Helper function to highlight search terms
  const highlightSearchTerm = (text, query) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.trim()})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-300">$1</mark>');
  };

  // Render export options in the transcript detail view
  const renderExportOptions = () => (
    <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <h3 className="text-md font-medium mb-3">Export Options</h3>
      <div className="flex flex-wrap gap-3 mb-3">
        {['json', 'csv', 'markdown', 'pdf', 'docx', 'txt'].map(format => (
          <button
            key={format}
            onClick={() => setExportFormat(format)}
            className={`px-3 py-1.5 rounded-lg text-sm ${
              exportFormat === format
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {format.toUpperCase()}
          </button>
        ))}
      </div>
      <button
        onClick={() => exportTranscript(selectedTranscript.id)}
        disabled={isLoading}
        className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Exporting...
          </>
        ) : (
          <>
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
            </svg>
            Export as {exportFormat.toUpperCase()}
          </>
        )}
      </button>
    </div>
  );

  return (
    <div className="relative">
      {/* Main content */}
      <div className="space-y-6">
        {error && (
          <div className="p-4 mb-4 bg-red-100 text-red-700 rounded-lg">
            {error}
          </div>
        )}
        
        <div className="mb-6">
          <div className="flex flex-col md:flex-row gap-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  className="w-full p-3 border rounded-lg pl-10"
                  placeholder="Search transcripts..."
                  value={searchQuery}
                  onChange={handleSearchChange}
                />
                <svg
                  className="absolute left-3 top-3.5 h-5 w-5 text-gray-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>
            
            <div>
              <label className="inline-block w-full md:w-auto">
                <span className="sr-only">Import Transcript</span>
                <input
                  type="file"
                  accept=".json,.csv,.md,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <span className="inline-block px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 cursor-pointer transition w-full md:w-auto text-center">
                  Import Transcript
                </span>
              </label>
            </div>
          </div>
          
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tags.map(tag => (
                <button
                  key={tag.id}
                  className={`px-3 py-1 rounded-full text-sm transition ${
                    selectedTags.includes(tag.name)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                  }`}
                  style={selectedTags.includes(tag.name) ? {} : { backgroundColor: tag.color || '#f3f4f6' }}
                  onClick={() => handleTagSelect(tag.name)}
                >
                  {tag.name}
                </button>
              ))}
            </div>
          )}
        </div>
        
        {viewMode === 'list' && renderTranscriptList()}
        {viewMode === 'detail' && renderTranscriptDetail()}
        {viewMode === 'search' && renderSearchResults()}
      </div>
      
      {/* Notification */}
      {notification.visible && (
        <div className={`fixed bottom-4 right-4 py-2 px-4 rounded-md shadow-lg transition-opacity ${
          notification.type === 'success' ? 'bg-green-500 text-white' :
          notification.type === 'error' ? 'bg-red-500 text-white' :
          'bg-blue-500 text-white'
        }`}>
          <div className="flex items-center">
            {notification.type === 'success' && (
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            )}
            {notification.type === 'error' && (
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            {notification.message}
          </div>
        </div>
      )}
    </div>
  );
};

export default TranscriptManager; 