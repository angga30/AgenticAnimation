from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import NotRequired

class Shot(TypedDict):
    id: str
    action: str
    duration: float
    entities: List[str]

class Treatment(TypedDict):
    mood: str
    tempo: str

class CameraData(TypedDict):
    position: List[float]
    target: List[float]
    fov: float
    movement: Dict[str, Any]

class LightingData(TypedDict):
    ambient: Dict[str, Any]
    directional: Dict[str, Any]
    fog: Dict[str, Any]

class SetDesignData(TypedDict):
    structures: List[Dict[str, Any]]
    props: List[Dict[str, Any]]

class PerformanceData(TypedDict):
    actor_id: str
    animation: str
    path_coords: List[List[float]]

class VisualAuditResult(TypedDict):
    status: str  # "VALID" or "RETAKE"
    issues: List[str]
    instructions: str

class ScenarioData(TypedDict):
    title: str
    setting: str
    characters: List[Dict[str, str]]
    dialogue: List[Dict[str, str]]

class ProductionState(TypedDict):
    # Inputs
    user_prompt: str

    # Pre-Production Outputs
    scenario: NotRequired[ScenarioData]
    generated_assets: NotRequired[Dict[str, str]] # map of actor_id -> filepath

    # Director Outputs
    treatment: NotRequired[Treatment]
    shots: NotRequired[List[Shot]]
    current_shot_index: NotRequired[int]

    # Per-shot Production Data (The JSON Contract parts)
    camera: NotRequired[CameraData]
    lighting: NotRequired[LightingData]
    set_design: NotRequired[SetDesignData]
    performance: NotRequired[PerformanceData]

    # Bridge and Render Outputs
    latest_dailies_path: NotRequired[Optional[str]]

    # Audit Outputs
    audit_result: NotRequired[VisualAuditResult]
    retake_count: NotRequired[int]
