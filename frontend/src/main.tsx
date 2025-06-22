import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Create main app root
createRoot(document.getElementById("root")!).render(<App />);

// Initialize stagewise toolbar in development mode only
if (import.meta.env.DEV) {
  import('@stagewise/toolbar-react').then(({ StagewiseToolbar }) => {
    // Create a separate div for the toolbar
    const toolbarDiv = document.createElement('div');
    toolbarDiv.id = 'stagewise-toolbar';
    document.body.appendChild(toolbarDiv);

    // Configure stagewise with empty plugins array
    const stagewiseConfig = {
      plugins: []
    };

    // Create separate root for toolbar to avoid interfering with main app
    const toolbarRoot = createRoot(toolbarDiv);
    toolbarRoot.render(<StagewiseToolbar config={stagewiseConfig} />);
  }).catch((error) => {
    console.warn('Failed to load stagewise toolbar:', error);
  });
}
