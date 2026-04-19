# Module 16: Distributed Orchestration (Ray)

## Files Covered
- `src/graph_cortex/infrastructure/inference/llm_router.py`
- `src/graph_cortex/core/agents/base_agent.py`
- `src/graph_cortex/core/agents/researcher.py`
- `src/graph_cortex/core/agents/summarizer.py`

---

## What These Files Do

These files form the **Orchestration Layer** (Phase 3). They replace the single-threaded script execution with a highly decoupled, asynchronous, scalable swarm of AI Agents. 

By leveraging the **Ray** distributed computing framework, we achieve three critical things:
1. **Hardware Decoupling:** The heavy LLM inference logic (`llm_router.py`) sits on its own compute deployment. It can scale across multiple GPUs without freezing the Neo4j queries.
2. **Concurrency:** The `ResearchAgent` answers the user immediately, while the `SummaryAgent` runs in the background analyzing the turn and updating the Graph Database silently.
3. **Provider Agnosticism:** The Agents do not know what an "API Key" or "Gemini" is. They just fire generic async requests at the Ray Serve endpoint.

---

## Full Code with Line-by-Line Explanation

### 1. The LLM Router (`llm_router.py`)

```python
from ray import serve
from google import genai
from graph_cortex.config.llm import GEMINI_API_KEY, LLM_MODEL

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1})
class LLMEngineDeployment:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = LLM_MODEL
```
`@serve.deployment`: This Python decorator is pure magic. It tells the Ray Cluster to spin up instances of this class on dedicated hardware worker nodes. If we set `num_replicas=5`, Ray would auto-balance traffic perfectly across 5 copies.

```python
    async def __call__(self, request: dict) -> dict:
        system_prompt = request.get("system_prompt", "")
        user_input = request.get("user_input", "")
        context = request.get("context", "")
        
        # ... prompt building logic ...
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt
        )
        return {"status": "success", "response": response.text}

app = LLMEngineDeployment.bind()
```
`__call__`: This is the endpoint that receives Remote Procedure Calls (RPCs).
`LLMEngineDeployment.bind()`: This binds the code into an application that `main.py` can serve on `localhost:8000`.

### 2. The Base Agent (`base_agent.py`)

```python
import ray
from ray import serve

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
```
Any child inheriting from `BaseAgent` automatically checks if the Ray runtime is active.

```python
    async def query_llm(self, user_input: str, context: str = "") -> dict:
        handle = serve.get_deployment("LLMEngineDeployment").get_handle()
        
        response_ref = await handle.remote({
            "system_prompt": self.system_prompt,
            "user_input": user_input,
            "context": context
        })
        return response_ref
```
`.get_handle()` finds the deployment inside the Ray cluster. 
`await handle.remote()` sends the JSON packet asynchronously over the local network to the LLM node, yielding execution so the Python loop isn't frozen.

### 3. The Researcher (`researcher.py`)

```python
class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Researcher", system_prompt=DEFAULT_RESEARCHER_PROMPT)
        self.retrieval_engine = RetrievalEngine()
```
The Researcher holds an instance of the `RetrievalEngine` we built in Phase 2.

```python
    async def process_query(self, user_query: str) -> dict:
        retrieval_results = self.retrieval_engine.retrieve([user_query])
        
        # ... logic to format retrieval_results into a string block ...
            
        llm_response = await self.query_llm(user_input=user_query, context=context_string)
        return {"answer": llm_response.get("response")}
```
The flow is strictly sequential:
1. Hit the Neo4j Graph.
2. Package the Graph Output into text.
3. Throw it over the Ray async wall to the `LLMRouter`.

### 4. The Summarizer (`summarizer.py`)

```python
class SummaryAgent(BaseAgent):
    def __init__(self):
        struct_prompt = (
            "You MUST return ONLY a valid JSON object ...\n"
            '{"summary": "...", "entities": [{"entity": "Name1", ...}]}'
        )
        super().__init__(name="Summarizer", system_prompt=struct_prompt)
```
The Summarizer is built for strict JSON compliance. In a larger iteration, we would use strict schema tools (like Outlines or Instructor), but prompt engineering handles the base logic.

```python
    async def extract_and_consolidate(self, user_input: str, agent_response: str) -> dict:
        interaction_text = f"User: {user_input}\nAgent: {agent_response}"
        llm_response = await self.query_llm(user_input=interaction_text)
        
        raw_text =  llm_response.get("response", "{}")
        # Cleans out annoying markdown block tags often hallucinated by Gemini
        raw_text = re.sub(r"^```json\s*", "", raw_text)

        extracted_data = json.loads(raw_text)
        return extracted_data
```
The Summarizer receives BOTH sides of the conversation (`user_input` and `agent_response`), analyzes them objectively, and forces an extraction that `main.py` can pipe into `MemoryManager.consolidate_episode()`.

---

## How it Upgrades the Core Architecture

By removing the `LLM` code from `MemoryManager` and placing it here, **GraphCortex achieves true architectural decoupling.** 
You can switch your LLM provider to Claude tomorrow, and the Database Logic will never need a single line of code modified. You can scale the DB into Kubeernetes, and the Agents won't break.
