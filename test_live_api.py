#!/usr/bin/env python3
"""
Test the live API to see if the agentic coach fixes are working
"""

import asyncio
import httpx
import json

async def test_live_agentic_coach():
    """Test the live API with a fresh interview session."""
    print("🧪 Testing Live Agentic Coach API...")
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. Start a new interview session
        print("\n📋 1. Starting new interview session...")
        start_response = await client.post(f"{base_url}/api/interview/start", json={
            "job_role": "Software Engineer",
            "job_description": "Looking for a developer with strong algorithmic skills and system design knowledge",
            "resume_content": "Software Engineer with 2 years experience in Python. Have built web applications but need to improve algorithmic thinking.",
            "style": "technical",
            "difficulty": "intermediate",
            "target_question_count": 3,
            "company_name": "Test Company"
        })
        
        if start_response.status_code != 200:
            print(f"❌ Failed to start interview: {start_response.text}")
            return
        
        session_data = start_response.json()
        print(f"✅ Interview started successfully")
        
        # 2. Simulate a weak interview performance
        print("\n💬 2. Simulating interview responses...")
        
        responses = [
            "Um, I think I would use bubble sort because it's simple?",
            "I'm not really sure about time complexity calculations.",
            "I can't remember the specific technical details of my projects."
        ]
        
        for i, response in enumerate(responses, 1):
            print(f"   Response {i}: {response[:50]}...")
            
            message_response = await client.post(
                f"{base_url}/api/interview/message",
                json={"message": response}
            )
            
            if message_response.status_code != 200:
                print(f"❌ Failed to send message {i}: {message_response.text}")
                continue
            
            # Small delay between responses
            await asyncio.sleep(0.5)
        
        # 3. End the interview and get coaching summary
        print("\n🏁 3. Ending interview and generating coaching summary...")
        
        end_response = await client.post(f"{base_url}/api/interview/end")
        
        if end_response.status_code != 200:
            print(f"❌ Failed to end interview: {end_response.text}")
            return
        
        results = end_response.json()
        
        # 4. Analyze the coaching summary
        print("\n📊 4. Analyzing coaching summary...")
        
        coaching_summary = results.get("coaching_summary", {})
        recommended_resources = coaching_summary.get("recommended_resources", [])
        
        print(f"\n🔍 Results Analysis:")
        print(f"📚 Number of resources found: {len(recommended_resources)}")
        print(f"🎯 Target: 3-4 resources minimum")
        
        if len(recommended_resources) >= 3:
            print("✅ SUCCESS: Found 3+ resources as required!")
        else:
            print("❌ ISSUE: Found fewer than 3 resources")
        
        print(f"\n📋 Resource Details:")
        for i, resource in enumerate(recommended_resources, 1):
            print(f"\n{i}. {resource.get('title', 'No title')}")
            print(f"   📎 URL: {resource.get('url', 'No URL')}")
            print(f"   📄 Type: {resource.get('resource_type', 'No type')}")
            print(f"   📝 Description: {resource.get('description', 'No description')[:100]}...")
            
            # Check for placeholder URLs
            url = resource.get('url', '')
            if 'query=' in url or 'search_query=' in url or 'example.com' in url:
                print(f"   ⚠️  WARNING: Looks like a placeholder URL!")
            else:
                print(f"   ✅ URL looks like a real resource")
        
        # 5. Check feedback generation speed
        per_turn_feedback = results.get("per_turn_feedback", [])
        print(f"\n⚡ Per-turn feedback:")
        print(f"📝 Number of feedback entries: {len(per_turn_feedback)}")
        
        if len(per_turn_feedback) > 0:
            print("✅ Per-turn feedback generated successfully")
        else:
            print("❌ No per-turn feedback found")
        
        print(f"\n🏁 Live API Test Complete!")
        return results

if __name__ == "__main__":
    try:
        results = asyncio.run(test_live_agentic_coach())
    except Exception as e:
        print(f"❌ Live API test failed: {e}")
        import traceback
        traceback.print_exc() 