import ollama
import json
from datetime import datetime
import re

class CBTNLPExtractor:
    def __init__(self):
        self.extraction_prompt = """You are an AI trained to extract structured CBT therapy-relevant information from user conversations. Extract the following elements from their message, formatted as JSON:

1. Situations: Specific contexts where distressing thoughts/feelings occurred
2. Automatic Thoughts: Immediate thoughts that popped up in those situations
3. Meaning of Automatic Thoughts: Deeper interpretation of the thought's meaning
4. Emotions: Emotions felt during each situation, linked to thoughts
5. Behaviors: Actions taken or avoided in response to those thoughts/emotions
6. Inferred Core Beliefs: Deep beliefs about self, others, or the world
7. Intermediate Beliefs: Rules, assumptions, and attitudes that influence behavior
8. Coping Strategies: Maladaptive ways the user handled distress

Example format:
{
  "situations": [
    {
      "description": "",
      "context": "",
      "category": "work/personal/social/etc"
    }
  ],
  "automatic_thoughts": [
    {
      "thought": "",
      "situation_description": "",
      "linked_emotion": {"emotion": "", "intensity": "low/medium/high"}
    }
  ],
  "thought_meanings": [
    {
      "meaning": "",
      "linked_thought": "",
      "user_inferred_core_belief": ""
    }
  ],
  "emotions": [
    {
      "emotion": "",
      "intensity": "low/medium/high",
      "context": "",
      "linked_thought": "",
      "linked_situation": ""
    }
  ],
  "behaviors": [
    {
      "action": "",
      "behavior_type": "avoidance/assertive/passive/help-seeking/etc",
      "linked_situation": "",
      "linked_thought": ""
    }
  ],
  "core_beliefs": ["I'm not good enough", "I'm unlovable", "I'm a failure"],
  "intermediate_beliefs": [
    "If I try too hard, I'll fail",
    "I should always be helpful",
    "If I show emotions, people will think I'm weak"
  ],
  "coping_strategies": [
    "Avoid asking for help",
    "Overwork to avoid criticism",
    "Procrastination to avoid potential failure"
  ]
}

Focus on extracting present-moment psychological patterns, not medical history, diagnoses, or trauma.
User message: """

        self.background_extraction_prompt = """Extract basic background information from the user's message. Return only JSON format:

{
  "identifying_info": {
    "age_range": "",
    "gender_identity": "",
    "occupation": "",
    "interests": ""
  },
  "cbt_patterns": {
    "stress_response": "",
    "coping_style": ""
  }
}

Only extract information explicitly mentioned. Leave empty if not provided.
User message: """

    def extract_cbt_information(self, message):
        """Extract CBT-relevant information from user message"""
        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": self.extraction_prompt + message
                    }
                ]
            )
            
            # Extract the JSON part from the response
            json_str = re.search(r'\{.*\}', response['message']['content'], re.DOTALL)
            if not json_str:
                return None
            
            extracted = json.loads(json_str.group())
            return extracted
            
        except Exception as e:
            print(f"Error extracting CBT information: {e}")
            return None

    def extract_background_information(self, message):
        """Extract background information for case formulation"""
        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": self.background_extraction_prompt + message
                    }
                ]
            )
            
            # Extract the JSON part from the response more robustly
            content = response['message']['content']
            
            # Try to find JSON block
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return None
                
            json_str = content[json_start:json_end]
            
            # Clean up common JSON issues
            json_str = json_str.replace('\n', ' ').replace('\r', ' ')
            json_str = ' '.join(json_str.split())  # Remove extra whitespace
            
            extracted = json.loads(json_str)
            return extracted
            
        except json.JSONDecodeError as e:
            print(f"Error extracting background information: {e}")
            # Try to extract partial information manually
            return self._extract_partial_background(response['message']['content'])
        except Exception as e:
            print(f"Error extracting background information: {e}")
            return None

    def _extract_partial_background(self, content):
        """Fallback method to extract some background info even if JSON parsing fails"""
        # Basic fallback - just return empty structure for now
        return {
            "identifying_info": {},
            "cbt_patterns": {},
            "functioning": {},
            "history": {}
        }

    def update_cbt_memory(self, cbt_memory_manager, extracted_info):
        """Update CBT memory with extracted information"""
        if not extracted_info:
            return
            
        # Create situation mapping for linking
        situation_map = {}
        
        # First pass: Create situations
        for situation_data in extracted_info.get('situations', []):
            situation = cbt_memory_manager.add_situation(
                description=situation_data['description'],
                context=situation_data.get('context', ''),
                category=situation_data.get('category', 'general')
            )
            situation_map[situation_data['description']] = situation
        
        # Create automatic thoughts and link to situations
        thought_map = {}
        for thought_data in extracted_info.get('automatic_thoughts', []):
            linked_situation = None
            if thought_data.get('situation_description'):
                linked_situation = situation_map.get(thought_data['situation_description'])
            
            thought = cbt_memory_manager.add_automatic_thought(
                thought=thought_data['thought'],
                situation=linked_situation
            )
            thought_map[thought_data['thought']] = thought
        
        # Create thought meanings and link to thoughts
        for meaning_data in extracted_info.get('thought_meanings', []):
            linked_thought = None
            if meaning_data.get('linked_thought'):
                linked_thought = thought_map.get(meaning_data['linked_thought'])
            
            cbt_memory_manager.add_thought_meaning(
                meaning=meaning_data['meaning'],
                automatic_thought=linked_thought,
                user_inferred_core_belief=meaning_data.get('user_inferred_core_belief', '')
            )
        
        # Create emotions and link them
        for emotion_data in extracted_info.get('emotions', []):
            linked_situation = None
            linked_thought = None
            
            if emotion_data.get('linked_situation'):
                linked_situation = situation_map.get(emotion_data['linked_situation'])
            if emotion_data.get('linked_thought'):
                linked_thought = thought_map.get(emotion_data['linked_thought'])
            
            cbt_memory_manager.add_emotion(
                emotion=emotion_data['emotion'],
                intensity=emotion_data['intensity'],
                context=emotion_data.get('context', ''),
                situation=linked_situation,
                automatic_thought=linked_thought
            )
        
        # Create behaviors and link them
        for behavior_data in extracted_info.get('behaviors', []):
            linked_situation = None
            linked_thought = None
            
            if behavior_data.get('linked_situation'):
                linked_situation = situation_map.get(behavior_data['linked_situation'])
            if behavior_data.get('linked_thought'):
                linked_thought = thought_map.get(behavior_data['linked_thought'])
            
            cbt_memory_manager.add_behavior(
                action=behavior_data['action'],
                behavior_type=behavior_data.get('behavior_type', 'general'),
                situation=linked_situation,
                automatic_thought=linked_thought
            )
        
        # Update beliefs and coping strategies
        beliefs_data = {
            'core_beliefs': extracted_info.get('core_beliefs', []),
            'intermediate_beliefs': extracted_info.get('intermediate_beliefs', []),
            'coping_strategies': extracted_info.get('coping_strategies', [])
        }
        
        if any(beliefs_data.values()):
            cbt_memory_manager.update_beliefs(beliefs_data)

    def update_background_info(self, cbt_memory_manager, extracted_info):
        """Update background information for case formulation"""
        if not extracted_info:
            return
            
        cbt_memory_manager.update_background_info(extracted_info) 