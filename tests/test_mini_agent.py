"""
Test script for Mini Chat Agent functionality
"""

import logging
from pathlib import Path
import sys
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.mini_chat_agent import MiniChatAgent, InteractiveChatSession
from src.utils.transcription_utils import list_transcriptions


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_mini_chat_agent():
    """Test mini chat agent with sample questions"""
    
    print("🧪 Testing Mini Chat Agent")
    print("=" * 50)
    
    # Check if we have mock data
    mock_file = Path("mock_supabase_data.json")
    if not mock_file.exists():
        print("❌ No mock data found. Run embedding test first.")
        return
    
    # Initialize agent
    agent = MiniChatAgent()
    
    # Test questions
    test_questions = [
        "Was ist das Thema des Videos?",
        "Wer spricht in dem Video?",
        "Was wird über Performance gesagt?",
        "Welche wichtigen Punkte werden erwähnt?"
    ]
    
    print(f"📝 Testing {len(test_questions)} sample questions...")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 Question {i}: {question}")
        
        try:
            response = agent.ask_question(question)
            
            print(f"🤖 Answer: {response['answer']}")
            print(f"📊 Confidence: {response['confidence']}")
            print(f"📚 Sources: {response['context_chunks_used']}/{response['total_chunks_found']}")
            
            if response['sources']:
                print(f"📝 First source: {response['sources'][0]['text'][:100]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Show conversation history
    print(f"\n📝 Conversation History:")
    history = agent.get_conversation_history()
    for i, exchange in enumerate(history, 1):
        print(f"{i}. Q: {exchange['question']}")
        print(f"   A: {exchange['answer'][:100]}...")


def test_mini_chat_agent_with_real_data():
    """Test mini chat agent with real Supabase data"""
    
    print("🧪 Testing Mini Chat Agent with Real Supabase Data")
    print("=" * 60)
    
    # Initialize agent
    agent = MiniChatAgent()
    
    # Test questions
    test_questions = [
        "Was ist das Thema des Videos?",
        "Wer spricht in dem Video?",
        "Was wird über Performance gesagt?",
        "Welche wichtigen Punkte werden erwähnt?",
        "Was sind die Hauptaussagen?",
        "Welche Beispiele werden gegeben?"
    ]
    
    print(f"📝 Testing {len(test_questions)} sample questions with real data...")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 Question {i}: {question}")
        
        try:
            response = agent.ask_question(question)
            
            print(f"🤖 Answer: {response['answer']}")
            print(f"📊 Confidence: {response['confidence']}")
            
            # Handle the context_chunks_used field properly
            if 'context_chunks_used' in response:
                print(f"📚 Sources: {response['context_chunks_used']}/{response['total_chunks_found']}")
            else:
                print(f"📚 Sources: {len(response.get('sources', []))}/{response['total_chunks_found']}")
            
            if response.get('sources'):
                print(f"📝 First source: {response['sources'][0]['text'][:100]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Show conversation history
    print(f"\n📝 Conversation History:")
    history = agent.get_conversation_history()
    for i, exchange in enumerate(history, 1):
        print(f"{i}. Q: {exchange['question']}")
        print(f"   A: {exchange['answer'][:100]}...")


def test_interactive_session():
    """Test interactive chat session"""
    
    print(f"\n🧪 Testing Interactive Chat Session")
    print("-" * 40)
    
    # Use None to search across all videos (like the normal test)
    video_id = None
    
    print(f"📹 Searching across all videos in database")
    
    # Initialize session
    session = InteractiveChatSession(video_id)
    
    print("💡 Starting interactive session...")
    print("   (This will run until you type 'quit')")
    
    # Start session
    session.start_session()


def test_agent_without_data():
    """Test agent behavior without data"""
    
    print(f"\n🧪 Testing Agent Without Data")
    print("-" * 40)
    
    # Temporarily rename mock file
    mock_file = Path("mock_supabase_data.json")
    backup_file = Path("mock_supabase_data.json.backup")
    
    if mock_file.exists():
        mock_file.rename(backup_file)
        print("📁 Temporarily moved mock data")
    
    try:
        agent = MiniChatAgent()
        response = agent.ask_question("Test question")
        
        print(f"🤖 Answer: {response['answer']}")
        print(f"📊 Confidence: {response['confidence']}")
        
    finally:
        # Restore mock file
        if backup_file.exists():
            backup_file.rename(mock_file)
            print("📁 Restored mock data")


def main():
    """Main test function"""
    
    print("🧪 Testing Umsetzer Mini Chat Agent")
    print("=" * 60)
    
    # Test 1: Basic agent functionality with real data
    test_mini_chat_agent_with_real_data()
    
    # Test 2: Agent without data (fallback test)
    test_agent_without_data()
    
    # Test 3: Interactive session (optional)
    print(f"\n💡 Interactive Session Test:")
    print("   Run 'python tests/test_mini_agent.py --interactive' to start interactive chat")
    
    print(f"\n🎉 Mini Chat Agent tests completed!")
    print(f"\n💡 Next steps:")
    print(f"   1. Test with interactive mode: python tests/test_mini_agent.py --interactive")
    print(f"   2. Deploy the agent")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Mini Chat Agent")
    parser.add_argument("--interactive", action="store_true", 
                       help="Start interactive chat session")
    parser.add_argument("--mock", action="store_true", 
                       help="Use mock data instead of real Supabase data")
    
    args = parser.parse_args()
    
    if args.interactive:
        test_interactive_session()
    elif args.mock:
        # Use original test with mock data
        test_mini_chat_agent()
        test_agent_without_data()
    else:
        main()
