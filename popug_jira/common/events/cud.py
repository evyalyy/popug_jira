from typing import List
from datetime import datetime
from pydantic import BaseModel


class AccountCreatedCUDv2(BaseModel):
    account_id: int
    name: str
    email: str
    phone_number: str
    slack_id: str
    roles: List[int]


class AccountChangedCUDv2(BaseModel):
    account_id: int
    name: str
    email: str
    phone_number: str
    slack_id: str
    roles: List[int]


class TransactionCreated(BaseModel):
    account_id: int
    task_id: int = 0
    kind: int
    ts: datetime


class TaskCostAssigned(BaseModel):
    task_id: int
    description: str
    cost_assign: int
    cost_close: int
