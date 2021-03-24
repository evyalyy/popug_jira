from pydantic import BaseModel

class TaskCreatedBE(BaseModel):
    task_id: int
    description: str

class TaskAssignedBE(BaseModel):
    task_id: int
    assignee_id: int

class TaskClosedBE(BaseModel):
    task_id: int
    assignee_id: int
