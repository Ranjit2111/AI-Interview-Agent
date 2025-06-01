#!/usr/bin/env python3
"""
Live test script to verify agentic coach implementation.
Tests resource generation and validates the fixes implemented.
"""

import asyncio
import sys
import os
import logging

# Add backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.agents.agentic_coach import AgenticCoachAgent
from backend.services.llm_service import LLMService
from backend.services.search_service import SearchService
from backend.utils.event_bus import EventBus

def test_agentic_coach_resources():
    """Test the agentic coach to see if it generates multiple resources."""
    print("🧪 Testing Agentic Coach Resource Generation...")
    
    # Set up services
    llm_service = LLMService()
    search_service = SearchService()
    event_bus = EventBus()
    logger = logging.getLogger("test")
    
    # Create agentic coach
    coach = AgenticCoachAgent(
        llm_service=llm_service,
        search_service=search_service,
        event_bus=event_bus,
        logger=logger,
        resume_content="Software Engineer with 2 years experience in Python and web development",
        job_description="Senior Python Developer position requiring strong algorithmic skills"
    )
    
    # Simulate conversation history with weak algorithm knowledge
    conversation_history = [
        {
            "role": "assistant",
            "agent": "interviewer",
            "content": "Can you explain how you would implement a sorting algorithm?",
            "timestamp": "2024-01-01T10:00:00"
        },
        {
            "role": "user",
            "content": "Um, I think I would use bubble sort because it's simple to understand.",
            "timestamp": "2024-01-01T10:01:00"
        },
        {
            "role": "assistant",
            "agent": "interviewer",
            "content": "What's the time complexity of your sorting approach?",
            "timestamp": "2024-01-01T10:02:00"
        },
        {
            "role": "user",
            "content": "I'm not really sure about time complexity calculations.",
            "timestamp": "2024-01-01T10:03:00"
        },
        {
            "role": "assistant",
            "agent": "interviewer",
            "content": "Tell me about a challenging project you worked on.",
            "timestamp": "2024-01-01T10:04:00"
        },
        {
            "role": "user",
            "content": "I built a web application but I can't remember the specific technical details.",
            "timestamp": "2024-01-01T10:05:00"
        }
    ]
    
    print("\n📊 Generating final summary with resources...")
    
    # Generate final summary with resources
    result = coach.generate_final_summary_with_resources(conversation_history)
    
    print(f"\n✅ Final Summary Generated!")
    print(f"📝 Summary Keys: {list(result.keys())}")
    
    # Check resources
    resources = result.get("recommended_resources", [])
    print(f"\n🔍 Resources Analysis:")
    print(f"📚 Number of resources found: {len(resources)}")
    print(f"🎯 Target: 3-4 resources minimum")
    
    if len(resources) >= 3:
        print("✅ SUCCESS: Found 3+ resources as required!")
    else:
        print("❌ ISSUE: Found fewer than 3 resources")
    
    print(f"\n📋 Resource Details:")
    for i, resource in enumerate(resources, 1):
        print(f"\n{i}. {resource.get('title', 'No title')}")
        print(f"   📎 URL: {resource.get('url', 'No URL')}")
        print(f"   📄 Type: {resource.get('resource_type', 'No type')}")
        print(f"   📝 Description: {resource.get('description', 'No description')[:100]}...")
        
        # Check for placeholder URLs
        url = resource.get('url', '')
        if 'query=' in url or 'search_query=' in url:
            print(f"   ⚠️  WARNING: Looks like a placeholder search URL!")
        else:
            print(f"   ✅ URL looks like a real resource")
    
    print(f"\n🏁 Test Complete!")
    return result

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        result = test_agentic_coach_resources()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 