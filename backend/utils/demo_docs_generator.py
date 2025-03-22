"""
Demo script to showcase API documentation generation.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import our demo API
from backend.utils.demo_api import app
from backend.utils.docs_generator import generate_static_docs

def main():
    """Generate API documentation for demo API."""
    try:
        # Create output directory
        output_dir = Path(__file__).parent / "demo_docs"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Generating API documentation in: {output_dir}")
        
        # Generate documentation
        docs_dir = generate_static_docs(app, str(output_dir))
        
        print(f"\nDocumentation successfully generated in: {docs_dir}")
        print("\nYou can view the documentation by opening these files in a browser:")
        print(f"- Swagger UI: {os.path.join(docs_dir, 'index.html')}")
        print(f"- ReDoc: {os.path.join(docs_dir, 'redoc.html')}")
        print("\nThis is how the docs_generator.py is used in the main application.")
        print("When the FastAPI application starts, it automatically generates")
        print("up-to-date API documentation based on your routes and models.")
    except Exception as e:
        print(f"Error generating documentation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 