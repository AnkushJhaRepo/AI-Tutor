import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    # Environment detection
    IS_VERCEL = os.getenv('VERCEL') == '1'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-pro')
    
    # Timeouts (adjusted for Vercel's 10s limit)
    TIMEOUT = 8.0 if IS_VERCEL else 30.0  # Main timeout
    CONNECTION_TIMEOUT = 3.0 if IS_VERCEL else 5.0  # Connection timeout
    REQUEST_TIMEOUT = 35 if IS_VERCEL else 60  # Frontend timeout in seconds
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 30
    CIRCUIT_BREAKER_THRESHOLD = 5
    CIRCUIT_BREAKER_TIMEOUT = 60
    
    # Request cleanup
    REQUEST_CLEANUP_DELAY = 60 if IS_VERCEL else 300  # 1 min for Vercel, 5 min for local
    
    # History limits
    MAX_HISTORY_PER_SESSION = 50
    
    # Logging
    LOG_LEVEL = 'INFO' if ENVIRONMENT == 'production' else 'DEBUG'
    
    # Physical constants for physics calculations
    PHYSICS_CONSTANTS = {
        "c": 299792458,  # Speed of light (m/s)
        "g": 9.81,       # Acceleration due to gravity (m/s²)
        "h": 6.62607015e-34,  # Planck constant (J⋅s)
        "k": 1.380649e-23,    # Boltzmann constant (J/K)
        "e": 1.602176634e-19, # Elementary charge (C)
        "m_e": 9.1093837015e-31,  # Electron mass (kg)
        "m_p": 1.67262192369e-27, # Proton mass (kg)
        "N_A": 6.02214076e23,     # Avogadro's number (mol⁻¹)
        "R": 8.314462618,         # Gas constant (J/(mol⋅K))
        "epsilon_0": 8.8541878128e-12,  # Vacuum permittivity (F/m)
        "mu_0": 1.25663706212e-6,       # Vacuum permeability (H/m)
    }
    
    # Chemistry constants
    CHEMISTRY_CONSTANTS = {
        "R": 8.314462618,      # Gas constant (J/(mol⋅K))
        "N_A": 6.02214076e23,  # Avogadro's number (mol⁻¹)
        "F": 96485.33212,      # Faraday constant (C/mol)
        "STP_PRESSURE": 101325, # Standard pressure (Pa)
        "STP_TEMPERATURE": 273.15, # Standard temperature (K)
    }

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        if not cls.GEMINI_MODEL:
            raise ValueError("GEMINI_MODEL not found in environment variables")

config = Config()