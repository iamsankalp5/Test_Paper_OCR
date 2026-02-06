"""
Answer parser to extract question-answer pairs from OCR text.
"""

import re
from typing import List, Tuple, Dict, Any
from app.config.logging_config import get_logger
from app.models.enums import QuestionType

logger = get_logger(__name__)

class AnswerParser:
    """Parses OCR text to extract structured question-answer pairs."""
    
    def __init__(self):
        """Initialize answer parser."""
        logger.info("AnswerParser initialized")

    def parse(self, text: str, total_marks: int) -> List[Dict[str, Any]]:
        """
        Parse OCR text to extract question-answer pairs.
        
        Args:
            text: OCR extracted text
            total_marks: Total marks for the exam
            
        Returns:
            List of parsed answers
            
        Raises:
            Exception: If parsing fails
        """
        try:
            logger.info(f"Starting answer parsing. Text length: {len(text)}")

            # Split text into lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            answers = []
            current_question = None
            current_answer_lines = []

            for line in lines:
                # Check if line starts with question number pattern
                question_match = re.match(r'^(?:Q(?:uestion)?\.?\s*|)(\d+)[\.\:\)]\s*(.*)', line, re.IGNORECASE)

                if question_match:
                    # Save previous question-answer pair if exists
                    if current_question is not None:
                        answer = self._build_answer(
                            current_question, current_answer_lines, 
                            len(answers) + 1, total_marks
                        )
                        answers.append(answer)

                    # Start new question
                    current_question = {
                        'number': int(question_match.group(1)),
                        'text': question_match.group(2).strip()
                    }
                    current_answer_lines = []
                    logger.debug(f"Found question {current_question['number']}: {current_question['text']}")
                else:
                    # Add to current answer lines
                    if current_question is not None:
                        current_answer_lines.append(line)

            # Add last question-answer
            if current_question is not None:
                answer = self._build_answer(
                    current_question, current_answer_lines, 
                    len(answers) + 1, total_marks
                )
                answers.append(answer)

            logger.info(f"Parsing completed. Found {len(answers)} questions")

            # If no structured questions found, create generic parsing
            if not answers:
                logger.warning("No structured questions found. Creating generic parse.")
                answers = self._generic_parse(lines, total_marks)

            return answers
        
        except Exception as e:
            logger.error(f"Answer parsing failed: {str(e)}", exc_info=True)
            raise Exception(f"Answer parsing failed: {str(e)}")
    
    def _build_answer(
        self, question: Dict[str, Any], answer_lines: List[str], 
        position: int, total_marks: int
    ) -> Dict[str, Any]:
        """
        Build a structured answer dictionary.
        
        Args:
            question: Question dictionary
            answer_lines: List of answer text lines
            position: Question position
            total_marks: Total marks for exam
            
        Returns:
            Structured answer dictionary
        """
        # Use newline (not space) to avoid one giant paragraph
        answer_text = '\n'.join(answer_lines).strip()
        
        # Detect question type (simple heuristic)
        question_type = self._detect_question_type(question['text'],answer_text)

        # Estimate marks per question (simple division)
        estimated_marks = total_marks / 10  # Assume 10 questions by default

        return {
            "question_number": question['number'],
            "question_text": question['text'],
            "answer_text": answer_text,
            "question_type": question_type,
            "max_marks": round(estimated_marks, 1)
        }
    
    def _detect_question_type(self, question_text: str, answer_text: str) -> str:
        """
        Detect the type of question based on text patterns.
        
        Args:
            question_text: Question text
            answer_text: Answer text
            
        Returns:
            Question type string
        """
        question_lower = question_text.lower()
        answer_lower = answer_text.lower()

        # Multiple choice indicators
        if any(indicator in question_lower for indicator in ['(a)', '(b)', '(c)', '(d)', 'choose', 'select']):
            return QuestionType.MULTIPLE_CHOICE.value
        
        # True/False indicators
        if any(indicator in question_lower for indicator in ['true or false', 't/f', 'true/false']):
            return QuestionType.TRUE_FALSE.value
        
        # Fill in the blank indicators
        if any(indicator in question_lower for indicator in ['fill in', 'blank', '______', '___']):
            return QuestionType.FILL_IN_THE_BLANK.value
        
        # Essay indicators
        if len(answer_text.split()) > 50:
            return QuestionType.ESSAY.value
        
        # Default to short answer
        return QuestionType.SHORT_ANSWER.value
    
    def _generic_parse(self, lines: List[str], total_marks: int) -> List[Dict[str, Any]]:
        """
        Create generic parsing when no structured questions found.
        
        Args:
            text: Full OCR text
            total_marks: Total marks
            
        Returns:
            List with single generic answer
        """
        return [{
            "question_number": 1,
            "question_text": "Full Test Paper Response",
            "answer_text": '\n'.join(lines),
            "question_type": QuestionType.ESSAY.value,
            "max_marks": float(total_marks)
        }]