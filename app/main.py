from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from agent.message_graph import get_agent_response, conversation_sessions
from app.memory import update_state, get_state, get_all_states, clear_state
import uuid
import logging
from typing import Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TailorTalk API", 
    version="1.0.0",
    description="AI-powered calendar assistant using LangGraph and OpenRouter"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel):
    message: str = Field(..., description="User message to process")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant response")
    user_id: str = Field(..., description="User session identifier")
    tool_calls_made: Optional[list] = Field(default=[], description="List of tools called during processing")
    session_info: Optional[dict] = Field(default={}, description="Additional session information")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    active_sessions: int

@app.get("/", response_model=dict)
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "TailorTalk API is running!",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "test_calendar": "/test-calendar",
            "test_llm": "/test-llm",
            "sessions": "/sessions"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(input: ChatInput):
    """Main chat endpoint for interacting with TailorTalk"""
    try:
        # Generate user ID if not provided
        user_id = input.user_id or str(uuid.uuid4())
        
        # Log the incoming request
        logger.info(f"Chat request from user {user_id[:8]}...: {input.message[:100]}...")
        
        # Update conversation state in memory module
        user_state = get_state(user_id)
        message_count = user_state.get('message_count', 0) + 1
        update_state(user_id, 'message_count', message_count)
        update_state(user_id, 'last_message', input.message)
        update_state(user_id, 'last_interaction', datetime.now().isoformat())
        
        # Get agent response using LangGraph
        response = get_agent_response(input.message, user_id)
        
        # Get session info from LangGraph state
        session_state = conversation_sessions.get(user_id, {})
        tool_calls_made = session_state.get('tool_calls_made', [])
        
        # Log the response
        logger.info(f"Response to user {user_id[:8]}...: {response[:100]}...")
        
        return ChatResponse(
            response=response,
            user_id=user_id,
            tool_calls_made=tool_calls_made,
            session_info={
                "message_count": message_count,
                "pending_clarification": session_state.get('pending_clarification', False)
            }
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        active_sessions=len(conversation_sessions)
    )

@app.get("/test-calendar")
def test_calendar():
    """Test endpoint to check calendar connectivity"""
    try:
        from app.tools import tool_list_events
        logger.info("Testing calendar connectivity...")
        result = tool_list_events()
        return {
            "status": "success",
            "message": "Calendar connection successful",
            "calendar_test": result
        }
    except Exception as e:
        logger.error(f"Calendar test failed: {str(e)}")
        return {
            "status": "error",
            "message": "Calendar connection failed",
            "error": str(e)
        }

@app.get("/test-llm")
def test_llm():
    """Test endpoint to check OpenRouter/LLM connectivity"""
    try:
        logger.info("Testing LLM connectivity...")
        result = get_agent_response("Hello, this is a connectivity test", "test_user")
        return {
            "status": "success",
            "message": "LLM connection successful",
            "llm_test": result
        }
    except Exception as e:
        logger.error(f"LLM test failed: {str(e)}")
        return {
            "status": "error",
            "message": "LLM connection failed",
            "error": str(e)
        }

@app.get("/sessions")
def get_sessions():
    """Get information about active sessions"""
    try:
        memory_states = get_all_states()
        langgraph_sessions = len(conversation_sessions)
        
        session_info = {}
        for user_id, state in memory_states.items():
            session_info[user_id] = {
                "message_count": state.get('message_count', 0),
                "last_interaction": state.get('last_interaction', 'Unknown'),
                "last_message": state.get('last_message', '')[:50] + '...' if state.get('last_message', '') else '',
                "has_langgraph_session": user_id in conversation_sessions
            }
        
        return {
            "status": "success",
            "total_memory_sessions": len(memory_states),
            "total_langgraph_sessions": langgraph_sessions,
            "sessions": session_info
        }
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.delete("/sessions/{user_id}")
def clear_user_session(user_id: str):
    """Clear a specific user's session"""
    try:
        # Clear from memory module
        clear_state(user_id)
        
        # Clear from LangGraph sessions
        if user_id in conversation_sessions:
            del conversation_sessions[user_id]
        
        return {
            "status": "success",
            "message": f"Session for user {user_id} cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.delete("/sessions")
def clear_all_sessions():
    """Clear all user sessions"""
    try:
        # Clear memory states
        from app.memory import conversation_state
        conversation_state.clear()
        
        # Clear LangGraph sessions
        conversation_sessions.clear()
        
        return {
            "status": "success",
            "message": "All sessions cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing all sessions: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting TailorTalk API server...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=True
    )