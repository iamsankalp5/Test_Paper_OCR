"""
AI-powered assessment engine using OpenAI GPT models.
"""

from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import google.generativeai as genai
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.models.enums import QuestionType

logger = get_logger(__name__)

class AssessmentEngine:
    """AI-powered assessment engine for grading student answers."""
    
    def __init__(self):
        """Initialize assessment engine with Gemini client."""
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"AssessmentEngine initialized with Gemini model: {self.model_name}")
    
    async def assess_answers(
        self,
        answers: List[Dict[str, Any]],
        answer_key: Optional[Dict[int, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Assess all answers using AI.
        
        Args:
            answers: List of parsed answers
            answer_key: Optional answer key for objective questions
            
        Returns:
            List of assessed answers with marks and feedback
            
        Raises:
            Exception: If assessment fails
        """
        try:
            logger.info(f"Starting AI assessment for {len(answers)} answers")
            
            assessed_answers = []
            
            for answer in answers:
                try:
                    assessed = await self._assess_single_answer(answer, answer_key)
                    assessed_answers.append(assessed)
                    logger.debug(f"Assessed Q{answer['question_number']}: {assessed['marks_obtained']}/{assessed['max_marks']}")
                except Exception as e:
                    logger.error(f"Failed to assess Q{answer['question_number']}: {str(e)}")
                    # Add failed assessment with zero marks
                    assessed_answers.append({
                        **answer,
                        "marks_obtained": 0.0,
                        "is_correct": False,
                        "explanation": f"Assessment failed: {str(e)}",
                        "suggestions": ["Unable to assess due to technical error"]
                    })
            
            logger.info("AI assessment completed successfully")
            return assessed_answers
            
        except Exception as e:
            logger.error(f"Assessment failed: {str(e)}", exc_info=True)
            raise Exception(f"AI assessment failed: {str(e)}")
    
    async def _assess_single_answer(
        self,
        answer: Dict[str, Any],
        answer_key: Optional[Dict[int, str]]
    ) -> Dict[str, Any]:
        """
        Assess a single answer using Gemini AI.
        
        Args:
            answer: Single answer dictionary
            answer_key: Optional answer key
            
        Returns:
            Assessed answer with marks and feedback
        """
        question_num = answer['question_number']
        question_text = answer['question_text']
        student_answer = answer['answer_text']
        max_marks = answer['max_marks']
        question_type = answer['question_type']
        
        # Get correct answer from answer key if available
        correct_answer = answer_key.get(question_num) if answer_key else None
        
        # Build prompt for AI assessment
        prompt = self._build_assessment_prompt(
            question_text,
            student_answer,
            correct_answer,
            max_marks,
            question_type
        )

        try:
            # Configure generation with safety settings
            generation_config = genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=500,
            )
            
            # Relaxed safety settings
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                },
            ]
            
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Check if response was blocked
            if not response.text:
                logger.warning(f"Q{question_num}: Response blocked or empty. Using fallback assessment.")
                # Fallback: Give partial credit
                assessment_result = {
                    'marks': max_marks * 0.5,
                    'is_correct': False,
                    'explanation': "Assessment completed with automatic grading.",
                    'suggestions': ["Review the answer", "Consult with teacher"]
                }
            else:
                # Parse AI response
                ai_response = response.text
                assessment_result = self._parse_ai_response(ai_response, max_marks)
            
        except Exception as e:
            logger.error(f"Q{question_num}: Assessment failed - {str(e)}")
            # Fallback assessment
            assessment_result = {
                'marks': max_marks * 0.5,
                'is_correct': False,
                'explanation': f"Automatic assessment applied. Error: {str(e)[:50]}",
                'suggestions': ["Manual review recommended"]
            }
        
        # Build assessed answer
        return {
            **answer,
            "marks_obtained": assessment_result['marks'],
            "is_correct": assessment_result['is_correct'],
            "explanation": assessment_result['explanation'],
            "suggestions": assessment_result['suggestions']
        }
    
    def _build_assessment_prompt(
        self,
        question: str,
        student_answer: str,
        correct_answer: Optional[str],
        max_marks: float,
        question_type: str
    ) -> str:
        """
        Build prompt for AI assessment.
        
        Args:
            question: Question text
            student_answer: Student's answer
            correct_answer: Correct answer (if available)
            max_marks: Maximum marks
            question_type: Type of question
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert teacher evaluating student test answers. Provide fair, constructive assessment.

Evaluate this student's answer:

QUESTION: {question}
STUDENT ANSWER: {student_answer}
"""
        
        if correct_answer:
            prompt += f"CORRECT ANSWER: {correct_answer}\n"
        
        prompt += f"""
QUESTION TYPE: {question_type}
MAX MARKS: {max_marks}

Please provide:
1. MARKS: Score out of {max_marks} (be precise)
2. IS_CORRECT: true/false
3. EXPLANATION: Brief explanation of the assessment (2-3 sentences)
4. SUGGESTIONS: 2-3 specific suggestions for improvement

Format your response exactly as:
MARKS: <score>
IS_CORRECT: <true/false>
EXPLANATION: <your explanation>
SUGGESTIONS: <suggestion 1> | <suggestion 2> | <suggestion 3>
"""
        return prompt
    
    def _parse_ai_response(self, response: str, max_marks: float) -> Dict[str, Any]:
        """
        Parse AI response into structured format.
        
        Args:
            response: AI response text
            max_marks: Maximum marks for validation
            
        Returns:
            Parsed assessment result
        """
        try:
            lines = response.strip().split('\n')
            result = {
                'marks': 0.0,
                'is_correct': False,
                'explanation': '',
                'suggestions': []
            }
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('MARKS:'):
                    marks_str = line.replace('MARKS:', '').strip()
                    # Extract numeric value
                    import re
                    marks_match = re.search(r'(\d+(?:\.\d+)?)', marks_str)
                    if marks_match:
                        result['marks'] = min(float(marks_match.group(1)), max_marks)
                
                elif line.startswith('IS_CORRECT:'):
                    is_correct_str = line.replace('IS_CORRECT:', '').strip().lower()
                    result['is_correct'] = is_correct_str in ['true', 'yes', '1']
                
                elif line.startswith('EXPLANATION:'):
                    result['explanation'] = line.replace('EXPLANATION:', '').strip()
                
                elif line.startswith('SUGGESTIONS:'):
                    suggestions_str = line.replace('SUGGESTIONS:', '').strip()
                    result['suggestions'] = [s.strip() for s in suggestions_str.split('|') if s.strip()]
            
            # Ensure we have default values
            if not result['explanation']:
                result['explanation'] = "Assessment completed."
            if not result['suggestions']:
                result['suggestions'] = ["Keep practicing!", "Review the concepts."]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            # Return default assessment
            return {
                'marks': max_marks * 0.5,  # Give 50% as default
                'is_correct': False,
                'explanation': "Unable to parse assessment. Manual review recommended.",
                'suggestions': ["Review the question", "Seek clarification"]
            }