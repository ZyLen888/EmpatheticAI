import json
from datetime import datetime, timedelta
from sqlalchemy import and_

class MemoryManager:
    def __init__(self, session, user):
        self.session = session
        self.user = user
        
    def add_preference(self, category, item, sentiment):
        from utils.database import Preference
        preference = Preference(
            user_id=self.user.id,
            category=category,
            item=item,
            sentiment=sentiment
        )
        self.session.add(preference)
        self.session.commit()
        return preference
        
    def add_event(self, title, date, importance="medium"):
        from utils.database import Event
        event = Event(
            user_id=self.user.id,
            title=title,
            date=date,
            importance=importance,
            status="upcoming" if date > datetime.utcnow() else "past"
        )
        self.session.add(event)
        self.session.commit()
        return event
        
    def add_concern(self, type, description, urgency="medium"):
        from utils.database import Concern
        concern = Concern(
            user_id=self.user.id,
            type=type,
            description=description,
            urgency=urgency,
            status="active"
        )
        self.session.add(concern)
        self.session.commit()
        return concern
        
    def add_emotion(self, emotion, intensity, context, related_event=None, related_concern=None):
        from utils.database import Emotion
        emotion_obj = Emotion(
            user_id=self.user.id,
            emotion=emotion,
            intensity=intensity,
            context=context
        )
        
        if related_event:
            emotion_obj.event_id = related_event.id
            # Also update the event's primary emotion if not set
            if not related_event.primary_emotion_id:
                related_event.primary_emotion_id = emotion_obj.id
                self.session.add(related_event)
            
        if related_concern:
            emotion_obj.concern_id = related_concern.id
            # Also update the concern's primary emotion if not set
            if not related_concern.primary_emotion_id:
                related_concern.primary_emotion_id = emotion_obj.id
                self.session.add(related_concern)
            
        self.session.add(emotion_obj)
        self.session.commit()
        return emotion_obj
        
    def get_recent_preferences(self, limit=5):
        from utils.database import Preference
        return self.session.query(Preference)\
            .filter(Preference.user_id == self.user.id)\
            .order_by(Preference.mentioned_at.desc())\
            .limit(limit)\
            .all()
        
    def get_active_events(self, days_window=7):
        from utils.database import Event
        cutoff_date = datetime.utcnow() - timedelta(days=days_window)
        return self.session.query(Event).filter(
            and_(
                Event.user_id == self.user.id,
                Event.date >= cutoff_date
            )
        ).order_by(Event.date).all()
        
    def get_active_concerns(self):
        from utils.database import Concern
        return self.session.query(Concern).filter(
            and_(
                Concern.user_id == self.user.id,
                Concern.status == "active"
            )
        ).order_by(Concern.mentioned_at.desc()).all()
        
    def get_recent_emotions(self, limit=5):
        from utils.database import Emotion
        return self.session.query(Emotion)\
            .filter(Emotion.user_id == self.user.id)\
            .order_by(Emotion.mentioned_at.desc())\
            .limit(limit)\
            .all()
        
    def get_context_for_conversation(self):
        active_events = self.get_active_events()
        active_concerns = self.get_active_concerns()
        recent_emotions = self.get_recent_emotions()
        recent_preferences = self.get_recent_preferences()
        
        context = {
            'preferences': [
                {
                    'category': pref.category,
                    'item': pref.item,
                    'sentiment': pref.sentiment
                } for pref in recent_preferences
            ],
            'active_events': [
                {
                    'title': event.title,
                    'date': event.date.isoformat(),
                    'importance': event.importance,
                    'primary_emotion': (
                        {'emotion': event.primary_emotion.emotion, 'intensity': event.primary_emotion.intensity}
                        if event.primary_emotion else None
                    )
                } for event in active_events
            ],
            'active_concerns': [
                {
                    'type': concern.type,
                    'description': concern.description,
                    'urgency': concern.urgency,
                    'primary_emotion': (
                        {'emotion': concern.primary_emotion.emotion, 'intensity': concern.primary_emotion.intensity}
                        if concern.primary_emotion else None
                    )
                } for concern in active_concerns
            ],
            'recent_emotions': [
                {
                    'emotion': emotion.emotion,
                    'intensity': emotion.intensity,
                    'context': emotion.context,
                    'related_event': emotion.related_event.title if emotion.related_event else None,
                    'related_concern': emotion.related_concern.description if emotion.related_concern else None
                } for emotion in recent_emotions
            ],
            'user_identifier': self.user.identifier
        }
        return context

    def get_recent_conversations(self, limit=5):
        """Get recent conversations for the current user."""
        from utils.database import get_user_history
        return get_user_history(self.session, self.user.id, limit=limit) 