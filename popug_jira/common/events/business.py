from pydantic import BaseModel
from datetime import datetime


class TaskCreated(BaseModel):
    task_public_id: str
    description: str


class TaskAssigned(BaseModel):
    task_public_id: str
    assignee_public_id: str


class TaskClosed(BaseModel):
    task_public_id: str
    assignee_public_id: str


class DailyPaymentCompleted(BaseModel):
    account_public_id: int
    amount: int
    ts: datetime
