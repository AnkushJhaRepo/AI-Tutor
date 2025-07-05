from enum import Enum

class Subject(str, Enum):
    MATH = "math"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    UNKNOWN = "unknown"
    RATE_LIMITED = "rate_limited"

class ToolType(str, Enum):
    CALCULATOR = "calculator"
    EQUATION_SOLVER = "equation_solver"
    CONSTANT_LOOKUP = "constant_lookup"
    FORMULA_FETCHER = "formula_fetcher"
    MOLAR_MASS = "molar_mass"
    PERIODIC_TABLE = "periodic_table"