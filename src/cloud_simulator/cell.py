"""
Cell module for cloud simulator.

Represents a datacenter cell containing resources, network, and statistics.
"""

from typing import Dict, List
from .resource import Resource
from .network import Network
from .statistics import Statistics


class Cell:
    def __init__(self):
        self.resources: Dict[int, List[Resource]] = {}
        self.network: Network = None
        self.statistics: Dict[int, Statistics] = {}

    def add_resource_type(self, resource_type: int, resources: List[Resource]) -> None:
        self.resources[resource_type] = resources

    def set_network(self, network: Network) -> None:
        self.network = network

    def add_statistics(self, resource_type: int, stats: Statistics) -> None:
        self.statistics[resource_type] = stats

    def get_state(self) -> dict:
        return {
            "resources": {
                res_type: [r.get_state() for r in resources]
                for res_type, resources in self.resources.items()
            },
            "network": self.network.get_state() if self.network else {},
            "statistics": {
                res_type: stats.get_summary()
                for res_type, stats in self.statistics.items()
            },
        }
