"""
Network module for cloud simulator.

Manages network bandwidth allocation and tracking.
"""

from typing import List


class Network:
    def __init__(self, total_bandwidth: float):
        self.total_bandwidth = total_bandwidth
        self.available_bandwidth = total_bandwidth
        self.running_network_util = 0.0
        self.deployed_tasks: List[int] = []

    def probe(self, req_bandwidth: float) -> int:
        if self.available_bandwidth >= req_bandwidth:
            return 0
        return -1

    def deploy(self, task) -> bool:
        req_bandwidth = task.get_resource_requirements()[2]
        if self.probe(req_bandwidth) != -1:
            self.available_bandwidth -= req_bandwidth
            self.deployed_tasks.append(task.id)
            return True
        return False

    def unload(self, task) -> None:
        req_bandwidth = task.get_resource_requirements()[2]
        self.available_bandwidth += req_bandwidth
        if task.id in self.deployed_tasks:
            self.deployed_tasks.remove(task.id)

    def initialize_running_quantities(self) -> None:
        self.running_network_util = 0.0

    def increment_running_quantities(self, network_util: float) -> None:
        self.running_network_util += network_util

    def get_state(self) -> dict:
        return {
            "total_bandwidth": self.total_bandwidth,
            "available_bandwidth": self.available_bandwidth,
            "running_network_util": self.running_network_util,
            "deployed_tasks_count": len(self.deployed_tasks),
        }
