from preprocessing.clean_data import run_phase2
from preprocessing.raw_inspection import run_phase1

PHASE_MAP = {
    1: run_phase1,
    2: run_phase2,
}

def run_phase(phase: int) -> None:
    if phase not in PHASE_MAP:
        raise ValueError(f"Unsupported phase: {phase}")
    PHASE_MAP[phase]()


def available_phases() -> list[int]:
    return sorted(PHASE_MAP.keys())


def run_workflow() -> None:
    for phase in available_phases():
        run_phase(phase)
