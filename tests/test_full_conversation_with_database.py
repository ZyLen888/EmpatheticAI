#!/usr/bin/env python3

"""
Test script to simulate the exact conversation with both personalization approaches
Shows real differences in AI questions with full database storage and retrieval
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cbt_database import init_cbt_db, get_or_create_user
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager
import ollama

def simulate_full_conversation(personalization_type, user_responses):
    """Simulate full conversation with given personalization type"""
    print(f"\n{'='*80}")
    print(f"🧠 SIMULATING: {personalization_type.upper()}")
    print(f"{'='*80}")
    
    # Initialize components
    session = init_cbt_db()
    
    # Always create User 1 first with background data (for consistent IDs)
    user1 = get_or_create_user(session, "background_user_1")
    cbt_memory1 = CBTMemoryManager(session, user1)
    
    # Add background data for User 1 for personalization
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
    
    # Create main conversation user
    if personalization_type == "with_personalization":
        user2 = get_or_create_user(session, "conversation_user_personalized")
        print(f"👤 User ID: {user2.id} (will reference User {user1.id} data in personalized questions)")
    else:
        user2 = get_or_create_user(session, "conversation_user_nonpersonalized") 
        print(f"👤 User ID: {user2.id} (pure CBT questions without personalization)")
    
    cbt_memory = CBTMemoryManager(session, user2)
    conversation_manager = ConversationManager(cbt_memory)
    
    # Start conversation
    intro_base = "Hi! I'm here to support you today through a structured conversation that will help us understand your thinking patterns. What's been on your mind lately?"
    starter = conversation_manager._rephrase_question_with_ai(intro_base, 'introduction')
    
    print(f"\n🤖 AI > {starter}")
    
    ai_questions = [starter]  # Store all AI questions for comparison
    
    # Process each user response
    for i, user_input in enumerate(user_responses):
        print(f"\n👤 You > {user_input}")
        
        # Save user response
        conversation_manager.save_response_data(user_input)
        
        # Advance phase
        conversation_manager.advance_phase()
        
        # Get current phase
        phase = conversation_manager.get_current_phase()
        
        if phase == 'complete':
            break
        
        # Get next question based on personalization type
        if personalization_type == "with_personalization":
            next_question = conversation_manager.get_contextual_starter()
        else:
            next_question = conversation_manager.get_contextual_starter_without_personalization()
        
        if next_question:
            ai_questions.append(next_question)
            print(f"\n🤖 AI > {next_question}")
        else:
            break
    
    # Generate CBT formulation
    print(f"\n📋 Generating CBT Formulation...")
    formulation = generate_cbt_formulation(conversation_manager)
    print(f"\n📊 CBT FORMULATION:")
    print(formulation)
    
    session.close()
    return ai_questions, formulation

def generate_cbt_formulation(conversation_manager):
    """Generate CBT formulation using the conversation manager's system"""
    # Use the existing system prompt formatting
    system_prompt = conversation_manager.format_system_prompt("")
    
    # Get all stored data for formulation
    session = conversation_manager.memory.session
    user_id = conversation_manager.memory.user.id
    
    from utils.cbt_database import Situation, AutomaticThought, Emotion, Behavior, BackgroundInfo
    
    situations = session.query(Situation).filter_by(user_id=user_id).all()
    thoughts = session.query(AutomaticThought).filter_by(user_id=user_id).all()
    emotions = session.query(Emotion).filter_by(user_id=user_id).all()
    behaviors = session.query(Behavior).filter_by(user_id=user_id).all()
    background = session.query(BackgroundInfo).filter_by(user_id=user_id).first()
    
    # Create comprehensive context for formulation
    formulation_context = f"""
Based on our structured CBT assessment, here is the collected information:

PRESENTING CONCERN:
{background.chief_complaint if background and background.chief_complaint else "Binge eating behavior"}

SITUATIONS EXPLORED:
"""
    
    for i, situation in enumerate(situations, 1):
        formulation_context += f"{i}. {situation.description}\n"
    
    formulation_context += "\nAUTOMATIC THOUGHTS:\n"
    for i, thought in enumerate(thoughts, 1):
        formulation_context += f"{i}. {thought.thought}\n"
    
    formulation_context += "\nEMOTIONAL & PHYSICAL RESPONSES:\n"
    for i, emotion in enumerate(emotions, 1):
        formulation_context += f"{i}. {emotion.emotion}\n"
    
    formulation_context += "\nBEHAVIORAL RESPONSES:\n"
    for i, behavior in enumerate(behaviors, 1):
        formulation_context += f"{i}. {behavior.action}\n"
    
    if background and background.stress_response_patterns:
        formulation_context += f"\nIDENTIFIED PATTERNS:\n{background.stress_response_patterns}\n"
    
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formulation_context}
            ]
        )
        
        formulation = response['message']['content'].strip()
        
        # Save the formulation
        conversation_manager.save_cbt_beliefs(formulation)
        
        return formulation
        
    except Exception as e:
        print(f"Formulation generation failed: {e}")
        return "CBT formulation could not be generated at this time."

