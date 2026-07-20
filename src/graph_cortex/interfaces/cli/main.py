import sys
import os
import asyncio
import uuid
import logging
import warnings

os.makedirs("Logs", exist_ok=True)
logging.basicConfig(
    filename='Logs/admin_system.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def _redirect_warnings(message, category, filename, lineno, *args, **kwargs):
    with open('Logs/warnings.log', 'a') as f:
        f.write(f"{category.__name__}: {message} ({filename}:{lineno})\n")

warnings.showwarning = _redirect_warnings

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.agents.researcher import ResearchAgent
from graph_cortex.core.agents.summarizer import SummaryAgent
from graph_cortex.core.agents.librarian import LibrarianAgent
from graph_cortex.core.rl.trainer import RLPyTorchTrainer
from graph_cortex.infrastructure.db.falkordb_connection import get_graph

console = Console()

BANNER = """
[bold #FFBF00] ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗[/][bold #10B981]  ██████╗  ██████╗ ██████╗ ████████╗███████╗██╗  ██╗[/]
[bold #FFBF00]██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║[/][bold #10B981] ██╔════╝ ██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝[/]
[bold #FFBF00]██║  ███╗██████╔╝███████║██████╔╝███████║[/][bold #10B981] ██║      ██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ [/]
[bold #FFBF00]██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║[/][bold #10B981] ██║      ██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ [/]
[bold #FFBF00]╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║[/][bold #10B981] ╚██████╗ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗[/]
[bold #FFBF00] ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝[/][bold #10B981]  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝[/]

[dim italic #6B7280]          neuro-symbolic graph memory for AI agents[/]
[dim italic #3B82F6]                    powered by FalkorDB[/]
"""


async def _librarian_loop(librarian: LibrarianAgent, session_id: str):
    logging.info(f"Librarian background loop started ({session_id})")
    while True:
        try:
            await asyncio.sleep(60)
            await librarian.curate("Periodic maintenance cycle", session_id=session_id)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Librarian loop error: {e}")
            await asyncio.sleep(10)


async def run_repl():
    console.print(Panel(BANNER, border_style="#1D9E75", padding=(1, 2), expand=False))

    with console.status("[bold #1D9E75]Initializing schema...[/]"):
        load_dotenv(override=False)
        initialize_schema()

        manager = MemoryManager()
        researcher = ResearchAgent()
        summarizer = SummaryAgent()
        librarian = LibrarianAgent()

    console.print()
    console.print("[bold green]Online.[/] Memory swarm active.")
    console.print("[dim]Tip: tail -f Logs/admin_system.log in another terminal[/]")
    console.print("Type [bold cyan]/help[/] for commands.\n")

    session_id = "hard_bench"
    manager.working.add_interaction(session_id)
    logging.info(f"New session: {session_id}")

    pending_tasks = set()
    librarian_task = asyncio.create_task(_librarian_loop(librarian, session_id))

    while True:
        try:
            user_input = await asyncio.to_thread(console.input, "\n[bold cyan]User >[/] ")
            user_input = user_input.strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                break

            if user_input.startswith("/"):
                cmd = user_input.split()[0].lower()

                if cmd == "/clear":
                    librarian_task.cancel()
                    session_id = f"session_{uuid.uuid4().hex[:8]}"
                    manager.working.add_interaction(session_id)
                    console.print(f"[bold yellow]New session:[/] {session_id}")
                    librarian_task = asyncio.create_task(_librarian_loop(librarian, session_id))

                elif cmd == "/history":
                    console.print(f"[cyan]Session:[/] {session_id}")

                elif cmd == "/stats":
                    console.print("[cyan]Swarm:[/] Researcher/Summarizer/Librarian alive")

                elif cmd == "/monitor":
                    stats = librarian.get_stats()
                    table = Table(title="Librarian Monitor", border_style="purple")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="bold white")
                    table.add_row("Sanitized", str(stats["sanitized_nodes"]))
                    table.add_row("Curations", str(stats["total_curations"]))
                    for k, v in stats["actions"].items():
                        table.add_row(f"  {k}", str(v))
                    console.print(Panel(table, border_style="purple"))

                elif cmd == "/curate":
                    console.print("[yellow]Running librarian...[/]")
                    info = await librarian.curate(f"Manual trigger for {session_id}", session_id=session_id)
                    console.print(f"[green]Done:[/] {info.get('action_name', '?')} -> {info.get('status', '?')}")

                elif cmd == "/data":
                    graph = get_graph()
                    result = graph.query("MATCH (n) RETURN labels(n)[0] as label, count(*) as count")
                    node_str = " | ".join([
                        f"{row[0]}: [bold]{row[1]}[/]"
                        for row in result.result_set
                    ])

                    ds_path = "data/rl_training/hotpot_qa_sample.jsonl"
                    ds_count = 0
                    if os.path.exists(ds_path):
                        with open(ds_path) as f:
                            ds_count = sum(1 for _ in f)

                    console.print(Panel(
                        f"Graph: {node_str}\nRL Dataset: [bold yellow]{ds_count}[/] samples",
                        title="[green]Dashboard[/]", border_style="green"
                    ))

                elif cmd == "/train":
                    console.print("[yellow]Starting RL training...[/]")
                    trainer = RLPyTorchTrainer()
                    await asyncio.to_thread(trainer.run_training_loop, episodes=3)
                    console.print("[green]Done.[/]")

                elif cmd == "/help":
                    help_text = (
                        "• [cyan]/data[/]     - graph + dataset stats\n"
                        "• [cyan]/train[/]    - run RL training\n"
                        "• [cyan]/curate[/]   - trigger librarian manually\n"
                        "• [cyan]/monitor[/]  - librarian metrics\n"
                        "• [cyan]/stats[/]    - swarm health\n"
                        "• [cyan]/history[/]  - current session\n"
                        "• [cyan]/clear[/]    - new session\n"
                        "• [cyan]/exit[/]     - shutdown"
                    )
                    console.print(Panel(help_text, title="Commands", border_style="cyan"))

                elif cmd in ("/quit", "/exit"):
                    break
                else:
                    console.print("[red]Unknown command. Try /help[/]")
                continue

            manager.working.add_message(session_id, role="user", content=user_input)
            logging.info(f"Query: {user_input}")

            with console.status("[bold #7F77DD]Querying...[/]"):
                result = await researcher.process_query(user_input, session_id=session_id)
                answer = result["answer"]

            console.print("[bold #22C55E]Agent:[/] ", end="")
            console.print(Markdown(answer))
            console.print("")
            manager.working.add_message(session_id, role="agent", content=answer)

            async def _consolidate(u_in, a_resp, s_id):
                try:
                    extracted = await summarizer.extract_and_consolidate(u_in, a_resp)
                    manager.consolidate_episode(s_id, extracted.get("summary", ""), extracted.get("entities", []))
                except Exception as e:
                    logging.error(f"Consolidation failed: {e}")

            task = asyncio.create_task(_consolidate(user_input, answer, session_id))
            pending_tasks.add(task)
            task.add_done_callback(pending_tasks.discard)

        except (EOFError, KeyboardInterrupt):
            break

    librarian_task.cancel()
    if pending_tasks:
        with console.status(f"[#1D9E75]Syncing {len(pending_tasks)} background tasks...[/]"):
            await asyncio.gather(*pending_tasks, return_exceptions=True)

    console.print("\n[bold green]Shutdown complete.[/]")


def main():
    try:
        asyncio.run(run_repl())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
