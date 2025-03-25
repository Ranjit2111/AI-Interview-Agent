#!/bin/bash

echo "Running AI Interviewer Agent dependency fixer..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH."
    echo "Please install Python 3.8 or higher and try again."
    echo ""
    exit 1
fi

# Make the Python script executable
chmod +x fix_dependencies.py

# Run the dependency fixer script
python3 ./fix_dependencies.py

echo ""
if [ $? -ne 0 ]; then
    echo "There was an error running the script."
    echo "Please check the output above for more details."
else
    echo "Dependencies fixed successfully!"
fi

# Wait for user to read the message
read -p "Press Enter to continue..." 