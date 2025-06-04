#!/usr/bin/env python3

"""
Simple test to verify the template fix is working.
Tests that the template can be parsed without the malformed Python expression.
"""

def test_template_parsing():
    """Test that the template variables are correctly formatted."""
    
    # Read the template file
    with open('agents/templates/interviewer_templates.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that the malformed line was fixed
    if '{"Time-based" if use_time_based else "Question-based"}' in content:
        print("❌ FAILED: Malformed template still present")
        return False
    
    # Check that the correct template variable is present
    if '- Interview Type: {interview_type}' in content:
        print("✅ SUCCESS: Template syntax fixed correctly")
        return True
    else:
        print("❌ FAILED: Correct template variable not found")
        return False

def test_build_action_inputs_method():
    """Test that the _build_action_inputs method has interview_type logic."""
    
    # Read the interviewer.py file
    with open('agents/interviewer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that interview_type is being set in both branches
    time_based_check = '"interview_type": "Time-based"' in content
    question_based_check = '"interview_type": "Question-based"' in content
    
    if time_based_check and question_based_check:
        print("✅ SUCCESS: interview_type computation added to both branches")
        return True
    else:
        print(f"❌ FAILED: interview_type missing - time_based: {time_based_check}, question_based: {question_based_check}")
        return False

if __name__ == "__main__":
    print("Testing template fix...")
    
    template_ok = test_template_parsing()
    method_ok = test_build_action_inputs_method()
    
    if template_ok and method_ok:
        print("\n🎉 ALL TESTS PASSED: Template fix is complete!")
        print("The interviewer agent should now work without LLM chain errors.")
    else:
        print("\n❌ TESTS FAILED: Template fix incomplete")
    
    print("\nNext: Test TTS timing fix by running the application and checking visual effects timing.") 