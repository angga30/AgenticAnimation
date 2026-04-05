from langchain_core.prompts import ChatPromptTemplate
from src.core.state import ProductionState
from src.core.llm_factory import get_llm
from pydantic import BaseModel, Field
from typing import List

class CharacterModel(BaseModel):
    id: str = Field(description="Unique character ID, e.g., char_01")
    name: str = Field(description="Character's name")
    description: str = Field(description="Visual description of the character for asset generation")

class DialogueLine(BaseModel):
    character_id: str
    text: str = Field(description="What the character says")
    action: str = Field(description="What the character is doing while speaking")

class ScenarioOutput(BaseModel):
    title: str
    setting: str = Field(description="Where the scene takes place")
    characters: List[CharacterModel]
    dialogue: List[DialogueLine]

def screenwriter_node(state: ProductionState) -> ProductionState:
    """Parses raw prompt into a structured screenplay."""
    llm = get_llm(temperature=0.8)
    structured_llm = llm.with_structured_output(ScenarioOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Role: You are the Screenwriter.
Task: Convert a simple idea into a structured scenario with characters and dialogue.

Rules:
1. Create 1 to 3 characters.
2. Define their visual appearance clearly.
3. Write a short sequence of dialogue and actions."""),
        ("user", "Prompt: {user_prompt}")
    ])

    chain = prompt | structured_llm
    result = chain.invoke({"user_prompt": state["user_prompt"]})

    state["scenario"] = result.model_dump()
    print(f"✍️ Screenwriter: Wrote scenario '{state['scenario']['title']}' with {len(state['scenario']['characters'])} characters.")
    return state
