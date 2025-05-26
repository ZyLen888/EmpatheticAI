#!/usr/bin/env python3

"""
Test script to demonstrate AI question rephrasing for CBT assessment
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cbt_database import init_cbt_db, get_or_create_user
from utils.cbt_memory import CBTMemoryManager
from utils.conversation_manager import ConversationManager
import uuid

def test_question_variations():
    print("🔄 Testing AI Question Rephrasing\n")
    
    # Initialize components
    session = init_cbt_db()
    user = get_or_create_user(session, str(uuid.uuid4()))
    cbt_memory = CBTMemoryManager(session, user)
    conversation_manager = ConversationManager(cbt_memory)
    
    # Test different phases
    test_phases = [
        'introduction',
        'situation_1', 
        'thoughts_1',
        'emotions_1',
        'behavior_1',
        'situation_2',
        'patterns_beliefs'
    ]
    
    for phase in test_phases:
        print(f"🔸 Phase: {phase}")
        base_question = conversation_manager.base_questions.get(phase, "Test question")
        print(f"   Base: {base_question}")
        
        # Generate 2 variations
        for i in range(2):
            varied = conversation_manager._rephrase_question_with_ai(base_question, phase)
            print(f"   Var{i+1}: {varied}")
        
        print()

if __name__ == "__main__":
    test_question_variations() 