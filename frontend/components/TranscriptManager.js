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
              exportFormat === 'markdown' ? 'text/markdown' : 'text/plain' 
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
      
    } catch (err) {
      setError(err.message);
      console.error("Failed to export transcript:", err);
    } finally {
      setIsLoading(false);
    }
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
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <button
            className="text-blue-600 hover:underline"
            onClick={() => {
              setSelectedTranscript(null);
              setViewMode('list');
            }}
          >
            &larr; Back to List
          </button>
          
          <div className="flex items-center gap-2">
            <select
              className="p-2 border rounded"
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
            >
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
              <option value="markdown">Markdown</option>
              <option value="text">Plain Text</option>
            </select>
            <button
              className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
              onClick={() => exportTranscript(selectedTranscript.id)}
              disabled={isLoading}
            >
              {isLoading ? 'Exporting...' : 'Export'}
            </button>
          </div>
        </div>

        <div className="p-6 border rounded-lg">
          <h2 className="text-2xl font-bold">{selectedTranscript.title}</h2>
          
          <div className="flex flex-wrap gap-2 mt-3">
            {selectedTranscript.tags.map(tag => (
              <span 
                key={tag.id}
                className="px-2 py-1 text-xs rounded-full"
                style={{ backgroundColor: tag.color || '#e6f2ff' }}
              >
                {tag.name}
              </span>
            ))}
          </div>
          
          {selectedTranscript.summary && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium">Summary</h3>
              <p className="text-gray-700 mt-1">{selectedTranscript.summary}</p>
            </div>
          )}
          
          <div className="mt-6">
            <h3 className="font-medium mb-4">Conversation</h3>
            <div className="space-y-4">
              {selectedTranscript.content.map((message, index) => {
                const isUser = message.role === 'user';
                
                return (
                  <div 
                    key={index} 
                    className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div 
                      className={`max-w-3/4 p-3 rounded-lg ${
                        isUser 
                          ? 'bg-blue-600 text-white rounded-br-none' 
                          : 'bg-gray-200 text-gray-800 rounded-bl-none'
                      }`}
                    >
                      {!isUser && message.agent && (
                        <div className="font-medium text-sm mb-1">
                          {message.agent}
                        </div>
                      )}
                      <div>{message.content}</div>
                      {message.timestamp && (
                        <div className="text-xs mt-1 opacity-70">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          
          {selectedTranscript.metadata && Object.keys(selectedTranscript.metadata).length > 0 && (
            <div className="mt-6 border-t pt-4">
              <h3 className="font-medium mb-2">Metadata</h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(selectedTranscript.metadata).map(([key, value]) => (
                  <div key={key} className="text-sm">
                    <span className="font-medium">{key}: </span>
                    <span className="text-gray-700">{typeof value === 'string' ? value : JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
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

  return (
    <div className="container mx-auto p-4">
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
      
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 border-4 border-t-blue-600 border-r-transparent border-b-blue-600 border-l-transparent rounded-full animate-spin"></div>
              <p>Loading...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TranscriptManager; 