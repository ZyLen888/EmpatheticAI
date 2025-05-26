import ollama
from utils.prompt_loader import load_prompt_template
from utils.database import init_db, get_or_create_user, save_conversation, get_user_by_name
from utils.memory import MemoryManager
from utils.conversation_manager import ConversationManager
from utils.nlp_extractor import NLPExtractor
import json
import uuid
import os
from pathlib import Path

def get_user_identifier():
    print("\nHow would you like me to address you?")
    name = input("Enter your preferred name > ").strip()
    
    # Create user data directory if it doesn't exist
    user_data_dir = Path.home() / ".empathetic_ai" / "users"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if this name has been used before
    session = init_db()
    existing_user = get_user_by_name(session, name)
    
    if existing_user:
        # Check if we have stored UUID for this user
        user_file = user_data_dir / f"{name}.txt"
        if user_file.exists():
            stored_uuid = user_file.read_text().strip()
            if stored_uuid == existing_user.identifier:
                print(f"\nWelcome back, {name}! I remember our previous conversations.")
                return existing_user.identifier
        
        # If UUID doesn't match or file doesn't exist, this might be a different user with the same name
        print("\nI notice someone with this name has chatted with me before.")
        print("1. I am that person (continue previous conversations)")
        print("2. I am a different person (start fresh)")
        
        choice = input("Your choice (1-2) > ").strip()
        if choice == "1":
            # Store the UUID for future reference
            user_file.write_text(existing_user.identifier)
            return existing_user.identifier
    
    # Generate new UUID for new user
    new_uuid = str(uuid.uuid4())
    
    # Store the UUID locally for future reference
    user_file = user_data_dir / f"{name}.txt"
    user_file.write_text(new_uuid)
    
    return new_uuid

def run_chat():
    # Initialize components
    session = init_db()
    nlp_extractor = NLPExtractor()
    
    # Get or create user
    user_identifier = get_user_identifier()
    user = get_or_create_user(session, user_identifier)
    memory = MemoryManager(session, user)
    conversation_manager = ConversationManager(memory)
    
    print("\n🎭 Choose a therapy style:")
    print("1. Person-Centered Therapy (PCT)")
    print("2. Motivational Interviewing (MI)")
    print("3. Integrated (PCT + MI)")
    
    style_map = {
        "1": "pct",
        "2": "mi",
        "3": "integrated"
    }
    
    style_choice = input("Style (1-3) > ").strip()
    if style_choice not in style_map:
        print("Invalid choice. Please select 1, 2, or 3.")
        return
        
    style = style_map[style_choice]
    
    print("\n📝 Choose prompt approach:")
    print("1. Zero-shot")
    print("2. One-shot")
    print("3. Few-shot")
    
    approach_map = {
        "1": "zero_shot",
        "2": "one_shot",
        "3": "few_shot"
    }
    
    approach_choice = input("Approach (1-3) > ").strip()
    if approach_choice not in approach_map:
        print("Invalid choice. Please select 1, 2, or 3.")
        return
        
    approach = approach_map[approach_choice]

    try:
        base_prompt = load_prompt_template(style, approach)
    except ValueError as e:
        print(e)
        return

    print(f"\n🧠 Using '{style}' style with {approach} approach. Type 'exit' to quit.\n")
    
    # Add user context to system prompt
    context = memory.get_context_for_conversation()
    system_prompt = conversation_manager.format_system_prompt(base_prompt)
    system_prompt += f"\nUser Context: {json.dumps(context, ensure_ascii=False)}"

    # Start with a conversation starter
    if conversation_manager.should_initiate_conversation():
        starter = conversation_manager.get_contextual_starter()
        print(f"AI > {starter}\n")
        save_conversation(session, user.id, "", starter, context)  # Pass context directly

    while True:
        user_input = input("You > ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye! 🌱")
            break

        # Extract and store information from user message
        extracted_info = nlp_extractor.extract_information(user_input)
        if extracted_info:
            nlp_extractor.update_memory(memory, extracted_info)
            # Update context with new information
            context = memory.get_context_for_conversation()
            system_prompt = conversation_manager.format_system_prompt(base_prompt)
            system_prompt += f"\nUser Context: {json.dumps(context, ensure_ascii=False)}"

        response = ollama.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        ai_response = response['message']['content']
        print("\nAI > " + ai_response + "\n")
        
        # Save conversation with context as native JSON
        save_conversation(session, user.id, user_input, ai_response, context)

if __name__ == "__main__":
    run_chat()
