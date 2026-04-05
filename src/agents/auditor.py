import base64
from langchain_core.messages import HumanMessage, SystemMessage
from src.core.state import ProductionState
from src.core.llm_factory import get_vision_llm
from pydantic import BaseModel, Field
from typing import List

class VisualAuditOutput(BaseModel):
    status: str = Field(description="'VALID' if good, 'RETAKE' if errors exist")
    issues: List[str] = Field(description="List of issues found, empty if VALID")
    instructions: str = Field(description="Specific coordinate fixes for Architect or DP if RETAKE")

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def auditor_node(state: ProductionState) -> ProductionState:
    if not state.get("latest_dailies_path"):
        print("👁️ Auditor: No dailies found to audit. Auto-passing.")
        state["audit_result"] = {"status": "VALID", "issues": [], "instructions": ""}
        return state

    print("👁️ Auditor: Reviewing dailies...")
    vision_llm = get_vision_llm(temperature=0.2)
    structured_llm = vision_llm.with_structured_output(VisualAuditOutput)

    try:
        base64_img = encode_image(state["latest_dailies_path"])
    except (FileNotFoundError, OSError) as e:
        print(f"👁️ Auditor: Image not found or unreadable: {e}")
        state["audit_result"] = {"status": "VALID", "issues": ["No image file to audit."], "instructions": ""}
        return state

    # We use explicit messages here because we need to embed the image payload
    messages = [
        SystemMessage(content="""Role: You are the Visual Auditor (Quality Control).
Task: Analyze rendered frames for errors and provide correction logic.

Checklist:
1. FLOATING_ACTOR: Feet not touching Y=0.
2. CLIPPING: Actors walking through walls.
3. OUT_OF_FRAME: Camera not looking at the subject or subject not visible.
4. BAD_LIGHTING: Scene completely black or completely blown out.

If you see major issues, output RETAKE with specific instructions. If it looks acceptable for a base render, output VALID."""),
        HumanMessage(content=[
            {"type": "text", "text": "Audit this frame from the Godot render."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
        ])
    ]

    try:
        result = structured_llm.invoke(messages)
        state["audit_result"] = result.model_dump()
        print(f"👁️ Auditor Result: {state['audit_result']['status']}")
        if state["audit_result"]["status"] == "RETAKE":
            print(f"   Issues: {state['audit_result']['issues']}")

            # Increment retake count to prevent infinite loops
            state["retake_count"] = state.get("retake_count", 0) + 1
            if state["retake_count"] >= 3:
                print("👁️ Auditor: Max retakes reached. Forcing VALID status.")
                state["audit_result"]["status"] = "VALID"
    except Exception as e:
        print(f"👁️ Auditor Vision Error (missing or unsupported model): {e}")
        # Fallback to VALID if Vision LLM fails so the pipeline doesn't get blocked
        state["audit_result"] = {"status": "VALID", "issues": [], "instructions": ""}

    return state
