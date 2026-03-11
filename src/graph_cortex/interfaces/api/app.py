from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uuid
import ray
import asyncio
from ray import serve
import logging
import os

from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.agents.researcher import ResearchAgent
from graph_cortex.core.agents.summarizer import SummaryAgent
from graph_cortex.core.agents.librarian import LibrarianAgent
from graph_cortex.infrastructure.inference.llm_router import LLMEngineDeployment

# Global components
manager = None
researcher = None
summarizer = None
librarian = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager, researcher, summarizer, librarian
    
    # Initialize Ray
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    serve.start(detached=True)
    
    # Deploy LLM Router (assuming ENV vars are present)
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("LLM_MODEL", "models/gemini-1.5-flash")
    
    if not api_key:
        logging.error("GEMINI_API_KEY missing. API will fail.")
    
    serve.run(LLMEngineDeployment.bind(api_key=api_key, model=model_name), name="LLMEngineDeployment", route_prefix="/llm")
    
    # Initialize agents
    manager = MemoryManager()
    researcher = ResearchAgent()
    summarizer = SummaryAgent()
    librarian = LibrarianAgent()
    
    # Start Librarian background task
    librarian_task = asyncio.create_task(librarian.run_autonomous_loop(interval=60))
    app.state.librarian_task = librarian_task
    
    yield
    
    # Cleanup
    librarian_task.cancel()
    serve.shutdown()
    ray.shutdown()

app = FastAPI(title="GraphCortex Memory Swarm API", lifespan=lifespan)

class QueryRequest(BaseModel):
    message: str
    session_id: str = None

class QueryResponse(BaseModel):
    session_id: str
    response: str
    status: str

@app.get("/health")
async def health():
    return {"status": "online", "ray": ray.is_initialized()}

@app.get("/monitor")
async def monitor():
    if not librarian:
        raise HTTPException(status_code=503, detail="Librarian not initialized")
    return librarian.get_stats()

@app.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    session_id = request.session_id or f"api_session_{uuid.uuid4().hex[:8]}"
    
    try:
        # 1. Research
        research_context = f"Internal Swarm Memory Session: {session_id}"
        thought_process = await researcher.research(request.message, context=research_context)
        
        # 2. Summarize & Extract
        summary_obj = await summarizer.summarize_and_extract(thought_process["thoughts"])
        
        # 3. Commit to Long-Term Memory
        manager.long_term.commit_knowledge(summary_obj)
        
        return QueryResponse(
            session_id=session_id,
            response=thought_process["thoughts"],
            status="committed"
        )
    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/curate")
async def manual_curate():
    if not librarian:
        raise HTTPException(status_code=503, detail="Librarian not initialized")
    
    context = "Manual API trigger for graph optimization."
    result = librarian.curate(context)
    return result
