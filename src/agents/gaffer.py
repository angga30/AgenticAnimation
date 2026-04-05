from langchain_core.prompts import ChatPromptTemplate
from src.core.state import ProductionState
from src.core.llm_factory import get_llm
from pydantic import BaseModel, Field
from typing import Dict, Any

class LightSettings(BaseModel):
    color: str = Field(description="Hex color code")
    energy: float = Field(description="Intensity from 0.0 to 2.0")

class DirectionalLight(LightSettings):
    direction: list[float] = Field(description="[x, y, z] normalized vector for light direction")

class FogSettings(BaseModel):
    enabled: bool
    density: float

class LightingOutput(BaseModel):
    ambient: LightSettings
    directional: DirectionalLight
    fog: FogSettings

def gaffer_node(state: ProductionState) -> ProductionState:
    llm = get_llm(temperature=0.6)
    structured_llm = llm.with_structured_output(LightingOutput)

    current_shot = state["shots"][state.get("current_shot_index", 0)]
    treatment = state.get("treatment", {})

    audit_feedback = ""
    if state.get("audit_result") and state["audit_result"]["status"] == "RETAKE":
        audit_feedback = f"AUDITOR FEEDBACK TO FIX: {state['audit_result']['instructions']}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Role: You are the Gaffer (Lighting & Mood Specialist).
Task: Configure WorldEnvironment and Light3D nodes.

Directives:
1. COLOR: Use Hex codes based on the mood (e.g., #FF4400 for sunset).
2. INTENSITY: Set Energy from 0.0 to 2.0.
3. ENVIRONMENT: Use Fog if mood is mysterious or horror.
4. SHADOWS: Shadows are enabled globally. Ensure lighting highlights the actor.

{audit_feedback}"""),
        ("user", "Design lighting for action: {action} with mood: {mood}.")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "action": current_shot["action"],
        "mood": treatment.get("mood", "neutral"),
        "audit_feedback": audit_feedback
    })

    state["lighting"] = result.model_dump()
    print("💡 Gaffer: Designed lighting rig.")
    return state
