"""
Central router combining all API routes.
"""
from fastapi import APIRouter
from api import (
    health,
    auth,
    image_upload,
    reference,
    teacher_dashboard,
    preprocessing,
    ocr_extract,
    parse_answers,
    ai_assessment,
    feedback,
    review,
    report,
    workflow,
    files,
    reassess,
    history
)

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(teacher_dashboard.router)
api_router.include_router(reference.router, prefix="/reference", tags=["Reference"])
api_router.include_router(image_upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(preprocessing.router, prefix="/preprocess", tags=["Preprocessing"])
api_router.include_router(ocr_extract.router, prefix="/ocr", tags=["OCR"])
api_router.include_router(parse_answers.router, prefix="/parse", tags=["Parsing"])
api_router.include_router(ai_assessment.router, prefix="/assess", tags=["Assessment"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
api_router.include_router(review.router, prefix="/review", tags=["Review"])
api_router.include_router(report.router, prefix="/report", tags=["Report"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["Autonomous Workflow"])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(reassess.router, prefix="/reassess", tags=["Reassess"])
api_router.include_router(history.router, prefix="/history", tags=["History"])
