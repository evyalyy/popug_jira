from pydantic import BaseModel
from datetime import datetime


class TaskCreatedBE(BaseModel):
    task_public_id: str
    description: str


class TaskAssignedBE(BaseModel):
    task_public_id: str
    assignee_public_id: str


class TaskClosedBE(BaseModel):
    task_public_id: str
    assignee_public_id: str


class DailyPaymentCompleted(BaseModel):
    account_public_id: int
    amount: int
    ts: datetime
