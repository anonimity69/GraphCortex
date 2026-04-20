import sys
import os
import asyncio
import uuid
import logging
import warnings

# --- Global Logging & Warning Suppression (Must execute BEFORE 3rd party imports) ---
os.makedirs("Logs", exist_ok=True)
logging.basicConfig(
    filename='Logs/admin_system.log',
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logging.info("--- Boot Sequence Started ---")

def custom_formatwarning(message, category, filename, lineno, *args, **kwargs):
    with open('Logs/warnings.log', 'a') as f:
        f.write(f"{category.__name__}: {message} ({filename}:{lineno})\n")

warnings.showwarning = custom_formatwarning
from dotenv import load_dotenv
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.agents.researcher import ResearchAgent
from graph_cortex.core.agents.summarizer import SummaryAgent
from graph_cortex.core.agents.librarian import LibrarianAgent
from graph_cortex.core.rl.trainer import RLPyTorchTrainer
from graph_cortex.infrastructure.db.neo4j_connection import get_session
from rich.table import Table

console = Console()

# Stylized ASCII representation of the banner.svg SVG connections
BANNER = """
[bold #FFBF00] ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗[/][bold #10B981]  ██████╗  ██████╗ ██████╗ ████████╗███████╗██╗  ██╗[/]
[bold #FFBF00]██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║[/][bold #10B981] ██╔════╝ ██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝[/]
[bold #FFBF00]██║  ███╗██████╔╝███████║██████╔╝███████║[/][bold #10B981] ██║      ██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ [/]
[bold #FFBF00]██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║[/][bold #10B981] ██║      ██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ [/]
[bold #FFBF00]╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║[/][bold #10B981] ╚██████╗ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗[/]
[bold #FFBF00] ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝[/][bold #10B981]  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝[/]

[dim italic #6B7280]          Distributed neuro-symbolic graph memory[/]
[dim italic #6B7280]                        for AI agents[/]
"""

async def background_librarian_task(librarian_agent: LibrarianAgent):
    """
    Periodic background loop that triggers the Librarian to curate the graph.
    """
    logging.info("[Background] Librarian automation started.")
    while True:
        try:
            # Wake up every 60 seconds
            await asyncio.sleep(60)
            logging.info("[Background] Librarian waking up for periodic curation...")
            
            # Use current system heat as 'state' context for the policy
            context = "Self-maintenance cycle: Periodic graph optimization."
            librarian_agent.curate(context)
            
        except asyncio.CancelledError:
            logging.info("[Background] Librarian automation stopping...")
            break
        except Exception as e:
            logging.error(f"[Background Error] Librarian automation failed: {e}")
            await asyncio.sleep(10) # Wait before retry

async def run_repl():
    console.print(Panel(BANNER, border_style="#1D9E75", padding=(1, 2), expand=False))
    
    with console.status("[bold #1D9E75]Initializing Database Schema and Soft-Deletion Constraints...[/]") as status:
        load_dotenv(override=True)
        initialize_schema()
        
        manager = MemoryManager()
        researcher = ResearchAgent()
        summarizer = SummaryAgent()
        librarian = LibrarianAgent()

    console.print()
    console.print("[bold green]System Online.[/] Memory Swarm deployed and observing.")
    console.print("[dim]Admin Tip: View live architecture operations by running `tail -f Logs/admin_system.log` in another terminal.[/]")
    console.print("Type [bold cyan]/help[/] for commands. Press [bold cyan]Ctrl+C[/] to exit.\n")
    
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    manager.working.add_interaction(session_id)
    logging.info(f"Initialized new REPL Session: {session_id}")
    
    # Track background consolidation tasks to ensure they finish before CLI exit
    pending_tasks = set()
    
    # Start the automated Librarian loop
    librarian_task = asyncio.create_task(background_librarian_task(librarian))
    # librarian_task is NOT in pending_tasks because it's infinite.
    
    while True:
        try:
            # Safely release the asyncio thread to wait for standard input so it doesn't freeze the console spinner!
            user_input = await asyncio.to_thread(console.input, "\n[bold cyan]User >[/] ")
            user_input = user_input.strip()
            if not user_input:
                continue
                
            # Allow 'exit' or 'quit' as plain text commands
            if user_input.lower() in ("exit", "quit"):
                break
                
            if user_input.startswith("/"):
                cmd = user_input.split()[0].lower()
                if cmd == "/clear":
                    session_id = f"session_{uuid.uuid4().hex[:8]}"
                    manager.working.add_interaction(session_id)
                    console.print(f"[bold yellow]Working Memory flushed. New Session ID:[/] {session_id}")
                    logging.info(f"User commanded /clear. New Session: {session_id}")
                elif cmd == "/history":
                    console.print(f"[bold cyan]Current Active Session:[/] {session_id}")
                    logging.info("User requested /history.")
                elif cmd == "/stats":
                    console.print("[bold cyan]Swarm Stats:[/] Local Swarm Active (Direct SDK). Researcher/Summarizer/Librarian Alive.")
                elif cmd == "/monitor":
                    stats = librarian.get_stats()
                    
                    table = Table(title="[bold purple]Librarian Swarm Monitor[/]", border_style="purple")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="bold white")
                    
                    table.add_row("Nodes Sanitized (Error Purge)", str(stats["sanitized_nodes"]))
                    table.add_row("Total Curation Cycles", str(stats["total_curations"]))
                    table.add_row("Actions: NOOP", str(stats["actions"]["NOOP"]))
                    table.add_row("Actions: ADD", str(stats["actions"]["ADD"]))
                    table.add_row("Actions: UPDATE", str(stats["actions"]["UPDATE"]))
                    table.add_row("Actions: DELETE", str(stats["actions"]["DELETE"]))
                    
                    console.print(Panel(table, border_style="purple"))
                elif cmd == "/curate":
                    console.print("[bold yellow]Librarian Agent analyzing Graph topology...[/]")
                    context = f"Session {session_id} active. Continuous reasoning required."
                    curation_info = librarian.curate(context)
                    console.print(f"[bold green]Success:[/] Librarian took action: [bold cyan]{curation_info['status']}[/]")
                elif cmd == "/data":
                    # DB Dashboard
                    with get_session() as s:
                        nodes = s.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count")
                        node_str = " | ".join([f"{r['label']}: [bold]{r['count']}[/]" for r in nodes])
                        
                    # Dataset Dashboard
                    ds_path = "data/rl_training/hotpot_qa_sample.jsonl"
                    ds_count = 0
                    if os.path.exists(ds_path):
                        with open(ds_path, "r") as f:
                            ds_count = sum(1 for _ in f)
                    
                    console.print(Panel(
                        f"Graph Layer: {node_str}\n"
                        f"RL Dataset: [bold yellow]{ds_count}[/] samples in '{ds_path}'",
                        title="[bold green]Environment Dashboard[/]",
                        border_style="green"
                    ))
                elif cmd == "/train":
                    console.print("[bold yellow]Initiating RL Fine-Tuning Simulation...[/] (HotpotQA Dataset)")
                    trainer = RLPyTorchTrainer()
                    await asyncio.to_thread(trainer.run_training_loop, episodes=3)
                    console.print("[bold green]Success:[/] RL Session complete. Local policy gradients cached.")
                elif cmd == "/help":
                    help_text = (
                        "• [bold cyan]/help[/]    - Show this menu\n"
                        "• [bold cyan]/data[/]    - Display Graph and Training dataset statistics\n"
                        "• [bold cyan]/train[/]   - Run RL fine-tuning trial (Phase 4)\n"
                        "• [bold cyan]/stats[/]    - Show system operational health\n"
                        "• [bold cyan]/curate[/]   - Manually trigger the [bold purple]Librarian RL Agent[/] to optimize graph topology\n"
                        "• [bold cyan]/monitor[/]  - Live dashboard of Librarian sanitization & curation metrics\n"
                        "• [bold cyan]/history[/] - Show current session info\n"
                        "• [bold cyan]/clear[/]   - Flush working memory and start new session\n"
                        "• [bold cyan]/exit[/]    - Gracefully shutdown the swarm"
                    )
                    console.print(Panel(help_text, title="GraphCortex Commands", border_style="cyan"))
                elif cmd in ("/quit", "/exit"):
                    break
                else:
                    console.print("[red]Unknown command. Supported: /clear, /history, /stats, /exit[/]")
                continue

            manager.working.add_message(session_id, role="user", content=user_input)
            logging.info(f"[Query] {user_input}")
            
            with console.status("[bold #7F77DD]Researcher Agent querying Graph Topology...[/]"):
                research_result = await researcher.process_query(user_input)
                agent_response = research_result["answer"]
            
            console.print(f"[bold #22C55E]Agent:[/] ", end="")
            console.print(Markdown(agent_response))
            console.print("")
            manager.working.add_message(session_id, role="agent", content=agent_response)
            
            # Fire summarizer in the background
            async def background_consolidation(u_in, a_resp, s_id):
                try:
                    logging.info("[Summarizer] Beginning background memory consolidation...")
                    extracted = await summarizer.extract_and_consolidate(u_in, a_resp)
                    event_id = manager.consolidate_episode(s_id, extracted.get("summary", ""), extracted.get("entities", []))
                    logging.info(f"[Summarizer] Success. Episodic Event created: {event_id}")
                except Exception as e:
                    logging.error(f"[Summarizer Error] Background compilation failed: {str(e)}")
            
            task = asyncio.create_task(background_consolidation(user_input, agent_response, session_id))
            pending_tasks.add(task)
            task.add_done_callback(pending_tasks.discard)
            
        except (EOFError, KeyboardInterrupt):
            break

    # Shutdown flow
    librarian_task.cancel()
    if pending_tasks:
        with console.status(f"[bold #1D9E75]Syncing {len(pending_tasks)} pending background memories to Neo4j...[/]"):
            await asyncio.gather(*pending_tasks, return_exceptions=True)

    console.print("\n[bold green]GraphCortex Swarm shutting down. Goodbye![/]")

def main():
    try:
        asyncio.run(run_repl())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
