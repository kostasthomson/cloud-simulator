from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from .cell import Cell
    from .resource import Resource
    from .network import Network
    from .statistics import Statistics
    from .task import Task
    from .inputs import SimulationInputs


class BaseBroker(ABC):

    def __init__(self):
        self.alloc: int = 0
        self.number_of_types: int = 0
        self.types: Optional[List[int]] = None
        self.number_of_resources_per_type: Optional[List[int]] = None
        self.available_network: float = 0.0
        self.total_network: float = 0.0

    @abstractmethod
    def deploy(self, resources: List[List['Resource']], network: 'Network',
               stats: List['Statistics'], task: 'Task') -> None:
        pass

    def init(self, cell: 'Cell', sim_inputs: Optional['SimulationInputs'] = None) -> None:
        if sim_inputs is None:
            return
        self.init_with_inputs(cell, sim_inputs)

    @abstractmethod
    def init_with_inputs(self, cell: 'Cell', sim_inputs: 'SimulationInputs') -> None:
        pass

    @abstractmethod
    def print(self) -> None:
        pass

    @abstractmethod
    def timestep(self, cell: 'Cell') -> None:
        pass

    @abstractmethod
    def update_state_info(self, cell: 'Cell', tstep: float) -> None:
        pass

    def get_alloc(self) -> int:
        return self.alloc

    def get_types(self) -> Optional[List[int]]:
        return self.types

    def get_number_of_types(self) -> int:
        return self.number_of_types

    def get_number_of_resources_per_type(self) -> Optional[List[int]]:
        return self.number_of_resources_per_type

    def get_available_network(self) -> float:
        return self.available_network

    def get_total_network(self) -> float:
        return self.total_network
