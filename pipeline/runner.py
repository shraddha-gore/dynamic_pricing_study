from models.demand_model import run_phase6
from preprocessing.aggregate_daily import run_phase4
from preprocessing.clean_data import run_phase2
from preprocessing.feature_engineering import run_phase5
from preprocessing.raw_inspection import run_phase1
from preprocessing.select_products import run_phase3


def _phase_map():
    return {
        1: run_phase1,
        2: run_phase2,
        3: run_phase3,
        4: run_phase4,
        5: run_phase5,
        6: run_phase6,
    }


def run_phase(phase: int) -> None:
    phase_map = _phase_map()
    if phase not in phase_map:
        raise ValueError(f"Unsupported phase: {phase}")
    phase_map[phase]()


def available_phases() -> list[int]:
    return sorted(_phase_map().keys())


def run_workflow() -> None:
    for phase in available_phases():
        run_phase(phase)
