"""
Guardrails system for filtering inappropriate content and enforcing responsible AI behavior.
Monitors user prompts for flagged keywords and responds with appropriate warnings.
"""

from typing import List, Dict, Tuple
import json
from enum import Enum


class ContentSeverity(Enum):
    """Severity levels for content violations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailsManager:
    """Manages content filtering and guardrails for the chatbot"""

    def __init__(self):
        """Initialize with default guardrail keywords"""
        self.guardrail_keywords = self._load_guardrail_keywords()

    def _load_guardrail_keywords(self) -> Dict[str, Dict]:
        """
        Load guardrail keywords and their severity levels.
        Returns a dictionary with keyword info.
        """
        return {
            # Harmful/Violent Content
            "violence": {
                "keywords": [
                    "hurt", "kill", "murder", "harm", "violence", "attack",
                    "bomb", "weapon", "shoot", "stab", "torture", "abuse"
                ],
                "severity": ContentSeverity.CRITICAL,
                "message": "I cannot provide assistance with harmful or violent content. Please ask about legitimate university services instead."
            },

            # Illegal Activities
            "illegal": {
                "keywords": [
                    "hack", "crack", "cheat exam", "plagiarize", "forge", "fake",
                    "steal", "drugs", "smuggle", "illegal exam", "illegal access",
                    "break in", "bypass security"
                ],
                "severity": ContentSeverity.CRITICAL,
                "message": "I cannot help with illegal activities. All academic work must follow university policies and laws."
            },

            # Academic Dishonesty
            "academic_dishonesty": {
                "keywords": [
                    "copy homework", "buy assignment", "write my essay", "cheat sheet",
                    "answer key", "exam answers", "plagiarized", "contract cheating",
                    "do my work", "homework solution"
                ],
                "severity": ContentSeverity.HIGH,
                "message": "I cannot assist with academic dishonesty. I can help you understand concepts, but the work must be your own. Please refer to the university's academic integrity policy."
            },

            # Bullying/Harassment
            "harassment": {
                "keywords": [
                    "bully", "harass", "threaten", "intimidate", "discriminate",
                    "racist", "sexist", "hate", "abuse", "demean", "mock",
                    "discriminatory", "harassment"
                ],
                "severity": ContentSeverity.CRITICAL,
                "message": "I cannot assist with bullying, harassment, or discrimination. All university members must treat each other with respect."
            },

            # Personal Information Abuse
            "privacy_violation": {
                "keywords": [
                    "doxx", "leak personal", "expose identity", "share phone",
                    "share email", "share address", "private information",
                    "someone's password", "someone's data"
                ],
                "severity": ContentSeverity.CRITICAL,
                "message": "I cannot help with accessing or sharing private information. Protect your own data and respect others' privacy."
            },

            # Suspicious Behavior
            "suspicious": {
                "keywords": [
                    "bypass login", "hack account", "get admin access", "bypass password",
                    "unauthorized access", "system exploit", "security bypass"
                ],
                "severity": ContentSeverity.HIGH,
                "message": "I cannot assist with bypassing security measures or unauthorized access. Please use official university channels."
            },

            # Misinformation
            "misinformation": {
                "keywords": [
                    "spread false rumor", "fake news about", "spread misinformation",
                    "false information", "make up story"
                ],
                "severity": ContentSeverity.MEDIUM,
                "message": "I'm designed to provide accurate information. Please verify information from official sources."
            }
        }

    def check_content(self, user_message: str) -> Tuple[bool, str, ContentSeverity]:
        """
        Check if user message contains flagged keywords.

        Args:
            user_message: The user's input message

        Returns:
            Tuple of (is_flagged, response_message, severity_level)
        """
        message_lower = user_message.lower()

        # Check each category
        for category_name, category_info in self.guardrail_keywords.items():
            keywords = category_info["keywords"]
            severity = category_info["severity"]
            response_message = category_info["message"]

            # Check if any keyword matches (case-insensitive)
            for keyword in keywords:
                if keyword in message_lower:
                    return True, response_message, severity

        # No violations found
        return False, "", ContentSeverity.LOW

    def get_flag_report(self, user_message: str) -> Dict:
        """
        Get detailed flag report for a message.

        Returns:
            Dictionary with flag details
        """
        is_flagged, message, severity = self.check_content(user_message)

        return {
            "is_flagged": is_flagged,
            "severity": severity.value if is_flagged else None,
            "response_message": message,
            "flagged_keyword": self._find_flagged_keyword(user_message) if is_flagged else None
        }

    def _find_flagged_keyword(self, user_message: str) -> str:
        """Find the specific keyword that triggered the flag"""
        message_lower = user_message.lower()

        for category_info in self.guardrail_keywords.values():
            for keyword in category_info["keywords"]:
                if keyword in message_lower:
                    return keyword
        return "unknown"

    def add_custom_keyword(self, category: str, keyword: str, severity: str):
        """
        Add a custom guardrail keyword.

        Args:
            category: Category name (e.g., "violence", "illegal")
            keyword: The keyword to add
            severity: Severity level
        """
        if category not in self.guardrail_keywords:
            self.guardrail_keywords[category] = {
                "keywords": [],
                "severity": ContentSeverity(severity),
                "message": f"This request violates our content policy."
            }

        if keyword not in self.guardrail_keywords[category]["keywords"]:
            self.guardrail_keywords[category]["keywords"].append(keyword)

    def remove_keyword(self, keyword: str):
        """Remove a keyword from guardrails"""
        for category_info in self.guardrail_keywords.values():
            if keyword in category_info["keywords"]:
                category_info["keywords"].remove(keyword)

    def get_all_keywords(self) -> Dict:
        """Get all current guardrail keywords organized by category"""
        return {
            category: {
                "severity": info["severity"].value,
                "keywords": info["keywords"]
            }
            for category, info in self.guardrail_keywords.items()
        }

    def export_keywords(self, filepath: str):
        """Export guardrail keywords to JSON file"""
        keywords_data = {
            category: {
                "severity": info["severity"].value,
                "keywords": info["keywords"],
                "message": info["message"]
            }
            for category, info in self.guardrail_keywords.items()
        }

        with open(filepath, 'w') as f:
            json.dump(keywords_data, f, indent=2)

    def import_keywords(self, filepath: str):
        """Import guardrail keywords from JSON file"""
        try:
            with open(filepath, 'r') as f:
                keywords_data = json.load(f)

            self.guardrail_keywords = {}
            for category, info in keywords_data.items():
                self.guardrail_keywords[category] = {
                    "keywords": info["keywords"],
                    "severity": ContentSeverity(info["severity"]),
                    "message": info.get("message", f"Content violation in {category}")
                }
        except FileNotFoundError:
            print(f"Guardrails file not found: {filepath}")
        except json.JSONDecodeError:
            print(f"Invalid JSON in guardrails file: {filepath}")


# Global guardrails manager instance
_guardrails_manager = None


def get_guardrails_manager() -> GuardrailsManager:
    """Get or create the global guardrails manager instance"""
    global _guardrails_manager
    if _guardrails_manager is None:
        _guardrails_manager = GuardrailsManager()
    return _guardrails_manager


def check_user_input(user_message: str) -> Tuple[bool, str]:
    """
    Convenience function to check if user input violates guardrails.

    Args:
        user_message: The message to check

    Returns:
        Tuple of (is_violation, violation_message)
    """
    manager = get_guardrails_manager()
    is_flagged, message, _ = manager.check_content(user_message)
    return is_flagged, message
