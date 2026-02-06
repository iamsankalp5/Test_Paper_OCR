"""
Application constants and thresholds.
"""

# Image preprocessing constants
IMAGE_MAX_WIDTH = 2000
IMAGE_MAX_HEIGHT = 2000
IMAGE_MIN_WIDTH = 300
IMAGE_MIN_HEIGHT = 300

# OCR confidence thresholds
OCR_MIN_CONFIDENCE = 60
OCR_HIGH_CONFIDENCE = 85

# Assessment thresholds
PASSING_GRADE_PERCENTAGE = 40
EXCELLENT_GRADE_PERCENTAGE = 90
GOOD_GRADE_PERCENTAGE = 75

# Workflow states
WORKFLOW_STATES = {
    "UPLOADED": "uploaded",
    "PREPROCESSING": "preprocessing",
    "PREPROCESSED": "preprocessed",
    "OCR_EXTRACTING": "ocr_extracting",
    "OCR_EXTRACTED": "ocr_extracted",
    "PARSING": "parsing",
    "PARSED": "parsed",
    "ASSESSING": "assessing",
    "ASSESSED": "assessed",
    "GENERATING_FEEDBACK": "generating_feedback",
    "FEEDBACK_GENERATED": "feedback_generated",
    "UNDER_REVIEW": "under_review",
    "REVIEWED": "reviewed",
    "REPORT_GENERATING": "report_generating",
    "COMPLETED": "completed",
    "FAILED": "failed"
}

# Grade mappings
GRADE_MAPPINGS = {
    "A+": (95, 100),
    "A": (90, 94),
    "B+": (85, 89),
    "B": (80, 84),
    "C+": (75, 79),
    "C": (70, 74),
    "D": (60, 69),
    "E": (40, 59),
    "F": (0, 39)
}

# Supported subjects
SUPPORTED_SUBJECTS = [
    "Mathematics",
    "Science",
    "English",
    "History",
    "Geography",
    "Physics",
    "Chemistry",
    "Biology",
    "Computer Science",
    "Economics"
]