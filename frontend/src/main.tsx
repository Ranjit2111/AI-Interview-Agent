import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Create main app root
createRoot(document.getElementById("root")!).render(<App />);

// Initialize stagewise toolbar in development mode only (unless explicitly disabled)
if (import.meta.env.DEV && !import.meta.env.VITE_DISABLE_STAGEWISE) {
  // Create a separate container for the toolbar
  const toolbarContainer = document.createElement('div');
  toolbarContainer.id = 'stagewise-toolbar';
  document.body.appendChild(toolbarContainer);

  // Dynamic import to ensure it's not included in production build
  import('@stagewise/toolbar').then(({ initToolbar }) => {
    const stagewiseConfig = {
      plugins: []
    };
    
    initToolbar(stagewiseConfig);
  }).catch(error => {
    console.warn('Failed to load stagewise toolbar:', error);
  });
}
