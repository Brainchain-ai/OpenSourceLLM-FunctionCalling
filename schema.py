from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class Step(BaseModel):
    plan_step_index: int
    dependencies: List[int] = []
    step: str

class Plan(BaseModel):
    steps: List[Step]
