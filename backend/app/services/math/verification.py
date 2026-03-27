from dataclasses import dataclass

import sympy
from sympy import SympifyError, latex, simplify


@dataclass(slots=True)
class MathValidationResult:
    valid: bool
    expression: sympy.Expr | None
    simplified: str | None
    latex_expression: str | None
    error: str | None = None


class MathVerificationEngine:
    def validate_expression(self, expression: str) -> MathValidationResult:
        try:
            expr = sympy.sympify(expression)
        except SympifyError as exc:
            return MathValidationResult(
                valid=False,
                expression=None,
                simplified=None,
                latex_expression=None,
                error=str(exc),
            )

        simplified = simplify(expr)
        return MathValidationResult(
            valid=True,
            expression=expr,
            simplified=str(simplified),
            latex_expression=latex(expr),
        )

    def verify_equivalence(self, left: str, right: str) -> bool:
        try:
            lhs = sympy.sympify(left)
            rhs = sympy.sympify(right)
        except SympifyError:
            return False
        return simplify(lhs - rhs) == 0

    def to_latex(self, expression: str) -> str:
        return latex(sympy.sympify(expression))
