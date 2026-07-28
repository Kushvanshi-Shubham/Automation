from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VisualEngine(ABC):
    @abstractmethod
    async def generate_assets(self, script_data: Dict[str, Any]) -> List[str]:
        pass
