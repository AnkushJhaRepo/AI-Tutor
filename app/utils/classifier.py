from app.models.enums import Subject
from app.services.gemini_client import gemini_client
from app.utils.logger import logger

class SubjectClassifier:
    def classify(self, question: str) -> Subject:
        """Classify a question into a subject using Gemini's natural language understanding."""
        try:
            # Only check for greetings/short messages
            question = question.strip().lower()
            if len(question) < 3 or question in ['hi', 'hello', 'hey', 'greetings']:
                logger.info("Question too short or just a greeting")
                return Subject.UNKNOWN

            prompt = f"""You are a subject classifier for an AI tutoring system. Your task is to analyze the following question and determine which subject it belongs to: math, physics, or chemistry.

Question: {question}

Consider the following guidelines:
- Math questions involve calculations, equations, algebra, geometry, calculus, etc.
- Physics questions involve forces, energy, motion, waves, electricity, etc.
- Chemistry questions involve elements, reactions, compounds, molecules, etc.

Respond with ONLY one word: math, physics, or chemistry. If the question doesn't clearly fit any of these subjects, respond with 'unknown'."""

            response = gemini_client.generate_response(prompt)
            if not response:
                logger.error("Empty response from Gemini")
                return Subject.UNKNOWN

            subject = response.strip().lower()
            logger.info(f"Gemini classification: {subject}")

            # Map the response to our Subject enum
            if subject == "physics":
                return Subject.PHYSICS
            elif subject == "math":
                return Subject.MATH
            elif subject == "chemistry":
                return Subject.CHEMISTRY
            else:
                return Subject.UNKNOWN

        except Exception as e:
            logger.error(f"Error in classification: {str(e)}")
            return Subject.UNKNOWN

# Global instance
classifier = SubjectClassifier()