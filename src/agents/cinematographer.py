from langchain_core.prompts import ChatPromptTemplate
from src.core.state import ProductionState
from src.core.llm_factory import get_llm
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class MovementModel(BaseModel):
    type: str = Field(description="e.g., 'dolly', 'pan', 'orbit', or 'static'")
    speed: float = Field(description="duration of movement in seconds")

class CameraOutput(BaseModel):
    position: List[float] = Field(description="[x, y, z] starting position")
    target: List[float] = Field(description="[x, y, z] look_at target coordinates")
    fov: float = Field(description="35 for emotional/tight, 75 for wide/epic")
    movement: MovementModel

def cinematographer_node(state: ProductionState) -> ProductionState:
    llm = get_llm(temperature=0.5)
    structured_llm = llm.with_structured_output(CameraOutput)

    current_shot = state["shots"][state.get("current_shot_index", 0)]
    treatment = state.get("treatment", {})
    performance = state.get("performance", {})
    actor_pos = performance.get("path_coords", [[0,0,0]])[0] if performance else [0,0,0]

    audit_feedback = ""
    if state.get("audit_result") and state["audit_result"]["status"] == "RETAKE":
        audit_feedback = f"AUDITOR FEEDBACK TO FIX: {state['audit_result']['instructions']}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Role: You are the Cinematographer (Camera Operator).
Task: Define Camera3D parameters and movement.

Logic:
1. FOV: 35 for emotional/tight shots, 75 for wide/environment shots.
2. MOVEMENT: Use "dolly", "pan", or "orbit". Don't use static unless absolutely necessary.
3. TARGETING: Always use 'look_at' target coordinates to keep the actor in frame.

{audit_feedback}"""),
        ("user", "Shot Action: {action} | Mood: {mood} | Actor is at: {actor_pos}. Plan the shot.")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "action": current_shot["action"],
        "mood": treatment.get("mood", "neutral"),
        "actor_pos": actor_pos,
        "audit_feedback": audit_feedback
    })

    state["camera"] = result.model_dump()
    print(f"🎥 Cinematographer: Set camera FOV {state['camera']['fov']} and movement {state['camera']['movement']['type']}.")
    return state
