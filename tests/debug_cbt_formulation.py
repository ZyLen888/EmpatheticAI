#!/usr/bin/env python3

"""
Debug script to investigate why CBT formulation is inaccurate
Check what data is being stored, retrieved, and sent to AI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cbt_database import init_cbt_db, get_or_create_user, Situation, AutomaticThought, Emotion, Behavior, BackgroundInfo
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager
import ollama

def debug_data_storage_and_formulation():
    """Debug the entire data flow from storage to formulation"""
    print("🔍 DEBUG: CBT Formulation Data Flow")
    print("="*60)
    
    # Initialize components
    session = init_cbt_db()
    user = get_or_create_user(session, "debug_user")
    cbt_memory = CBTMemoryManager(session, user)
    conversation_manager = ConversationManager(cbt_memory)
    
    print(f"✅ Created user with ID: {user.id}")
    
    # Simulate the exact conversation data
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
    
    print(f"\n🔍 PART 2: Verifying stored data...")
    
    # Check what was actually stored
    situations = session.query(Situation).filter_by(user_id=user.id).all()
    thoughts = session.query(AutomaticThought).filter_by(user_id=user.id).all()
    emotions = session.query(Emotion).filter_by(user_id=user.id).all()
    behaviors = session.query(Behavior).filter_by(user_id=user.id).all()
    background = session.query(BackgroundInfo).filter_by(user_id=user.id).first()
    
    print(f"📊 STORED DATA SUMMARY:")
    print(f"   Situations: {len(situations)}")
    for i, sit in enumerate(situations, 1):
        print(f"      {i}. {sit.description}")
    
    print(f"   Thoughts: {len(thoughts)}")
    for i, thought in enumerate(thoughts, 1):
        print(f"      {i}. {thought.thought}")
    
    print(f"   Emotions: {len(emotions)}")
    for i, emotion in enumerate(emotions, 1):
        print(f"      {i}. {emotion.emotion}")
    
    print(f"   Behaviors: {len(behaviors)}")
    for i, behavior in enumerate(behaviors, 1):
        print(f"      {i}. {behavior.action}")
    
    print(f"   Background Info:")
    if background:
        print(f"      Chief complaint: {background.chief_complaint}")
        print(f"      Stress patterns: {background.stress_response_patterns}")
        print(f"      Coping styles: {background.coping_styles}")
    else:
        print(f"      No background info found!")
    
    print(f"\n🤖 PART 3: Testing AI formulation generation...")
    
    # Check the system prompt being used
    system_prompt = conversation_manager.format_system_prompt("")
    print(f"📋 SYSTEM PROMPT BEING USED:")
    print("-" * 40)
    print(system_prompt)
    print("-" * 40)
    
    # Create the exact context that gets sent to AI
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
    
    print(f"\n📄 CONTEXT SENT TO AI:")
    print("-" * 40)
    print(formulation_context)
    print("-" * 40)
    
    # Test different AI models
    models_to_test = ["llama3.2", "llama3.1", "qwen2.5"]
    
    for model in models_to_test:
        print(f"\n🧠 Testing with model: {model}")
        print("-" * 50)
        
        try:
            response = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": formulation_context}
                ]
            )
            
            formulation = response['message']['content'].strip()
            
            print(f"✅ {model} Response (first 500 chars):")
            print(formulation[:500] + "..." if len(formulation) > 500 else formulation)
            
            # Check if the response mentions binge eating
            binge_mentioned = "binge" in formulation.lower() or "eating" in formulation.lower()
            assignment_mentioned = "assignment" in formulation.lower() or "university" in formulation.lower()
            parents_mentioned = "parent" in formulation.lower() or "family" in formulation.lower()
            
            print(f"🔍 Accuracy Check:")
            print(f"   Mentions binge/eating: {binge_mentioned}")
            print(f"   Mentions assignment/university: {assignment_mentioned}")
            print(f"   Mentions parents/family: {parents_mentioned}")
            
        except Exception as e:
            print(f"❌ {model} failed: {e}")
    
    # Test with a more explicit prompt
    print(f"\n🎯 PART 4: Testing with improved prompt...")
    
    explicit_prompt = """You are a CBT therapist creating a comprehensive formulation. 

CRITICAL INSTRUCTIONS:
- Use ONLY the data provided in the user message
- Focus on the ACTUAL situations, thoughts, emotions, and behaviors described
- Do NOT use generic CBT templates or examples
- The user's specific presenting concern is about binge eating behavior
- Reference the exact situations: university assignment stress, family conflict, and restriction/fasting patterns
- DO NOT mention anything not specifically discussed (like assertiveness, saying no, passive-aggressive behavior)

Create a CBT formulation that directly addresses the user's actual experiences with binge eating, academic stress, family conflicts, and restriction patterns."""
    
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": explicit_prompt},
                {"role": "user", "content": formulation_context}
            ]
        )
        
        improved_formulation = response['message']['content'].strip()
        
        print(f"✅ IMPROVED FORMULATION:")
        print("-" * 40)
        print(improved_formulation)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Improved formulation failed: {e}")
    
    session.close()

if __name__ == "__main__":
    debug_data_storage_and_formulation() 