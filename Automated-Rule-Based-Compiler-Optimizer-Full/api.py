
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from optimizer_api import optimize_source, OptimizerAPIError


app = FastAPI(
    title="Automated Rule-Based Compiler Code Optimizer",
    description=(
        "API for compiling, optimizing, and testing "
        "source code using rule-based compiler optimizations."
    ),
    version="1.0.0"
)


class OptimizeRequest(BaseModel):
    source: str = Field(
        ...,
        min_length=1,
        description="Source code written in the project's custom language."
    )

    inputs: Optional[List[int]] = Field(
        default=None,
        description="Input values for input statements."
    )

    enabled_optimizers: Optional[List[str]] = Field(
        default=None,
        description="Names of optimization rules to enable."
    )

    max_passes: int = Field(
        default=20,
        ge=1,
        le=100
    )


@app.get("/")
def home():
    return {
        "message": "Compiler Optimizer API is running.",
        "docs": "/docs"
    }


@app.post("/optimize")
def optimize_code(request: OptimizeRequest):
    try:
        result = optimize_source(
            source=request.source,
            inputs=request.inputs,
            enabled=request.enabled_optimizers,
            max_passes=request.max_passes
        )

        return result

    except OptimizerAPIError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )
