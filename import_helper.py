"""
Import helper for Streamlit Cloud deployment
"""
import sys
from pathlib import Path

def setup_imports():
    """Setup import paths for cloud deployment"""
    # Add current directory to path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Add src directory to path
    src_dir = current_dir / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
    
    # Add config directory to path
    config_dir = current_dir / "config"
    if config_dir.exists():
        sys.path.insert(0, str(config_dir))

def get_agent():
    """Get the MiniChatAgent class"""
    try:
        from src.agent.mini_chat_agent import MiniChatAgent
        return MiniChatAgent
    except ImportError:
        try:
            from agent.mini_chat_agent import MiniChatAgent
            return MiniChatAgent
        except ImportError:
            raise ImportError("Could not import MiniChatAgent")

def get_settings():
    """Get the settings object"""
    try:
        from config.settings import settings
        return settings
    except ImportError:
        try:
            from settings import settings
            return settings
        except ImportError:
            raise ImportError("Could not import settings")
