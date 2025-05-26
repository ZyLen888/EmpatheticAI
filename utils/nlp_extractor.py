import ollama
import json
from datetime import datetime, timedelta
import re

class NLPExtractor:
    def __init__(self):
        self.extraction_prompt = """You are an AI trained to extract structured information from text. Extract the following from the user's message:
1. Events: Any meetings, deadlines, assignments, or time-bound activities
2. Concerns: Worries, issues, or ongoing challenges
3. Emotions: Emotional states and their intensities, including what triggered them
4. Preferences: Things the user likes or dislikes
5. Time references: Dates and times mentioned

Format your response as a JSON object with these exact keys:
{
    "events": [
        {
            "title": "",
            "date": "",
            "importance": "low/medium/high",
            "primary_emotion": {"emotion": "", "intensity": "low/medium/high"}
        }
    ],
    "concerns": [
        {
            "type": "work/personal/health/education",
            "description": "",
            "urgency": "low/medium/high",
            "primary_emotion": {"emotion": "", "intensity": "low/medium/high"}
        }
    ],
    "emotions": [
        {
            "emotion": "",
            "intensity": "low/medium/high",
            "context": "",
            "related_event_title": "",
            "related_concern_description": ""
        }
    ],
    "preferences": [
        {
            "category": "food/music/activity/etc",
            "item": "",
            "sentiment": "like/dislike/love/hate"
        }
    ],
    "time_references": ["tomorrow", "next week", etc.]
}

User message: """

    def _parse_date(self, date_str, time_references):
        now = datetime.now()
        
        # Handle common time references
        if "tomorrow" in time_references:
            return now + timedelta(days=1)
        elif "next week" in time_references:
            return now + timedelta(weeks=1)
        elif "today" in time_references:
            return now
        
        # Try to parse explicit date if provided
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            # Default to near future if date is unclear
            return now + timedelta(days=1)

    def extract_information(self, message):
        # Get structured analysis from LLM
        response = ollama.chat(
            model="llama3",
            messages=[
                {
                    "role": "system",
                    "content": self.extraction_prompt + message
                }
            ]
        )
        
        try:
            # Extract the JSON part from the response
            json_str = re.search(r'\{.*\}', response['message']['content'], re.DOTALL)
            if not json_str:
                return None
            
            extracted = json.loads(json_str.group())
            
            # Process events with proper dates
            for event in extracted.get('events', []):
                event['date'] = self._parse_date(
                    event.get('date', ''),
                    extracted.get('time_references', [])
                ).isoformat()
            
            return extracted
        except Exception as e:
            print(f"Error extracting information: {e}")
            return None

    def update_memory(self, memory_manager, extracted_info):
        if not extracted_info:
            return
            
        # Add preferences
        for pref in extracted_info.get('preferences', []):
            memory_manager.add_preference(
                category=pref['category'],
                item=pref['item'],
                sentiment=pref['sentiment']
            )
            
        # Process events and concerns first, then emotions with relationships
        event_map = {}  # title -> event object
        concern_map = {}  # description -> concern object
        emotion_map = {}  # emotion + context -> emotion object
        
        # First pass: Create events
        for event_data in extracted_info.get('events', []):
            event = memory_manager.add_event(
                title=event_data['title'],
                date=datetime.fromisoformat(event_data['date']),
                importance=event_data.get('importance', 'medium')
            )
            event_map[event_data['title']] = event
        
        # First pass: Create concerns
        for concern_data in extracted_info.get('concerns', []):
            concern = memory_manager.add_concern(
                type=concern_data['type'],
                description=concern_data['description'],
                urgency=concern_data.get('urgency', 'medium')
            )
            concern_map[concern_data['description']] = concern
        
        # Second pass: Create emotions and link them
        for emotion_data in extracted_info.get('emotions', []):
            related_event = None
            related_concern = None
            
            # Find related event
            if emotion_data.get('related_event_title'):
                related_event = event_map.get(emotion_data['related_event_title'])
                
            # Find related concern
            if emotion_data.get('related_concern_description'):
                related_concern = concern_map.get(emotion_data['related_concern_description'])
            
            # Create the emotion and link
            emotion = memory_manager.add_emotion(
                emotion=emotion_data['emotion'],
                intensity=emotion_data['intensity'],
                context=emotion_data['context'],
                related_event=related_event,
                related_concern=related_concern
            )
            
            # Save for third pass
            key = f"{emotion_data['emotion']}:{emotion_data['context']}"
            emotion_map[key] = emotion
            
        # Third pass: Link emotions to events and concerns as primary emotions
        for event_data in extracted_info.get('events', []):
            if 'primary_emotion' in event_data and event_data['primary_emotion']:
                event = event_map.get(event_data['title'])
                if event and not event.primary_emotion_id:
                    for emotion in emotion_map.values():
                        if (emotion.emotion == event_data['primary_emotion']['emotion'] and 
                            emotion.intensity == event_data['primary_emotion']['intensity']):
                            event.primary_emotion_id = emotion.id
                            memory_manager.session.add(event)
                            memory_manager.session.commit()
                            break
                    
        # Third pass: Link emotions to concerns as primary emotions
        for concern_data in extracted_info.get('concerns', []):
            if 'primary_emotion' in concern_data and concern_data['primary_emotion']:
                concern = concern_map.get(concern_data['description'])
                if concern and not concern.primary_emotion_id:
                    for emotion in emotion_map.values():
                        if (emotion.emotion == concern_data['primary_emotion']['emotion'] and 
                            emotion.intensity == concern_data['primary_emotion']['intensity']):
                            concern.primary_emotion_id = emotion.id
                            memory_manager.session.add(concern)
                            memory_manager.session.commit()
                            break 