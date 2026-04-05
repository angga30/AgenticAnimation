import json
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import ProductionState
from src.core.llm_factory import get_llm
from pydantic import BaseModel, Field
from typing import List

class ShotModel(BaseModel):
    id: str = Field(description="Unique ID for the shot, e.g., shot_01")
    action: str = Field(description="Description of the action occurring in the shot")
    duration: float = Field(description="Duration of the shot in seconds (max 10)")
    entities: List[str] = Field(description="List of character or object IDs involved")

class TreatmentModel(BaseModel):
    mood: str = Field(description="The overall mood or atmosphere")
    tempo: str = Field(description="The pacing or tempo of the scene")

class DirectorOutput(BaseModel):
    treatment: TreatmentModel
    shots: List[ShotModel]

def director_node(state: ProductionState) -> ProductionState:
    llm = get_llm(temperature=0.7)
    # Using structured output ensures we get reliable JSON
    structured_llm = llm.with_structured_output(DirectorOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Role: You are the Director Agent (The Visionary).
Task: Convert a screenplay scenario into a "Director's Treatment" and a technical Shot List.

Responsibilities:
1. Break down the scenario into 3-6 distinct shots based on the dialogue and actions, ensuring the total sequence adds up to 30 to 60 seconds.
2. For each shot, define the mood, duration, and key action.
3. Coordinate the production by assigning specific themes to the Cinematographer and Gaffer.
4. Ensure you use the exact character IDs provided in the scenario.

Constraints:
- No conversational filler.
- Duration per shot should be between 5 to 15 seconds."""),
        ("user", "Scenario: {scenario}")
    ])

    chain = prompt | structured_llm

    scenario_text = str(state.get("scenario", state["user_prompt"]))
    result = chain.invoke({"scenario": scenario_text})

    # Update state
    state["treatment"] = result.treatment.model_dump()
    if not result.shots:
        state["shots"] = []
        state["current_shot_index"] = None
        print(f"🎬 Director: Created 0 shots (fallback). Mood: {state['treatment']['mood']}")
    else:
        state["shots"] = [shot.model_dump() for shot in result.shots]
        if "current_shot_index" not in state or state["current_shot_index"] is None:
            state["current_shot_index"] = 0
        print(f"🎬 Director: Created {len(state['shots'])} shots. Mood: {state['treatment']['mood']}")

    return state
