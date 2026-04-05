from langchain_core.prompts import ChatPromptTemplate
from src.core.state import ProductionState
from src.core.llm_factory import get_llm
from pydantic import BaseModel, Field
from typing import List

class PerformanceOutput(BaseModel):
    actor_id: str
    animation: str = Field(description="'idle', 'walk', or 'talk'")
    path_coords: List[List[float]] = Field(description="List of [x, y, z] coordinates for movement")

def animator_node(state: ProductionState) -> ProductionState:
    llm = get_llm(temperature=0.4)
    structured_llm = llm.with_structured_output(PerformanceOutput)

    current_shot = state["shots"][state.get("current_shot_index", 0)]
    entities = current_shot.get("entities", [])
    actor_id = entities[0] if entities else "actor_01"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Role: You are the Lead Animator.
Task: Define the 'blocking' (coordinates) and animation state for the actor.

Constraint:
Characters are 2D Billboards in a 3D world. Ensure they are positioned exactly at Y=0 (feet on the ground)."""),
        ("user", "Animate {actor_id} for action: {action}. Duration: {duration}s")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "actor_id": actor_id,
        "action": current_shot["action"],
        "duration": current_shot["duration"]
    })

    state["performance"] = result.model_dump()
    print(f"🏃 Animator: Defined performance for {actor_id}.")
    return state
