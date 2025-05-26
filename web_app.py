from flask import Flask, render_template, request, jsonify, session, make_response
import ollama
from utils.prompt_loader import load_prompt_template
from utils.cbt_database import init_cbt_db, get_or_create_user, save_conversation
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager
import uuid
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Global storage for user sessions
user_sessions = {}

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('chat.html')

@app.route('/start_session', methods=['POST'])
def start_session():
    """Initialize a new chat session"""
    try:
        data = request.get_json()
        personalization_type = data.get('personalization_type', 'with_personalization')
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Initialize components
        db_session = init_cbt_db()
        user_identifier = str(uuid.uuid4())
        user = get_or_create_user(db_session, user_identifier)
        cbt_memory = CBTMemoryManager(db_session, user)
        conversation_manager = ConversationManager(cbt_memory)
        
        # Store session data
        user_sessions[session_id] = {
            'db_session': db_session,
            'user': user,
            'cbt_memory': cbt_memory,
            'conversation_manager': conversation_manager,
            'personalization_type': personalization_type,
            'conversation_history': [],
            'session_start_time': datetime.now(),
            'user_identifier': user_identifier
        }
        
        # Terminal logging for researcher (hidden from user interface)
        print(f"\n🔬 USER STUDY LOG - User {user.id} selected: {'WITH PERSONALIZATION' if personalization_type == 'with_personalization' else 'WITHOUT PERSONALIZATION (Pure CBT)'}")
        print(f"   Session ID: {session_id}")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("   =" * 60)
        
        # Load base prompt
        try:
            base_prompt = load_prompt_template("cbt", "with_context")
        except ValueError as e:
            return jsonify({'error': str(e)}), 500
        
        # Create initial greeting
        intro_base = "Hi! I'm here to support you today through a structured conversation that will help us understand your thinking patterns. What's been on your mind lately?"
        starter = conversation_manager._rephrase_question_with_ai(intro_base, 'introduction')
        
        # Clean up any quotation marks for consistency
        starter = starter.strip('"').strip("'").strip()
        
        # Save initial conversation
        context = cbt_memory.get_context_for_conversation()
        save_conversation(db_session, user.id, "", starter, context, personalization_type)
        
        # Add initial AI message to conversation history
        user_sessions[session_id]['conversation_history'].append({
            'timestamp': datetime.now(),
            'sender': 'AI', 
            'message': starter,
            'phase': 'introduction'
        })
        
        return jsonify({
            'success': True,
            'message': starter,
            'session_id': session_id,
            'personalization_type': personalization_type
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to start session: {str(e)}'}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handle user message and return AI response"""
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        session_id = session.get('session_id')
        
        if not session_id or session_id not in user_sessions:
            return jsonify({'error': 'Session not found. Please start a new session.'}), 400
        
        if not user_input:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get session data
        session_data = user_sessions[session_id]
        conversation_manager = session_data['conversation_manager']
        cbt_memory = session_data['cbt_memory']
        db_session = session_data['db_session']
        user = session_data['user']
        personalization_type = session_data['personalization_type']
        
        # Add user message to conversation history
        session_data['conversation_history'].append({
            'timestamp': datetime.now(),
            'sender': 'User',
            'message': user_input,
            'phase': conversation_manager.get_current_phase()
        })
        
        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "end session"]:
            # Terminal logging for researcher
            print(f"\n📊 USER STUDY LOG - User {user.id} ({personalization_type.upper()}) ENDED SESSION EARLY")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Clean up session
            db_session.close()
            del user_sessions[session_id]
            return jsonify({
                'success': True,
                'message': "Thank you for sharing. Take care! 🌱",
                'session_ended': True
            })
        
        # Process based on personalization type
        if personalization_type == "with_personalization":
            # Enhanced logging for personalization research
            print(f"\n🧠 MEMORY-ENHANCED AI PROCESSING for User {user.id}")
            print(f"   Using PERSONALIZED mode with database memory retrieval")
            print(f"   Timestamp: {datetime.now().strftime('%H:%M:%S')}")
            
            ai_response, session_ended = process_with_personalization(
                user_input, conversation_manager, cbt_memory, db_session, user, personalization_type, session_data
            )
        else:
            # Terminal logging for researcher  
            user_id = conversation_manager.memory.user.id
            print(f"\n🔍 USER STUDY LOG - User {user_id} (WITHOUT personalization) processing message")
            print(f"   Input: {user_input[:100]}...")
            print(f"   Timestamp: {datetime.now().strftime('%H:%M:%S')}")
            
            ai_response, session_ended = process_without_personalization(
                user_input, conversation_manager, cbt_memory, db_session, user, personalization_type, session_data
            )
        
        # Add AI message to conversation history
        session_data['conversation_history'].append({
            'timestamp': datetime.now(),
            'sender': 'AI',
            'message': ai_response,
            'phase': conversation_manager.get_current_phase()
        })
        
        return jsonify({
            'success': True,
            'message': ai_response,
            'phase': conversation_manager.get_current_phase(),
            'session_ended': session_ended
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500

def process_with_personalization(user_input, conversation_manager, cbt_memory, db_session, user, personalization_type, session_data):
    """Process message with personalization"""
    # Save user response
    conversation_manager.save_response_data(user_input)
    
    # Advance phase
    conversation_manager.advance_phase()
    
    # Get current phase
    phase = conversation_manager.get_current_phase()
    
    if phase == 'complete':
        # Generate CBT formulation
        print("📋 Generating CBT Formulation...")
        ai_response = conversation_manager.generate_improved_cbt_formulation()
        
        session_data['conversation_history'].append({
            'timestamp': datetime.now(),
            'sender': 'AI',
            'message': ai_response,
            'phase': phase
        })
        
        context = cbt_memory.get_context_for_conversation()
        save_conversation(db_session, user.id, user_input, ai_response, context, personalization_type)
        
        return ai_response, True
    
    else:
        # Get next structured question WITH personalization
        next_question = conversation_manager.get_contextual_starter()
        
        if next_question:
            # CRITICAL FIX: Use the personalized question directly without additional AI framing
            # The personalized question already contains proper acknowledgment and memory references
            ai_response = next_question
            
            session_data['conversation_history'].append({
                'timestamp': datetime.now(),
                'sender': 'AI',
                'message': ai_response,
                'phase': phase
            })
            
            context = cbt_memory.get_context_for_conversation()
            save_conversation(db_session, user.id, user_input, ai_response, context, personalization_type)
            
            return ai_response, False
        else:
            return "Assessment complete!", True

def process_without_personalization(user_input, conversation_manager, cbt_memory, db_session, user, personalization_type, session_data):
    """Process message without personalization"""
    # Save user response
    conversation_manager.save_response_data(user_input)
    
    # Advance phase
    conversation_manager.advance_phase()
    phase = conversation_manager.get_current_phase()
    
    if phase == 'complete':
        # Generate CBT formulation
        print("📋 Generating CBT Formulation...")
        ai_response = conversation_manager.generate_improved_cbt_formulation()
        
        context = cbt_memory.get_context_for_conversation()
        save_conversation(db_session, user.id, user_input, ai_response, context, personalization_type)
        
        return ai_response, True
    else:
        # Get next structured question WITHOUT personalization
        next_question = conversation_manager.get_contextual_starter_without_personalization()
        
        if next_question:
            # For non-personalized questions, we can still use AI framing since there's no bold formatting to preserve
            collection_phase = conversation_manager.get_current_collection_phase()
            
            if collection_phase == 'introduction':
                framing_prompt = f"""The user shared their presenting concern: "{user_input}"

You need to naturally deliver this question: "{next_question}"

CRITICAL RULES:
- Create ONE flowing response that briefly acknowledges their concern and naturally leads into the question
- Don't separate acknowledgment and question - blend them together smoothly
- Keep it warm, empathetic, and professional
- Total response should be 30-50 words as ONE complete statement"""
            
            elif collection_phase == 'cbt_assessment':
                framing_prompt = f"""The user responded: "{user_input}"

You need to naturally ask this question: "{next_question}"

CRITICAL RULES:
- Create ONE flowing response that briefly acknowledges what they shared and naturally transitions to the question
- Don't separate acknowledgment and question - make it one smooth statement
- Keep it therapeutic and supportive
- Total response should be 25-45 words as ONE complete statement"""
            
            elif collection_phase == 'patterns_beliefs':
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

            try:
                base_prompt = load_prompt_template("cbt", "with_context")
                system_prompt = conversation_manager.format_system_prompt(base_prompt)
                
                response = ollama.chat(
                    model="llama3.2",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": framing_prompt}
                    ]
                )
                
                ai_response = response['message']['content']
                ai_response = ai_response.strip('"').strip("'").strip()
            
                context = cbt_memory.get_context_for_conversation()
                save_conversation(db_session, user.id, user_input, ai_response, context, personalization_type)
                
                return ai_response, False
                
            except Exception as e:
                return f"I'm sorry, I encountered an error. Could you please try again? Error: {str(e)}", False
        else:
            return "Assessment complete!", True

@app.route('/download_report', methods=['GET'])
def download_report():
    """Generate and download conversation report"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in user_sessions:
            return jsonify({'error': 'Session not found'}), 400
            
        session_data = user_sessions[session_id]
        conversation_history = session_data['conversation_history']
        personalization_type = session_data['personalization_type']
        session_start_time = session_data['session_start_time']
        user_identifier = session_data['user_identifier']
        
        # Generate report
        report_content = generate_conversation_report(
            conversation_history, 
            personalization_type, 
            session_start_time,
            user_identifier
        )
        
        # Create response with file download
        response = make_response(report_content.encode('utf-8'))
        
        # Generate filename with timestamp (ASCII-safe)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_type = 'with_personalization' if personalization_type == 'with_personalization' else 'pure_cbt'
        filename = f'CBT_Session_Report_{session_type}_{timestamp}.txt'
        
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-cache'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

def generate_conversation_report(conversation_history, personalization_type, session_start_time, user_identifier):
    """Generate a formatted conversation report"""
    
    session_end_time = datetime.now()
    session_duration = session_end_time - session_start_time
    
    # Format duration
    duration_minutes = int(session_duration.total_seconds() / 60)
    duration_seconds = int(session_duration.total_seconds() % 60)
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("EMPATHETIC AI - CBT SESSION REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Session metadata
    report_lines.append("SESSION INFORMATION")
    report_lines.append("-" * 40)
    report_lines.append(f"Session Type: {'WITH Personalization (Memory-Enhanced)' if personalization_type == 'with_personalization' else 'WITHOUT Personalization (Pure CBT)'}")
    report_lines.append(f"User ID: {user_identifier[:8]}***")
    report_lines.append(f"Session Start: {session_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Session End: {session_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Duration: {duration_minutes} minutes, {duration_seconds} seconds")
    report_lines.append(f"Total Messages: {len(conversation_history)}")
    report_lines.append("")
    
    # Session description
    report_lines.append("SESSION DESCRIPTION")
    report_lines.append("-" * 40)
    if personalization_type == 'with_personalization':
        report_lines.append("This session used PERSONALIZED responses that referenced previous")
        report_lines.append("conversation data and patterns from the database. The AI demonstrated")
        report_lines.append("memory of past interactions and contextual awareness.")
    else:
        report_lines.append("This session used PURE CBT ASSESSMENT without personalization.")
        report_lines.append("The AI followed structured CBT questions without referencing")
        report_lines.append("previous conversation data or showing memory behaviors.")
    report_lines.append("")
    
    # Conversation transcript
    report_lines.append("CONVERSATION TRANSCRIPT")
    report_lines.append("-" * 40)
    
    for i, entry in enumerate(conversation_history, 1):
        timestamp = entry['timestamp'].strftime('%H:%M:%S')
        sender = entry['sender']
        message = entry['message']
        phase = entry.get('phase', 'unknown')
        
        report_lines.append(f"[{timestamp}] {sender.upper()} (Phase: {phase})")
        
        # Clean message of any emojis/special characters that might cause encoding issues
        cleaned_message = clean_text_for_report(message)
        
        # Format message with proper wrapping
        message_lines = cleaned_message.split('\n')
        for line in message_lines:
            # Wrap long lines
            while len(line) > 75:
                wrap_point = line.rfind(' ', 0, 75)
                if wrap_point == -1:
                    wrap_point = 75
                report_lines.append(f"  {line[:wrap_point]}")
                line = line[wrap_point:].strip()
            if line:
                report_lines.append(f"  {line}")
        
        report_lines.append("")
    
    # Session summary
    ai_messages = [entry for entry in conversation_history if entry['sender'] == 'AI']
    user_messages = [entry for entry in conversation_history if entry['sender'] == 'User']
    
    report_lines.append("SESSION STATISTICS")
    report_lines.append("-" * 40)
    report_lines.append(f"AI Messages: {len(ai_messages)}")
    report_lines.append(f"User Messages: {len(user_messages)}")
    
    # Check for CBT formulation
    formulation_found = any('formulation' in msg['message'].lower() or 
                           'based on everything you\'ve shared' in msg['message'].lower() 
                           for msg in ai_messages)
    
    report_lines.append(f"CBT Formulation Generated: {'Yes' if formulation_found else 'No'}")
    report_lines.append(f"Session Completed: {'Yes' if formulation_found else 'Partial'}")
    report_lines.append("")
    
    # Personalization analysis
    if personalization_type == 'with_personalization':
        # Count personalization markers
        personalization_count = sum(
            msg['message'].count('**') // 2 for msg in ai_messages
        )
        report_lines.append("PERSONALIZATION ANALYSIS")
        report_lines.append("-" * 40)
        report_lines.append(f"Memory References Detected: {personalization_count}")
        report_lines.append("Note: Personalization appears as **bold text** in AI responses")
        report_lines.append("")
    
    # Footer
    report_lines.append("=" * 80)
    report_lines.append("Generated by Empathetic AI - CBT Assessment System")
    report_lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    
    return '\n'.join(report_lines)

def clean_text_for_report(text):
    """Clean text by removing problematic emojis and special characters"""
    import re
    
    # Remove or replace common emojis that cause encoding issues
    emoji_replacements = {
        '🧠': '[BRAIN]',
        '📋': '[CLIPBOARD]', 
        '💬': '[CHAT]',
        '📊': '[CHART]',
        '📝': '[NOTES]',
        '📈': '[GRAPH]',
        '🌱': '[PLANT]',
        '✨': '[SPARKLES]',
        '🔬': '[MICROSCOPE]',
        '✅': '[CHECK]',
        '📊': '[STATS]',
        '💡': '[LIGHTBULB]',
        '🎯': '[TARGET]',
        '🏁': '[FLAG]',
        '❌': '[X]',
        '🆕': '[NEW]',
        '📄': '[PAGE]',
        '📥': '[DOWNLOAD]'
    }
    
    # Replace known problematic emojis
    cleaned_text = text
    for emoji, replacement in emoji_replacements.items():
        cleaned_text = cleaned_text.replace(emoji, replacement)
    
    # Remove any remaining emoji characters (Unicode ranges for emojis)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002702-\U000027B0"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+",
        flags=re.UNICODE
    )
    
    cleaned_text = emoji_pattern.sub('[EMOJI]', cleaned_text)
    
    return cleaned_text

@app.route('/end_session', methods=['POST'])
def end_session():
    """End the current session"""
    session_id = session.get('session_id')
    
    if session_id and session_id in user_sessions:
        # Clean up session
        user_sessions[session_id]['db_session'].close()
        del user_sessions[session_id]
    
    session.pop('session_id', None)
    
    return jsonify({'success': True, 'message': 'Session ended successfully'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 