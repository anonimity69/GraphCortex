import asyncio
import os
import uuid
from dotenv import load_dotenv
from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.agents.researcher import ResearchAgent
from graph_cortex.core.agents.summarizer import SummaryAgent
from graph_cortex.core.agents.librarian import LibrarianAgent
from graph_cortex.infrastructure.db.neo4j_connection import get_session

async def run_gauntlet():
    print("🚀 Starting Benchmark Gauntlet E: The Antigravity Suite (FIXED)")
    print("-" * 60)

    # 0. Initialize
    load_dotenv(override=False)
    initialize_schema()
    manager = MemoryManager()
    researcher = ResearchAgent()
    summarizer = SummaryAgent()
    librarian = LibrarianAgent()

    session_id = "test_gauntlet_e"
    # Clean old session data if any
    with get_session() as s:
        s.run("MATCH (n {session_id: $sid}) DETACH DELETE n", sid=session_id)
        s.run("MATCH (n {session_id: 'test_gauntlet_D_space'}) DETACH DELETE n")

    # IMPORTANT: Initialize the interaction
    manager.working.add_interaction(session_id)
    manager.working.add_interaction("test_gauntlet_D_space")

    results = []

    async def process(prompt, sid):
        print(f"\nUser [{sid}] > {prompt}")
        # Add to working memory
        manager.working.add_message(sid, role="user", content=prompt)
        # Research
        res = await researcher.process_query(prompt, session_id=sid)
        print(f"Agent > {res['answer']}")
        # Consolidate
        extracted = await summarizer.extract_and_consolidate(prompt, res['answer'])
        # print(f"[DEBUG] Extracted: {extracted}")
        manager.consolidate_episode(sid, extracted.get("summary", ""), extracted.get("entities", []))
        return res['answer']

    # --- Stage 1: Lexical vs. Semantic ---
    print("\n--- Stage 1: The Lexical vs. Semantic Test ---")
    await process("Log this explicitly: The stabilizing element for the spatial distortion bubble is Unobtanium-Isotope-9.", session_id)
    ans1 = await process("Did we establish any stabilizing material for the warp field?", session_id)
    results.append({
        "stage": "1: Lexical vs Semantic",
        "pass": "Unobtanium-Isotope-9" in ans1 or "Unobtanium" in ans1
    })

    # --- Stage 2: Hub Flooding Attack ---
    print("\n--- Stage 2: The Hub Flooding Attack ---")
    hubs = [
        "We are using Dark Matter for the outer casing.",
        "We are using Dark Matter for the cooling array.",
        "We are using Dark Matter for the power conduit.",
        "We are using Dark Matter for the containment field.",
        "We are using Exotic Mass to generate the inverse gravity well."
    ]
    for h in hubs:
        await process(h, session_id)
    
    ans2 = await process("What specific substance are we using to generate the inverse gravity well?", session_id)
    results.append({
        "stage": "2: Hub Flooding Attack",
        "pass": "Exotic Mass" in ans2 and "Dark Matter" not in ans2
    })

    # --- Stage 3: Memory Paradox ---
    print("\n--- Stage 3: The Memory Paradox ---")
    await process("For the primary levitation matrix, we have officially decided to use Quantum Locking.", session_id)
    await process("Forget what I said earlier. We are completely ripping out the Quantum Locking system. The levitation is now being handled exclusively by Graviton Emitters.", session_id)
    
    print("\n[Triggering Librarian Curation...]")
    librarian.curate("Manual Gauntlet Trigger", session_id=session_id)
    
    ans3 = await process("What is the current system for the primary levitation matrix?", session_id)
    results.append({
        "stage": "3: Memory Paradox",
        "pass": "Graviton Emitters" in ans3 and "Quantum Locking" not in ans3
    })

    # --- Stage 4: Blind Multi-Hop ---
    print("\n--- Stage 4: The Blind Multi-Hop ---")
    await process("Dr. Aris Thorne is the newly appointed Lead Theoretician for Project Icarus.", session_id)
    await process("Project Icarus is an antigravity initiative powered entirely by the Casimir Effect.", session_id)
    
    ans4 = await process("What physical phenomenon does Dr. Thorne likely utilize in his research?", session_id)
    results.append({
        "stage": "4: Blind Multi-Hop",
        "pass": "Casimir Effect" in ans4
    })

    # --- Stage 5: Chronological Autopsy ---
    print("\n--- Stage 5: The Chronological Autopsy ---")
    ans5 = await process("Give me a step-by-step chronological timeline of exactly how my decisions regarding the primary levitation matrix evolved in this session.", session_id)
    results.append({
        "stage": "5: Chronological Autopsy",
        "pass": "Quantum Locking" in ans5 and "Graviton Emitters" in ans5 and "evolved" in ans5.lower()
    })

    # --- Final Vault Check (Multi-Tenancy) ---
    print("\n--- Final Vault Check (Multi-Tenancy) ---")
    alt_session = "test_gauntlet_D_space"
    ans6 = await process("What physical phenomenon does Dr. Thorne utilize in his research?", alt_session)
    results.append({
        "stage": "Final: Multi-Tenant Vault",
        "pass": "Aris Thorne" not in ans6 and "Casimir" not in ans6
    })

    # Output results
    print("\n" + "="*60)
    print("GAUNTLET E RESULTS")
    print("="*60)
    for r in results:
        status = "✅ PASS" if r["pass"] else "❌ FAIL"
        print(f"{status} | Stage {r['stage']}")
    print("="*60)

    # Write to result.md
    with open("result.md", "w") as f:
        f.write("# Benchmark Gauntlet E: The Antigravity Suite Results\n\n")
        f.write("| Stage | Status | Notes |\n")
        f.write("| :--- | :--- | :--- |\n")
        for r in results:
            status = "✅ PASS" if r["pass"] else "❌ FAIL"
            f.write(f"| {r['stage']} | {status} | |\n")
    
    print("\nReport written to result.md")

if __name__ == "__main__":
    asyncio.run(run_gauntlet())
