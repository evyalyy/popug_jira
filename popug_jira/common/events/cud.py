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
