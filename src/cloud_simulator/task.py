"""
Task module for cloud simulator.

Represents a workload/application to be executed on the cloud infrastructure.
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TaskConfig:
    processors_per_vm: float
    memory_per_vm: float
    network_bandwidth: float
    storage_per_vm: float
    accelerators_per_vm: int
    num_vms: int
    total_instructions: float
    processor_utilization: float
    memory_utilization: float
    storage_utilization: float
    accelerator_utilization: float
    available_implementations: List[int]
    arrival_time: float


class Task:
    def __init__(self, task_id: int, config: TaskConfig):
        self.id = task_id
        self.config = config

        self.processors_per_vm = config.processors_per_vm
        self.memory_per_vm = config.memory_per_vm
        self.network_bandwidth = config.network_bandwidth
        self.storage_per_vm = config.storage_per_vm
        self.accelerators_per_vm = [config.accelerators_per_vm]
        self.num_vms = config.num_vms

        self.total_instructions = config.total_instructions
        self.remaining_instructions = config.total_instructions

        self.processor_utilization = config.processor_utilization
        self.memory_utilization = config.memory_utilization
        self.storage_utilization = config.storage_utilization
        self.accelerator_utilization = config.accelerator_utilization

        self.available_implementations = config.available_implementations[:]
        self.selected_type: Optional[int] = None

        self.arrival_time = config.arrival_time
        self.start_time: Optional[float] = None
        self.completion_time: Optional[float] = None

        self.resource_ids: List[int] = []
        self.current_util_pmns = [0.0, 0.0, 0.0, 0.0]

    def get_resource_requirements(self) -> List[float]:
        return [
            self.processors_per_vm,
            self.memory_per_vm,
            self.network_bandwidth,
            self.storage_per_vm,
        ]

    def attach_resources(self, resource_ids: List[int]) -> None:
        self.resource_ids = resource_ids.copy()

    def remap_type(self, resource_type: int) -> None:
        self.selected_type = resource_type

    def compute_utilization_pmns(self) -> None:
        self.current_util_pmns = [
            self.processors_per_vm * self.processor_utilization,
            self.memory_per_vm * self.memory_utilization,
            self.network_bandwidth * self.processor_utilization,
            self.storage_per_vm * self.storage_utilization,
        ]

    def reduce_instructions(self, completed_instructions: float) -> None:
        self.remaining_instructions -= completed_instructions

    def is_completed(self) -> bool:
        return self.remaining_instructions <= 0.0

    def get_state(self) -> dict:
        return {
            "id": self.id,
            "arrival_time": self.arrival_time,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "num_vms": self.num_vms,
            "processors_per_vm": self.processors_per_vm,
            "memory_per_vm": self.memory_per_vm,
            "network_bandwidth": self.network_bandwidth,
            "storage_per_vm": self.storage_per_vm,
            "accelerators": self.accelerators_per_vm,
            "total_instructions": self.total_instructions,
            "remaining_instructions": self.remaining_instructions,
            "selected_type": self.selected_type,
            "resource_ids": self.resource_ids,
        }

    def get_number_of_vms(self) -> int:
        return self.num_vms

    def get_available_implementations(self) -> List[int]:
        return self.available_implementations

    def get_number_of_available_implementations(self) -> int:
        return len(self.available_implementations)

    def get_req_pmns(self) -> List[float]:
        return [
            self.processors_per_vm,
            self.memory_per_vm,
            self.network_bandwidth,
            self.storage_per_vm,
        ]

    def get_av_acc(self) -> List[int]:
        return self.accelerators_per_vm

    def get_resource_ids(self) -> List[int]:
        return self.resource_ids

    def reduce_impl(self, impl_index: int) -> None:
        if 0 <= impl_index < len(self.available_implementations):
            selected = self.available_implementations[impl_index]
            self.available_implementations = [selected]
            if len(self.accelerators_per_vm) > impl_index:
                self.accelerators_per_vm = [self.accelerators_per_vm[impl_index]]

    def remap_type(self, resource_type: int, count: int = 1) -> None:
        self.selected_type = resource_type

    def comp_c_util_pmnr(self) -> None:
        self.current_util_pmns = [
            self.processors_per_vm * self.processor_utilization,
            self.memory_per_vm * self.memory_utilization,
            self.network_bandwidth * self.processor_utilization,
            self.storage_per_vm * self.storage_utilization,
        ]

    def get_c_util_pmnr(self) -> List[float]:
        return self.current_util_pmns

    def reduce_ins(self, completed_instructions: float) -> None:
        self.remaining_instructions -= completed_instructions

    def get_requested_instructions(self) -> float:
        return self.remaining_instructions
