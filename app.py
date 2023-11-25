from fastapi import FastAPI
from fastapi import HTTPException, BackgroundTasks
from planner import Planner
from executor import Executor
from pydantic import BaseModel
import asyncio
import os
import promptlayer
from promptlayer import openai
promptlayer.api_key = os.environ["PROMPTLAYER_API_KEY"]
openai.api_type = "azure"
openai.api_key = os.environ["AZURE_OPENAI_API_KEY"]
openai.api_base = "https://brainchainuseast2.openai.azure.com"
openai.api_version = "2023-08-01-preview"
from schema import Step, Plan

class PlanRequest(BaseModel):
    prompt: str

app = FastAPI()

@app.post("/v1/agents/plans/create")
async def create_plan(plan_request: PlanRequest):
    api_keys = {
        "PROMPTLAYER_API_KEY": os.environ["PROMPTLAYER_API_KEY"],
        "AZURE_OPENAI_API_KEY": os.environ["AZURE_OPENAI_API_KEY"]
    }
    planner = Planner(model="gpt-4-32k", temperature=0.5)
    try:
        plan = await planner.generate_plan(plan_request.prompt)
        return {"plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




from typing import Optional

class PlanAndExecuteRequest(BaseModel):
    temp: float = 0.2
    prompt: Optional[str] = None
    plan: Plan = None

class ExecuteRequest(BaseModel):
    temp: float = 0.2
    prompt: Optional[str] = None
    plan: Plan = None

@app.post("/v1/agents/executions/create")
async def execute_plan(execute_request: ExecuteRequest):
    plan = execute_request.plan
    temp = execute_request.temp
    if plan == None or len(plan.dict()) == 0 and execute_request.prompt != None and len(execute_request.prompt) != 0:
        api_keys = {
            "PROMPTLAYER_API_KEY": os.environ["PROMPTLAYER_API_KEY"],
            "AZURE_OPENAI_API_KEY": os.environ["AZURE_OPENAI_API_KEY"]
        }
        planner = Planner(model="gpt-4-32k", temperature=temp)
        try:
            plan = await planner.generate_plan(execute_request.prompt)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    if plan:        
        plan_length = len(plan.steps)
        prompt = execute_request    .prompt
        step_results = {}
        futures = {}

    # Function to execute a single step
        async def execute_step(step):
            # Wait for dependencies to be resolved
            for dep in step.dependencies:
                await futures[dep]
        # Execute the step and store the result
            executor = Executor(step=step, dependency_results={k: step_results[k] for k in step.dependencies})
            result = await executor.begin(prev_steps=[step_results[d] for d in step.dependencies])
            step_results[step.plan_step_index] = result
            return result

        # Create and execute futures for each step
        try:
            for step in plan.steps:
                futures[step.plan_step_index] = asyncio.ensure_future(execute_step(step))
            await asyncio.gather(*futures.values())

            step = Step(step=f"Based on the original user's question: {prompt}, use the results from the plan execution to respond to the user's question. Please include footnotes, references to other sources, and citations for the information used in the response. You may use the following information: {step_results}.", plan_step_index=plan_length, dependencies=[])
            
            answering_agent = Executor(step=step, dependency_results={})
            response = await answering_agent.begin(prev_steps=[])
            return {"response": response, "results": step_results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=500, detail="No plan provided")