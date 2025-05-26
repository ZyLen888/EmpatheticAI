from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    events = relationship("Event", back_populates="user")
    concerns = relationship("Concern", back_populates="user")
    emotions = relationship("Emotion", back_populates="user")
    preferences = relationship("Preference", back_populates="user")

class Preference(Base):
    __tablename__ = 'preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    category = Column(String(50))  # e.g., food, music, activity
    item = Column(String(200))  # what they like/dislike
    sentiment = Column(String(20))  # like, dislike, love, hate
    mentioned_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="preferences")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(200))
    date = Column(DateTime)
    importance = Column(String(20))  # low, medium, high
    status = Column(String(20))  # upcoming, past, ongoing
    mentioned_at = Column(DateTime, default=datetime.utcnow)
    
    # For primary emotion related to this event
    primary_emotion_id = Column(Integer, ForeignKey('emotions.id'), nullable=True)
    # For related concern
    concern_id = Column(Integer, ForeignKey('concerns.id'), nullable=True)
    
    user = relationship("User", back_populates="events")
    primary_emotion = relationship("Emotion", foreign_keys=[primary_emotion_id])
    # Events can have multiple related emotions
    related_emotions = relationship("Emotion", back_populates="related_event", 
                                   foreign_keys="Emotion.event_id")
    # Relationship with concern
    related_concern = relationship("Concern", back_populates="related_events")

class Concern(Base):
    __tablename__ = 'concerns'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(String(50))  # work, personal, health, education
    description = Column(Text)
    urgency = Column(String(20))  # low, medium, high
    status = Column(String(20))  # active, resolved
    mentioned_at = Column(DateTime, default=datetime.utcnow)
    
    # For primary emotion related to this concern
    primary_emotion_id = Column(Integer, ForeignKey('emotions.id'), nullable=True)
    
    user = relationship("User", back_populates="concerns")
    primary_emotion = relationship("Emotion", foreign_keys=[primary_emotion_id])
    # Concerns can have multiple related emotions
    related_emotions = relationship("Emotion", back_populates="related_concern", 
                                   foreign_keys="Emotion.concern_id")
    # Back reference to related events
    related_events = relationship("Event", back_populates="related_concern")

class Emotion(Base):
    __tablename__ = 'emotions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    emotion = Column(String(50))  # happy, sad, anxious, etc.
    intensity = Column(String(20))  # low, medium, high
    context = Column(Text)  # Brief description of what triggered the emotion
    mentioned_at = Column(DateTime, default=datetime.utcnow)
    
    # Direct links to a single event or concern (can be null)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    concern_id = Column(Integer, ForeignKey('concerns.id'), nullable=True)
    
    user = relationship("User", back_populates="emotions")
    related_event = relationship("Event", back_populates="related_emotions", 
                                foreign_keys=[event_id])
    related_concern = relationship("Concern", back_populates="related_emotions", 
                                  foreign_keys=[concern_id])

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(Text)
    response = Column(Text)
    context = Column(JSON)
    
    # Optional links to mentioned entities
    emotion_id = Column(Integer, ForeignKey('emotions.id'), nullable=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    concern_id = Column(Integer, ForeignKey('concerns.id'), nullable=True)
    
    user = relationship("User", back_populates="conversations")
    emotion = relationship("Emotion")
    event = relationship("Event")
    concern = relationship("Concern")

def init_db():
    engine = create_engine('sqlite:///chatbot.db')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def get_or_create_user(session, identifier):
    user = session.query(User).filter_by(identifier=identifier).first()
    if not user:
        user = User(identifier=identifier)
        session.add(user)
        session.commit()
    return user

def save_conversation(session, user_id, message, response, context):
    if isinstance(context, str):
        try:
            context = json.loads(context)
        except:
            context = {}
            
    conversation = Conversation(
        user_id=user_id,
        message=message,
        response=response,
        context=context
    )
    session.add(conversation)
    session.commit()
    return conversation

def get_user_history(session, user_id, limit=5):
    return session.query(Conversation)\
        .filter_by(user_id=user_id)\
        .order_by(Conversation.timestamp.desc())\
        .limit(limit)\
        .all()

def get_user_by_name(session, name):
    """
    Look up a user by their display name in previous conversations.
    Returns None if no user is found.
    """
    return session.query(User).filter(User.identifier.like(f"%{name}%")).first() 