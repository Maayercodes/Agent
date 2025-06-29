import unittest
from src.ai_assistant.assistant import AIAssistant

class TestAIAssistant(unittest.TestCase):
    def setUp(self):
        # Minimal mock or dummy session object
        class DummySession:
            pass
        
        self.dummy_session = DummySession()
        self.assistant = AIAssistant(self.dummy_session)

    def test_initialization(self):
        """Test if the AI Assistant initializes correctly"""
        self.assertIsNotNone(self.assistant)

if __name__ == '__main__':
    unittest.main()
 