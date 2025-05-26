import json
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

class CBTMemoryManager:
    def __init__(self, session, user):
        self.session = session
        self.user = user
        
    def add_situation(self, description, context="", category="general"):
        """Add a situation to the database"""
        from utils.cbt_database import Situation
        situation = Situation(
            user_id=self.user.id,
            description=description,
            context=context,
            category=category
        )
        self.session.add(situation)
        self.session.commit()
        return situation
        
    def add_automatic_thought(self, thought, situation=None):
        """Add an automatic thought linked to a situation"""
        from utils.cbt_database import AutomaticThought
        automatic_thought = AutomaticThought(
            user_id=self.user.id,
            situation_id=situation.id if situation else None,
            thought=thought
        )
        self.session.add(automatic_thought)
        self.session.commit()
        return automatic_thought
        
    def add_thought_meaning(self, meaning, automatic_thought=None, user_inferred_core_belief=""):
        """Add meaning interpretation for an automatic thought"""
        from utils.cbt_database import ThoughtMeaning
        thought_meaning = ThoughtMeaning(
            user_id=self.user.id,
            automatic_thought_id=automatic_thought.id if automatic_thought else None,
            meaning=meaning,
            user_inferred_core_belief=user_inferred_core_belief
        )
        self.session.add(thought_meaning)
        self.session.commit()
        return thought_meaning
        
    def add_emotion(self, emotion, intensity, context="", situation=None, automatic_thought=None):
        """Add an emotion linked to situation and/or automatic thought"""
        from utils.cbt_database import Emotion
        emotion_obj = Emotion(
            user_id=self.user.id,
            situation_id=situation.id if situation else None,
            automatic_thought_id=automatic_thought.id if automatic_thought else None,
            emotion=emotion,
            intensity=intensity,
            context=context
        )
        self.session.add(emotion_obj)
        self.session.commit()
        return emotion_obj
        
    def add_behavior(self, action, behavior_type="general", situation=None, automatic_thought=None):
        """Add a behavior linked to situation and/or automatic thought"""
        from utils.cbt_database import Behavior
        behavior = Behavior(
            user_id=self.user.id,
            situation_id=situation.id if situation else None,
            automatic_thought_id=automatic_thought.id if automatic_thought else None,
            action=action,
            behavior_type=behavior_type
        )
        self.session.add(behavior)
        self.session.commit()
        return behavior
        
    def update_beliefs(self, beliefs_data):
        """Update or create beliefs (core beliefs, intermediate beliefs, coping strategies)"""
        from utils.cbt_database import CBTBeliefs
        
        # Check if user already has beliefs record
        existing_beliefs = self.session.query(CBTBeliefs).filter_by(user_id=self.user.id).first()
        
        if existing_beliefs:
            # Merge new beliefs with existing ones
            current_core = existing_beliefs.core_beliefs or []
            current_intermediate = existing_beliefs.intermediate_beliefs or []
            current_coping = existing_beliefs.coping_strategies or []
            
            # Add new beliefs if they don't already exist
            for belief in beliefs_data.get('core_beliefs', []):
                if belief and belief not in current_core:
                    current_core.append(belief)
                    
            for belief in beliefs_data.get('intermediate_beliefs', []):
                if belief and belief not in current_intermediate:
                    current_intermediate.append(belief)
                    
            for strategy in beliefs_data.get('coping_strategies', []):
                if strategy and strategy not in current_coping:
                    current_coping.append(strategy)
            
            existing_beliefs.core_beliefs = current_core
            existing_beliefs.intermediate_beliefs = current_intermediate
            existing_beliefs.coping_strategies = current_coping
            existing_beliefs.updated_at = datetime.utcnow()
            
        else:
            # Create new beliefs record
            beliefs = CBTBeliefs(
                user_id=self.user.id,
                core_beliefs=beliefs_data.get('core_beliefs', []),
                intermediate_beliefs=beliefs_data.get('intermediate_beliefs', []),
                coping_strategies=beliefs_data.get('coping_strategies', [])
            )
            self.session.add(beliefs)
            
        self.session.commit()
        
    def update_background_info(self, background_data):
        """Update or create background information for case formulation"""
        from utils.cbt_database import BackgroundInfo
        
        existing_background = self.session.query(BackgroundInfo).filter_by(user_id=self.user.id).first()
        
        if existing_background:
            # Update existing background info
            identifying_info = background_data.get('identifying_info', {})
            cbt_patterns = background_data.get('cbt_patterns', {})
            functioning = background_data.get('functioning', {})
            history = background_data.get('history', {})
            
            # Update only non-empty fields
            for field, value in identifying_info.items():
                if value:
                    setattr(existing_background, field, value)
                    
            for field, value in cbt_patterns.items():
                if value:
                    setattr(existing_background, field, value)
                    
            for field, value in functioning.items():
                if value:
                    setattr(existing_background, field, value)
                    
            for field, value in history.items():
                if value:
                    setattr(existing_background, field, value)
                    
            existing_background.updated_at = datetime.utcnow()
            
        else:
            # Create new background info
            identifying_info = background_data.get('identifying_info', {})
            cbt_patterns = background_data.get('cbt_patterns', {})
            functioning = background_data.get('functioning', {})
            history = background_data.get('history', {})
            
            background = BackgroundInfo(
                user_id=self.user.id,
                **identifying_info,
                **cbt_patterns,
                **functioning,
                **history
            )
            self.session.add(background)
            
        self.session.commit()
        
    def get_recent_situations(self, limit=10):
        """Get recent situations for the user"""
        from utils.cbt_database import Situation
        return self.session.query(Situation)\
            .filter_by(user_id=self.user.id)\
            .order_by(Situation.timestamp.desc())\
            .limit(limit)\
            .all()
            
    def get_recent_automatic_thoughts(self, limit=10):
        """Get recent automatic thoughts for the user"""
        from utils.cbt_database import AutomaticThought
        return self.session.query(AutomaticThought)\
            .filter_by(user_id=self.user.id)\
            .order_by(AutomaticThought.timestamp.desc())\
            .limit(limit)\
            .all()
            
    def get_recent_emotions(self, limit=10):
        """Get recent emotions for the user"""
        from utils.cbt_database import Emotion
        return self.session.query(Emotion)\
            .filter_by(user_id=self.user.id)\
            .order_by(Emotion.timestamp.desc())\
            .limit(limit)\
            .all()
            
    def get_recent_behaviors(self, limit=10):
        """Get recent behaviors for the user"""
        from utils.cbt_database import Behavior
        return self.session.query(Behavior)\
            .filter_by(user_id=self.user.id)\
            .order_by(Behavior.timestamp.desc())\
            .limit(limit)\
            .all()
            
    def get_beliefs(self):
        """Get user's beliefs and coping strategies"""
        from utils.cbt_database import CBTBeliefs
        return self.session.query(CBTBeliefs).filter_by(user_id=self.user.id).first()
        
    def get_background_info(self):
        """Get user's background information"""
        from utils.cbt_database import BackgroundInfo
        return self.session.query(BackgroundInfo).filter_by(user_id=self.user.id).first()
        
    def get_context_for_conversation(self):
        """Build context for CBT-informed conversations"""
        recent_situations = self.get_recent_situations(5)
        recent_thoughts = self.get_recent_automatic_thoughts(5)
        recent_emotions = self.get_recent_emotions(5)
        recent_behaviors = self.get_recent_behaviors(5)
        beliefs = self.get_beliefs()
        background = self.get_background_info()
        
        context = {
            'recent_situations': [
                {
                    'description': situation.description,
                    'context': situation.context,
                    'category': situation.category,
                    'timestamp': situation.timestamp.isoformat()
                } for situation in recent_situations
            ],
            'recent_automatic_thoughts': [
                {
                    'thought': thought.thought,
                    'situation_description': thought.situation.description if thought.situation else None,
                    'timestamp': thought.timestamp.isoformat()
                } for thought in recent_thoughts
            ],
            'recent_emotions': [
                {
                    'emotion': emotion.emotion,
                    'intensity': emotion.intensity,
                    'context': emotion.context,
                    'linked_situation': emotion.situation.description if emotion.situation else None,
                    'linked_thought': emotion.automatic_thought.thought if emotion.automatic_thought else None,
                    'timestamp': emotion.timestamp.isoformat()
                } for emotion in recent_emotions
            ],
            'recent_behaviors': [
                {
                    'action': behavior.action,
                    'behavior_type': behavior.behavior_type,
                    'linked_situation': behavior.situation.description if behavior.situation else None,
                    'linked_thought': behavior.automatic_thought.thought if behavior.automatic_thought else None,
                    'timestamp': behavior.timestamp.isoformat()
                } for behavior in recent_behaviors
            ]
        }
        
        if beliefs:
            context['beliefs'] = {
                'core_beliefs': beliefs.core_beliefs or [],
                'intermediate_beliefs': beliefs.intermediate_beliefs or [],
                'coping_strategies': beliefs.coping_strategies or []
            }
            
        if background:
            context['background'] = {
                'age_range': background.age_range,
                'employment_status': background.employment_status,
                'stress_response_patterns': background.stress_response_patterns,
                'cognitive_tendencies': background.cognitive_tendencies,
                'coping_styles': background.coping_styles,
                'chief_complaint': background.chief_complaint,
                'strengths_and_resources': background.strengths_and_resources
            }
        
        context['user_identifier'] = self.user.identifier
        return context
        
    def get_case_formulation_data(self):
        """Get comprehensive data for CBT case formulation"""
        background = self.get_background_info()
        beliefs = self.get_beliefs()
        all_situations = self.get_recent_situations(50)  # Get more for case formulation
        all_thoughts = self.get_recent_automatic_thoughts(50)
        all_emotions = self.get_recent_emotions(50)
        all_behaviors = self.get_recent_behaviors(50)
        
        return {
            'background_info': background,
            'beliefs_and_strategies': beliefs,
            'situations': all_situations,
            'automatic_thoughts': all_thoughts,
            'emotions': all_emotions,
            'behaviors': all_behaviors
        }
    
    def get_recent_conversations(self, limit=5):
        """Get recent conversations for compatibility with ConversationManager"""
        from utils.cbt_database import Conversation
        return self.session.query(Conversation)\
            .filter_by(user_id=self.user.id)\
            .order_by(Conversation.timestamp.desc())\
            .limit(limit)\
            .all()
    
    def get_recent_preferences(self):
        """Get user preferences from background info for compatibility"""
        background = self.get_background_info()
        if background:
            # Extract preference-like information from background
            preferences = []
            if background.strengths_and_resources:
                preferences.append({'type': 'strengths', 'content': background.strengths_and_resources})
            if background.coping_styles:
                preferences.append({'type': 'coping', 'content': background.coping_styles})
            return preferences
        return []
    
    def get_active_events(self):
        """Get recent situations as events for compatibility"""
        recent_situations = self.get_recent_situations(5)
        return [{'description': situation.description, 'context': situation.context} 
                for situation in recent_situations] 