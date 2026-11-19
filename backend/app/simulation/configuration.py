"""
BankFlow AI - Simulation Configuration
Defines configurable parameters for the Mesa multi-agent execution model.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulationConfig:
    """Configurable runtime parameters for the multi-agent banking simulation."""
    num_request_agents: int = 3
    num_service_agents: int = 4
    tick_delay_seconds: float = 0.1
    random_seed: int = 42
    auto_load_from_db: bool = True
    max_ticks: Optional[int] = None
    scenario_name: str = "DEFAULT"
    auto_generate_synthetic_requests: bool = False
    synthetic_batch_size: int = 20
