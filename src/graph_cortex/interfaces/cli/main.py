import sys
import asyncio
import uuid
import ray
from ray import serve
from dotenv import load_dotenv
import logging
import os

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.markdown import Markdown

from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.agents.researcher import ResearchAgent
from graph_cortex.core.agents.summarizer import SummaryAgent
from graph_cortex.infrastructure.inference.llm_router import LLMEngineDeployment

console = Console()

# Stylized ASCII representation of the banner.svg SVG connections
BANNER = """
[bold #1a1a1a]Graph[/][bold #0F6E56]Cortex[/]
[dim italic #6B7280]Distributed neuro-symbolic graph memory for AI agents[/]

    [#9FE1CB]o[/][dim #1D9E75]----[/][#CECBF6]o[/]                   [#CECBF6]o[/][dim #1D9E75]-[/][#9FE1CB]o[/]
  [dim #1D9E75]/[/]       [dim #1D9E75]\\[/][#9FE1CB]o[/]                 [dim #1D9E75]/[/]  [dim #1D9E75]\\[/][#CECBF6]o[/]
[#CECBF6]o[/][dim #1D9E75]--[/][#9FE1CB]o[/]          [#9FE1CB]o[/]         [#9FE1CB]o[/]       [#CECBF6]o[/]
"""

async def run_repl():
    console.print(Panel(BANNER, border_style="#1D9E75", padding=(1, 2), expand=False))
    
    with console.status("[bold #1D9E75]Initializing Database Schema and Soft-Deletion Constraints...[/]") as status:
        # Explicitly reload .env to ensure the latest API keys are loaded into the current process
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")

        initialize_schema()
        
        status.update("[bold #7F77DD]Connecting to local Ray cluster...[/]")
        # Suppress massive ray dashboard logs on standard out for clean REPL
        if not ray.is_initialized():
            try:
                ray.init(ignore_reinit_error=True, log_to_driver=False, include_dashboard=False)
            except ConnectionError:
                os.environ.pop("RAY_ADDRESS", None)
                ray.init(ignore_reinit_error=True, log_to_driver=False, include_dashboard=False)
            
        status.update("[bold #1D9E75]Deploying Gemini LLM Router via Ray Serve...[/]")
        serve.start(detached=True)
        # Use bind() parameters to force-feed the fresh API key into the Ray workers
        serve.run(LLMEngineDeployment.bind(api_key=api_key, model=model_name), name="LLMEngineDeployment", route_prefix="/llm")
        
        manager = MemoryManager()
        researcher = ResearchAgent()
        summarizer = SummaryAgent()

    console.print()
    console.print("[bold green]System Online.[/] Memory Swarm deployed and observing.")
    console.print("[dim]Admin Tip: View live architecture operations by running `tail -f Logs/admin_system.log` in another terminal.[/]")
    console.print("Type [bold cyan]/help[/] for commands. Press [bold cyan]Ctrl+C[/] to exit.\n")
    
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    manager.working.add_interaction(session_id)
    logging.info(f"Initialized new REPL Session: {session_id}")
    
    while True:
        try:
            # Safely release the asyncio thread to wait for standard input so it doesn't freeze the console spinner!
            user_input = await asyncio.to_thread(console.input, "\n[bold cyan]User >[/] ")
            user_input = user_input.strip()
            if not user_input:
                continue
                
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
                    console.print("[bold cyan]Swarm Stats:[/] Ray Cluster Active. Gemini Router Bound. Researcher/Summarizer Alive.")
                    logging.info("User requested /stats.")
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
            
            console.print(Markdown(f"**Agent**: {agent_response}"))
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
            
            asyncio.create_task(background_consolidation(user_input, agent_response, session_id))
            
        except (EOFError, KeyboardInterrupt):
            break

    console.print("\n[bold green]GraphCortex Swarm shutting down. Goodbye![/]")

def setup_admin_logger():
    """Sets up the split admin pipeline to a physical file so the REPL is never corrupted by debug prints."""
    os.makedirs("Logs", exist_ok=True)
    logging.basicConfig(
        filename='Logs/admin_system.log',
        level=logging.INFO, 
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logging.info("--- Boot Sequence Started ---")

def main():
    setup_admin_logger()
    try:
        asyncio.run(run_repl())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
