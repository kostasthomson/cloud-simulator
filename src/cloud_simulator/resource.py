"""
Resource module for cloud simulator.

Represents a physical/virtual resource node with compute, memory, storage,
and accelerator capacity.
"""

from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class ResourceConfig:
    total_processors: float
    total_memory: float
    total_storage: float
    total_accelerators: int
    comp_cap_per_proc: float
    comp_cap_per_acc: float
    overcommitment_processors: float = 1.0


class Resource:
    def __init__(
        self,
        resource_id: int,
        resource_type: int,
        config: ResourceConfig
    ):
        self.id = resource_id
        self.type = resource_type

        self.total_processors = config.total_processors
        self.total_memory = config.total_memory
        self.total_storage = config.total_storage
        self.total_accelerators = config.total_accelerators

        self.available_processors = config.total_processors
        self.available_memory = config.total_memory
        self.available_storage = config.total_storage
        self.available_accelerators = config.total_accelerators

        self.comp_cap_per_proc = config.comp_cap_per_proc
        self.comp_cap_per_acc = config.comp_cap_per_acc
        self.overcommitment_processors = config.overcommitment_processors

        self.current_comp_cap_per_proc = 0.0
        self.current_comp_cap_per_acc = 0.0

        self.running_vms = 0
        self.active = 0
        self.movable = 1

        self.actual_utilized_processors = 0.0
        self.actual_utilized_memory = 0.0
        self.actual_utilized_storage = 0.0
        self.actual_rho_accelerators = 0.0

        self.deployed_tasks: List[int] = []

    def probe(
        self,
        req_processors: float,
        req_memory: float,
        req_storage: float,
        req_accelerators: int
    ) -> int:
        if (
            self.available_processors >= req_processors
            and self.available_memory >= req_memory
            and self.available_storage >= req_storage
            and self.available_accelerators >= req_accelerators
        ):
            return self.id
        return -1

    def deploy(self, task) -> bool:
        req = task.get_resource_requirements()

        if self.probe(req[0], req[1], req[3], task.accelerators) != -1:
            self.available_processors -= req[0]
            self.available_memory -= req[1]
            self.available_storage -= req[3]
            self.available_accelerators -= task.accelerators

            self.running_vms += 1
            if self.running_vms > 0:
                self.active = 1

            self.deployed_tasks.append(task.id)
            return True
        return False

    def unload(self, task) -> None:
        req = task.get_resource_requirements()

        self.available_processors += req[0]
        self.available_memory += req[1]
        self.available_storage += req[3]
        self.available_accelerators += task.accelerators

        self.running_vms -= 1
        if self.running_vms <= 0:
            self.active = 0
            self.running_vms = 0

        if task.id in self.deployed_tasks:
            self.deployed_tasks.remove(task.id)

    def initialize_running_quantities(self) -> None:
        self.actual_utilized_processors = 0.0
        self.actual_utilized_memory = 0.0
        self.actual_utilized_storage = 0.0
        self.actual_rho_accelerators = 0.0

    def increment_running_quantities(
        self,
        proc_util: float,
        mem_util: float,
        storage_util: float
    ) -> None:
        self.actual_utilized_processors += proc_util
        self.actual_utilized_memory += mem_util
        self.actual_utilized_storage += storage_util

    def compute_current_comp_cap_per_proc(self) -> None:
        if self.running_vms > 0 and self.actual_utilized_processors > 0:
            util_ratio = self.actual_utilized_processors / self.total_processors
            self.current_comp_cap_per_proc = self.comp_cap_per_proc * (
                1.0 / max(util_ratio / self.overcommitment_processors, 1.0)
            )
        else:
            self.current_comp_cap_per_proc = self.comp_cap_per_proc

    def compute_current_comp_cap_per_acc(self) -> None:
        if self.total_accelerators > 0 and self.running_vms > 0:
            used_acc = self.total_accelerators - self.available_accelerators
            if used_acc > 0:
                self.actual_rho_accelerators = self.actual_rho_accelerators / used_acc
                self.current_comp_cap_per_acc = self.comp_cap_per_acc * (
                    1.0 / max(self.actual_rho_accelerators, 1.0)
                )
            else:
                self.current_comp_cap_per_acc = self.comp_cap_per_acc
        else:
            self.current_comp_cap_per_acc = self.comp_cap_per_acc

    def get_state(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "total_processors": self.total_processors,
            "available_processors": self.available_processors,
            "total_memory": self.total_memory,
            "available_memory": self.available_memory,
            "total_storage": self.total_storage,
            "available_storage": self.available_storage,
            "total_accelerators": self.total_accelerators,
            "available_accelerators": self.available_accelerators,
            "running_vms": self.running_vms,
            "active": self.active,
        }

    def get_id(self) -> int:
        return self.id

    def get_movable(self) -> int:
        return self.movable

    def get_available_processors(self) -> float:
        return self.available_processors

    def get_total_processors(self) -> float:
        return self.total_processors

    def get_available_memory(self) -> float:
        return self.available_memory

    def get_total_memory(self) -> float:
        return self.total_memory

    def get_available_storage(self) -> float:
        return self.available_storage

    def get_total_storage(self) -> float:
        return self.total_storage

    def get_available_accelerators(self) -> int:
        return int(self.available_accelerators)

    def get_total_accelerators(self) -> int:
        return self.total_accelerators

    def get_compute_capability(self) -> float:
        return self.comp_cap_per_proc * self.total_processors

    def get_accelerator_compute_capability(self) -> float:
        return self.comp_cap_per_acc * self.total_accelerators

    def get_running_vms(self) -> int:
        return self.running_vms

    def get_active(self) -> int:
        return self.active

    def get_actual_utilized_processors(self) -> float:
        return self.actual_utilized_processors

    def get_actual_rho_accelerators(self) -> float:
        return self.actual_rho_accelerators

    def get_overcommitment_processors(self) -> float:
        return self.overcommitment_processors

    def get_current_comp_cap_per_proc(self) -> float:
        return self.current_comp_cap_per_proc

    def get_current_comp_cap_per_acc(self) -> float:
        return self.current_comp_cap_per_acc

    def comp_current_comp_cap_per_proc(self) -> None:
        self.compute_current_comp_cap_per_proc()

    def comp_current_comp_cap_per_acc(self) -> None:
        self.compute_current_comp_cap_per_acc()
