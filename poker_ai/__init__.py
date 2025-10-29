"""
Heads-Up Poker AI - Simple MVP
"""

# Try to import C++ engine
try:
    from . import poker_engine
except ImportError:
    import warnings
    warnings.warn("C++ poker engine not built. Run build_simple.py", ImportWarning)

