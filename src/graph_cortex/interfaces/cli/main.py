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
os.environ["RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO"] = "0"
os.environ["RAY_SERVE_LOG_LEVEL"] = "error"

# Forcefully silence noisy third-party loggers BEFORE they initialize
logging.getLogger("ray").setLevel(logging.ERROR)
logging.getLogger("ray.serve").setLevel(logging.ERROR)
logging.getLogger("uvicorn").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
# ---------------------------------------------------------------------------------

import ray
from ray import serve
from dotenv import load_dotenv
# ---------------------------------------------------------------------------------

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.agents.researcher import ResearchAgent
from graph_cortex.core.agents.summarizer import SummaryAgent
from graph_cortex.core.agents.librarian import LibrarianAgent
from graph_cortex.infrastructure.inference.llm_router import LLMEngineDeployment
from graph_cortex.core.rl.trainer import RLPyTorchTrainer
from graph_cortex.infrastructure.db.neo4j_connection import get_session

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
        # Explicitly reload .env to ensure the latest API keys are loaded into the current process
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("LLM_MODEL")

        initialize_schema()
        
        status.update("[bold #7F77DD]Connecting to local Ray cluster...[/]")
        # Suppress massive ray dashboard logs on standard out for clean REPL
        if not ray.is_initialized():
            try:
                ray.init(
                    ignore_reinit_error=True, 
                    log_to_driver=False, 
                    include_dashboard=False,
                    logging_level=logging.ERROR,
                    configure_logging=True
                )
            except ConnectionError:
                os.environ.pop("RAY_ADDRESS", None)
                ray.init(
                    ignore_reinit_error=True, 
                    log_to_driver=False, 
                    include_dashboard=False,
                    logging_level=logging.ERROR,
                    configure_logging=True
                )
            
        status.update("[bold #1D9E75]Deploying LLM Router via Ray Serve...[/]")
        serve.start(detached=True)
        # Use bind() parameters to force-feed the fresh API key into the Ray workers
        serve.run(LLMEngineDeployment.bind(api_key=api_key, model=model_name), name="LLMEngineDeployment", route_prefix="/llm")
        
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
    
    # Track background summarization and librarian tasks to ensure they finish before CLI exit
    pending_tasks = set()
    
    # Start the automated Librarian loop
    librarian_task = asyncio.create_task(background_librarian_task(librarian))
    pending_tasks.add(librarian_task)
    
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
                    console.print("[bold cyan]Swarm Stats:[/] Ray Cluster Active. Gemini Router Bound. Researcher/Summarizer/Librarian Alive.")
                elif cmd == "/curate":
                    console.print("[bold yellow]Librarian Agent analyzing Graph topology...[/]")
                    # Use the last user query or a default as the "state" context
                    context = f"Session {session_id} active. Continuous reasoning required."
                    curation_info = librarian.curate(context)
                    console.print(f"[bold green]Success:[/] Librarian took action: [bold cyan]{curation_info['status']}[/]")
                    logging.info("User requested /stats.")
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
                    # Run a small batch to avoid quota exhaustion
                    await asyncio.to_thread(trainer.run_training_loop, episodes=3)
                    console.print("[bold green]Success:[/] RL Session complete. Local policy gradients cached.")
                elif cmd == "/help":
                    help_text = (
                        "• [bold cyan]/help[/]    - Show this menu\n"
                        "• [bold cyan]/data[/]    - Display Graph and Training dataset statistics\n"
                        "• [bold cyan]/train[/]   - Run RL fine-tuning trial (Phase 4)\n"
                        "• [bold cyan]/stats[/]    - Show system operational health\n"
                        "• [bold cyan]/curate[/]   - Manually trigger the [bold purple]Librarian RL Agent[/] to optimize graph topology\n"
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
            logging.info(f"[Response Generated]")
            
            # Fire summarizer in the background so the user is never blocked while Graph extracts
            async def background_consolidation(u_in, a_resp, s_id):
                try:
                    logging.info("[Summarizer] Beginning background memory consolidation...")
                    extracted = await summarizer.extract_and_consolidate(u_in, a_resp)
                    event_id = manager.consolidate_episode(s_id, extracted.get("summary", ""), extracted.get("entities", []))
                    logging.info(f"[Summarizer] Success. Episodic Event created: {event_id} with {len(extracted.get('entities', []))} relationships.")
                except Exception as e:
                    logging.error(f"[Summarizer Error] Background compilation failed: {str(e)}")
            
            task = asyncio.create_task(background_consolidation(user_input, agent_response, session_id))
            pending_tasks.add(task)
            task.add_done_callback(pending_tasks.discard)
            
        except (EOFError, KeyboardInterrupt):
            break

    if pending_tasks:
        with console.status(f"[bold #1D9E75]Syncing {len(pending_tasks)} pending background memories to Neo4j...[/]"):
            await asyncio.gather(*pending_tasks)

    console.print("\n[bold green]GraphCortex Swarm shutting down. Goodbye![/]")

def main():
    try:
        asyncio.run(run_repl())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
