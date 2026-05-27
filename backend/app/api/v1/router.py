from fastapi import APIRouter

from app.modules.cover_letters.router import router as cover_letters_router
from app.modules.cv.router import router as cv_router
from app.modules.cv_tailor.router import router as cv_tailor_router
from app.modules.interview_prep.router import router as interview_prep_router
from app.modules.jobs.router import router as jobs_router
from app.modules.matching.router import router as matching_router

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


router.include_router(cv_router)
router.include_router(jobs_router)
router.include_router(matching_router)
router.include_router(cover_letters_router)
router.include_router(cv_tailor_router)
router.include_router(interview_prep_router)
