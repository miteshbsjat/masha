from pydantic import BaseModel, ValidationError, field_validator

class ConfigModel(BaseModel):
    name: str
    version: str
    debug: bool
    age: int

    @field_validator('age', mode='after')
    @classmethod
    def validate_age(cls, value: int) -> int:
        if value < 0 or value > 150:
            raise ValueError(f'{value} is not a valid date [0, 150]')
        return value