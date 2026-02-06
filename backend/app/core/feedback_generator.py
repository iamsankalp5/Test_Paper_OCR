"""
Personalized feedback generator for students.
"""
from typing import List, Dict, Any
import re
import google.generativeai as genai
from openai import AsyncOpenAI
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.core.utils import get_grade_from_percentage


logger = get_logger(__name__)


class FeedbackGenerator:
    """Generates personalized feedback for students based on assessment."""
    
    def __init__(self):
        """Initialize feedback generator with Gemini."""
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"FeedbackGenerator initialized with Gemini model: {self.model_name}")
    
    async def generate_feedback(
        self,
        student_name: str,
        subject: str,
        assessed_answers: List[Dict[str, Any]],
        percentage: float
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feedback for student.
        
        Args:
            student_name: Name of the student
            subject: Subject name
            assessed_answers: List of assessed answers
            percentage: Overall percentage score
            
        Returns:
            Dictionary containing feedback components
            
        Raises:
            Exception: If feedback generation fails
        """
        try:
            logger.info(f"Generating feedback for {student_name}, Score: {percentage}%")
            
            # Calculate statistics
            total_questions = len(assessed_answers)
            correct_answers = sum(1 for a in assessed_answers if a['is_correct'])
            
            # Build prompt
            prompt = self._build_feedback_prompt(
                student_name,
                subject,
                assessed_answers,
                percentage,
                total_questions,
                correct_answers
            )
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=800,
            )
            
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Parse response
            ai_feedback = response.text
            feedback = self._parse_feedback(ai_feedback)
            
            # Add grade
            feedback['grade'] = get_grade_from_percentage(percentage)
            
            logger.info(f"Feedback generated successfully. Grade: {feedback['grade']}")
            logger.info(f"Overall feedback length: {len(feedback['overall_feedback'])}")
            logger.info(f"Strengths count: {len(feedback['strengths'])}")
            logger.info(f"Improvements count: {len(feedback['areas_for_improvement'])}")
            logger.info(f"Recommendations count: {len(feedback['recommendations'])}")
            return feedback
            
        except Exception as e:
            logger.error(f"Feedback generation failed: {str(e)}", exc_info=True)
            raise Exception(f"Feedback generation failed: {str(e)}")
    
    def _build_feedback_prompt(
        self,
        student_name: str,
        subject: str,
        assessed_answers: List[Dict[str, Any]],
        percentage: float,
        total_questions: int,
        correct_answers: int
    ) -> str:
        """Build prompt for feedback generation."""
        
        # Identify performance level
        if percentage >= 80:
            performance_level = "excellent"
        elif percentage >= 60:
            performance_level = "good"
        else:
            performance_level = "needs improvement"
        
        # Get question summaries
        question_summary = []
        for i, answer in enumerate(assessed_answers[:5], 1):  # First 5 questions
            marks = answer.get('marks_obtained', 0)
            max_marks = answer.get('max_marks', 10)
            status = "✓" if marks >= max_marks * 0.7 else "×"
            question_summary.append(f"Q{i}: {marks}/{max_marks} {status}")
        
        prompt = f"""You are a supportive teacher providing feedback to {student_name}.

STUDENT PERFORMANCE:
- Subject: {subject}
- Score: {percentage:.1f}% ({correct_answers}/{total_questions} questions correct)
- Performance Level: {performance_level}

QUESTION SUMMARY:
{chr(10).join(question_summary)}

Please provide encouraging and constructive feedback in the following format:

Overall Assessment:
[Write 2-3 sentences acknowledging their effort, commenting on their performance level, and encouraging them]

Strengths:
• [Strength 1]
• [Strength 2]
• [Strength 3]

Areas for Improvement:
• [Area 1]
• [Area 2]
• [Area 3]

Recommendations:
• [Recommendation 1]
• [Recommendation 2]
• [Recommendation 3]
• [Recommendation 4]

Use clear bullet points and be specific, encouraging, and actionable.
DO NOT number the sections (1., 2., 3., 4.). Use section headings only.
"""
        return prompt
    
    def _parse_feedback(self, response: str) -> Dict[str, Any]:
        """
        Parse AI feedback response.
        Cleanly extract sections without numbered headers.
        """
        try:
            lines = response.strip().split('\n')

            feedback = {
                'overall_feedback': '',
                'strengths': [],
                'areas_for_improvement': [],
                'recommendations': []
            }

            current_section = None
            overall_buffer = []
            
            for line in lines:
                line = line.strip()

                if not line:
                    continue
                
                # Skip numbered section headers (e.g., "1.", "2.", "3.", "4.")
                if re.match(r'^\s*\d+\.\s*(Overall|Strengths|Areas|Recommendations|Suggestions)', line, re.IGNORECASE):
                    continue
                
                # Detect section headers (without numbers)
                lower_line = line.lower()
                
                if any(x in lower_line for x in ['overall assessment', 'overall feedback', 'performance review']):
                    # Save any buffered overall feedback before switching
                    if overall_buffer and not feedback['overall_feedback']:
                        feedback['overall_feedback'] = '\n\n'.join(overall_buffer)
                        overall_buffer = []
                    current_section = 'overall'
                    continue
                    
                elif 'strength' in lower_line or 'celebration' in lower_line or 'well done' in lower_line:
                    # Save buffered overall feedback before switching section
                    if overall_buffer and not feedback['overall_feedback']:
                        feedback['overall_feedback'] = '\n\n'.join(overall_buffer)
                        overall_buffer = []
                    current_section = 'strengths'
                    continue
                    
                elif 'improvement' in lower_line or 'growth' in lower_line or 'work on' in lower_line:
                    current_section = 'improvements'
                    continue
                    
                elif 'recommendation' in lower_line or 'action plan' in lower_line or 'suggestion' in lower_line or 'next step' in lower_line:
                    current_section = 'recommendations'
                    continue
                
                # Extract bullet points or regular lines
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    clean_line = line.lstrip('•-* ').strip()
                    
                    if current_section == 'strengths' and clean_line:
                        feedback['strengths'].append(clean_line)
                    elif current_section == 'improvements' and clean_line:
                        feedback['areas_for_improvement'].append(clean_line)
                    elif current_section == 'recommendations' and clean_line:
                        feedback['recommendations'].append(clean_line)
                        
                elif current_section == 'overall' and line:
                    # Add to overall feedback buffer (creates paragraphs)
                    overall_buffer.append(line)
            
            # Save any remaining overall feedback
            if overall_buffer and not feedback['overall_feedback']:
                feedback['overall_feedback'] = '\n\n'.join(overall_buffer)
            
            # If no overall feedback was extracted, format the whole response but filter out section headers
            if not feedback['overall_feedback']:
                # Remove section headers and numbered items from the raw response
                filtered_response = self._filter_section_headers(response)
                feedback['overall_feedback'] = self._format_text_with_spacing(filtered_response)

            # Provide defaults if parsing failed
            if not feedback['strengths']:
                feedback['strengths'] = [
                    "Completed the assessment",
                    "Shows understanding of key concepts",
                    "Demonstrated effort in answering questions"
                ]
            
            if not feedback['areas_for_improvement']:
                feedback['areas_for_improvement'] = [
                    "Review incorrect answers and understand mistakes",
                    "Practice similar problems to strengthen understanding",
                    "Focus on time management during tests"
                ]
            
            if not feedback['recommendations']:
                feedback['recommendations'] = [
                    "Study regularly and review class notes",
                    "Practice with sample questions",
                    "Ask questions when concepts are unclear",
                    "Work on weak areas identified in this assessment"
                ]
            
            # Limit to reasonable lengths
            feedback['strengths'] = feedback['strengths'][:5]
            feedback['areas_for_improvement'] = feedback['areas_for_improvement'][:5]
            feedback['recommendations'] = feedback['recommendations'][:5]
            
            logger.info(f"Parsed feedback: {len(feedback['strengths'])} strengths, " +
                    f"{len(feedback['areas_for_improvement'])} improvements, " +
                    f"{len(feedback['recommendations'])} recommendations")
            
            return feedback
            
        except Exception as e:
            logger.error(f"Failed to parse feedback: {str(e)}", exc_info=True)
            
            # Return safe defaults
            return {
                'overall_feedback': self._format_text_with_spacing(response) if response else (
                "Your assessment has been completed.\n\n"
                "Review the detailed question feedback below to understand your performance.\n\n"
                "Keep practicing and don't hesitate to ask for help when needed."
                ),
                'strengths': [
                    "Completed all questions",
                    "Demonstrated effort",
                    "Shows potential for improvement"
                ],
                'areas_for_improvement': [
                    "Review key concepts from class",
                    "Practice more problems",
                    "Improve time management"
                ],
                'recommendations': [
                    "Study regularly",
                    "Seek help when needed",
                    "Practice with sample tests"
                ]
            }
    
    def _filter_section_headers(self, text: str) -> str:
        """
        Remove section headers and numbered items from text.
        
        Args:
            text: Raw text with section headers
            
        Returns:
            Text with section headers removed
        """
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Skip numbered section headers
            if re.match(r'^\s*\d+\.\s*(Overall|Strengths|Areas|Recommendations|Suggestions)', line, re.IGNORECASE):
                continue
            # Skip standalone section headers
            lower_line = line.lower().strip()
            if lower_line in ['strengths:', 'areas for improvement:', 'recommendations:', 'suggestions:', 'overall assessment:']:
                continue
            
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _format_text_with_spacing(self, text: str) -> str:
        """
        Format text with proper spacing and paragraphs.
        Converts wall of text into readable paragraphs.
        
        Args:
            text: Raw text to format
            
        Returns:
            Formatted text with line breaks
        """
        # Split into sentences
        sentences = []
        for sent in text.replace('! ', '!|').replace('. ', '.|').replace('? ', '?|').split('|'):
            sent = sent.strip()
            if sent and not sent.endswith(('.', '!', '?')):
                sent += '.'
            if sent:
                sentences.append(sent)
        
        # Group sentences into paragraphs (2-3 sentences each)
        paragraphs = []
        for i in range(0, len(sentences), 3):
            paragraph = ' '.join(sentences[i:i+3])
            paragraphs.append(paragraph)
        
        # Join paragraphs with double line breaks for readability
        return '\n\n'.join(paragraphs)
