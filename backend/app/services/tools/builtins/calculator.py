"""Calculator tool: safe arithmetic expression evaluation.

Expressions are parsed to an AST and evaluated over an explicit allow-list of
node types, so arbitrary code execution (the risk with ``eval``) is impossible.
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from app.services.tools.base import BaseTool, ToolContext, ToolExecutionError

_BINARY_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
# Guard against trivially abusive exponents (e.g. 9**9**9).
_MAX_EXPONENT = 1000


class CalculatorParams(BaseModel):
    expression: str = Field(min_length=1, max_length=256, description="Arithmetic expression")


class CalculatorTool(BaseTool[CalculatorParams]):
    name = "calculator"
    description = "Evaluate a basic arithmetic expression (+, -, *, /, //, %, ** and parentheses)."
    params_model = CalculatorParams

    async def run(self, params: CalculatorParams, context: ToolContext) -> dict[str, Any]:
        try:
            tree = ast.parse(params.expression, mode="eval")
        except SyntaxError as exc:
            raise ToolExecutionError(f"Invalid expression: {exc.msg}") from exc
        value = _evaluate(tree.body)
        return {"expression": params.expression, "result": value}


def _evaluate(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise ToolExecutionError("Only numeric literals are allowed.")
        return node.value
    if isinstance(node, ast.BinOp):
        binary_op = _BINARY_OPS.get(type(node.op))
        if binary_op is None:
            raise ToolExecutionError(f"Unsupported operator: {type(node.op).__name__}")
        left, right = _evaluate(node.left), _evaluate(node.right)
        if type(node.op) is ast.Pow and isinstance(right, int | float) and right > _MAX_EXPONENT:
            raise ToolExecutionError("Exponent too large.")
        try:
            return binary_op(left, right)
        except ZeroDivisionError as exc:
            raise ToolExecutionError("Division by zero.") from exc
    if isinstance(node, ast.UnaryOp):
        unary_op = _UNARY_OPS.get(type(node.op))
        if unary_op is None:
            raise ToolExecutionError(f"Unsupported unary operator: {type(node.op).__name__}")
        return unary_op(_evaluate(node.operand))
    raise ToolExecutionError(f"Unsupported expression element: {type(node).__name__}")
