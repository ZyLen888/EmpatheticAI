import random
from datetime import datetime, timedelta
import uuid
import re

class ConversationManager:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.last_interaction = None
        
        # CBT Assessment Phases
        self.phases = [
            'introduction',     # Phase 1: Introduction & Rapport
            'situation_1',      # Phase 2: First triggering situation
            'thoughts_1',       # Phase 3: Automatic thoughts for situation 1
            'emotions_1',       # Phase 4: Emotional & physical responses for situation 1
            'behavior_1',       # Phase 5: Behavioral responses for situation 1
            'situation_2',      # Repeat for second situation
            'thoughts_2',
            'emotions_2', 
            'behavior_2',
            'situation_3',      # Repeat for third situation
            'thoughts_3',
            'emotions_3',
            'behavior_3',
            'patterns_beliefs', # Phase 6: Patterns, coping & beliefs
            'complete'
        ]
        
        self.current_phase_index = 0
        self.user_name = None
        
        # Store current situation data temporarily
        self.current_situation_data = {}
        
        # Base question templates for rephrasing
        self.base_questions = {
            'introduction': "What's been on your mind lately? Is there anything specific you'd like to discuss?",
            'situation_1': "Can you tell me about a recent specific time when you felt really overwhelmed, anxious, stressed, or upset? I'd like to understand exactly what happened in that situation.",
            'thoughts_1': "What was going through your mind at that moment? What specific thoughts or internal dialogue were you having?",
            'emotions_1': "How did you feel emotionally and physically in that situation? What emotions came up, and did you notice any physical sensations?",
            'behavior_1': "What did you do in response to those thoughts and feelings? How did you behave or what actions did you take?",
            'situation_2': "Now, can you think of another similar situation where you experienced difficult thoughts or feelings? What happened in that second situation?",
            'thoughts_2': "What thoughts went through your mind during that second situation?",
            'emotions_2': "How did you feel emotionally and physically in that second situation?",
            'behavior_2': "What did you do in response during that second situation?",
            'situation_3': "Let's explore one more situation. Can you describe a third time when you experienced similar difficulties? What happened?",
            'thoughts_3': "What thoughts were running through your mind in that third situation?",
            'emotions_3': "How did you feel emotionally and physically during that third situation?",
            'behavior_3': "What was your response or behavior in that third situation?",
            'patterns_beliefs': "Now I'd like to explore some patterns. Do you notice any common ways you tend to respond to stress or difficult situations? What usually helps you cope - even temporarily - when things get difficult? And do you have any beliefs about yourself that seem to come up again and again?"
        }
        
    def _rephrase_question_with_ai(self, base_question, phase):
        """Use AI to create natural variations of the structured questions"""
        import ollama
        
        # Store original bold content for restoration if needed
        import re
        bold_pattern = r'\*\*(.*?)\*\*'
        bold_matches = re.findall(bold_pattern, base_question)
        
        # Define the purpose and constraints for each phase type
        phase_contexts = {
            'introduction': "building initial rapport and understanding presenting concerns",
            'situation': "gathering specific details about a triggering situation", 
            'thoughts': "exploring automatic thoughts and internal dialogue",
            'emotions': "identifying emotional and physical responses",
            'behavior': "understanding behavioral responses and actions taken",
            'patterns_beliefs': "exploring patterns, coping strategies, and core beliefs"
        }
        
        # Determine phase type
        if 'situation' in phase:
            phase_type = 'situation'
        elif 'thoughts' in phase:
            phase_type = 'thoughts'
        elif 'emotions' in phase:
            phase_type = 'emotions'
        elif 'behavior' in phase:
            phase_type = 'behavior'
        elif phase == 'patterns_beliefs':
            phase_type = 'patterns_beliefs'
        else:
            phase_type = 'introduction'
        
        context = phase_contexts.get(phase_type, "conducting CBT assessment")
        
        # Enhanced rephrase prompt with stronger emphasis on preserving bold formatting
        rephrase_prompt = f"""You are a CBT therapist creating natural question variations for a structured assessment.

Base question: "{base_question}"

Context: You are {context} during a CBT assessment.

CRITICAL FORMATTING RULES:
- The base question contains **bold text** that represents PERSONALIZED MEMORY RETRIEVAL
- You MUST preserve ALL **bold formatting markers** EXACTLY as they appear
- The bold text shows what the AI "remembers" about the user - this is crucial for the study
- DO NOT remove, modify, or rephrase any content inside **bold markers**
- Keep the exact same bold text but you can rephrase the surrounding words

Create a natural, conversational variation that:
- Maintains the exact same clinical purpose and information gathering goal
- Sounds warm, professional, and therapeutic
- Uses slightly different wording for non-bold text only
- PRESERVES every single **bold marker** and its content exactly
- Keeps the same level of specificity and detail
- Maintains appropriate therapeutic boundaries

EXAMPLE:
Original: "I remember you mentioned **eating late at night**. What specific thoughts went through your mind?"
Good rephrase: "I recall you sharing about **eating late at night**. What thoughts were you having in that moment?"
Bad rephrase: "I remember your nighttime eating habits. What thoughts occurred?" (bold markers removed!)

Provide ONLY the rephrased question, nothing else."""

        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {"role": "system", "content": rephrase_prompt}
                ]
            )
            
            rephrased = response['message']['content'].strip()
            
            # Clean up any quotation marks or extra formatting
            rephrased = rephrased.strip('"').strip("'").strip()
            
            # Check if bold formatting was preserved
            rephrased_bold_matches = re.findall(bold_pattern, rephrased)
            
            # If bold content was lost, restore it using post-processing
            if bold_matches and len(rephrased_bold_matches) < len(bold_matches):
                print(f"⚠️  Bold formatting partially lost during rephrasing. Attempting restoration...")
                
                # Try to restore bold formatting by finding the content in the rephrased text
                restored_text = rephrased
                for original_bold in bold_matches:
                    # Look for the content without bold markers in the rephrased text
                    if original_bold in restored_text and f"**{original_bold}**" not in restored_text:
                        # Replace the plain text with bold version
                        restored_text = restored_text.replace(original_bold, f"**{original_bold}**")
                        print(f"   Restored bold formatting for: {original_bold}")
                
                rephrased = restored_text
            
            # Final verification
            final_bold_matches = re.findall(bold_pattern, rephrased)
            if bold_matches and len(final_bold_matches) == 0:
                print(f"❌ Bold formatting completely lost. Using original question.")
                return base_question
            
            # Fallback to original if rephrasing fails or is too short
            if len(rephrased) < 20 or len(rephrased) > len(base_question) * 2.5:
                return base_question
                
            # Success - log if bold formatting was preserved
            if bold_matches and len(final_bold_matches) >= len(bold_matches):
                print(f"✅ Bold formatting preserved in rephrased question")
                
            return rephrased
            
        except Exception as e:
            print(f"Question rephrasing failed: {e}")
            return base_question
        
    def should_initiate_conversation(self):
        if not self.last_interaction:
            return True
        time_since_last = datetime.utcnow() - self.last_interaction
        return time_since_last > timedelta(hours=24)
        
    def get_current_phase(self):
        """Get current phase name"""
        if self.current_phase_index < len(self.phases):
            return self.phases[self.current_phase_index]
        return 'complete'
    
    def advance_phase(self):
        """Move to next phase"""
        self.current_phase_index += 1
        
    def _get_personalized_question(self, base_question, phase):
        """Create personalized questions that reference previous database information"""
        # Get previous data from database - include current user AND previous user (user_id - 1)
        from utils.cbt_database import Situation, AutomaticThought, Emotion, Behavior, BackgroundInfo
        
        current_user_id = self.memory.user.id
        previous_user_id = current_user_id - 1
        
        # Determine which user IDs to query (handle case where current user is first user)
        if current_user_id == 1:
            # First user - only query current user data
            user_ids_to_query = [current_user_id]
        else:
            # Later users - query current user AND previous user for personalization
            user_ids_to_query = [current_user_id, previous_user_id]
        
        # Get data from relevant users
        recent_situations = self.memory.session.query(Situation)\
            .filter(Situation.user_id.in_(user_ids_to_query))\
            .order_by(Situation.timestamp.desc())\
            .limit(5)\
            .all()
            
        recent_thoughts = self.memory.session.query(AutomaticThought)\
            .filter(AutomaticThought.user_id.in_(user_ids_to_query))\
            .order_by(AutomaticThought.timestamp.desc())\
            .limit(7)\
            .all()
            
        recent_emotions = self.memory.session.query(Emotion)\
            .filter(Emotion.user_id.in_(user_ids_to_query))\
            .order_by(Emotion.timestamp.desc())\
            .limit(7)\
            .all()
            
        recent_behaviors = self.memory.session.query(Behavior)\
            .filter(Behavior.user_id.in_(user_ids_to_query))\
            .order_by(Behavior.timestamp.desc())\
            .limit(7)\
            .all()
            
        # Get background info from relevant users if available
        background = self.memory.session.query(BackgroundInfo)\
            .filter(BackgroundInfo.user_id.in_(user_ids_to_query))\
            .order_by(BackgroundInfo.updated_at.desc())\
            .first()
        
        # Build MUCH MORE OBVIOUS personalization context with explicit memory language
        personalization_context = ""
        memory_references = []
        
        if phase == 'introduction' and background and background.chief_complaint:
            # Reference any previous concerns from database
            prev_concern = background.chief_complaint[:100]
            personalization_context = f"I remember from our previous conversations that you've dealt with **{prev_concern}**. "
            memory_references.append(f"Previous concern: {prev_concern}")
            
        elif phase == 'situation_1' and recent_situations:
            # Reference any similar past situations
            prev_situation = recent_situations[0].description[:80]
            personalization_context = f"I recall you previously shared about **{prev_situation}**. Building on what I know about your experiences, "
            memory_references.append(f"Past situation: {prev_situation}")
            
        elif phase == 'situation_2' and recent_situations:
            # Much more explicit memory reference
            prev_situation = recent_situations[0].description[:80]
            personalization_context = f"I'm looking back at what you told me earlier about **{prev_situation}**. From my memory of your experiences, "
            memory_references.append(f"Earlier situation: {prev_situation}")
            
        elif phase == 'situation_3' and len(recent_situations) >= 2:
            # Very obvious reference to multiple past situations
            prev_sit1 = recent_situations[1].description[:60]
            prev_sit2 = recent_situations[0].description[:60]
            personalization_context = f"I've been reflecting on the patterns I remember from your previous sharing - specifically **{prev_sit1}** and **{prev_sit2}**. Based on what's stored in my memory about your experiences, "
            memory_references.append(f"Pattern 1: {prev_sit1}")
            memory_references.append(f"Pattern 2: {prev_sit2}")
            
        elif 'thoughts' in phase and recent_thoughts:
            # Explicit memory retrieval language for thoughts
            situation_num = phase.split('_')[1]
            if situation_num == '1' and recent_thoughts:
                prev_thought = recent_thoughts[0].thought[:80]
                personalization_context = f"I remember you sharing thoughts like **'{prev_thought}'** in the past. Drawing from what I know about your thinking patterns, "
                memory_references.append(f"Past thought pattern: {prev_thought}")
            elif situation_num == '2' and len(recent_thoughts) >= 1:
                prev_thought = recent_thoughts[0].thought[:80]
                personalization_context = f"Looking back at my records, I recall you had thoughts about **'{prev_thought}'** in your previous situation. Connecting this to what I know about you, "
                memory_references.append(f"Previous thought: {prev_thought}")
            elif situation_num == '3' and len(recent_thoughts) >= 2:
                prev_thought1 = recent_thoughts[1].thought[:60]
                prev_thought2 = recent_thoughts[0].thought[:60]
                personalization_context = f"I've been tracking your thought patterns and I remember you expressing **'{prev_thought1}'** and **'{prev_thought2}'**. Based on these patterns I've observed about you, "
                memory_references.append(f"Thought pattern A: {prev_thought1}")
                memory_references.append(f"Thought pattern B: {prev_thought2}")
                
        elif 'emotions' in phase and recent_emotions:
            # Very explicit emotional memory references
            situation_num = phase.split('_')[1]
            if situation_num == '1' and recent_emotions:
                prev_emotion = recent_emotions[0].emotion[:80]
                personalization_context = f"I remember from our previous sessions that you experienced **'{prev_emotion}'**. Given what I know about your emotional responses, "
                memory_references.append(f"Past emotional response: {prev_emotion}")
            elif situation_num == '2' and len(recent_emotions) >= 1:
                prev_emotion = recent_emotions[0].emotion[:80]
                personalization_context = f"I'm recalling that you previously felt **'{prev_emotion}'**. From what's documented about your emotional patterns, "
                memory_references.append(f"Previous emotion: {prev_emotion}")
            elif situation_num == '3' and len(recent_emotions) >= 2:
                prev_em1 = recent_emotions[1].emotion[:60]
                prev_em2 = recent_emotions[0].emotion[:60]
                personalization_context = f"Looking through my memory of your emotional responses, I see you've experienced **'{prev_em1}'** and **'{prev_em2}'**. Based on this emotional history I have about you, "
                memory_references.append(f"Emotion A: {prev_em1}")
                memory_references.append(f"Emotion B: {prev_em2}")
                
        elif 'behavior' in phase and recent_behaviors:
            # Explicit behavioral memory references
            situation_num = phase.split('_')[1]
            if situation_num == '1' and recent_behaviors:
                prev_behavior = recent_behaviors[0].action[:80]
                personalization_context = f"I remember from your past sharing that you responded by **'{prev_behavior}'**. Considering what I know about your coping behaviors, "
                memory_references.append(f"Past behavior: {prev_behavior}")
            elif situation_num == '2' and len(recent_behaviors) >= 1:
                prev_behavior = recent_behaviors[0].action[:80]
                personalization_context = f"Looking back at my records, I recall you previously responded by **'{prev_behavior}'**. Drawing from what I've learned about your behavioral patterns, "
                memory_references.append(f"Previous behavior: {prev_behavior}")
            elif situation_num == '3' and len(recent_behaviors) >= 2:
                prev_beh1 = recent_behaviors[1].action[:60]
                prev_beh2 = recent_behaviors[0].action[:60]
                personalization_context = f"From my memory of your responses, I've documented that you've reacted by **'{prev_beh1}'** and **'{prev_beh2}'**. Based on these behavioral patterns I've observed in you, "
                memory_references.append(f"Behavior pattern A: {prev_beh1}")
                memory_references.append(f"Behavior pattern B: {prev_beh2}")
                
        elif phase == 'patterns_beliefs':
            # Comprehensive memory reference for final phase
            patterns = []
            memory_items = []
            
            if background and background.stress_response_patterns:
                patterns.append(f"**stress response patterns I've documented about you**")
                memory_items.append(f"Stress patterns: {background.stress_response_patterns[:60]}")
                
            if len(recent_situations) >= 2:
                categories = [s.description[:40] for s in recent_situations[:2]]
                patterns.append(f"**situations involving '{categories[0]}' and '{categories[1]}' that I remember you sharing**")
                memory_items.extend([f"Situation memory: {cat}" for cat in categories])
            
            if recent_thoughts:
                thought_sample = recent_thoughts[0].thought[:60]
                patterns.append(f"**thought patterns like '{thought_sample}' that I've recorded from you**")
                memory_items.append(f"Thought memory: {thought_sample}")
            
            if patterns:
                personalization_context = f"I've been reflecting on everything I remember about you - the {', '.join(patterns)} we've discussed together. Looking through my comprehensive memory of your experiences, "
                memory_references.extend(memory_items)
        
        # Combine personalization with base question
        if personalization_context and memory_references:
            # Terminal logging for researcher with detailed memory retrieval info
            print(f"🧠 STRONG PERSONALIZATION APPLIED - Phase: {phase}")
            print(f"   Memory Context: {personalization_context.strip()}")
            for ref in memory_references:
                print(f"   Database Reference: {ref}")
            print("   =" * 50)
            
            # Create the fully personalized question
            personalized_question = personalization_context + base_question.lower()
            # Capitalize first letter after context
            if len(personalized_question) > len(personalization_context):
                personalized_question = personalization_context + base_question[0].upper() + base_question[1:]
            
            # Store the memory references for later bold formatting
            self._current_memory_references = memory_references
            
            return personalized_question
        
        # No personalization available
        self._current_memory_references = []
        return base_question
        
    def get_contextual_starter(self):
        """Get the appropriate question for current phase with AI variation"""
        phase = self.get_current_phase()
        
        if phase == 'complete':
            return "Based on everything you've shared, let me reflect back what I've noticed about your patterns..."
        
        # Get base question
        base_question = self.base_questions.get(phase)
        if not base_question:
            return None
            
        # Add contextual prefixes for flow
        if phase == 'situation_2':
            base_question = f"Thank you for sharing that. {base_question}"
        elif phase == 'situation_3':
            base_question = f"I appreciate you sharing these experiences. {base_question}"
        elif phase == 'patterns_beliefs':
            base_question = f"Thank you for sharing those three situations with me. {base_question}"
        
        # Apply personalization (references to previous database information)
        personalized_question = self._get_personalized_question(base_question, phase)
        
        # CRITICAL FIX: Only use AI rephrasing if there's no bold formatting to preserve
        # Check if personalized question contains bold markers
        if '**' in personalized_question:
            # Personalized question with memory references - don't rephrase to preserve bold formatting
            return personalized_question
        else:
            # No personalization or no bold formatting - safe to rephrase
            varied_question = self._rephrase_question_with_ai(personalized_question, phase)
            return varied_question

    def get_contextual_starter_without_personalization(self):
        """Get pure CBT questions without any personalization/database references"""
        phase = self.get_current_phase()
        
        if phase == 'complete':
            return "Based on everything you've shared, let me reflect back what I've noticed about your patterns..."
        
        # Get base question without any personalization
        base_question = self.base_questions.get(phase)
        if not base_question:
            return None
            
        # Add contextual prefixes for flow
        if phase == 'situation_2':
            base_question = f"Thank you for sharing that. {base_question}"
        elif phase == 'situation_3':
            base_question = f"I appreciate you sharing these experiences. {base_question}"
        elif phase == 'patterns_beliefs':
            base_question = f"Thank you for sharing those three situations with me. {base_question}"
        
        # Use AI to create natural variation WITHOUT personalization
        varied_question = self._rephrase_question_with_ai(base_question, phase)
        
        return varied_question

    def save_response_data(self, user_input):
        """Save user response to appropriate database table based on current phase"""
        phase = self.get_current_phase()
        
        if phase == 'introduction':
            self._save_introduction_data(user_input)
            
        elif 'situation' in phase:
            situation_num = int(phase.split('_')[1])
            self._save_situation_data(user_input, situation_num)
            
        elif 'thoughts' in phase:
            situation_num = int(phase.split('_')[1])
            self._save_thoughts_data(user_input, situation_num)
            
        elif 'emotions' in phase:
            situation_num = int(phase.split('_')[1])
            self._save_emotions_data(user_input, situation_num)
            
        elif 'behavior' in phase:
            situation_num = int(phase.split('_')[1])
            self._save_behavior_data(user_input, situation_num)
            
        elif phase == 'patterns_beliefs':
            self._save_patterns_beliefs_data(user_input)
    
    def _save_introduction_data(self, user_input):
        """Save presenting concern from introduction"""
        from utils.cbt_database import BackgroundInfo
        
        # Extract name if mentioned
        self._extract_name_if_present(user_input)
        
        # Save as chief complaint
        background = self.memory.session.query(BackgroundInfo).filter_by(user_id=self.memory.user.id).first()
        if not background:
            background = BackgroundInfo(user_id=self.memory.user.id)
            self.memory.session.add(background)
        
        background.chief_complaint = user_input[:500]
        self.memory.session.commit()
    
    def _save_situation_data(self, user_input, situation_num):
        """Save situation description"""
        from utils.cbt_database import Situation
        
        situation = Situation(
            user_id=self.memory.user.id,
            description=user_input,
            category=f'assessment_situation_{situation_num}',
            context=f'CBT Assessment - Situation {situation_num}'
        )
        self.memory.session.add(situation)
        self.memory.session.commit()
        
        # Store for linking to subsequent data
        self.current_situation_data[f'situation_{situation_num}'] = situation
    
    def _save_thoughts_data(self, user_input, situation_num):
        """Save automatic thoughts linked to current situation"""
        from utils.cbt_database import AutomaticThought
        
        current_situation = self.current_situation_data.get(f'situation_{situation_num}')
        if not current_situation:
            # Fallback: get most recent situation
            from utils.cbt_database import Situation
            current_situation = self.memory.session.query(Situation).filter_by(
                user_id=self.memory.user.id).order_by(Situation.timestamp.desc()).first()
        
        if current_situation:
            thought = AutomaticThought(
                user_id=self.memory.user.id,
                situation_id=current_situation.id,
                thought=user_input
            )
            self.memory.session.add(thought)
            self.memory.session.commit()
    
    def _save_emotions_data(self, user_input, situation_num):
        """Save emotional and physical responses"""
        from utils.cbt_database import Emotion
        
        current_situation = self.current_situation_data.get(f'situation_{situation_num}')
        if not current_situation:
            from utils.cbt_database import Situation
            current_situation = self.memory.session.query(Situation).filter_by(
                user_id=self.memory.user.id).order_by(Situation.timestamp.desc()).first()
        
        if current_situation:
            # Parse emotions and physical symptoms from response
            emotion = Emotion(
                user_id=self.memory.user.id,
                situation_id=current_situation.id,
                emotion=user_input,
                intensity='medium',  # Default, could be enhanced with NLP
                context='CBT Assessment - Emotional and Physical Response'
            )
            self.memory.session.add(emotion)
            self.memory.session.commit()
            
            # Also save to background info for physical symptoms
            from utils.cbt_database import BackgroundInfo
            background = self.memory.session.query(BackgroundInfo).filter_by(user_id=self.memory.user.id).first()
            if background:
                if not background.major_symptoms_physiological:
                    background.major_symptoms_physiological = user_input[:500]
                else:
                    background.major_symptoms_physiological += f" | Situation {situation_num}: {user_input[:200]}"
                self.memory.session.commit()
    
    def _save_behavior_data(self, user_input, situation_num):
        """Save behavioral responses"""
        from utils.cbt_database import Behavior
        
        current_situation = self.current_situation_data.get(f'situation_{situation_num}')
        if not current_situation:
            from utils.cbt_database import Situation
            current_situation = self.memory.session.query(Situation).filter_by(
                user_id=self.memory.user.id).order_by(Situation.timestamp.desc()).first()
        
        if current_situation:
            behavior = Behavior(
                user_id=self.memory.user.id,
                situation_id=current_situation.id,
                action=user_input,
                behavior_type='assessment_response'
            )
            self.memory.session.add(behavior)
            self.memory.session.commit()
    
    def _save_patterns_beliefs_data(self, user_input):
        """Save patterns, coping strategies, and beliefs"""
        from utils.cbt_database import BackgroundInfo, CBTBeliefs
        
        # Save to background info for patterns and coping
        background = self.memory.session.query(BackgroundInfo).filter_by(user_id=self.memory.user.id).first()
        if not background:
            background = BackgroundInfo(user_id=self.memory.user.id)
            self.memory.session.add(background)
        
        background.stress_response_patterns = user_input[:500]
        background.coping_styles = user_input[:500]
        
        # Also create initial beliefs record
        beliefs = CBTBeliefs(
            user_id=self.memory.user.id,
            core_beliefs=[user_input],
            intermediate_beliefs=["Extracted from assessment"],
            coping_strategies=[user_input]
        )
        self.memory.session.add(beliefs)
        self.memory.session.commit()
    
    def _extract_name_if_present(self, user_input):
        """Try to extract name from introduction if mentioned"""
        # Look for common name patterns
        patterns = [
            r'(?:my name is|i am|i\'m|call me)\s+([a-zA-Z]+)',
            r'i\'m\s+([a-zA-Z]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                name = match.group(1).capitalize()
                if len(name) > 1:
                    self.user_name = name
                    return self.user_name
        return None

    def get_current_collection_phase(self):
        """Map current phase to collection type for compatibility"""
        phase = self.get_current_phase()
        
        if phase == 'introduction':
            return 'introduction'
        elif 'situation' in phase or 'thoughts' in phase or 'emotions' in phase or 'behavior' in phase:
            return 'cbt_assessment'
        elif phase == 'patterns_beliefs':
            return 'patterns_beliefs'
        else:
            return 'complete'

    def format_system_prompt(self, base_prompt):
        """Format system prompt based on current phase"""
        phase = self.get_current_phase()
        
        if phase == 'introduction':
            return f"""You are conducting a structured CBT assessment. You are collecting the user's presenting concern.

CRITICAL RULES:
- Give a brief, warm acknowledgment (15-20 words max)
- DO NOT ask questions - the system asks the next structured question
- Simply acknowledge their concern with empathy
- Example: "I hear that you're going through a difficult time" or "Thank you for sharing what's been troubling you"
- Be supportive but BRIEF"""
        
        elif phase in ['situation_1', 'situation_2', 'situation_3']:
            situation_num = phase.split('_')[1]
            return f"""You are in CBT assessment - collecting situation {situation_num} details.

CRITICAL RULES:
- Give a brief, encouraging acknowledgment (10-15 words max)
- DO NOT ask questions - the system asks the next structured question
- Simply acknowledge: "I can see that was a difficult situation" or "Thank you for sharing that specific example"
- BE BRIEF AND SUPPORTIVE"""
        
        elif phase in ['thoughts_1', 'thoughts_2', 'thoughts_3']:
            return f"""You are in CBT assessment - collecting automatic thoughts.

CRITICAL RULES:
- Give a brief acknowledgment of their thoughts (10-15 words max)
- DO NOT ask questions - the system asks the next question
- Example: "Those are some really powerful thoughts" or "I can understand how those thoughts affected you"
- BE BRIEF"""
        
        elif phase in ['emotions_1', 'emotions_2', 'emotions_3']:
            return f"""You are in CBT assessment - collecting emotional and physical responses.

CRITICAL RULES:
- Give a brief, validating acknowledgment (10-15 words max)
- DO NOT ask questions - the system asks the next question
- Example: "That sounds like an intense emotional and physical experience" or "I can hear how much that affected you"
- BE BRIEF AND VALIDATING"""
        
        elif phase in ['behavior_1', 'behavior_2', 'behavior_3']:
            return f"""You are in CBT assessment - collecting behavioral responses.

CRITICAL RULES:
- Give a brief acknowledgment (10-15 words max)
- DO NOT ask questions - the system asks the next question
- Example: "That's a very understandable response to those feelings" or "I can see how you tried to cope"
- BE BRIEF"""
        
        elif phase == 'patterns_beliefs':
            return f"""You are in CBT assessment - collecting patterns and beliefs.

CRITICAL RULES:
- Give a brief acknowledgment (15-20 words max)
- DO NOT ask questions - the system will move to analysis
- Example: "Thank you for sharing those insights about your patterns" or "That gives me a clear picture of how you typically respond"
- BE BRIEF AND PREPARE FOR ANALYSIS"""
        
        else:
            # Analysis or complete phase
            name_str = f"The user's name is {self.user_name}." if self.user_name else ""
            return f"""Generate a comprehensive CBT formulation based on all collected assessment data.

{name_str}

CRITICAL RULES:
- Start with warm acknowledgment of their sharing
- Present a structured formulation covering:
  * Presenting concerns
  * Common thought patterns across situations
  * Emotional and physical responses
  * Behavioral patterns
  * Identified core beliefs and coping strategies
- Use "I notice..." language
- Be insightful and therapeutic
- End with hope and validation of their self-awareness"""

    def save_cbt_beliefs(self, analysis_text):
        """Save the generated CBT formulation"""
        from utils.cbt_database import CBTBeliefs
        
        # Update or create beliefs with formulation
        existing_beliefs = self.memory.session.query(CBTBeliefs).filter_by(user_id=self.memory.user.id).first()
        
        if existing_beliefs:
            existing_beliefs.core_beliefs = [analysis_text]
            existing_beliefs.updated_at = datetime.utcnow()
        else:
            beliefs = CBTBeliefs(
                user_id=self.memory.user.id,
                core_beliefs=[analysis_text],
                intermediate_beliefs=["CBT Assessment Formulation"],
                coping_strategies=["Identified through structured assessment"]
            )
            self.memory.session.add(beliefs)
        
        self.memory.session.commit()

    def user_wants_to_skip(self, user_input):
        """Check if user wants to skip the current question"""
        skip_phrases = [
            'skip', 'don\'t want to', 'not comfortable', 'rather not', 
            'pass', 'next', 'don\'t feel like', 'uncomfortable',
            'prefer not to', 'don\'t want to share', 'too personal',
            'not ready', 'maybe later'
        ]
        
        user_lower = user_input.lower()
        return any(phrase in user_lower for phrase in skip_phrases)

    def generate_improved_cbt_formulation(self):
        """Generate CBT formulation with improved prompt that uses actual database data"""
        import ollama
        from utils.cbt_database import Situation, AutomaticThought, Emotion, Behavior, BackgroundInfo
        
        # Get all stored data for this user
        user_id = self.memory.user.id
        situations = self.memory.session.query(Situation).filter_by(user_id=user_id).all()
        thoughts = self.memory.session.query(AutomaticThought).filter_by(user_id=user_id).all()
        emotions = self.memory.session.query(Emotion).filter_by(user_id=user_id).all()
        behaviors = self.memory.session.query(Behavior).filter_by(user_id=user_id).all()
        background = self.memory.session.query(BackgroundInfo).filter_by(user_id=user_id).first()
        
        # Extract key topics dynamically from the stored data
        presenting_concern = background.chief_complaint if background and background.chief_complaint else "User concerns"
        
        # Extract key themes from situations
        situation_themes = []
        for situation in situations:
            desc = situation.description.lower()
            
            # Eating and body image
            if any(word in desc for word in ['eating', 'food', 'binge', 'purge', 'diet', 'weight', 'body', 'fat', 'skinny', 'appetite']):
                situation_themes.append('eating behavior')
            
            # Academic and work stress
            if any(word in desc for word in ['assignment', 'university', 'school', 'study', 'exam', 'grade', 'homework', 'class', 'teacher', 'professor']):
                situation_themes.append('academic stress')
            if any(word in desc for word in ['work', 'job', 'presentation', 'boss', 'colleague', 'office', 'career', 'deadline', 'meeting', 'interview']):
                situation_themes.append('work stress')
            
            # Family dynamics
            if any(word in desc for word in ['parent', 'family', 'fight', 'argument', 'mom', 'dad', 'mother', 'father', 'sibling', 'brother', 'sister']):
                situation_themes.append('family conflict')
            if any(word in desc for word in ['abuse', 'violence', 'hit', 'beat', 'violent', 'assault', 'domestic', 'yelling', 'screaming']):
                situation_themes.append('family violence')
            
            # Restriction and control behaviors
            if any(word in desc for word in ['fast', 'starve', 'restrict', 'control', 'punish', 'discipline']):
                situation_themes.append('restriction patterns')
            
            # Social and relationship issues
            if any(word in desc for word in ['social', 'friends', 'friendship', 'party', 'group', 'people', 'crowd', 'interaction']):
                situation_themes.append('social situations')
            if any(word in desc for word in ['relationship', 'partner', 'boyfriend', 'girlfriend', 'spouse', 'marriage', 'dating', 'breakup', 'divorce']):
                situation_themes.append('relationship issues')
            
            # Mental health conditions
            if any(word in desc for word in ['depressed', 'depression', 'sad', 'hopeless', 'empty', 'numb', 'suicidal', 'worthless']):
                situation_themes.append('depression and mood')
            if any(word in desc for word in ['anxiety', 'anxious', 'panic', 'worry', 'nervous', 'fear', 'scared', 'phobia', 'stress']):
                situation_themes.append('anxiety and fear')
            
            # Trauma and difficult experiences
            if any(word in desc for word in ['trauma', 'ptsd', 'flashback', 'nightmare', 'triggered', 'assault', 'rape', 'abuse']):
                situation_themes.append('trauma responses')
            if any(word in desc for word in ['death', 'died', 'funeral', 'grief', 'loss', 'mourning', 'bereavement']):
                situation_themes.append('grief and loss')
            
            # Substance use
            if any(word in desc for word in ['drink', 'alcohol', 'drunk', 'drugs', 'smoking', 'high', 'substance', 'addiction']):
                situation_themes.append('substance use')
            
            # Self-harm and dangerous behaviors
            if any(word in desc for word in ['cut', 'cutting', 'hurt', 'harm', 'self-harm', 'burn', 'scratch', 'pick']):
                situation_themes.append('self-harm behaviors')
            
            # Identity and self-concept
            if any(word in desc for word in ['identity', 'who am i', 'myself', 'self-worth', 'confidence', 'self-esteem', 'inadequate']):
                situation_themes.append('identity struggles')
            
            # Perfectionism and control
            if any(word in desc for word in ['perfect', 'perfectionist', 'mistake', 'failure', 'not good enough', 'standards', 'criticism']):
                situation_themes.append('perfectionism')
            
            # Sleep and daily functioning
            if any(word in desc for word in ['sleep', 'insomnia', 'tired', 'exhausted', 'wake up', 'bed', 'sleeping']):
                situation_themes.append('sleep difficulties')
            
            # Health and medical issues
            if any(word in desc for word in ['sick', 'illness', 'medical', 'doctor', 'hospital', 'pain', 'health', 'symptoms']):
                situation_themes.append('health concerns')
        
        # Remove duplicates and create theme string
        unique_themes = list(set(situation_themes))
        themes_text = ', '.join(unique_themes) if unique_themes else 'various life situations'
        
        # Extract key thought patterns
        thought_patterns = []
        for thought in thoughts:
            thought_text = thought.thought.lower()
            if any(word in thought_text for word in ['judge', 'judging', 'judgment']):
                thought_patterns.append('fear of judgment')
            if any(word in thought_text for word in ['comfort', 'better', 'feel']):
                thought_patterns.append('seeking comfort through behavior')
            if any(word in thought_text for word in ['overwhelm', 'too much', "can't"]):
                thought_patterns.append('feeling overwhelmed')
            if any(word in thought_text for word in ['repent', 'guilty', 'shame']):
                thought_patterns.append('guilt and shame')
        
        unique_thought_patterns = list(set(thought_patterns))
        thought_patterns_text = ', '.join(unique_thought_patterns) if unique_thought_patterns else 'various automatic thoughts'
        
        # Create comprehensive context for formulation
        formulation_context = f"""
Based on our structured CBT assessment, here is the collected information:

PRESENTING CONCERN:
{presenting_concern}

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
        
        # Create improved system prompt that forces AI to use actual data
        improved_system_prompt = f"""You are a CBT therapist creating a comprehensive formulation.

CRITICAL INSTRUCTIONS:
- Use ONLY the data provided in the user message - do NOT add generic examples
- Focus on the ACTUAL situations, thoughts, emotions, and behaviors described
- DO NOT use generic CBT templates or create fictional examples
- The user's specific presenting concern is: {presenting_concern}
- Reference the exact situations involving: {themes_text}
- Address the specific thought patterns: {thought_patterns_text}
- DO NOT mention anything not specifically discussed in the provided data
- Base your formulation entirely on what the user actually shared

FORMAT YOUR RESPONSE WITH MARKDOWN:
- Use **bold headers** for section titles
- Use bullet points (*) for lists
- Use proper paragraphs with line breaks
- Structure it professionally with clear sections

REQUIRED SECTIONS:
1. **Presenting Concerns** - What brought them here
2. **Situational Triggers** - The specific situations they described
3. **Maladaptive Thoughts** - The actual thought patterns they shared
4. **Emotional and Physical Responses** - Their specific emotional/physical reactions
5. **Behavioral Patterns** - The actual behaviors they described
6. **Potential Pathways for Exploration** - 3 specific, actionable areas for therapeutic work based ONLY on their actual data

The final section should provide 3 concrete therapeutic directions that directly address their specific patterns, situations, and concerns as documented in the assessment.

Create a CBT formulation that directly addresses the user's actual experiences as documented in the assessment data."""

        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {"role": "system", "content": improved_system_prompt},
                    {"role": "user", "content": formulation_context}
                ]
            )
            
            formulation = response['message']['content'].strip()
            
            # Clean up any quotation marks for consistency
            formulation = formulation.strip('"').strip("'").strip()
            
            # Save the formulation
            self.save_cbt_beliefs(formulation)
            
            return formulation
            
        except Exception as e:
            print(f"Improved formulation generation failed: {e}")
            return "CBT formulation could not be generated at this time." 