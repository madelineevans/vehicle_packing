from pydantic import BaseModel, conint

class Vehicle(BaseModel):
    length: conint(ge=0)
    quantity: conint(ge=1)