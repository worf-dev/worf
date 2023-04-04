import abc

from typing import List, Dict, Tuple, Callable, Any


class BaseProvider(abc.ABC):
    @abc.abstractproperty
    def routes(self) -> List[Dict[str, Tuple[Callable, Dict[str, Any]]]]:
        raise NotImplementedError

    def run_maintenance_tasks(self):
        pass
