import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-black via-gray-950 to-purple-950/20 px-4">
      <div className="text-center glass-card p-8 rounded-xl shadow-2xl">
        <h1 className="text-6xl font-bold mb-4 text-white">404</h1>
        <p className="text-xl text-gray-300 mb-6">Oops! Page not found</p>
        <p className="text-gray-400 mb-8">The page you're looking for doesn't exist.</p>
        <Link 
          to="/" 
          className="inline-block bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold py-3 px-6 rounded-md hover:from-purple-700 hover:to-blue-700 transition-all duration-200"
        >
          Return to Home
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
