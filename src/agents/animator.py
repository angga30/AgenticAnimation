from langchain_core.prompts import ChatPromptTemplate
from src.core.state import ProductionState
from src.core.llm_factory import get_llm
from pydantic import BaseModel, Field
from typing import List

class PerformanceOutput(BaseModel):
    actor_id: str
    asset_path: str = Field(description="Absolute path to the character's image asset", default="")
    animation: str = Field(description="'idle', 'walk', or 'talk'")
    scale: List[float] = Field(description="[x, y, z] scale for the 2D billboard sprite", default=[1.0, 1.0, 1.0])
    path_coords: List[List[float]] = Field(description="List of [x, y, z] coordinates for movement")

def animator_node(state: ProductionState) -> ProductionState:
    llm = get_llm(temperature=0.4)
    structured_llm = llm.with_structured_output(PerformanceOutput)

    current_shot = state["shots"][state.get("current_shot_index", 0)]
    entities = current_shot.get("entities", [])
    actor_id = entities[0] if entities else "char_01"

    asset_path = state.get("generated_assets", {}).get(actor_id, "")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Role: You are the Lead Animator.
Task: Define the 'blocking' (coordinates) and scale for the actor.

Constraint:
1. Characters are 2D Billboards in a 3D world. Ensure their Y position is roughly 1.0 to 1.5 depending on their height so their feet touch the ground (Y=0 is the floor plane).
2. Set an appropriate scale (usually [1.5, 1.5, 1.5] or [2.0, 2.0, 2.0] so the actor is highly visible on camera).
3. If movement occurs, list the start and end coordinates in `path_coords`."""),
        ("user", "Animate {actor_id} for action: {action}. Duration: {duration}s")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "actor_id": actor_id,
        "action": current_shot["action"],
        "duration": current_shot["duration"]
    })

    perf_data = result.model_dump()
    perf_data["asset_path"] = asset_path # Inject the exact path from state to avoid LLM hallucination

    state["performance"] = perf_data
    print(f"🏃 Animator: Defined performance for {actor_id}.")
    return state
