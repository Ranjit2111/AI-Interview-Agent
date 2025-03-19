import { useEffect, useRef, useState } from 'react';

// This component is rendered only on the client side
// It handles camera access and display
const CameraView = () => {
  const videoRef = useRef(null);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let stream = null;

    const startCamera = async () => {
      try {
        // Request camera access
        stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            width: { ideal: 1920 },
            height: { ideal: 1080 },
            facingMode: "user" 
          }
        });
        
        // Set the video stream to the video element
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Error accessing camera:", err);
        setHasError(true);
      }
    };
    
    // Start the camera when the component mounts
    startCamera();
    
    // Clean up when the component unmounts
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  if (hasError) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-dark-800">
        <p className="text-red-400">Camera access denied or not available</p>
      </div>
    );
  }

  return (
    <video 
      ref={videoRef} 
      autoPlay 
      playsInline 
      muted 
      className="w-full h-full object-cover"
    />
  );
};

export default CameraView; 