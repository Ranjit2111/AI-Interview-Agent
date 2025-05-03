"""
API documentation generator.
Provides utilities for generating and exporting API documentation.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


def generate_static_docs(app, output_dir: str, template_dir: Optional[str] = None) -> str:
    """
    Generate static HTML documentation.
    
    Args:
        app: FastAPI application instance
        output_dir: Directory to save the documentation
        template_dir: Optional custom template directory
        
    Returns:
        Path to the documentation directory
    """
    # Create directories
    docs_dir = os.path.join(output_dir, "api_docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    # Save OpenAPI spec    
    # Generate HTML index file
    index_path = os.path.join(docs_dir, "index.html")
    with open(index_path, "w") as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Interviewer Agent API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: "./openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                validatorUrl: null
            }});
            window.ui = ui;
        }};
    </script>
</body>
</html>
        """)
    
    # Generate ReDoc version
    redoc_path = os.path.join(docs_dir, "redoc.html")
    with open(redoc_path, "w") as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Interviewer Agent API Documentation (ReDoc)</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0;">
    <redoc spec-url="./openapi.json"></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
</body>
</html>
        """)
    
    print(f"API documentation generated in {docs_dir}")
    return docs_dir


if __name__ == "__main__":
    # Example usage (only runs when script is executed directly)
    import uvicorn
    import sys
    
    # Add the parent directory to the path to import the app
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    
    # Import the FastAPI app
    from main import app
    
    # Generate documentation
    docs_dir = generate_static_docs(app, "../docs/api")
    
    print(f"Documentation generated in {docs_dir}")
    print("You can view the documentation by opening the following files in a browser:")
    print(f"- Swagger UI: {os.path.join(docs_dir, 'index.html')}")
    print(f"- ReDoc: {os.path.join(docs_dir, 'redoc.html')}") 