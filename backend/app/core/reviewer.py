"""
Manual review and correction module for teacher oversight.
"""
from typing import List, Dict, Any
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class Reviewer:
    """Handles manual review and correction of assessments."""
    
    def __init__(self):
        """Initialize reviewer."""
        logger.info("Reviewer initialized")
    
    def apply_review_updates(
        self,
        assessed_answers: List[Dict[str, Any]],
        updates: List[Dict[str, Any]],
        reviewer_name: str
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Apply teacher review updates to assessed answers.
        
        Args:
            assessed_answers: List of assessed answers
            updates: List of review updates
            reviewer_name: Name of the reviewer
            
        Returns:
            Tuple of (updated answers, number of updates applied)
            
        Raises:
            Exception: If review update fails
        """
        try:
            logger.info(f"Applying {len(updates)} review updates by {reviewer_name}")
            
            updates_applied = 0
            
            # Create a mapping for quick lookup
            answers_map = {
                answer['question_number']: answer
                for answer in assessed_answers
            }
            
            # Apply each update
            for update in updates:
                q_num = update['question_number']
                
                if q_num not in answers_map:
                    logger.warning(f"Question {q_num} not found, skipping update")
                    continue
                
                answer = answers_map[q_num]
                
                # Update marks if provided
                if update.get('marks_obtained') is not None:
                    old_marks = answer['marks_obtained']
                    answer['marks_obtained'] = min(
                        update['marks_obtained'],
                        answer['max_marks']
                    )
                    logger.debug(f"Q{q_num} marks updated: {old_marks} -> {answer['marks_obtained']}")
                    
                    # Update is_correct based on new marks
                    answer['is_correct'] = answer['marks_obtained'] >= (answer['max_marks'] * 0.5)
                
                # Update explanation if provided
                if update.get('explanation'):
                    answer['explanation'] = update['explanation']
                    logger.debug(f"Q{q_num} explanation updated")
                
                # Add reviewer notes
                if update.get('reviewer_notes'):
                    answer['reviewer_notes'] = update['reviewer_notes']
                    logger.debug(f"Q{q_num} reviewer notes added")
                
                # Mark as reviewed
                answer['reviewed_by'] = reviewer_name
                
                updates_applied += 1
            
            logger.info(f"Review updates completed. {updates_applied} updates applied.")
            return list(answers_map.values()), updates_applied
            
        except Exception as e:
            logger.error(f"Review update failed: {str(e)}", exc_info=True)
            raise Exception(f"Review update failed: {str(e)}")
    
    def recalculate_totals(
        self,
        assessed_answers: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Recalculate total marks and percentage after review.
        
        Args:
            assessed_answers: List of assessed answers
            
        Returns:
            Dictionary with recalculated totals
        """
        try:
            total_marks = sum(answer['max_marks'] for answer in assessed_answers)
            total_obtained = sum(answer['marks_obtained'] for answer in assessed_answers)
            percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
            
            logger.info(f"Recalculated: {total_obtained}/{total_marks} = {percentage:.2f}%")
            
            return {
                'total_marks': total_marks,
                'total_marks_obtained': round(total_obtained, 2),
                'percentage': round(percentage, 2)
            }
            
        except Exception as e:
            logger.error(f"Recalculation failed: {str(e)}")
            raise
