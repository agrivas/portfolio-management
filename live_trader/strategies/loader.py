import importlib.util
import logging
from pathlib import Path
from typing import Type

def get_strategies_dir() -> Path:
    return Path(__file__).parent.parent.parent / "robo-trader" / "robo_trader" / "strategies"

STRATEGIES_DIR = get_strategies_dir()

logger = logging.getLogger(__name__)

def load_strategy_class(strategy_name: str) -> Type:
    file_path = STRATEGIES_DIR / f"{strategy_name}.py"
    if not file_path.exists():
        raise ValueError(f"Strategy not found: {strategy_name}")
    
    spec = importlib.util.spec_from_file_location(f"strategy_{strategy_name}", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and hasattr(obj, "evaluate_market") and name != "Strategy":
            return obj
    
    raise ValueError(f"No strategy class found in {strategy_name}.py")

def list_strategies() -> list[str]:
    if not STRATEGIES_DIR.exists():
        return []
    return [f.stem for f in STRATEGIES_DIR.glob("*.py") if f.stem not in ["__init__", "StrategyBase"]]