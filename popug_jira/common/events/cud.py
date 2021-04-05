from typing import List
from datetime import datetime
from pydantic import BaseModel


class AccountCreatedCUDv2(BaseModel):
    account_public_id: str
    name: str
    email: str
    phone_number: str
    slack_id: str
    roles: List[int]


class AccountChangedCUDv2(BaseModel):
    account_public_id: str
    name: str
    email: str
    phone_number: str
    slack_id: str
    roles: List[int]


class TransactionCreated(BaseModel):
    account_public_id: str
    task_public_id: str = None
    kind: int
    ts: datetime


class TaskCostAssigned(BaseModel):
    task_public_id: str
    description: str
    cost_assign: int
    cost_close: int
