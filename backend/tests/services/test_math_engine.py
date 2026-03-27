from app.services.math import MathVerificationEngine


def test_math_engine_verifies_equivalence():
    engine = MathVerificationEngine()
    result = engine.validate_expression("x**2 + 2*x + 1")

    assert result.valid is True
    assert result.latex_expression is not None
    assert engine.verify_equivalence("(x+1)**2", "x**2 + 2*x + 1") is True
