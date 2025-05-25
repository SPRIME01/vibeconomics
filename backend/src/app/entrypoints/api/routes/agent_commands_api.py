from fastapi import APIRouter

router = APIRouter(prefix="/agent/commands", tags=["Agent Commands"])

# @router.post("/execute-pattern")
# async def execute_pattern(): ...
