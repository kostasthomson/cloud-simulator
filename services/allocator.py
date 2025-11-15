"""
Core allocation service implementing the smart allocation algorithm.
Starts with a simple heuristic approach optimizing for energy efficiency.
"""
from typing import Optional, Tuple, List
import logging
from models.schemas import AllocationRequest, AllocationDecision, VMAllocation, CellStatus, HardwareType
from services.energy_calculator import EnergyCalculator
from utils.allocation_logger import AllocationLogger

logger = logging.getLogger(__name__)


class TaskAllocator:
    """
    Smart task allocation service.

    Current implementation: Heuristic-based energy-aware allocation.
    Future extensions: ML-based prediction, RL-based optimization.
    """

    def __init__(self):
        """Initialize the allocator with energy calculator."""
        self.energy_calc = EnergyCalculator()
        self.logger = AllocationLogger()
        self.allocation_count = 0
        self.rejection_count = 0

    def allocate_task(self, request: AllocationRequest) -> AllocationDecision:
        """
        Main allocation decision logic.

        Args:
            request: Allocation request with system state and task requirements

        Returns:
            AllocationDecision with selected cell/server or rejection
        """
        self.allocation_count += 1
        decision = None
        try:
            allocation = self._heuristic_energy_aware_allocation(request)

            if allocation:
                vm_allocations, energy_cost, reason = allocation
                logger.info(
                    f"Task {request.task.task_id} allocated {len(vm_allocations)} VMs, "
                    f"Est. Energy: {energy_cost:.4f} kWh"
                )
                decision = AllocationDecision(
                    success=True,
                    num_vms_allocated=len(vm_allocations),
                    vm_allocations=vm_allocations,
                    estimated_energy_cost=energy_cost,
                    reason=reason,
                    allocation_method="heuristic_energy_aware",
                    timestamp=request.timestamp
                )
            else:
                self.rejection_count += 1
                logger.warning(f"Task {request.task.task_id} rejected - no suitable resources")
                decision = AllocationDecision(
                    success=False,
                    num_vms_allocated=0,
                    reason="No suitable resources available in any cell",
                    allocation_method="heuristic_energy_aware",
                    timestamp=request.timestamp
                )

        except Exception as e:
            logger.error(f"Error allocating task {request.task.task_id}: {str(e)}")
            decision = AllocationDecision(
                success=False,
                reason=f"Internal error: {str(e)}",
                allocation_method="heuristic_energy_aware",
                timestamp=request.timestamp
            )
        finally:
            self.logger.log_decision(request, decision)
        return decision

    def _heuristic_energy_aware_allocation(
            self,
            request: AllocationRequest
    ) -> Optional[Tuple[List[VMAllocation], float, str]]:
        """
        Heuristic allocation optimizing for energy efficiency with multi-VM support.

        Strategy:
        1. Filter cells/HW types that can accommodate ALL VMs
        2. For each candidate, estimate energy cost and allocate VMs to specific servers
        3. Select the one with lowest energy cost

        Args:
            request: Allocation request

        Returns:
            Tuple of (vm_allocations, energy_cost, reason) or None if no allocation
        """
        task = request.task
        candidates = []

        for cell in request.cells:
            for hw_type in cell.hw_types:
                if not self._is_compatible(task, hw_type):
                    continue

                if not self._has_sufficient_resources(task, hw_type, cell):
                    continue

                energy_cost = self._estimate_energy_cost(task, hw_type, cell)
                efficiency = self._calculate_efficiency_score(hw_type, cell)

                candidates.append({
                    'cell': cell,
                    'hw_type': hw_type,
                    'energy_cost': energy_cost,
                    'efficiency': efficiency,
                    'score': energy_cost * (2.0 - efficiency)
                })

        if not candidates:
            return None

        best = min(candidates, key=lambda x: x['score'])

        vm_allocations = self._allocate_vms_to_servers(
            task,
            best['cell'],
            best['hw_type']
        )

        if not vm_allocations:
            return None

        reason = (
            f"Allocated {len(vm_allocations)} VMs to {best['hw_type'].hw_type_name} "
            f"in Cell {best['cell'].cell_id} (Est: {best['energy_cost']:.4f} kWh)"
        )

        return (vm_allocations, best['energy_cost'], reason)

    def _is_compatible(self, task, hw_type: HardwareType) -> bool:
        """
        Check if hardware type is compatible with task implementation.

        Implementation mapping:
        1 = CPU only
        2 = GPU (needs CPU+GPU)
        3 = DFE (needs CPU+DFE)
        4 = MIC (needs CPU+MIC)
        """
        if task.implementation_id == 1:
            # CPU-only tasks can run on any hardware
            return True
        elif task.implementation_id == 2:
            # GPU tasks need GPU accelerators
            return hw_type.accelerators > 0 and "GPU" in hw_type.hw_type_name.upper()
        elif task.implementation_id == 3:
            # DFE tasks need DFE accelerators
            return hw_type.accelerators > 0 and "DFE" in hw_type.hw_type_name.upper()
        elif task.implementation_id == 4:
            # MIC tasks need MIC accelerators
            return hw_type.accelerators > 0 and "MIC" in hw_type.hw_type_name.upper()
        return False

    def _has_sufficient_resources(
            self,
            task,
            hw_type: HardwareType,
            cell: CellStatus
    ) -> bool:
        """Check if sufficient resources are available."""
        hw_id = hw_type.hw_type_id

        if hw_id not in cell.available_resources:
            return False

        available = cell.available_resources[hw_id]

        # Calculate total resource requirements
        total_cpus_needed = task.num_vms * task.vcpus_per_vm
        total_memory_needed = task.num_vms * task.memory_per_vm
        total_storage_needed = task.num_vms * task.storage_per_vm
        total_network_needed = task.num_vms * task.network_per_vm
        total_accelerators_needed = task.num_vms if task.requires_accelerator else 0

        # Check each resource
        checks = [
            available.get('cpu', 0) >= total_cpus_needed,
            available.get('memory', 0) >= total_memory_needed,
            available.get('storage', 0) >= total_storage_needed,
            available.get('network', 0) >= total_network_needed,
        ]

        if task.requires_accelerator:
            checks.append(available.get('accelerators', 0) >= total_accelerators_needed)

        return all(checks)

    def _estimate_energy_cost(
            self,
            task,
            hw_type: HardwareType,
            cell: CellStatus
    ) -> float:
        """Estimate energy cost for running task on this hardware."""
        # Use estimated task duration or default
        duration = task.estimated_duration if task.estimated_duration else 3600.0  # 1 hour default

        # Estimate CPU utilization (assume high utilization for HPC tasks)
        cpu_utilization = 0.8

        # Calculate energy using the energy calculator
        energy = self.energy_calc.estimate_task_energy(
            task_vcpus=task.num_vms * task.vcpus_per_vm,
            task_duration=duration,
            cpu_utilization=cpu_utilization,
            utilization_bins=hw_type.cpu_utilization_bins,
            power_values=hw_type.cpu_power_consumption,
            has_accelerator=task.requires_accelerator,
            accelerator_utilization=task.accelerator_utilization,
            accelerator_idle_power=hw_type.accelerator_idle_power,
            accelerator_max_power=hw_type.accelerator_max_power
        )

        return energy

    def _calculate_efficiency_score(
            self,
            hw_type: HardwareType,
            cell: CellStatus
    ) -> float:
        """Calculate efficiency score for this hardware type in the cell."""
        hw_id = hw_type.hw_type_id

        if hw_id not in cell.available_resources:
            return 0.0

        available = cell.available_resources[hw_id]

        total_cpus = hw_type.num_servers * hw_type.num_cpus_per_server
        total_memory = hw_type.num_servers * hw_type.memory_per_server
        total_accelerators = hw_type.num_servers * hw_type.num_accelerators_per_server

        return self.energy_calc.calculate_server_efficiency(
            available_cpus=available.get('cpu', 0),
            total_cpus=total_cpus,
            available_memory=available.get('memory', 0),
            total_memory=total_memory,
            available_accelerators=available.get('accelerators', 0),
            total_accelerators=total_accelerators
        )

    def _allocate_vms_to_servers(
            self,
            task,
            cell: CellStatus,
            hw_type: HardwareType
    ) -> List[VMAllocation]:
        """
        Allocate VMs to specific servers using first-fit strategy.

        Args:
            task: Task requirements
            cell: Selected cell
            hw_type: Selected hardware type

        Returns:
            List of VM allocations with server assignments
        """
        vm_allocations = []
        hw_id = hw_type.hw_type_id

        available = cell.available_resources.get(hw_id, {})
        total_servers = hw_type.num_servers
        cpus_per_server = hw_type.num_cpus_per_server
        memory_per_server = hw_type.memory_per_server
        storage_per_server = hw_type.storage_per_server
        accelerators_per_server = hw_type.num_accelerators_per_server

        available_cpus_per_server = [cpus_per_server] * total_servers
        available_memory_per_server = [memory_per_server] * total_servers
        available_storage_per_server = [storage_per_server] * total_servers
        available_accelerators_per_server = [accelerators_per_server] * total_servers

        total_available_cpus = available.get('cpu', 0)
        total_available_memory = available.get('memory', 0)
        total_available_storage = available.get('storage', 0)
        total_available_accelerators = available.get('accelerators', 0)

        total_used_cpus = (total_servers * cpus_per_server) - total_available_cpus
        total_used_memory = (total_servers * memory_per_server) - total_available_memory
        total_used_storage = (total_servers * storage_per_server) - total_available_storage
        total_used_accelerators = (total_servers * accelerators_per_server) - total_available_accelerators

        avg_used_cpus = total_used_cpus / max(total_servers, 1)
        avg_used_memory = total_used_memory / max(total_servers, 1)
        avg_used_storage = total_used_storage / max(total_servers, 1)
        avg_used_accelerators = total_used_accelerators / max(total_servers, 1) if accelerators_per_server > 0 else 0

        for server_idx in range(total_servers):
            available_cpus_per_server[server_idx] = max(0, cpus_per_server - avg_used_cpus)
            available_memory_per_server[server_idx] = max(0, memory_per_server - avg_used_memory)
            available_storage_per_server[server_idx] = max(0, storage_per_server - avg_used_storage)
            if accelerators_per_server > 0:
                available_accelerators_per_server[server_idx] = max(0, accelerators_per_server - avg_used_accelerators)

        for vm_idx in range(task.num_vms):
            allocated = False

            for server_idx in range(total_servers):
                can_fit = (
                        available_cpus_per_server[server_idx] >= task.vcpus_per_vm and
                        available_memory_per_server[server_idx] >= task.memory_per_vm and
                        available_storage_per_server[server_idx] >= task.storage_per_vm
                )

                if task.requires_accelerator:
                    can_fit = can_fit and (available_accelerators_per_server[server_idx] >= 1)

                if can_fit:
                    vm_allocations.append(VMAllocation(
                        vm_index=vm_idx,
                        cell_id=cell.cell_id,
                        hw_type_id=hw_id,
                        server_index=server_idx
                    ))

                    available_cpus_per_server[server_idx] -= task.vcpus_per_vm
                    available_memory_per_server[server_idx] -= task.memory_per_vm
                    available_storage_per_server[server_idx] -= task.storage_per_vm
                    if task.requires_accelerator:
                        available_accelerators_per_server[server_idx] -= 1

                    allocated = True
                    break

            if not allocated:
                logger.warning(
                    f"Could not allocate VM {vm_idx} for task {task.task_id}. "
                    f"Only {len(vm_allocations)}/{task.num_vms} VMs allocated."
                )
                return []

        return vm_allocations

    def get_statistics(self) -> dict:
        """Get allocator statistics."""
        return {
            "total_allocations": self.allocation_count,
            "rejections": self.rejection_count,
            "success_rate": ((self.allocation_count - self.rejection_count) / max(self.allocation_count, 1)) * 100
        }

    def get_logs(self) -> dict:
        return self.logger.get_summary()

    def save_logs(self) -> None:
        self.logger.save_to_file()
