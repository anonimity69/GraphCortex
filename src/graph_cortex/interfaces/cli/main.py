import uuid
import sys
import asyncio
import ray
from ray import serve

from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.agents.researcher import ResearchAgent
from graph_cortex.core.agents.summarizer import SummaryAgent
from graph_cortex.infrastructure.inference.llm_router import LLMEngineDeployment

async def async_main():
    print("=====================================================")
    print("🧠 GraphCortex Phase 3: Distributed Orchestration")
    print("=====================================================")
    
    print("\n[INIT] Initializing Neo4j Schema (Soft Deletion rules enabled)...")
    initialize_schema()
    
    print("\n[INIT] Connecting to Ray Cluster...")
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
        
    print("[INIT] Deploying LLMEngine (Gemini) to Ray Serve...")
    serve.start(detached=True)
    serve.run(LLMEngineDeployment.bind(), name="LLMEngineDeployment", route_prefix="/llm")
    
    # Instantiate Swarm and Utilities
    manager = MemoryManager()
    researcher = ResearchAgent()
    summarizer = SummaryAgent()
    
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    print(f"\n[SESSION] Started new multi-agent session: {session_id}")
    
    # ─── ACT 1: Working Memory Buffering ────────────────────────────────────
    user_input = "Could you explain what Clean Architecture is, and why we use it for Graph Databases?"
    print(f"\n[USER]: {user_input}")
    manager.working.add_interaction(session_id)
    manager.working.add_message(session_id, role="user", content=user_input)
    
    # ─── ACT 2: Research Agent (Retrieval + LLM Generation) ─────────────────
    print(f"\n[RESEARCHER] Taking the query...")
    research_result = await researcher.process_query(user_input)
    agent_response = research_result["answer"]
    
    print(f"\n[AGENT]: {agent_response}")
    manager.working.add_message(session_id, role="agent", content=agent_response)
    
    # ─── ACT 3: Summary Agent (Concurrent Knowledge Extraction) ─────────────
    print(f"\n[SUMMARIZER] Launching background extraction task...")
    
    # This simulates the summary agent running entirely decoupled from the main response loop
    extracted_knowledge = await summarizer.extract_and_consolidate(user_input, agent_response)
    
    print(f"\n[SUMMARIZER OUTPUT]:")
    print(f"  Summary: {extracted_knowledge.get('summary')}")
    print(f"  Entities Discovered: {len(extracted_knowledge.get('entities', []))}")
    for ent in extracted_knowledge.get("entities", []):
        print(f"    - {ent.get('entity', 'Unknown')} [{ent.get('relation', '--')}] -> {ent.get('concept', 'Unknown')}")
        
    # ─── ACT 4: Database Committing ─────────────────────────────────────────
    event_id = manager.consolidate_episode(
        session_id=session_id,
        generated_summary=extracted_knowledge.get("summary", ""),
        extracted_entities=extracted_knowledge.get("entities", [])
    )
    print(f"\n[STORAGE] Episode consolidated and written to graph. Event ID: {event_id}")

    print("\nPhase 3 Multi-Agent Orchestration complete! Check Neo4j Browser to see the new entities.")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    sys.exit(main())
