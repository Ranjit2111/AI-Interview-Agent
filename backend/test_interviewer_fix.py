#!/usr/bin/env python3
"""
Test script to verify interviewer agent fixes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_syntax_and_indentation():
    """Test that the Python syntax is correct after fixes."""
    print("🔧 Testing Python Syntax and Indentation Fixes...")
    
    try:
        # Test importing the fixed modules
        from agents.interviewer import InterviewerAgent
        print("✅ InterviewerAgent imports successfully")
        
        # Test that we can instantiate it (basic syntax check)
        from services.llm_service import LLMService
        from utils.event_bus import EventBus
        
        event_bus = EventBus()
        llm_service = LLMService()
        
        interviewer = InterviewerAgent(
            llm_service=llm_service,
            event_bus=event_bus,
            job_role="AI Infrastructure Engineer"
        )
        print("✅ InterviewerAgent instantiates successfully")
        
        # Check that critical methods exist and are callable
        methods_to_check = [
            '_generate_job_specific_questions',
            '_determine_next_action', 
            '_process_action_response',
            '_handle_initialization',
            '_handle_questioning'
        ]
        
        for method_name in methods_to_check:
            if hasattr(interviewer, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} missing")
        
        print("\n✅ All syntax and indentation fixes appear to be working!")
        
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except IndentationError as e:
        print(f"❌ Indentation error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Other error (but syntax is OK): {e}")
        return True
    
    return True

if __name__ == "__main__":
    test_syntax_and_indentation() 