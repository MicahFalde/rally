from app.adapters.base import StateAdapter
from app.adapters.ohio import OhioAdapter

# Registry of available state adapters
ADAPTERS: dict[str, type[StateAdapter]] = {
    "OH": OhioAdapter,
}


def get_adapter(state_code: str) -> StateAdapter:
    adapter_cls = ADAPTERS.get(state_code.upper())
    if adapter_cls is None:
        raise ValueError(f"No adapter available for state: {state_code}")
    return adapter_cls()
