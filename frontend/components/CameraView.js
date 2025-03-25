import { useEffect, useRef, useState } from 'react';

// This component is rendered only on the client side
// It handles camera access and display
const CameraView = ({ autoStart = false }) => {
  const videoRef = useRef(null);
  const [hasError, setHasError] = useState(false);
  const [isActive, setIsActive] = useState(autoStart);
  const [stream, setStream] = useState(null);

  useEffect(() => {
    // Only start camera if isActive is true
    if (isActive) {
      startCamera();
    }
    
    // Clean up when the component unmounts
    return () => {
      stopCamera();
    };
  }, [isActive]);

  const startCamera = async () => {
    try {
      // Request camera access
      const videoStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          facingMode: "user" 
        }
      });
      
      // Set the video stream to the video element
      if (videoRef.current) {
        videoRef.current.srcObject = videoStream;
      }
      
      setStream(videoStream);
      setHasError(false);
    } catch (err) {
      console.error("Error accessing camera:", err);
      setHasError(true);
    }
  };
  
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      
      // Clear video source
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    }
  };
  
  const toggleCamera = () => {
    if (isActive) {
      stopCamera();
    } else {
      startCamera();
    }
    setIsActive(!isActive);
  };

  return (
    <div className="relative w-full h-full">
      {isActive ? (
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          muted 
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-dark-800">
          <p className="text-gray-400">Camera is turned off</p>
        </div>
      )}
      
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70">
          <p className="text-red-400">Camera access denied or not available</p>
        </div>
      )}
      
      {/* Camera controls */}
      <div className="absolute bottom-3 left-1/2 transform -translate-x-1/2 flex items-center space-x-2">
        <button
          onClick={toggleCamera}
          className={`p-3 rounded-full ${
            isActive ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'
          } text-white transition-colors`}
          aria-label={isActive ? 'Turn off camera' : 'Turn on camera'}
        >
          {isActive ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
};

export default CameraView; 