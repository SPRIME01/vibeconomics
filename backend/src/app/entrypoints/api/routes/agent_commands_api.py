from fastapi import APIRouter, HTTPException, Body, Depends, Request, Query, Path
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Dict, Any, AsyncGenerator, Union, Optional
from uuid import UUID
from pydantic import BaseModel, Field
import json
import asyncio

router = APIRouter(prefix="/agent/commands", tags=["Agent Commands"])

# @router.post("/execute-pattern")
# async def execute_pattern(): ...
