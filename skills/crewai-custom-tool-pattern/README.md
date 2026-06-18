# Skill: CrewAI Custom Tool Pattern

The correct shape for a CrewAI `BaseTool` subclass — with typed inputs, Pydantic validation, and a description the LLM can actually use.

---

## Problem

CrewAI agents can use tools, but the tool must be structured in a specific way for the framework to wire it up correctly: typed inputs defined with Pydantic, a clear description the LLM uses to decide when to call the tool, and a `_run()` method that returns a string.

Get any of these wrong and the agent either ignores the tool, calls it with wrong arguments, or the framework raises a validation error.

## The pattern

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class MyToolInput(BaseModel):
    param_one: str = Field(..., description="Clear description — the LLM reads this.")
    param_two: int = Field(default=10, description="Optional param with a default.")

class MyTool(BaseTool):
    name: str = "my_tool"           # snake_case, unique per crew
    description: str = (
        "One or two sentences the LLM uses to decide when to call this tool. "
        "Be specific about what it does and what inputs it expects."
    )
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, param_one: str, param_two: int = 10) -> str:
        # Do the work
        result = f"Did something with {param_one}"
        return result  # always return a string
```

## Key rules

**`args_schema` is required.** Without it, the LLM has no type information and will make up arguments or fail validation.

**`description` is the tool's "pitch" to the LLM.** Write it as if you're explaining to a person when and why they should use this tool. Vague descriptions lead to the agent ignoring the tool or calling it at the wrong time.

**`_run()` must return a string.** Even if the result is structured data, return it as a formatted string or JSON-encoded string. The agent reads the return value as text.

**Keep `_run()` synchronous.** CrewAI handles async execution at the framework level. Your tool logic should be regular Python.

**One tool, one job.** If a tool does two things (e.g. "fetch price AND send email"), split it into two tools. Agents reason better with narrow, named tools.

## Passing the tool to an agent

```python
from crewai import Agent

agent = Agent(
    role="My Agent",
    goal="Do the thing",
    backstory="...",
    tools=[MyTool()],   # pass instances, not classes
)
```

## Large outputs

If your tool returns a very large string (e.g. a full transcript or a 10KB HTML document), the LLM may struggle to pass that entire string back as an argument to a downstream tool call. The solution: have the downstream tool read from a file rather than accept the large value as a parameter. See the `send_email` tool in [sreeram-agent-crew](https://github.com/sreeramg-hub/sreeram-agent-crew) for an example — it reads `digest.html` directly rather than accepting the HTML body as an argument.

---

## Files

- [`example_tool.py`](example_tool.py) — annotated template, ready to copy and modify
