from pydantic import BaseModel, Field, field_validator


class QueryRewriterInput(BaseModel):
    current_description: str = Field(..., min_length=1)
    memory_context: str = Field(..., min_length=1)

    @field_validator("current_description", "memory_context")
    @classmethod
    def fields_must_not_be_blank(cls, value: str):
        if not value.strip():
            raise ValueError("field cannot be empty")
        return value.strip()


class QueryRewriterOutput(BaseModel):
    optimized_query: str = Field(..., min_length=1, max_length=300)

    @field_validator("optimized_query")
    @classmethod
    def optimized_query_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("optimized_query cannot be empty")
        return value.strip()
