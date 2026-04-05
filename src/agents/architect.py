from langchain_core.prompts import ChatPromptTemplate
from src.core.state import ProductionState
from src.core.llm_factory import get_llm
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class CSGStructure(BaseModel):
    type: str = Field(description="Type of CSG node, usually 'csg_box'")
    operation: str = Field(description="'union' or 'subtraction'")
    size: List[float] = Field(description="[x, y, z] dimensions in meters")
    position: List[float] = Field(description="[x, y, z] coordinates")
    color: str = Field(description="Hex color code for the material")

class SetDesignOutput(BaseModel):
    structures: List[CSGStructure]
    props: List[Dict[str, Any]] = Field(default_factory=list)

def architect_node(state: ProductionState) -> ProductionState:
    llm = get_llm(temperature=0.2)
    structured_llm = llm.with_structured_output(SetDesignOutput)

    current_shot = state["shots"][state.get("current_shot_index", 0)]
    treatment = state.get("treatment", {})

    audit_feedback = ""
    if state.get("audit_result") and state["audit_result"]["status"] == "RETAKE":
        audit_feedback = f"AUDITOR FEEDBACK TO FIX: {state['audit_result']['instructions']}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Role: You are the Production Designer (3D Set Builder).
Task: Build a 3D set in Godot using CSG operations.

Rules:
1. SCALE: 1.0 unit = 1 meter. Floor is ALWAYS at Y=0.
2. GEOMETRY: Use "csg_box" for walls/floors. Use "union" to build, "subtraction" to create holes.
3. SPATIAL LOGIC: Ensure there is enough space (min 3m width) for actors. Floor thickness should be at negative Y to keep top at Y=0.

{audit_feedback}"""),
        ("user", "Build a set for this shot Action: {action} | Mood: {mood}")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "action": current_shot["action"],
        "mood": treatment.get("mood", "neutral"),
        "audit_feedback": audit_feedback
    })

    state["set_design"] = result.model_dump()
    print("🏗️ Architect: Built set geometry.")
    return state
