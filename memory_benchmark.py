import asyncio
import time
from rich.console import Console

from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.agents.researcher import ResearchAgent
from graph_cortex.core.agents.summarizer import SummaryAgent
from graph_cortex.infrastructure.db.falkordb_connection import get_graph

console = Console()

async def run_memory_recall_test():
    console.print("[bold cyan]Starting End-to-End Memory Recall Benchmark...[/bold cyan]\n")
    
    # 1. Reset Database
    graph = get_graph()
    graph.query("MATCH (n) DETACH DELETE n")
    initialize_schema()
    
    # 2. Initialize Agents
    session_id = "e2e_memory_bench"
    manager = MemoryManager()
    researcher = ResearchAgent()
    summarizer = SummaryAgent()
    
    manager.working.add_interaction(session_id)
    
    # 3. Define the Conversation Transcript
    conversation = [
        "i hear nasa is making a telescope that will use the sail is it true?",
        "wow thats so awesome.",
        "so i found out that jason my friends stored his keys in a place named orilona which is a box inside his bedroom. keep it in memory.",
        "what is the haber process?",
        "lets talk about solar wind propulsion system. what do you know about it?",
        "but whats the optimal angle for the sail to be in for maximum propulsion?",
        "Btw where did jason store his keys?"
    ]
    
    # 4. Simulate the Conversation Loop
    for turn_idx, user_input in enumerate(conversation):
        console.print(f"[bold yellow]Turn {turn_idx + 1}[/bold yellow] | [bold white]User:[/] {user_input}")
        
        manager.working.add_message(session_id, role="user", content=user_input)
        
        # Step A: Researcher answers the query (using graph retrieval if applicable)
        start_time = time.time()
        result = await researcher.process_query(user_input, session_id=session_id)
        answer = result["answer"]
        query_time = time.time() - start_time
        
        manager.working.add_message(session_id, role="agent", content=answer)
        
        # Shorten the printed answer so it doesn't flood the console
        short_answer = answer.replace('\n', ' ')[:150] + ("..." if len(answer) > 150 else "")
        console.print(f"[bold green]Agent ({query_time:.2f}s):[/] {short_answer}")
        
        # Step B: Summarizer extracts entities and saves to Episodic/Semantic Graph
        console.print(f"[dim]  -> Background Summarizer extracting entities...[/dim]")
        start_time = time.time()
        extracted = await summarizer.extract_and_consolidate(user_input, answer)
        
        entities = extracted.get("entities", [])
        if entities:
            console.print(f"[dim]  -> Extracted {len(entities)} entities! Consolidating into graph...[/dim]")
            manager.consolidate_episode(session_id, extracted.get("summary", ""), entities)
        else:
            console.print(f"[dim]  -> No entities extracted for this turn.[/dim]")
            
        sum_time = time.time() - start_time
        console.print(f"[dim]  -> Summarizer finished in {sum_time:.2f}s[/dim]\n")
        
        # If this is the final query, evaluate the recall success
        if "where did jason store his keys" in user_input.lower():
            console.print("[bold cyan]--- FINAL EVALUATION ---[/bold cyan]")
            success = "orilona" in answer.lower() or "bedroom" in answer.lower()
            if success:
                console.print("[bold green]✅ PASS: The agent successfully recalled where Jason stored his keys from the graph![/bold green]")
            else:
                console.print("[bold red]❌ FAIL: The agent failed to recall the memory fragment.[/bold red]")
                
    # Final Graph Stats
    count_res = graph.query("MATCH (n) RETURN count(n)").result_set
    console.print(f"\n[bold magenta]Total Nodes in Graph at end of test: {count_res[0][0]}[/bold magenta]")

if __name__ == "__main__":
    asyncio.run(run_memory_recall_test())
