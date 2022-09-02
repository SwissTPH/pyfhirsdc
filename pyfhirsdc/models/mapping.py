from __future__ import annotations 
from typing import List, Optional
from pydantic import BaseModel
# for recursive definition
import random
import string 
class MappingIO(BaseModel):
    url : str
    alias: Optional[str]
    
class MappingGroupIO(BaseModel):
    name : str
    type: Optional[str]
    note: Optional[str]
    
class MappingRule(BaseModel):
    name : Optional[str]
    expression: str
    rules : List[MappingRule] =[]
        
    def __init__(self, **data):
        super().__init__(**data)
        if self.name is None:
            self.name = ''.join(random.choices(string.ascii_lowercase, k=5))

class MappingGroup(BaseModel):
    name :str
    sources :  List[MappingGroupIO]
    targets :  List[MappingGroupIO]
    rules : List[MappingRule] = []
    groups: List[MappingGroup] = []
    note: Optional[str]


class Mapping(BaseModel):
    name: str
    url: str
    sources: List[MappingIO]
    targets : List[MappingIO]
    products: List[MappingIO] = []
    groups: List[MappingGroup] = []
    
    