"""Calculator tool implementation for arithmetic evaluation."""

from __future__ import annotations

import ast
import operator
from typing import Any

from tools.base_tool import BaseTool


class CalculatorTool(BaseTool):
    """Concrete Strategy - evaluates math expressions safely."""

    _binary_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _unary_operators = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def execute(self, expression: str) -> str:
        """Evaluate a mathematical expression and return the result as text.

        Args:
            expression: The arithmetic expression to evaluate.

        Returns:
            The computed result or a clean error message.
        """
        try:
            parsed = ast.parse(expression, mode="eval")
            result: Any = self._evaluate(parsed.body)
            return str(result)
        except Exception as error:
            return f"Error evaluating expression: {error}"

    def _evaluate(self, node: ast.AST) -> float | int:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp):
            operator_fn = self._binary_operators.get(type(node.op))
            if operator_fn is None:
                raise ValueError("unsupported operator")
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            return operator_fn(left, right)

        if isinstance(node, ast.UnaryOp):
            operator_fn = self._unary_operators.get(type(node.op))
            if operator_fn is None:
                raise ValueError("unsupported unary operator")
            return operator_fn(self._evaluate(node.operand))

        raise ValueError("expression contains unsupported syntax")

    def get_declaration(self) -> dict[str, Any]:
        """Return the Gemini function declaration for this tool.

        Returns:
            A JSON-schema-compatible declaration for calculator execution.
        """
        return {
            "name": "calculator",
            "description": (
                "Evaluates mathematical expressions. Use for any arithmetic, "
                "percentages, or number calculations the user asks about."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression to evaluate.",
                    }
                },
                "required": ["expression"],
            },
        }
