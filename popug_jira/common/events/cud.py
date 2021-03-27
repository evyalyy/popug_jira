from typing import List
from pydantic import BaseModel

class AccountCreatedCUD(BaseModel):
    account_id: int
    name: str
    email: str
    roles: List[int]

class AccountChangedCUD(BaseModel):
    account_id: int
    name: str
    email: str
    roles: List[int]

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