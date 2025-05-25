from fastapi import APIRouter, HTTPException, Body, Depends, Request, Query, Path
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Dict, Any, AsyncGenerator, Union, Optional
from uuid import UUID
from pydantic import BaseModel, Field
import json
import asyncio

router = APIRouter(prefix="/tools", tags=["NLWeb & MCP"])

# @router.post("/nlweb/ask")
# async def nlweb_ask(): ...
# @router.post("/mcp/execute")
# async def mcp_execute(): ...
