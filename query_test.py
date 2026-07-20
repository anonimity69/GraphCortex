import asyncio
from dotenv import load_dotenv
from graph_cortex.core.agents.researcher import ResearchAgent

async def main():
    load_dotenv(override=False)
    researcher = ResearchAgent()
    session_id = "hard_bench"
    user_input = "Can you tell me about the battery issues in Project Orion?"
    
    print(f"Querying: {user_input}")
    
    # We simulate an entity extraction step by passing the core entities to retrieval
    retrieval_results = researcher.retrieval_engine.retrieve(["Project Orion"], session_id=session_id)
    
    context_string = ""
    if retrieval_results["status"] == "Hit":
        nodes = retrieval_results["network"]
        edges = retrieval_results.get("edges", [])

        context_string = "Retrieved Knowledge Graph Context:\n"
        context_string += "### Entities & Concepts:\n"
        for node in nodes:
            context_string += f"- ({node['type']}) {node['name']} [Distance: {node['distance']}]\n"

        context_string += "\n### Relationships:\n"
        for edge in edges:
            context_string += f"- ({edge['source_name']}) -[{edge['rel_type']}]-> ({edge['target_name']})\n"
            
    print(context_string)
    
    llm_response = await researcher.query_llm(user_input=user_input, context=context_string)
    final_answer = llm_response.get("response", "Error generating response.")
    
    print("\n--- Agent Response ---")
    print(final_answer)
    print("----------------------\n")
    
    with open("agent_response.txt", "w") as f:
        f.write(final_answer)

if __name__ == "__main__":
    asyncio.run(main())
