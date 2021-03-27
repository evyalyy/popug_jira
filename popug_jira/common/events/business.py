from pydantic import BaseModel
from datetime import datetime


class TaskCreatedBE(BaseModel):
    task_id: int
    description: str


class TaskAssignedBE(BaseModel):
    task_id: int
    assignee_id: int


class TaskClosedBE(BaseModel):
    task_id: int
    assignee_id: int


class DailyPaymentCompleted(BaseModel):
    account_id: int
    amount: int
    ts: datetime
