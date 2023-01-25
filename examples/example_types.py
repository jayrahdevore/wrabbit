'''

example_types.py | example type for wrabbit
This file is used in both the producer and the consumer

'''
from wrabbit import BaseModel

class MyModel(BaseModel):
    name: str
