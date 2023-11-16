import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from langchain.agents import AgentExecutor


class AgentLogAdapter:
    """
    Usage:
        response = AgentLogAdapter(agent).call_agent({'input': 'Hello, World!'})
    """
    def __init__(self, agent: AgentExecutor):
        self.agent = agent

    def _jsonify_agent_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "input": response["input"],
            "output": response["output"],
            "intermediate_steps": [
                {
                    "log": step[0].log,
                    "tool": step[0].tool,
                    "tool_input": step[0].tool_input,
                    "output": step[1],
                }
                for step in response["intermediate_steps"]
            ],
        }

    def _save_result(self, response: Dict[str, Any]) -> str:
        logs_folder = Path("agent_logs")
        logs_folder.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f.json")
        file_path = logs_folder / filename

        try:
            with file_path.open("w") as f:
                json.dump(self._jsonify_agent_response(response), f, indent=4)
        except (TypeError, ValueError) as e:
            # Handle JSON serialization errors
            print(f"Error saving agent log: {e}")

        return str(file_path)

    def call_agent(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        response = self.agent(inputs)
        self._save_result(response)
        return response
