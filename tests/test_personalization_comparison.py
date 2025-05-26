#!/usr/bin/env python3

"""
Test script to compare personalized vs non-personalized CBT questions
Simulates user study where User 2 can reference User 1's data for personalization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cbt_database import init_cbt_db, get_or_create_user
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager
import uuid

def test_personalization_comparison():
    print("🔄 Testing Cross-User Personalization for User Study\n")
    
    # Initialize components
    session = init_cbt_db()
    
    # Create User 1 and add their data
    print("📝 Creating User 1 and adding their data...")
    user1 = get_or_create_user(session, "user_1")
    cbt_memory1 = CBTMemoryManager(session, user1)
    
    # Add User 1's data
    situation1 = cbt_memory1.add_situation(
        "I was really stressed before my job interview last week", 
        context="Work anxiety",
        category="performance_anxiety"
    )
    
    situation2 = cbt_memory1.add_situation(
        "I had a panic attack during the presentation to my boss",
        context="Work performance", 
        category="social_anxiety"
    )
    
    # Add User 1's thoughts
    cbt_memory1.add_automatic_thought(
        "I'm going to mess this up and everyone will think I'm incompetent",
        situation=situation1
    )
    
    cbt_memory1.add_automatic_thought(
        "They can see I'm nervous and they're judging me",
        situation=situation2
    )
    
    # Add User 1's emotions
    cbt_memory1.add_emotion(
        "Intense anxiety, racing heart, sweaty palms",
        intensity="high",
        context="Physical symptoms",
        situation=situation1
    )
    
    cbt_memory1.add_emotion(
        "Panic, feeling overwhelmed, shortness of breath", 
        intensity="very_high",
        context="Panic response",
        situation=situation2
    )
    
    # Add User 1's behaviors
    cbt_memory1.add_behavior(
        "I avoided eye contact and spoke very quietly",
        behavior_type="avoidance",
        situation=situation1
    )
    
    cbt_memory1.add_behavior(
        "I excused myself and left the room early",
        behavior_type="escape",
        situation=situation2
    )
    
    print("✅ User 1 data added to database")
    print(f"   User 1 ID: {user1.id}")
    print()
    
    # Create User 2 (who will reference User 1's data in personalized version)
    print("📝 Creating User 2 (for personalized experience)...")
    user2 = get_or_create_user(session, "user_2") 
    cbt_memory2 = CBTMemoryManager(session, user2)
    conversation_manager2 = ConversationManager(cbt_memory2)
    
    print(f"✅ User 2 created")
    print(f"   User 2 ID: {user2.id}")
    print(f"   📊 Personalized questions will reference data from User {user2.id - 1} and User {user2.id}")
    print()
    
    # Test different phases with both approaches
    test_phases = [
        ('situation_2', 'Asking for second situation'),
        ('thoughts_2', 'Asking for thoughts in second situation'), 
        ('emotions_3', 'Asking for emotions in third situation'),
        ('behavior_3', 'Asking for behavior in third situation'),
        ('patterns_beliefs', 'Asking about patterns and beliefs')
    ]
    
    for phase, description in test_phases:
        print(f"🔸 {description}")
        print(f"   Phase: {phase}")
        
        # Set conversation manager to this phase
        conversation_manager2.current_phase_index = conversation_manager2.phases.index(phase)
        
        # Get personalized question (will reference User 1's data)
        personalized_q = conversation_manager2.get_contextual_starter()
        print(f"   🏷️  WITH personalization: {personalized_q}")
        
        # Get non-personalized question
        non_personalized_q = conversation_manager2.get_contextual_starter_without_personalization()
        print(f"   🔘 WITHOUT personalization: {non_personalized_q}")
        
        print()
        
    print("💡 In the personalized version, User 2 gets questions that reference")
    print("   situations, thoughts, emotions, and behaviors from User 1,")
    print("   creating a sense of continuity and memory across users.")

if __name__ == "__main__":
    test_personalization_comparison() 