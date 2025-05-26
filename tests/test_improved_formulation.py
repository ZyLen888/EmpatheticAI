#!/usr/bin/env python3

"""
Test script to verify the improved CBT formulation system
Tests that the AI uses actual database data instead of generic templates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cbt_database import init_cbt_db, get_or_create_user
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager

def test_improved_formulation():
    """Test the improved CBT formulation with actual conversation data"""
    print("🔄 Testing Improved CBT Formulation System")
    print("="*60)
    
    # Initialize components
    session = init_cbt_db()
    user = get_or_create_user(session, "formulation_test_user")
    cbt_memory = CBTMemoryManager(session, user)
    conversation_manager = ConversationManager(cbt_memory)
    
    print(f"✅ Created user with ID: {user.id}")
    
    # Simulate the exact conversation data from the user's session
    user_responses = [
        "I have been thinking about my binge eating behaviour",
        "I was really stressed about my university assignment, I couldn't get anything done, so I was just frantically eating",
        "I was thinking that I just need some food to feel more comfortable",
        "I felt I was overwhelmed and can't do shit",
        "I didn't end up doing anything to be honest",
        "I also binge ate when I had fight with my parents",
        "I felt they just accused me wrongly and never apologize, which I am angry about",
        "I was very tensed and also my stomach was upset",
        "I just continued eating and drinking more sugary stuff",
        "I sometimes fast and starve myself after I eat too much",
        "I felt I needed to repent",
        "I felt sad and vulnerable",
        "I just didn't",
        "I think I usually just avoid stuff when my pressure hits maximum"
    ]
    
    phases = ['introduction', 'situation_1', 'thoughts_1', 'emotions_1', 'behavior_1',
              'situation_2', 'thoughts_2', 'emotions_2', 'behavior_2',
              'situation_3', 'thoughts_3', 'emotions_3', 'behavior_3', 'patterns_beliefs']
    
    print(f"\n📝 PART 1: Storing conversation data...")
    
    # Process each response and store data
    for i, (response, phase) in enumerate(zip(user_responses, phases)):
        conversation_manager.current_phase_index = i
        print(f"   Phase {phase}: '{response[:50]}...'")
        conversation_manager.save_response_data(response)
    
    print(f"\n🧠 PART 2: Testing improved formulation generation...")
    
    # Generate formulation with improved method
    print("Generating improved CBT formulation...")
    improved_formulation = conversation_manager.generate_improved_cbt_formulation()
    
    print(f"\n📊 IMPROVED FORMULATION RESULT:")
    print("="*60)
    print(improved_formulation)
    print("="*60)
    
    # Analyze the formulation for accuracy
    print(f"\n🔍 ACCURACY ANALYSIS:")
    
    formulation_lower = improved_formulation.lower()
    
    # Check for key topics that should be present
    accuracy_checks = {
        "Mentions binge eating": any(word in formulation_lower for word in ['binge', 'eating']),
        "Mentions university/assignment": any(word in formulation_lower for word in ['university', 'assignment', 'academic']),
        "Mentions parents/family": any(word in formulation_lower for word in ['parent', 'family']),
        "Mentions overwhelmed feelings": any(word in formulation_lower for word in ['overwhelm', 'overwhelmed']),
        "Mentions fasting/restriction": any(word in formulation_lower for word in ['fast', 'starve', 'restrict']),
        "Mentions comfort seeking": any(word in formulation_lower for word in ['comfort', 'comforting']),
        "Mentions avoidance": any(word in formulation_lower for word in ['avoid', 'avoidance']),
        "Mentions repent/guilt": any(word in formulation_lower for word in ['repent', 'guilt', 'shame'])
    }
    
    # Check for inappropriate content that shouldn't be there
    inappropriate_checks = {
        "Passive-aggressive behavior": any(word in formulation_lower for word in ['passive-aggressive', 'passive aggressive']),
        "Assertiveness issues": any(word in formulation_lower for word in ['assertiveness', 'assertive']),
        "Saying no to others": any(phrase in formulation_lower for phrase in ['saying no', 'say no', 'difficulty saying']),
        "Boundary setting": any(word in formulation_lower for word in ['boundary', 'boundaries'])
    }
    
    print("\n✅ SHOULD BE PRESENT:")
    for check, result in accuracy_checks.items():
        status = "✅ FOUND" if result else "❌ MISSING"
        print(f"   {check}: {status}")
    
    print("\n❌ SHOULD NOT BE PRESENT:")
    for check, result in inappropriate_checks.items():
        status = "❌ INCORRECTLY FOUND" if result else "✅ CORRECTLY ABSENT"
        print(f"   {check}: {status}")
    
    # Calculate accuracy score
    correct_present = sum(accuracy_checks.values())
    correct_absent = sum(not result for result in inappropriate_checks.values())
    total_checks = len(accuracy_checks) + len(inappropriate_checks)
    accuracy_score = (correct_present + correct_absent) / total_checks * 100
    
    print(f"\n🎯 OVERALL ACCURACY SCORE: {accuracy_score:.1f}%")
    
    if accuracy_score >= 90:
        print("🎉 EXCELLENT: Formulation is highly accurate!")
    elif accuracy_score >= 75:
        print("👍 GOOD: Formulation is mostly accurate with minor issues")
    elif accuracy_score >= 50:
        print("⚠️ FAIR: Formulation has accuracy issues that need attention")
    else:
        print("❌ POOR: Formulation is inaccurate and needs significant improvement")
    
    session.close()
    
    return improved_formulation, accuracy_score

if __name__ == "__main__":
    formulation, score = test_improved_formulation()
    print(f"\nTest completed with accuracy score: {score:.1f}%") 