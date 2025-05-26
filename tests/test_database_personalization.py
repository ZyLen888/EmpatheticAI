#!/usr/bin/env python3

"""
Test script to validate actual database storage and retrieval for personalization
Tests that data is properly saved and retrieved for cross-user personalization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cbt_database import init_cbt_db, get_or_create_user, Situation, AutomaticThought, Emotion, Behavior, BackgroundInfo
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager
from sqlalchemy import func

def test_database_storage_and_retrieval():
    """Test that data is actually stored and retrieved from database"""
    print("🔄 Testing Database Storage and Retrieval for Personalization")
    print("="*70)
    
    # Initialize fresh database
    session = init_cbt_db()
    
    # === PART 1: CREATE USER 1 AND STORE DATA ===
    print("\n📝 PART 1: Creating User 1 and storing CBT data...")
    user1 = get_or_create_user(session, "test_user_1")
    cbt_memory1 = CBTMemoryManager(session, user1)
    conversation_manager1 = ConversationManager(cbt_memory1)
    
    print(f"✅ User 1 created with ID: {user1.id}")
    
    # Simulate User 1 going through conversation phases
    user1_responses = [
        "I have anxiety about work presentations",
        "I was presenting to my team and felt nervous",
        "I thought everyone would judge me",
        "I felt anxious and my heart was racing",
        "I avoided eye contact and spoke quietly"
    ]
    
    phases = ['introduction', 'situation_1', 'thoughts_1', 'emotions_1', 'behavior_1']
    
    for i, (response, phase) in enumerate(zip(user1_responses, phases)):
        conversation_manager1.current_phase_index = i
        print(f"   Saving: {phase} -> '{response}'")
        conversation_manager1.save_response_data(response)
    
    # === PART 2: VERIFY USER 1 DATA IS STORED ===
    print(f"\n🔍 PART 2: Verifying User 1 data is stored in database...")
    
    # Check situations
    situations = session.query(Situation).filter_by(user_id=user1.id).all()
    print(f"✅ Situations stored: {len(situations)}")
    for sit in situations:
        print(f"   - {sit.description}")
    
    # Check thoughts
    thoughts = session.query(AutomaticThought).filter_by(user_id=user1.id).all()
    print(f"✅ Thoughts stored: {len(thoughts)}")
    for thought in thoughts:
        print(f"   - {thought.thought}")
    
    # Check emotions  
    emotions = session.query(Emotion).filter_by(user_id=user1.id).all()
    print(f"✅ Emotions stored: {len(emotions)}")
    for emotion in emotions:
        print(f"   - {emotion.emotion}")
    
    # Check behaviors
    behaviors = session.query(Behavior).filter_by(user_id=user1.id).all()
    print(f"✅ Behaviors stored: {len(behaviors)}")
    for behavior in behaviors:
        print(f"   - {behavior.action}")
        
    # === PART 3: CREATE USER 2 AND TEST RETRIEVAL ===
    print(f"\n👥 PART 3: Creating User 2 and testing cross-user retrieval...")
    user2 = get_or_create_user(session, "test_user_2")
    cbt_memory2 = CBTMemoryManager(session, user2)
    conversation_manager2 = ConversationManager(cbt_memory2)
    
    print(f"✅ User 2 created with ID: {user2.id}")
    print(f"🔍 User 2 should retrieve data from User {user2.id - 1} and User {user2.id}")
    
    # === PART 4: TEST PERSONALIZATION RETRIEVAL ===
    print(f"\n🏷️ PART 4: Testing personalized question generation...")
    
    # Test situation_2 phase (should reference User 1's situation)
    conversation_manager2.current_phase_index = conversation_manager2.phases.index('situation_2')
    
    # First, add one situation for User 2
    conversation_manager2.save_response_data("I get stressed about my exams")
    print("✅ Added User 2's first situation")
    
    # Now test personalized question for situation_2
    personalized_q = conversation_manager2.get_contextual_starter()
    non_personalized_q = conversation_manager2.get_contextual_starter_without_personalization()
    
    print(f"\n📊 QUESTION COMPARISON:")
    print(f"🔘 Without personalization: {non_personalized_q}")
    print(f"🏷️ With personalization: {personalized_q}")
    
    # === PART 5: VERIFY CROSS-USER DATA RETRIEVAL ===
    print(f"\n🔍 PART 5: Verifying cross-user data retrieval...")
    
    # Manual verification of what the personalization method retrieves
    current_user_id = user2.id
    previous_user_id = current_user_id - 1
    user_ids_to_query = [current_user_id, previous_user_id]
    
    print(f"Querying data for users: {user_ids_to_query}")
    
    # Test actual database queries
    retrieved_situations = session.query(Situation)\
        .filter(Situation.user_id.in_(user_ids_to_query))\
        .order_by(Situation.timestamp.desc())\
        .all()
    
    retrieved_thoughts = session.query(AutomaticThought)\
        .filter(AutomaticThought.user_id.in_(user_ids_to_query))\
        .order_by(AutomaticThought.timestamp.desc())\
        .all()
    
    retrieved_emotions = session.query(Emotion)\
        .filter(Emotion.user_id.in_(user_ids_to_query))\
        .order_by(Emotion.timestamp.desc())\
        .all()
    
    retrieved_behaviors = session.query(Behavior)\
        .filter(Behavior.user_id.in_(user_ids_to_query))\
        .order_by(Behavior.timestamp.desc())\
        .all()
    
    print(f"✅ Retrieved {len(retrieved_situations)} situations from both users")
    for sit in retrieved_situations:
        print(f"   - User {sit.user_id}: {sit.description}")
        
    print(f"✅ Retrieved {len(retrieved_thoughts)} thoughts from both users")
    for thought in retrieved_thoughts:
        print(f"   - User {thought.user_id}: {thought.thought}")
        
    print(f"✅ Retrieved {len(retrieved_emotions)} emotions from both users")
    for emotion in retrieved_emotions:
        print(f"   - User {emotion.user_id}: {emotion.emotion}")
        
    print(f"✅ Retrieved {len(retrieved_behaviors)} behaviors from both users")
    for behavior in retrieved_behaviors:
        print(f"   - User {behavior.user_id}: {behavior.action}")
    
    # === PART 6: VALIDATE PERSONALIZATION ACTUALLY USES DATABASE DATA ===
    print(f"\n✅ PART 6: Validating personalization contains database data...")
    
    # Check if personalized question contains data from User 1
    user1_situation = "I was presenting to my team and felt nervous"
    user1_in_personalized = user1_situation[:30] in personalized_q
    user1_in_nonpersonalized = user1_situation[:30] in non_personalized_q
    
    print(f"🔍 User 1's situation in personalized question: {user1_in_personalized}")
    print(f"🔍 User 1's situation in non-personalized question: {user1_in_nonpersonalized}")
    
    if user1_in_personalized and not user1_in_nonpersonalized:
        print("✅ SUCCESS: Personalization is working correctly!")
    elif not user1_in_personalized:
        print("❌ FAILURE: Personalized question doesn't contain User 1's data")
    elif user1_in_nonpersonalized:
        print("❌ FAILURE: Non-personalized question contains User 1's data (should not)")
    
    # === PART 7: TEST FULL CONVERSATION FLOW ===
    print(f"\n🔄 PART 7: Testing full conversation with database persistence...")
    
    user2_responses = [
        "I get overwhelmed with schoolwork",
        "I was studying for finals and panicked", 
        "I thought I would fail everything",
        "I felt overwhelmed and nauseous",
        "I stopped studying and watched TV instead"
    ]
    
    print("Running User 2 through conversation phases...")
    conversation_manager2.current_phase_index = 0  # Reset to beginning
    
    for i, response in enumerate(user2_responses):
        current_phase = conversation_manager2.get_current_phase()
        print(f"\n📝 Phase {current_phase}: User says '{response}'")
        
        # Save response
        conversation_manager2.save_response_data(response)
        
        # Advance phase
        conversation_manager2.advance_phase()
        
        # Get next question (if not complete)
        if conversation_manager2.get_current_phase() != 'complete':
            next_question = conversation_manager2.get_contextual_starter()
            print(f"🤖 AI asks: {next_question[:100]}...")
    
    # Final verification
    print(f"\n📊 FINAL DATABASE STATE:")
    total_situations = session.query(Situation).count()
    total_thoughts = session.query(AutomaticThought).count() 
    total_emotions = session.query(Emotion).count()
    total_behaviors = session.query(Behavior).count()
    
    print(f"Total situations in database: {total_situations}")
    print(f"Total thoughts in database: {total_thoughts}")
    print(f"Total emotions in database: {total_emotions}")
    print(f"Total behaviors in database: {total_behaviors}")
    
    session.close()
    print(f"\n🎉 Database storage and retrieval test complete!")

if __name__ == "__main__":
    test_database_storage_and_retrieval() 