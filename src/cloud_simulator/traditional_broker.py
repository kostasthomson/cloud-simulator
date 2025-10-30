"""
Traditional Broker module for cloud simulator.

Implements the traditional provisioning schema with:
- Polling-based resource monitoring
- First-fit allocation strategy
- FIFO task queue
- All-or-nothing deployment
"""

from typing import List, Dict, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class TraditionalBroker:
    def __init__(self, poll_interval: float = 1.0):
        self.poll_interval = poll_interval

        self.available_processors: Dict[int, List[float]] = {}
        self.total_processors: Dict[int, List[float]] = {}
        self.available_memory: Dict[int, List[float]] = {}
        self.total_memory: Dict[int, List[float]] = {}
        self.available_accelerators: Dict[int, List[int]] = {}
        self.total_accelerators: Dict[int, List[int]] = {}
        self.available_storage: Dict[int, List[float]] = {}
        self.total_storage: Dict[int, List[float]] = {}

        self.available_network = 0.0
        self.total_network = 0.0

        self.task_queue = deque()

        self.resource_types: List[int] = []
        self.num_resources_per_type: Dict[int, int] = {}
        self.current_time = 0.0

    def init_with_inputs(self, cell, sim_inputs) -> None:
        self.initialize(cell)

    def initialize(self, cell) -> None:
        self.resource_types = cell.get_types()

        for i, res_type in enumerate(self.resource_types):
            num_resources = cell.get_number_of_resources_per_type()[i]
            self.num_resources_per_type[res_type] = num_resources

            self.available_processors[res_type] = [0.0] * num_resources
            self.total_processors[res_type] = [0.0] * num_resources
            self.available_memory[res_type] = [0.0] * num_resources
            self.total_memory[res_type] = [0.0] * num_resources
            self.available_accelerators[res_type] = [0] * num_resources
            self.total_accelerators[res_type] = [0] * num_resources
            self.available_storage[res_type] = [0.0] * num_resources
            self.total_storage[res_type] = [0.0] * num_resources

        if cell.get_network():
            self.available_network = cell.get_network().total_bandwidth
            self.total_network = cell.get_network().total_bandwidth

        self.update_state_info(cell, 0)

    def update_state_info(self, cell, timestep: float) -> None:
        self.current_time = timestep
        if int(timestep) % int(self.poll_interval) == 0:
            for type_idx, res_type in enumerate(self.resource_types):
                resources = cell.get_resources()[type_idx]
                for i, resource in enumerate(resources):
                    self.available_processors[res_type][i] = resource.available_processors
                    self.total_processors[res_type][i] = resource.total_processors
                    self.available_memory[res_type][i] = resource.available_memory
                    self.total_memory[res_type][i] = resource.total_memory
                    self.available_accelerators[res_type][i] = resource.available_accelerators
                    self.total_accelerators[res_type][i] = resource.total_accelerators
                    self.available_storage[res_type][i] = resource.available_storage
                    self.total_storage[res_type][i] = resource.total_storage

            if cell.get_network():
                self.available_network = cell.get_network().available_bandwidth
                self.total_network = cell.get_network().total_bandwidth

    def deploy(self, resources, network, stats, task) -> bool:
        req = task.get_resource_requirements()
        req_processors = req[0]
        req_memory = req[1]
        req_network = req[2]
        req_storage = req[3]
        req_accelerators = task.get_av_acc()[0] if task.get_av_acc() else 0
        num_vms = task.num_vms

        selected_type = None
        selected_type_idx = None
        for type_idx, res_type in enumerate(self.resource_types):
            if res_type in task.available_implementations:
                selected_type = res_type
                selected_type_idx = type_idx
                task.remap_type(res_type)
                break

        if selected_type is None:
            logger.error(f"Task {task.id}: No matching resource type found")
            return False

        if network.probe(req_network) == -1:
            stats[selected_type_idx].rejected_tasks += 1
            logger.debug(f"Task {task.id}: Rejected - insufficient network bandwidth")
            return False

        self.available_network -= req_network

        allocated_resource_ids = []

        for _ in range(num_vms):
            resource_id = -1

            for i in range(self.num_resources_per_type[selected_type]):
                if (
                    self.available_processors[selected_type][i] >= req_processors
                    and self.available_memory[selected_type][i] >= req_memory
                    and self.available_storage[selected_type][i] >= req_storage
                    and self.available_accelerators[selected_type][i] >= req_accelerators
                ):
                    probe_result = resources[selected_type_idx][i].probe(
                        req_processors, req_memory, req_storage, req_accelerators
                    )
                    if probe_result == i:
                        resource_id = i
                        break

            if resource_id == -1:
                for res_id in allocated_resource_ids:
                    self.available_processors[selected_type][res_id] += req_processors
                    self.available_memory[selected_type][res_id] += req_memory
                    self.available_storage[selected_type][res_id] += req_storage
                    self.available_accelerators[selected_type][res_id] += req_accelerators

                self.available_network += req_network
                stats[selected_type_idx].rejected_tasks += 1
                logger.debug(f"Task {task.id}: Rejected - insufficient resources for VM allocation")
                return False

            allocated_resource_ids.append(resource_id)
            self.available_processors[selected_type][resource_id] -= req_processors
            self.available_memory[selected_type][resource_id] -= req_memory
            self.available_storage[selected_type][resource_id] -= req_storage
            self.available_accelerators[selected_type][resource_id] -= req_accelerators

        for res_id in allocated_resource_ids:
            resources[selected_type_idx][res_id].deploy(task)

        network.deploy(task)
        task.attach_resources(allocated_resource_ids)
        self.task_queue.append(task)
        stats[selected_type_idx].accepted_tasks += 1

        logger.debug(f"Task {task.id}: Accepted and deployed on resources {allocated_resource_ids}")
        return True

    def timestep(self, cell) -> None:
        for type_idx in range(len(self.resource_types)):
            for resource in cell.get_resources()[type_idx]:
                if resource.running_vms > 0:
                    resource.initialize_running_quantities()

        if cell.get_network():
            cell.get_network().initialize_running_quantities()

        total_network_util = 0.0
        for task in self.task_queue:
            task.compute_utilization_pmns()
            total_network_util += task.current_util_pmns[2]

            res_type = task.selected_type
            type_idx = self.resource_types.index(res_type)
            for res_id in task.resource_ids:
                cell.get_resources()[type_idx][res_id].increment_running_quantities(
                    task.current_util_pmns[0],
                    task.current_util_pmns[1],
                    task.current_util_pmns[3],
                )

        if cell.get_network():
            cell.get_network().increment_running_quantities(total_network_util)

        for type_idx in range(len(self.resource_types)):
            for resource in cell.get_resources()[type_idx]:
                if resource.running_vms > 0:
                    resource.compute_current_comp_cap_per_proc()
                    resource.compute_current_comp_cap_per_acc()

        for type_idx in range(len(self.resource_types)):
            total_power = 0.0
            for resource in cell.get_resources()[type_idx]:
                proc_util = (
                    resource.actual_utilized_processors / resource.total_processors
                    if resource.total_processors > 0 else 0.0
                )
                acc_util = resource.actual_rho_accelerators
                total_power += self.calculate_power(proc_util, acc_util, resource.active, resource.total_accelerators)

            cell.get_stats()[type_idx].total_power_consumption += total_power

        tasks_to_remove = []
        for task in self.task_queue:
            res_type = task.selected_type
            type_idx = self.resource_types.index(res_type)
            res_id = task.resource_ids[0]

            min_comp_cap_proc = cell.get_resources()[type_idx][res_id].current_comp_cap_per_proc
            min_comp_cap_acc = cell.get_resources()[type_idx][res_id].current_comp_cap_per_acc

            for res_id in task.resource_ids[1:]:
                min_comp_cap_proc = min(
                    min_comp_cap_proc,
                    cell.get_resources()[type_idx][res_id].current_comp_cap_per_proc
                )
                min_comp_cap_acc = min(
                    min_comp_cap_acc,
                    cell.get_resources()[type_idx][res_id].current_comp_cap_per_acc
                )

            overcommit = cell.get_resources()[type_idx][res_id].overcommitment_processors
            vcpu = task.processors_per_vm

            proc_instructions = (
                task.num_vms * min_comp_cap_proc *
                min(task.current_util_pmns[0] / vcpu * overcommit, 1.0) * vcpu
            )
            acc_instructions = task.num_vms * min_comp_cap_acc * task.current_util_pmns[3]

            completed_instructions = proc_instructions + acc_instructions
            task.reduce_instructions(completed_instructions)

            if task.is_completed():
                if task.start_time is None:
                    task.start_time = task.arrival_time
                task.completion_time = self.current_time

                for res_id in task.resource_ids:
                    cell.get_resources()[type_idx][res_id].unload(task)

                if cell.get_network():
                    cell.get_network().unload(task)
                tasks_to_remove.append(task)

                logger.debug(f"Task {task.id}: Completed at time {self.current_time}")

        for task in tasks_to_remove:
            self.task_queue.remove(task)

    def calculate_power(self, processor_util: float, accelerator_util: float, is_active: int, total_accelerators: int) -> float:
        return 0.0

    def get_queue_length(self) -> int:
        return len(self.task_queue)
