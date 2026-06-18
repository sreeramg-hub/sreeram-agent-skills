"""
CrewAI Custom Tool Pattern — annotated template.

Copy this file, rename the classes, fill in the logic.
Extracted from: https://github.com/sreeramg-hub/sreeram-agent-crew
License: MIT
"""

from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# 1. Define the input schema with Pydantic.
#    Each field's `description` is what the LLM sees when deciding what to pass.
class ExampleToolInput(BaseModel):
    required_param: str = Field(
        ...,  # ... means required (no default)
        description="Describe what this param is and what values are valid.",
    )
    optional_param: int = Field(
        default=10,
        description="Optional param — describe what it controls and what the default means.",
    )


# 2. Subclass BaseTool.
class ExampleTool(BaseTool):
    # `name` must be unique within a crew. Use snake_case.
    name: str = "example_tool"

    # `description` is what the LLM reads to decide when to use this tool.
    # Be specific: what does it do, what does it return, when should it be called?
    description: str = (
        "Does X given Y. Returns Z as a plain string. "
        "Use this when the agent needs to [specific situation]."
    )

    # Wire up the input schema.
    args_schema: Type[BaseModel] = ExampleToolInput

    # 3. Implement _run(). Parameter names must match the schema field names.
    #    Always return a string — the agent reads the return value as text.
    def _run(self, required_param: str, optional_param: int = 10) -> str:
        # Your logic here.
        try:
            result = f"Processed '{required_param}' with limit {optional_param}"
            return result
        except Exception as e:
            # Return errors as strings too — let the agent decide what to do with them.
            return f"Error: {e}"


# 4. Usage in a crew:
#
#   from crewai import Agent
#   agent = Agent(
#       role="...",
#       goal="...",
#       backstory="...",
#       tools=[ExampleTool()],   # pass an instance, not the class
#   )