def compare_conversations():
    """Run both conversation types and compare the differences"""
    print("🔄 FULL CONVERSATION SIMULATION WITH DATABASE OPERATIONS")
    print("📝 Using exact user responses from your conversation")
    
    # Exact user responses from the conversation
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
    
    # Run without personalization first
    print("\n" + "🔘" * 35 + " WITHOUT PERSONALIZATION " + "🔘" * 35)
    ai_questions_without, formulation_without = simulate_full_conversation("without_personalization", user_responses)
    
    # Run with personalization
    print("\n" + "🏷️" * 35 + " WITH PERSONALIZATION " + "🏷️" * 35)
    ai_questions_with, formulation_with = simulate_full_conversation("with_personalization", user_responses)
    
    # Compare AI questions side by side
    print(f"\n{'='*100}")
    print("📊 AI QUESTIONS COMPARISON")
    print(f"{'='*100}")
    
    max_questions = max(len(ai_questions_without), len(ai_questions_with))
    
    for i in range(max_questions):
        print(f"\n🔹 QUESTION {i+1}:")
        print("-" * 80)
        
        if i < len(ai_questions_without):
            print(f"🔘 WITHOUT: {ai_questions_without[i]}")
        else:
            print(f"🔘 WITHOUT: [No more questions]")
        
        print()
        
        if i < len(ai_questions_with):
            print(f"🏷️ WITH: {ai_questions_with[i]}")
        else:
            print(f"🏷️ WITH: [No more questions]")
        
        # Highlight differences
        if i < len(ai_questions_without) and i < len(ai_questions_with):
            if ai_questions_without[i] != ai_questions_with[i]:
                print(f"💡 DIFFERENCE DETECTED: Personalized version differs from base")
            else:
                print(f"⚪ SAME: Both questions are identical")
    
    print(f"\n{'='*100}")
    print("📋 CBT FORMULATION COMPARISON")
    print(f"{'='*100}")
    
    print(f"\n🔘 FORMULATION WITHOUT PERSONALIZATION:")
    print("-" * 50)
    print(formulation_without)
    
    print(f"\n🏷️ FORMULATION WITH PERSONALIZATION:")
    print("-" * 50)
    print(formulation_with)
    
    print(f"\n{'='*100}")
    print("🎯 SUMMARY")
    print(f"{'='*100}")
    print(f"✅ Completed full conversation simulation with {len(user_responses)} user responses")
    print(f"✅ Generated {len(ai_questions_without)} AI questions without personalization")
    print(f"✅ Generated {len(ai_questions_with)} AI questions with personalization")
    print(f"✅ Database storage and retrieval operations completed")
    print(f"✅ CBT formulations generated for both approaches")
    
    # Count actual differences
    differences = 0
    for i in range(min(len(ai_questions_without), len(ai_questions_with))):
        if ai_questions_without[i] != ai_questions_with[i]:
            differences += 1
    
    print(f"📊 {differences} out of {min(len(ai_questions_without), len(ai_questions_with))} questions showed personalization differences")

if __name__ == "__main__":
    compare_conversations() 