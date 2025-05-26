from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
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
    situations = relationship("Situation", back_populates="user")
    automatic_thoughts = relationship("AutomaticThought", back_populates="user")
    thought_meanings = relationship("ThoughtMeaning", back_populates="user")
    emotions = relationship("Emotion", back_populates="user")
    behaviors = relationship("Behavior", back_populates="user")
    background_info = relationship("BackgroundInfo", back_populates="user", uselist=False)

class BackgroundInfo(Base):
    """Stores background information for context-informed sessions"""
    __tablename__ = 'background_info'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Identifying information (excluding sensitive data)
    age_range = Column(String(20))  # e.g., "20-30", "30-40"
    gender_identity = Column(String(50))
    cultural_heritage = Column(String(100))
    religious_orientation = Column(String(100))
    living_environment = Column(String(100))  # e.g., "urban", "suburban", "with family"
    employment_status = Column(String(100))
    
    # CBT-relevant patterns
    stress_response_patterns = Column(Text)
    cognitive_tendencies = Column(Text)
    coping_styles = Column(Text)
    recurring_thought_patterns = Column(Text)
    
    # Best functioning and strengths
    strengths_and_resources = Column(Text)
    best_lifetime_functioning = Column(Text)
    
    # Current functioning
    chief_complaint = Column(Text)
    major_symptoms_emotional = Column(Text)
    major_symptoms_cognitive = Column(Text)
    major_symptoms_behavioral = Column(Text)
    major_symptoms_physiological = Column(Text)
    
    # History (non-medical)
    educational_background = Column(Text)
    vocational_history = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="background_info")

class Situation(Base):
    """Specific contexts where thoughts/feelings occurred"""
    __tablename__ = 'situations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(Text)
    context = Column(Text)
    category = Column(String(50))  # work, personal, social, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="situations")
    automatic_thoughts = relationship("AutomaticThought", back_populates="situation")
    emotions = relationship("Emotion", back_populates="situation")
    behaviors = relationship("Behavior", back_populates="situation")

class AutomaticThought(Base):
    """Immediate thoughts that occurred in situations"""
    __tablename__ = 'automatic_thoughts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    situation_id = Column(Integer, ForeignKey('situations.id'))
    thought = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="automatic_thoughts")
    situation = relationship("Situation", back_populates="automatic_thoughts")
    meanings = relationship("ThoughtMeaning", back_populates="automatic_thought")
    emotions = relationship("Emotion", back_populates="automatic_thought")

class ThoughtMeaning(Base):
    """Deeper interpretations and meanings of automatic thoughts"""
    __tablename__ = 'thought_meanings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    automatic_thought_id = Column(Integer, ForeignKey('automatic_thoughts.id'))
    meaning = Column(Text)
    user_inferred_core_belief = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="thought_meanings")
    automatic_thought = relationship("AutomaticThought", back_populates="meanings")

class Emotion(Base):
    """Emotions experienced during situations"""
    __tablename__ = 'emotions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    situation_id = Column(Integer, ForeignKey('situations.id'), nullable=True)
    automatic_thought_id = Column(Integer, ForeignKey('automatic_thoughts.id'), nullable=True)
    emotion = Column(String(50))
    intensity = Column(String(20))  # low, medium, high
    context = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="emotions")
    situation = relationship("Situation", back_populates="emotions")
    automatic_thought = relationship("AutomaticThought", back_populates="emotions")

class Behavior(Base):
    """Actions taken or avoided in response to thoughts/emotions"""
    __tablename__ = 'behaviors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    situation_id = Column(Integer, ForeignKey('situations.id'), nullable=True)
    automatic_thought_id = Column(Integer, ForeignKey('automatic_thoughts.id'), nullable=True)
    action = Column(Text)
    behavior_type = Column(String(50))  # avoidance, assertive, passive, help-seeking, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="behaviors")
    situation = relationship("Situation", back_populates="behaviors")
    automatic_thought = relationship("AutomaticThought")

class CBTBeliefs(Base):
    """Core beliefs, intermediate beliefs, and coping strategies"""
    __tablename__ = 'cbt_beliefs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    core_beliefs = Column(JSON)  # List of core beliefs
    intermediate_beliefs = Column(JSON)  # List of intermediate beliefs/rules
    coping_strategies = Column(JSON)  # List of coping strategies
    timestamp = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(Text)
    response = Column(Text)
    context = Column(JSON)
    session_type = Column(String(20))  # with_context or without_context
    
    user = relationship("User", back_populates="conversations")

def init_cbt_db():
    engine = create_engine('sqlite:///cbt_chatbot.db')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def get_or_create_user(session, identifier):
    user = session.query(User).filter_by(identifier=identifier).first()
    if not user:
        user = User(identifier=identifier)
        session.add(user)
        session.commit()
    return user

def save_conversation(session, user_id, message, response, context, session_type="without_context"):
    if isinstance(context, str):
        try:
            context = json.loads(context)
        except:
            context = {}
            
    conversation = Conversation(
        user_id=user_id,
        message=message,
        response=response,
        context=context,
        session_type=session_type
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
    """Look up a user by their display name in previous conversations."""
    return session.query(User).filter(User.identifier.like(f"%{name}%")).first() 