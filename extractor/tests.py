from unittest.mock import patch

from django.test import SimpleTestCase

from .llm import ask_document, travel_assistant


class OllamaFallbackTests(SimpleTestCase):
    @patch('extractor.llm.ollama.chat', side_effect=ConnectionError('Failed to connect to Ollama'))
    def test_ask_document_returns_fallback_when_ollama_unavailable(self, _mock_chat):
        result = ask_document('Hotel booking details', 'What is the hotel name?')

        self.assertIn('Unable to connect to Ollama', result)
        self.assertIn('Hotel booking details', result)

    @patch('extractor.llm.ollama.chat', side_effect=ConnectionError('Failed to connect to Ollama'))
    def test_travel_assistant_returns_fallback_when_ollama_unavailable(self, _mock_chat):
        result = travel_assistant('Suggest a hotel in Paris')

        self.assertIn('Unable to connect to Ollama', result)
        self.assertIn('Paris', result)
