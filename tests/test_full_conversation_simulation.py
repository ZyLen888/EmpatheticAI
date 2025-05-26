#!/usr/bin/env python3

"""
Test script to simulate full conversation with and without personalization
Uses the exact user responses from the provided conversation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cbt_database import init_cbt_db, get_or_create_user
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager
import uuid

def simulate_conversation(personalization_type):
    """Simulate a full conversation with given personalization type"""
    print(f"\n{'='*60}")
    print(f"🧠 SIMULATING CONVERSATION: {personalization_type.upper()}")
    print(f"{'='*60}")
    
    # Initialize components
    session = init_cbt_db()
    
    # Always create User 1 first with background data (for consistent IDs)
    user1 = get_or_create_user(session, "background_user_1")
    cbt_memory1 = CBTMemoryManager(session, user1)
    
    # Add background data for User 1
    situation1 = cbt_memory1.add_situation(
        "I was anxious about my exam and started eating junk food",
        context="Academic stress",
        category="stress_eating"
    )
    cbt_memory1.add_automatic_thought(
        "I can't handle this pressure, food makes me feel better",
        situation=situation1
    )
    cbt_memory1.add_emotion(
        "Anxious and seeking comfort",
        intensity="medium",
        situation=situation1
    )
    cbt_memory1.add_behavior(
        "Ate a whole bag of chips while studying",
        behavior_type="stress_eating",
        situation=situation1
    )
    
    # Create User 2 (who will be the main conversation participant)
    if personalization_type == "with_personalization":
        user2 = get_or_create_user(session, "test_user_personalized")
        print(f"👤 User 1 (ID: {user1.id}) - background data")
        print(f"👤 User 2 (ID: {user2.id}) - will reference User 1 data in personalized questions")
        cbt_memory = CBTMemoryManager(session, user2)
    else:
        user2 = get_or_create_user(session, "test_user_nonpersonalized") 
        print(f"👤 User 2 (ID: {user2.id}) - pure CBT questions without personalization")
        cbt_memory = CBTMemoryManager(session, user2)
    
    conversation_manager = ConversationManager(cbt_memory)
    
    # User responses from the provided conversation
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
    
    # Start conversation
    intro_base = "Hi! I'm here to support you today through a structured conversation that will help us understand your thinking patterns. What's been on your mind lately?"
    starter = conversation_manager._rephrase_question_with_ai(intro_base, 'introduction')
    print(f"\nAI > {starter}")
    
    # Process each user response
    for i, user_input in enumerate(user_responses):
        print(f"\nYou > {user_input}")
        
        # Save user response
        conversation_manager.save_response_data(user_input)
        
        # Advance phase
        conversation_manager.advance_phase()
        
        # Get current phase
        phase = conversation_manager.get_current_phase()
        
        if phase == 'complete':
            print("\n🎯 CBT Assessment Complete!")
            break
        
        # Get next question based on personalization type
        if personalization_type == "with_personalization":
            next_question = conversation_manager.get_contextual_starter()
        else:
            next_question = conversation_manager.get_contextual_starter_without_personalization()
        
        if next_question:
            # Add debug info for personalization differences
            if personalization_type == "with_personalization":
                # Show if this question includes personalization
                base_question = conversation_manager.base_questions.get(phase, "")
                if base_question and base_question != next_question:
                    print(f"\n🔍 DEBUG: Personalized question detected!")
                    print(f"    Base: {base_question[:100]}...")
                    print(f"    Personalized: {next_question[:100]}...")
            
            print(f"\nAI > {next_question}")
        else:
            print("\n🎯 Assessment complete!")
            break
    
    return conversation_manager

def test_conversation_comparison():
    """Run the same conversation with both personalization types"""
    print("🔄 Testing Full Conversation: With vs Without Personalization")
    print("📝 Using exact user responses from provided conversation")
    
    # Test without personalization first
    print("\n" + "🔘" * 30 + " WITHOUT PERSONALIZATION " + "🔘" * 30)
    without_personalization = simulate_conversation("without_personalization")
    
    # Test with personalization
    print("\n" + "🏷️" * 30 + " WITH PERSONALIZATION " + "🏷️" * 30)
    with_personalization = simulate_conversation("with_personalization")
    
    print(f"\n{'='*80}")
    print("📊 COMPARISON SUMMARY")
    print(f"{'='*80}")
    print("🔘 WITHOUT personalization: Uses pure CBT questions")
    print("🏷️ WITH personalization: References previous situations, thoughts, emotions, and behaviors")
    print("\n💡 Key Difference: Personalized version creates continuity by referencing")
    print("   what was shared earlier, making the AI seem more attentive and empathetic.")

if __name__ == "__main__":
    test_conversation_comparison() 