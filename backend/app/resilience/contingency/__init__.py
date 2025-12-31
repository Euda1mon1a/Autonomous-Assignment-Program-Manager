"""N-1/N-2 contingency analysis from power grid standards."""

import importlib.util
import sys
from pathlib import Path

# Import from contingency.py file (shadowed by this package directory)
# We need to use importlib to load the module file directly
_contingency_file = Path(__file__).parent.parent / "contingency.py"
_spec = importlib.util.spec_from_file_location("contingency_base", _contingency_file)
_contingency_base = importlib.util.module_from_spec(_spec)
sys.modules["contingency_base"] = _contingency_base
_spec.loader.exec_module(_contingency_base)

# Re-export classes from contingency.py (the original module file)
CascadeSimulation = _contingency_base.CascadeSimulation
CentralityScore = _contingency_base.CentralityScore
ContingencyAnalyzer = _contingency_base.ContingencyAnalyzer
FatalPair = _contingency_base.FatalPair
Vulnerability = _contingency_base.Vulnerability
VulnerabilityReport = _contingency_base.VulnerabilityReport

# Import from package modules
from app.resilience.contingency.n1_analyzer import N1Analyzer, N1FailureScenario
from app.resilience.contingency.n2_analyzer import N2Analyzer, N2FailureScenario

__all__ = [
    # From contingency.py (base module)
    "CascadeSimulation",
    "CentralityScore",
    "ContingencyAnalyzer",
    "FatalPair",
    "Vulnerability",
    "VulnerabilityReport",
    # From package modules
    "N1Analyzer",
    "N1FailureScenario",
    "N2Analyzer",
    "N2FailureScenario",
]
