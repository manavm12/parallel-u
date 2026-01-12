"""FastAPI application for Parallel U MVP."""

import logging
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from parallel_u.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from parallel_u.schemas import (
    RunRequest,
    RunResponse,
    ChatRequest,
    ChatResponse,
    SynthesizeRequest,
)
from parallel_u.clients import OpenAIClient, MinoClient
from parallel_u.services import SessionStore


# Global instances
session_store = SessionStore()
openai_client: OpenAIClient | None = None
mino_client: MinoClient | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize clients on startup."""
    global openai_client, mino_client

    settings = get_settings()

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required")
    if not settings.mino_api_key:
        raise RuntimeError("MINO_API_KEY environment variable is required")

    openai_client = OpenAIClient(api_key=settings.openai_api_key)
    mino_client = MinoClient(
        api_key=settings.mino_api_key,
        base_url=settings.mino_base_url,
    )

    yield


app = FastAPI(
    title="Parallel U",
    description="Your digital clone that explores the web while you're busy",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/v1/plan")
async def plan_exploration(request: RunRequest):
    """
    Create a browsing plan using OpenAI.
    
    Returns the goal and list of browsing tasks without executing them.
    """
    if openai_client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        plan = openai_client.plan(
            topics=request.topics,
            depth=request.depth,
            time_budget_min=request.time_budget_min,
        )
        return {
            "goal": plan.goal,
            "tasks": [{"website": t.website, "instructions": t.instructions} for t in plan.tasks]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")


@app.post("/v1/run", response_model=RunResponse)
async def run_exploration(request: RunRequest):
    """
    Run a complete exploration cycle.

    Flow:
    1. OpenAI planner creates a browsing plan
    2. Mino executes the browsing tasks
    3. OpenAI synthesizer creates the condensed brief
    4. Returns brief + session_id for follow-up chat
    """
    settings = get_settings()
    debug_info = {} if settings.debug else None

    # Ensure clients are initialized
    if openai_client is None or mino_client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Step 1: Plan the exploration
    try:
        plan = openai_client.plan(
            topics=request.topics,
            depth=request.depth,
            time_budget_min=request.time_budget_min,
        )
        if debug_info is not None:
            debug_info["plan"] = plan.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")

    # Step 2: Execute browsing tasks with Mino
    try:
        tasks = [{"website": t.website, "instructions": t.instructions} for t in plan.tasks]
        logger.info(f"Executing {len(tasks)} browsing tasks with Mino...")
        for i, task in enumerate(tasks):
            logger.info(f"  Task {i+1}: {task['website']}")

        browsing_results = await mino_client.run_multiple(tasks)

        # Log results
        for i, result in enumerate(browsing_results):
            logger.info(f"  Result {i+1}: status={result.get('status')}, "
                       f"content_length={len(result.get('content', ''))}, "
                       f"error={result.get('error', 'none')}")

        if debug_info is not None:
            debug_info["browsing_results"] = browsing_results
    except Exception as e:
        logger.error(f"Browsing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Browsing failed: {str(e)}")

    # Check if any browsing succeeded
    successful_results = [r for r in browsing_results if r.get("status") == "completed"]
    if not successful_results:
        # Log warning but continue - synthesizer will handle empty results
        logger.warning("No browsing tasks completed successfully")
        # Check if there were errors
        errors = [r.get("error") for r in browsing_results if r.get("error")]
        if errors:
            logger.warning(f"Errors: {errors}")

    # Step 3: Synthesize the brief
    try:
        brief = openai_client.synthesize(
            goal=plan.goal,
            topics=request.topics,
            browsing_results=browsing_results,
        )
        if debug_info is not None:
            debug_info["brief"] = brief.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")

    # Step 4: Create session for follow-up chat
    session_id = session_store.create(
        user_id=request.user_id,
        topics=request.topics,
        goal=plan.goal,
        brief=brief,
        browsing_results=browsing_results,
    )

    return RunResponse(
        goal=plan.goal,
        brief=brief,
        session_id=session_id,
        debug=debug_info,
    )


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with your digital clone about the exploration results.

    Requires a valid session_id from a previous /v1/run call.
    """
    if openai_client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    session = session_store.get(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please run /v1/run first to create a session.",
        )

    try:
        # Get AI response
        response_text = openai_client.chat(
            question=request.message,
            goal=session.goal,
            topics=session.topics,
            brief=session.brief,
            browsing_results=session.browsing_results,
            chat_history=session.chat_history,
        )

        # Store the conversation
        session_store.add_chat_message(request.session_id, "user", request.message)
        session_store.add_chat_message(request.session_id, "assistant", response_text)

        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/v1/synthesize", response_model=RunResponse)
async def synthesize_results(request: SynthesizeRequest):
    """
    Synthesize browsing results into a condensed brief.
    
    Takes browsing results and creates a personalized intelligence brief.
    """
    if openai_client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        brief = openai_client.synthesize(
            goal=request.goal,
            topics=request.topics,
            browsing_results=request.browsing_results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")
    
    # Create session for follow-up chat
    session_id = session_store.create(
        user_id=request.user_id,
        topics=request.topics,
        goal=request.goal,
        brief=brief,
        browsing_results=request.browsing_results,
    )
    
    return RunResponse(
        goal=request.goal,
        brief=brief,
        session_id=session_id,
    )


@app.delete("/v1/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session to free up resources."""
    if session_store.delete(session_id):
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")
