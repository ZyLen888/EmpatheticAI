import ollama
from utils.prompt_loader import load_prompt_template
from utils.cbt_database import init_cbt_db, get_or_create_user, save_conversation, get_user_by_name
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager
from utils.cbt_nlp_extractor import CBTNLPExtractor
import json
import uuid
import os
from pathlib import Path

def get_user_identifier():
    # Generate unique UUID for each session
    new_uuid = str(uuid.uuid4())
    
    # Create user data directory if it doesn't exist
    user_data_dir = Path.home() / ".empathetic_ai" / "users"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    session = init_cbt_db()
    return new_uuid, session

def run_chat():
    # Initialize components
    cbt_nlp_extractor = CBTNLPExtractor()
    
    # Get or create user
    user_identifier, session = get_user_identifier()
    user = get_or_create_user(session, user_identifier)
    cbt_memory = CBTMemoryManager(session, user)
    conversation_manager = ConversationManager(cbt_memory)
    
    print("\n🧠 CBT-Informed AI Assistant")
    print("Choose session type:")
    print("1. With personalization (references previous sessions and patterns)")
    print("2. Without personalization (pure CBT questions only)")
    
    context_map = {
        "1": "with_personalization", 
        "2": "without_personalization"
    }
    
    context_choice = input("Session type (1-2) > ").strip()
    if context_choice not in context_map:
        print("Invalid choice. Please select 1 or 2.")
        return
        
    personalization_type = context_map[context_choice]

    try:
        base_prompt = load_prompt_template("cbt", "with_context")  # Both use same base prompt
    except ValueError as e:
        print(e)
        return

    print(f"\n🧠 Using CBT approach {'with personalization' if personalization_type == 'with_personalization' else 'without personalization'}. Type 'exit' to quit.\n")
    
    # Start structured CBT assessment (both versions use same structure)
    intro_base = "Hi! I'm here to support you today through a structured conversation that will help us understand your thinking patterns. What's been on your mind lately?"
    starter = conversation_manager._rephrase_question_with_ai(intro_base, 'introduction')
    print(f"AI > {starter}\n")
    
    context = cbt_memory.get_context_for_conversation()
    save_conversation(session, user.id, "", starter, context, personalization_type)

    while True:
        user_input = input("You > ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye! 🌱")
            break

        # Handle structured CBT assessment
        if personalization_type == "with_personalization":
            # Save the user's response to appropriate database table
            conversation_manager.save_response_data(user_input)
            
            # Advance to next phase after saving response
            conversation_manager.advance_phase()
            
            # Get current phase for system prompt
            phase = conversation_manager.get_current_phase()
            
            # Check if we're at the final analysis phase
            if phase == 'complete':
                # Generate improved CBT formulation based on actual stored data
                print("\n📋 Generating CBT Formulation...")
                ai_response = conversation_manager.generate_improved_cbt_formulation()
                
                print(f"\nAI > {ai_response}\n")
                
                context = cbt_memory.get_context_for_conversation()
                save_conversation(session, user.id, "CBT Formulation", ai_response, context, personalization_type)
                
                # End conversation after formulation
                print("CBT Assessment complete! 🌱")
                break
            
            else:
                # Get next structured question WITH personalization
                next_question = conversation_manager.get_contextual_starter()
                
                if next_question:
                    # Generate AI response with natural framing
                    phase = conversation_manager.get_current_collection_phase()
                    
                    if phase == 'introduction':
                        framing_prompt = f"""The user shared their presenting concern: "{user_input}"

You need to naturally deliver this question: "{next_question}"

CRITICAL RULES:
- Create ONE flowing response that briefly acknowledges their concern and naturally leads into the question
- Don't separate acknowledgment and question - blend them together smoothly
- Keep it warm, empathetic, and professional
- Total response should be 30-50 words as ONE complete statement"""
                    
                    elif phase == 'cbt_assessment':
                        framing_prompt = f"""The user responded: "{user_input}"

You need to naturally ask this question: "{next_question}"

CRITICAL RULES:
- Create ONE flowing response that briefly acknowledges what they shared and naturally transitions to the question
- Don't separate acknowledgment and question - make it one smooth statement
- Keep it therapeutic and supportive
- Total response should be 25-45 words as ONE complete statement"""
                    
                    elif phase == 'patterns_beliefs':
                        framing_prompt = f"""The user shared: "{user_input}"

You need to ask: "{next_question}"

CRITICAL RULES:
- Create ONE flowing response that acknowledges their insights and naturally leads into the question
- Don't separate acknowledgment and question - blend them together
- Keep it thoughtful and encouraging
- Total response should be 40-60 words as ONE complete statement"""
                    
                    else:
                        framing_prompt = f"""The user responded: "{user_input}"

You need to ask: "{next_question}"

Create ONE natural, flowing response that incorporates the question smoothly."""

                    system_prompt = conversation_manager.format_system_prompt(base_prompt)
                    
                    response = ollama.chat(
                        model="llama3.2",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": framing_prompt}
                        ]
                    )
                    
                    ai_response = response['message']['content']
                    print(f"\nAI > {ai_response}\n")
                    
                    context = cbt_memory.get_context_for_conversation()
                    save_conversation(session, user.id, user_input, ai_response, context, personalization_type)
                    
                else:
                    # No more questions - shouldn't happen in this flow
                    print("Assessment complete!\n")
                    break

        # Handle structured CBT assessment WITHOUT personalization 
        else:
            # Save the user's response to appropriate database table
            conversation_manager.save_response_data(user_input)
            
            # Advance to next phase after saving response
            conversation_manager.advance_phase()
            
            # Get current phase for system prompt
            phase = conversation_manager.get_current_phase()
            
            # Check if we're at the final analysis phase
            if phase == 'complete':
                # Generate improved CBT formulation based on actual stored data
                print("\n📋 Generating CBT Formulation...")
                ai_response = conversation_manager.generate_improved_cbt_formulation()
                
                print(f"\nAI > {ai_response}\n")
                
                context = cbt_memory.get_context_for_conversation()
                save_conversation(session, user.id, "CBT Formulation", ai_response, context, personalization_type)
                
                # End conversation after formulation
                print("CBT Assessment complete! 🌱")
                break
            
            else:
                # Get next structured question WITHOUT personalization
                next_question = conversation_manager.get_contextual_starter_without_personalization()
                
                if next_question:
                    # Generate AI response with natural framing
                    phase = conversation_manager.get_current_collection_phase()
                    
                    if phase == 'introduction':
                        framing_prompt = f"""The user shared their presenting concern: "{user_input}"

You need to naturally deliver this question: "{next_question}"

CRITICAL RULES:
- Create ONE flowing response that briefly acknowledges their concern and naturally leads into the question
- Don't separate acknowledgment and question - blend them together smoothly
- Keep it warm, empathetic, and professional
- Total response should be 30-50 words as ONE complete statement"""
                    
                    elif phase == 'cbt_assessment':
                        framing_prompt = f"""The user responded: "{user_input}"

You need to naturally ask this question: "{next_question}"

CRITICAL RULES:
- Create ONE flowing response that briefly acknowledges what they shared and naturally transitions to the question
- Don't separate acknowledgment and question - make it one smooth statement
- Keep it therapeutic and supportive
- Total response should be 25-45 words as ONE complete statement"""
                    
                    elif phase == 'patterns_beliefs':
                        framing_prompt = f"""The user shared: "{user_input}"

You need to ask: "{next_question}"

CRITICAL RULES:
- Create ONE flowing response that acknowledges their insights and naturally leads into the question
- Don't separate acknowledgment and question - blend them together
- Keep it thoughtful and encouraging
- Total response should be 40-60 words as ONE complete statement"""
                    
                    else:
                        framing_prompt = f"""The user responded: "{user_input}"

You need to ask: "{next_question}"

Create ONE natural, flowing response that incorporates the question smoothly."""

                    system_prompt = conversation_manager.format_system_prompt(base_prompt)
                    
                    response = ollama.chat(
                        model="llama3.2",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": framing_prompt}
                        ]
                    )
                    
                    ai_response = response['message']['content']
                    print(f"\nAI > {ai_response}\n")
                    
                    context = cbt_memory.get_context_for_conversation()
                    save_conversation(session, user.id, user_input, ai_response, context, personalization_type)
                    
                else:
                    # No more questions - shouldn't happen in this flow
                    print("Assessment complete!\n")
                    break

if __name__ == "__main__":
    run_chat()
