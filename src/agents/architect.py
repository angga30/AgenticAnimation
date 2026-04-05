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
Task: Build a 3D set in Godot using CSG operations and arrange props correctly.

Rules:
1. SCALE: 1.0 unit = 1 meter. Floor is ALWAYS at Y=0. Build tables or floors explicitly if requested using "csg_box".
2. GEOMETRY: Use "csg_box" for walls/floors. Use "union" to build, "subtraction" to create holes.
3. SPATIAL LOGIC: Ensure there is enough space (min 3m width) for actors. Avoid placing props exactly at 0,0,0 to prevent Z-fighting with actors.

{audit_feedback}"""),
        ("user", "Build a set for this shot Action: {action} | Mood: {mood}")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "action": current_shot["action"],
        "mood": treatment.get("mood", "neutral"),
        "audit_feedback": audit_feedback
    })

    set_data = result.model_dump()

    # Inject generated assets for background and props with realistic scaling and offset
    assets = state.get("generated_assets", {})
    props_list = []

    scenario_props = state.get("scenario", {}).get("props", [])
    for i, prop in enumerate(scenario_props):
        prop_id = prop.get("id")
        desc = prop.get("description", "").lower()
        if prop_id and prop_id in assets:
            # Simple heuristic scaling: if it's an apple or book, make it small
            scale_val = 1.0
            if any(word in desc for word in ["apple", "buku", "book", "small", "kecil", "ring", "coin"]):
                scale_val = 0.2
            elif any(word in desc for word in ["table", "meja", "chair", "kursi"]):
                scale_val = 1.2

            props_list.append({
                "id": prop_id,
                "asset_path": assets[prop_id],
                "position": [float(i * 1.0 - 1.5), scale_val/2.0, -2.0 - (i * 0.5)], # Spread props out in Z and X to prevent Z-fighting
                "scale": [scale_val, scale_val, scale_val]
            })

    set_data["props"] = props_list

    if "background_01" in assets:
        set_data["background"] = {
            "asset_path": assets["background_01"],
            "position": [0, 5, -15], # far back
            "size": [20, 10]
        }

    state["set_design"] = set_data
    print("🏗️ Architect: Built set geometry and placed props/background.")
    return state
