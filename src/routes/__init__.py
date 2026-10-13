from src.routes.instructionrouter import router as instruction_router
from src.routes.regularactionrouter import router as regular_action_router
from src.routes.singleactionrouter import router as single_action_router
from src.routes.logrouter import router as log_router
from src.routes.schedulerrouter import router as scheduler_router

__all__ = [
    "instruction_router",
    "regular_action_router",
    "single_action_router",
    "log_router",
    "scheduler_router",
]
