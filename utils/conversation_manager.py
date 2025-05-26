import random
from datetime import datetime, timedelta
import uuid

class ConversationManager:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.last_interaction = None
        self.conversation_flow = {
            'preferences_collected': False,
            'events_collected': False,
            'current_focus': None
        }
        self.conversation_starters = [
            "I've been thinking about you. How have you been feeling lately?",
            "It's been a while since we talked. What's been on your mind?",
            "I'm here to listen. What would you like to share today?",
            "How has your day been going? I'm here if you want to talk about anything.",
            "I'm curious about how you've been doing. Would you like to share what's been happening in your life?",
            "I'm here to support you. What's been occupying your thoughts recently?",
            "I've been wondering how you're doing. Would you like to talk about what's been going on?",
            "I'm here to listen and understand. What would you like to discuss today?",
            "I'm interested in hearing about your experiences. What's been happening in your world?",
            "I'm here to provide a safe space for you to share. What's on your mind?"
        ]
        
    def should_initiate_conversation(self):
        if not self.last_interaction:
            return True
        time_since_last = datetime.utcnow() - self.last_interaction
        return time_since_last > timedelta(hours=24)
        
    def get_conversation_starter(self):
        self.last_interaction = datetime.utcnow()
        return random.choice(self.conversation_starters)
        
    def get_contextual_starter(self):
        # Check what information we still need to collect
        if not self.conversation_flow['preferences_collected']:
            self.conversation_flow['current_focus'] = 'preferences'
            return "To help me understand you better, could you share some of your interests or things you enjoy?"
        elif not self.conversation_flow['events_collected']:
            self.conversation_flow['current_focus'] = 'events'
            return "I'd love to know what's coming up in your life. Any events or activities you're looking forward to or preparing for?"
        
        # If we have basic information, check emotions
        recent_emotions = self.memory.get_recent_emotions(limit=1)
        if recent_emotions:
            last_emotion = recent_emotions[0]
            if last_emotion.emotion in ['sad', 'anxious', 'stressed']:
                return "I've been thinking about our last conversation. How are you feeling about that situation now?"
            elif last_emotion.emotion in ['happy', 'excited', 'content']:
                return "I remember you were feeling positive last time we talked. How have things been going since then?"
        
        return self.get_conversation_starter()
        
    def get_next_guidance_prompt(self):
        """Returns a natural prompt to guide the conversation based on what information we still need."""
        recent_preferences = self.memory.get_recent_preferences()
        recent_events = self.memory.get_active_events()

        if not recent_preferences:
            return "I'm curious about what brings you joy. Would you mind sharing some activities or things you enjoy?"
        elif not recent_events:
            return "What's been keeping you busy lately? Any upcoming plans or recent activities you'd like to share?"
        return None

    def update_flow_state(self, extracted_info):
        """Updates the conversation flow state based on extracted information."""
        if extracted_info.get('preferences'):
            self.conversation_flow['preferences_collected'] = True
        if extracted_info.get('events'):
            self.conversation_flow['events_collected'] = True

    def format_system_prompt(self, base_prompt):
        # Get conversation history
        recent_history = self.memory.get_recent_conversations(limit=5)
        history_summary = self._summarize_conversation_history(recent_history)

        return f"""You are a warm, empathetic AI therapist who initiates natural conversations and responds with genuine care and understanding.

{base_prompt}

Conversation History Summary:
{history_summary}

Additional Guidelines:
- Start conversations naturally and proactively
- Use warm, conversational language
- Avoid direct questions about emotions unless the user brings them up
- Show genuine interest in the user's experiences
- Maintain a natural flow of conversation
- Use the user's name occasionally if they've shared it
- Remember previous conversations and refer to them naturally
- Avoid robotic or formulaic responses
- Be patient and allow the user to share at their own pace
- Use the context of previous interactions to make responses more personal and relevant
- Gradually and naturally guide users to share their preferences and upcoming events
- If the user hasn't shared preferences or events, find natural ways to ask about them"""

    def _summarize_conversation_history(self, history):
        if not history:
            return "No previous conversation history available."
        
        summary = "Previous conversations covered:\n"
        for conv in history:
            summary += f"- {conv.timestamp.strftime('%Y-%m-%d')}: {conv.message[:50]}...\n"
        return summary 