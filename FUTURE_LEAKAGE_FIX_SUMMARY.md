# Coach Agent Future Leakage Fix - Implementation Summary

## Problem Identified

### **Issue: Future Leakage in Coach Agent Prompting Logic**

The coach agent was receiving **future content** that the user hasn't seen yet, making the coaching feel unrealistic and delayed.

**Problematic Flow:**

1. User answers Question A
2. Interviewer generates Question B + justification (assessment of Answer A)
3. Coach evaluates Answer A but receives **full conversation history including Question B**
4. Coach feedback includes context about future questions user hasn't seen

**Impact:**

- ❌ Coach knows about future questions when providing feedback
- ❌ Feedback feels delayed or references future context
- ❌ Breaks simulation of real-time coaching companion
- ❌ Unrealistic coaching experience

## Solution Implemented

### **Core Fix: Filtered Conversation History**

**New Flow:**

1. User answers Question A
2. Interviewer generates Question B + justification
3. Coach evaluates Answer A with **filtered history** that:
   - ✅ **Includes:** Previous conversation up to Answer A
   - ✅ **Includes:** Interviewer's justification (assessment reasoning)
   - ❌ **Excludes:** Question B content (future question)

### **Technical Implementation**

#### **1. Modified `_get_coach_feedback()` in `orchestrator.py`**

```python
def _get_coach_feedback(self, coach_agent: AgenticCoachAgent, question: str, answer: str) -> str:
    """Get coaching feedback from the coach agent."""
    # Get justification from the latest interviewer metadata
    justification = None
    if self.conversation_history:
        latest_msg = self.conversation_history[-1]
        if latest_msg.get("agent") == "interviewer":
            justification = latest_msg.get("metadata", {}).get("justification")
  
    # Create filtered conversation history that excludes the latest interviewer response
    # to prevent future leakage (coach shouldn't see the next question)
    filtered_history = self._create_filtered_history_for_coach()
  
    # Log the filtering for debugging
    original_count = len(self.conversation_history)
    filtered_count = len(filtered_history)
    if original_count != filtered_count:
        self.logger.debug(f"Coach feedback: Filtered conversation history from {original_count} to {filtered_count} messages to prevent future leakage")
  
    return coach_agent.evaluate_answer(
        question=question,
        answer=answer,
        justification=justification,
        conversation_history=filtered_history  # ← Now uses filtered history
    )
```

#### **2. Added `_create_filtered_history_for_coach()` Method**

```python
def _create_filtered_history_for_coach(self) -> List[Dict[str, Any]]:
    """
    Create a filtered conversation history for coach feedback that excludes
    the latest interviewer response (next question) to prevent future leakage.
  
    Returns:
        Filtered conversation history up to the user's latest answer
    """
    if not self.conversation_history:
        return []
  
    # If the last message is from the interviewer (next question), exclude it
    # Coach should only see conversation up to the user's answer
    if (self.conversation_history and 
        self.conversation_history[-1].get("role") == "assistant" and
        self.conversation_history[-1].get("agent") == "interviewer"):
        # Return history excluding the last interviewer response (next question)
        return self.conversation_history[:-1]
    else:
        # Return full history if last message is not interviewer response
        return self.conversation_history
```

#### **3. Enhanced Coach Agent Prompting**

Updated `_build_evaluation_prompt()` in `agentic_coach.py`:

```python
**Important Context Notes:**
- The "Interviewer's Assessment" reflects how the interviewer evaluated this specific answer
- Focus ONLY on the current question-answer pair and previous context
- Do NOT anticipate or reference future questions or topics
- Provide coaching based solely on what has happened so far in the interview
```

### **Key Changes Made**

#### **Files Modified:**

1. **`backend/agents/orchestrator.py`**

   - Modified `_get_coach_feedback()` to use filtered history
   - Added `_create_filtered_history_for_coach()` method
   - Added debugging logs for filtering
2. **`backend/agents/agentic_coach.py`**

   - Enhanced `_build_evaluation_prompt()` with clear context instructions
   - Clarified that justification represents interviewer's assessment of current answer
   - Added explicit instructions to focus only on present context
3. **`test_future_leakage_fix.py`** (New)

   - Created test script to verify fix works correctly
   - Tests conversation flow and history filtering

### **What Coach Agent Now Receives**

#### **✅ Included in Coach Context:**

- Previous conversation history (up to current user answer)
- Current question that was asked
- User's answer to current question
- Interviewer's assessment/justification of the answer
- Resume and job description context

#### **❌ Excluded from Coach Context:**

- Next question content that user hasn't seen
- Future interviewer responses
- Any content that represents "future" state

### **Verification & Testing**

#### **Test Script Results:**

```bash
python test_future_leakage_fix.py
```

**Expected Output:**

- ✅ History filtering working (removes last interviewer message)
- ✅ Coach feedback focuses on present context
- ✅ No future indicators in coaching responses
- ✅ Original vs filtered history counts differ appropriately

#### **Debug Logging:**

```
Coach feedback: Filtered conversation history from 4 to 3 messages to prevent future leakage
```

## Impact & Benefits

### **✅ Fixed Issues:**

1. **No Future Leakage:** Coach only sees past and present context
2. **Realistic Coaching:** Feedback based on what has actually happened
3. **Real-time Feel:** Coaching companion simulation works properly
4. **Proper Assessment Flow:** Coach gets interviewer's assessment but not future questions

### **✅ Preserved Functionality:**

1. **Justification Access:** Coach still receives interviewer's assessment reasoning
2. **Context Awareness:** Full previous conversation history available
3. **Final Summary:** End-of-interview summary still uses complete history
4. **Performance:** No impact on coaching feedback generation speed

### **✅ Enhanced Experience:**

1. **Present-focused Feedback:** Coach advice based on current performance
2. **Logical Flow:** Coaching follows natural interview progression
3. **Professional Simulation:** Feels like real interview coaching scenario

## Future Considerations

### **Potential Enhancements:**

1. **User Preference:** Option to include/exclude future context (advanced users)
2. **Analytics:** Track coaching effectiveness with/without future context
3. **Advanced Filtering:** More sophisticated context filtering based on user settings

### **Monitoring:**

1. **Debug Logs:** Monitor filtering frequency and effectiveness
2. **User Feedback:** Track if coaching feels more realistic
3. **Performance:** Ensure no degradation in coaching quality

---

## Summary

This fix ensures the coach agent operates with **proper temporal boundaries**, providing coaching feedback based only on what has actually occurred in the interview. The interviewer's assessment reasoning is preserved while preventing knowledge of future questions, creating a more realistic and effective coaching experience.

**Result:** ✅ Coach agent now provides **present-focused, realistic coaching feedback** without future leakage.
