from aiogram import Router
from .main_menu import router as main_menu_router
from .exercises import router as exercises_router
from .templates import router as templates_router
from .workout_session import router as workout_session_router
from .history import router as history_router

router = Router()

router.include_router(main_menu_router)
router.include_router(exercises_router)
router.include_router(templates_router)
router.include_router(workout_session_router)
router.include_router(history_router)
