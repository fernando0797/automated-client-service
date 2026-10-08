from pydantic import BaseModel, Field


class PredefinedEscalationResponse(BaseModel):
    response: str = Field(..., min_length=1)


class PredefinedClosingResponse(BaseModel):
    response: str = Field(..., min_length=1)
