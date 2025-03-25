import { useState } from 'react';

const UserContextForm = ({
  onSubmit,
  initialData = {},
  isLoading = false
}) => {
  const [formData, setFormData] = useState({
    jobTitle: initialData.jobTitle || '',
    jobDescription: initialData.jobDescription || '',
    resume: initialData.resume || null,
    transcript: initialData.transcript || null,
    resumeFile: null,
    transcriptFile: null
  });
  
  const [errors, setErrors] = useState({});
  const [uploadProgress, setUploadProgress] = useState({
    resume: 0,
    transcript: 0
  });

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  // Handle file uploads
  const handleFileChange = (e) => {
    const { name, files } = e.target;
    
    if (files && files[0]) {
      // Store the File object for upload
      setFormData(prev => ({
        ...prev,
        [`${name}File`]: files[0]
      }));

      // Create a preview for the file
      const reader = new FileReader();
      reader.onloadstart = () => {
        setUploadProgress(prev => ({
          ...prev,
          [name]: 0
        }));
      };
      
      reader.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(prev => ({
            ...prev,
            [name]: progress
          }));
        }
      };
      
      reader.onload = () => {
        setFormData(prev => ({
          ...prev,
          [name]: reader.result
        }));
        setUploadProgress(prev => ({
          ...prev,
          [name]: 100
        }));
      };
      
      reader.onerror = () => {
        setErrors(prev => ({
          ...prev,
          [name]: 'Error reading file'
        }));
        setUploadProgress(prev => ({
          ...prev,
          [name]: 0
        }));
      };
      
      reader.readAsDataURL(files[0]);
    }
  };

  // Remove uploaded file
  const removeFile = (fileType) => {
    setFormData(prev => ({
      ...prev,
      [fileType]: null,
      [`${fileType}File`]: null
    }));
    setUploadProgress(prev => ({
      ...prev,
      [fileType]: 0
    }));
  };

  // Validate the form
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.jobTitle.trim()) {
      newErrors.jobTitle = 'Job title is required';
    }
    
    if (!formData.jobDescription.trim()) {
      newErrors.jobDescription = 'Job description is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      // Create FormData for multipart/form-data submission
      const data = new FormData();
      data.append('jobTitle', formData.jobTitle);
      data.append('jobDescription', formData.jobDescription);
      
      if (formData.resumeFile) {
        data.append('resume', formData.resumeFile);
      }
      
      if (formData.transcriptFile) {
        data.append('transcript', formData.transcriptFile);
      }
      
      onSubmit(data);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Job Details</h2>
        
        {/* Job Title */}
        <div className="mb-4">
          <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Job Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="jobTitle"
            name="jobTitle"
            value={formData.jobTitle}
            onChange={handleInputChange}
            placeholder="e.g. Frontend Developer"
            className={`w-full px-3 py-2 border ${errors.jobTitle ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white`}
          />
          {errors.jobTitle && (
            <p className="mt-1 text-sm text-red-500">{errors.jobTitle}</p>
          )}
        </div>
        
        {/* Job Description */}
        <div className="mb-4">
          <label htmlFor="jobDescription" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Job Description <span className="text-red-500">*</span>
          </label>
          <textarea
            id="jobDescription"
            name="jobDescription"
            value={formData.jobDescription}
            onChange={handleInputChange}
            placeholder="Paste the job description here..."
            rows={5}
            className={`w-full px-3 py-2 border ${errors.jobDescription ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white`}
          />
          {errors.jobDescription && (
            <p className="mt-1 text-sm text-red-500">{errors.jobDescription}</p>
          )}
        </div>
      </div>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Upload Documents</h2>
        
        {/* Resume Upload */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Resume
          </label>
          
          {!formData.resume ? (
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 dark:border-gray-600 border-dashed rounded-lg">
              <div className="space-y-1 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4h-12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div className="flex text-sm text-gray-600 dark:text-gray-400">
                  <label htmlFor="resumeFile" className="relative cursor-pointer bg-white dark:bg-gray-700 rounded-md font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500 focus-within:outline-none">
                    <span>Upload a file</span>
                    <input 
                      id="resumeFile" 
                      name="resume" 
                      type="file" 
                      accept=".pdf,.doc,.docx" 
                      className="sr-only"
                      onChange={handleFileChange}
                      disabled={isLoading}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  PDF, DOC or DOCX up to 10MB
                </p>
              </div>
            </div>
          ) : (
            <div className="mt-1 relative">
              <div className="flex items-center justify-between p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700">
                <div className="flex items-center">
                  <svg className="h-8 w-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 truncate">
                    {formData.resumeFile ? formData.resumeFile.name : 'Resume uploaded'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile('resume')}
                  className="ml-2 text-gray-400 hover:text-gray-500"
                  disabled={isLoading}
                >
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          )}
          {errors.resume && (
            <p className="mt-1 text-sm text-red-500">{errors.resume}</p>
          )}
        </div>
        
        {/* Previous Interview Transcript Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Previous Interview Transcript (Optional)
          </label>
          
          {!formData.transcript ? (
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 dark:border-gray-600 border-dashed rounded-lg">
              <div className="space-y-1 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4h-12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div className="flex text-sm text-gray-600 dark:text-gray-400">
                  <label htmlFor="transcriptFile" className="relative cursor-pointer bg-white dark:bg-gray-700 rounded-md font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500 focus-within:outline-none">
                    <span>Upload a file</span>
                    <input 
                      id="transcriptFile" 
                      name="transcript" 
                      type="file" 
                      accept=".json,.txt,.md,.csv" 
                      className="sr-only"
                      onChange={handleFileChange}
                      disabled={isLoading}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  JSON, TXT, MD or CSV up to 5MB
                </p>
              </div>
            </div>
          ) : (
            <div className="mt-1 relative">
              <div className="flex items-center justify-between p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700">
                <div className="flex items-center">
                  <svg className="h-8 w-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 truncate">
                    {formData.transcriptFile ? formData.transcriptFile.name : 'Transcript uploaded'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile('transcript')}
                  className="ml-2 text-gray-400 hover:text-gray-500"
                  disabled={isLoading}
                >
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          )}
          {errors.transcript && (
            <p className="mt-1 text-sm text-red-500">{errors.transcript}</p>
          )}
        </div>
      </div>
      
      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isLoading}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </>
          ) : (
            'Set Up Interview'
          )}
        </button>
      </div>
    </form>
  );
};

export default UserContextForm; 