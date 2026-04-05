import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.core.state import ProductionState
from src.agents import (
    director_node,
    architect_node,
    animator_node,
    cinematographer_node,
    gaffer_node,
    auditor_node,
    screenwriter_node,
    asset_generator_node
)
from src.bridge import GodotRunner
import uuid

def render_bridge_node(state: ProductionState) -> ProductionState:
    """Executes the Godot build and render for a dailies frame."""
    print("🎬 Render Bridge: Initiating digital production (Dailies)...")

    contract_data = {
        "set_design": state.get("set_design", {}),
        "lighting": state.get("lighting", {}),
        "camera": state.get("camera", {}),
        "performance": state.get("performance", {})
    }

    runner = GodotRunner(debug=True)
    unique_filename = f"dailies_shot_{state.get('current_shot_index', 0)}_retake_{state.get('retake_count', 0)}_{uuid.uuid4().hex[:6]}.png"

    dailies_path = runner.execute_pipeline(contract_data, output_path=unique_filename, mode="frame")

    if dailies_path:
        state["latest_dailies_path"] = dailies_path
    else:
        print("⚠️ Render Bridge: Failed to generate dailies!")
        state["latest_dailies_path"] = None

    return state

def final_video_render_node(state: ProductionState) -> ProductionState:
    """Executes the Godot movie writer after passing the audit."""
    print("🎞️ Render Bridge: Auditor passed. Rendering final video sequence...")

    contract_data = {
        "set_design": state.get("set_design", {}),
        "lighting": state.get("lighting", {}),
        "camera": state.get("camera", {}),
        "performance": state.get("performance", {})
    }

    runner = GodotRunner(debug=True)
    video_filename = f"final_shot_{state.get('current_shot_index', 0)}_{uuid.uuid4().hex[:6]}.mp4"

    video_path = runner.execute_pipeline(contract_data, output_path=video_filename, mode="video")
    if video_path:
        print(f"✅ Final video rendered: {video_path}")
    else:
        print("⚠️ Render Bridge: Failed to generate final video!")

    return state

def should_retake(state: ProductionState) -> str:
    """Router logic to handle self-healing loop with bounded retakes."""
    audit_status = state.get("audit_result", {}).get("status", "RETAKE") # Default fail closed

    if audit_status == "RETAKE":
        retake_count = state.get("retake_count", 0)

        MAX_RETAKES = 3
        if retake_count < MAX_RETAKES:
            print(f"🔄 Production: Retake requested by Auditor ({retake_count+1}/{MAX_RETAKES}). Rebuilding scene...")
            return "architect"
        else:
            print("⚠️ Production: Max retakes reached. Failing forward to final render.")
            return "final_video_render"

    return "final_video_render"

def next_shot_node(state: ProductionState) -> ProductionState:
    """Updates state to prepare for the next shot in the sequence."""
    current_index = state.get("current_shot_index", 0)

    next_index = current_index + 1
    state["current_shot_index"] = next_index
    state["retake_count"] = 0
    return state

def should_continue_shots(state: ProductionState) -> str:
    """Router logic to handle multiple shots in a sequence after state is updated."""
    current_index = state.get("current_shot_index", 0)
    total_shots = len(state.get("shots", []))

    if current_index < total_shots:
        print(f"🎬 Moving to Shot {current_index + 1}/{total_shots}")
        return "architect"

    print("🎉 Production Complete! All shots finished.")
    return END

def build_production_graph() -> StateGraph:
    """Constructs the LangGraph orchestration pipeline."""
    workflow = StateGraph(ProductionState)

    # Add nodes
    workflow.add_node("screenwriter", screenwriter_node)
    workflow.add_node("asset_generator", asset_generator_node)
    workflow.add_node("director", director_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("animator", animator_node)
    workflow.add_node("cinematographer", cinematographer_node)
    workflow.add_node("gaffer", gaffer_node)
    workflow.add_node("render_bridge", render_bridge_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("final_video_render", final_video_render_node)
    workflow.add_node("next_shot_node", next_shot_node)

    # The pipeline is fully sequential for production, then branches at audit
    workflow.add_edge("screenwriter", "asset_generator")
    workflow.add_edge("asset_generator", "director")
    workflow.add_edge("director", "architect")
    workflow.add_edge("architect", "animator")
    workflow.add_edge("animator", "cinematographer")
    workflow.add_edge("cinematographer", "gaffer")
    workflow.add_edge("gaffer", "render_bridge")
    workflow.add_edge("render_bridge", "auditor")

    # Conditional Edges for self-healing
    workflow.add_conditional_edges(
        "auditor",
        should_retake,
        {
            "architect": "architect",
            "final_video_render": "final_video_render"
        }
    )

    workflow.add_edge("final_video_render", "next_shot_node")

    workflow.add_conditional_edges(
        "next_shot_node",
        should_continue_shots,
        {
            "architect": "architect",
            END: END
        }
    )

    # Set Entry Point
    workflow.set_entry_point("screenwriter")

    return workflow.compile()

if __name__ == "__main__":
    # Ensure dependencies are loaded
    from dotenv import load_dotenv
    load_dotenv()

    app = build_production_graph()

    print("==================================================")
    print("🎬 Welcome to Aegis-Motion Digital Film Crew")
    print("==================================================")

    user_prompt = input("Enter your script or prompt: ")

    initial_state = ProductionState(
        user_prompt=user_prompt,
        retake_count=0
    )

    final_state = app.invoke(initial_state)
    print("Workflow executed successfully.")
