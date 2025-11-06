"""
Core allocation service implementing the smart allocation algorithm.
Starts with a simple heuristic approach optimizing for energy efficiency.
"""
from typing import Optional, Tuple, List
import logging
from models.schemas import AllocationRequest, AllocationDecision, CellStatus, HardwareType
from services.energy_calculator import EnergyCalculator


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

        try:
            # Find best allocation using energy-aware heuristic
            allocation = self._heuristic_energy_aware_allocation(request)

            if allocation:
                cell_id, hw_type_id, energy_cost, reason = allocation
                logger.info(
                    f"Task {request.task.task_id} allocated to Cell {cell_id}, "
                    f"HW Type {hw_type_id}, Est. Energy: {energy_cost:.4f} kWh"
                )
                return AllocationDecision(
                    success=True,
                    cell_id=cell_id,
                    hw_type_id=hw_type_id,
                    estimated_energy_cost=energy_cost,
                    reason=reason,
                    allocation_method="heuristic_energy_aware",
                    timestamp=request.timestamp
                )
            else:
                self.rejection_count += 1
                logger.warning(f"Task {request.task.task_id} rejected - no suitable resources")
                return AllocationDecision(
                    success=False,
                    reason="No suitable resources available in any cell",
                    allocation_method="heuristic_energy_aware",
                    timestamp=request.timestamp
                )

        except Exception as e:
            logger.error(f"Error allocating task {request.task.task_id}: {str(e)}")
            return AllocationDecision(
                success=False,
                reason=f"Internal error: {str(e)}",
                allocation_method="heuristic_energy_aware",
                timestamp=request.timestamp
            )

    def _heuristic_energy_aware_allocation(
        self, 
        request: AllocationRequest
    ) -> Optional[Tuple[int, int, float, str]]:
        """
        Heuristic allocation optimizing for energy efficiency.

        Strategy:
        1. Filter cells/HW types that can accommodate the task
        2. For each candidate, estimate energy cost
        3. Select the one with lowest energy cost

        Args:
            request: Allocation request

        Returns:
            Tuple of (cell_id, hw_type_id, energy_cost, reason) or None if no allocation
        """
        task = request.task
        candidates = []

        # Iterate through all cells and hardware types
        for cell in request.cells:
            for hw_type in cell.hw_types:
                # Check if this HW type matches task requirements
                if not self._is_compatible(task, hw_type):
                    continue

                # Check resource availability
                if not self._has_sufficient_resources(task, hw_type, cell):
                    continue

                # Estimate energy cost for this allocation
                energy_cost = self._estimate_energy_cost(task, hw_type, cell)

                # Calculate efficiency score (prefer less utilized servers for energy savings)
                efficiency = self._calculate_efficiency_score(hw_type, cell)

                candidates.append({
                    'cell_id': cell.cell_id,
                    'hw_type_id': hw_type.hw_type_id,
                    'hw_type_name': hw_type.hw_type_name,
                    'energy_cost': energy_cost,
                    'efficiency': efficiency,
                    'score': energy_cost * (2.0 - efficiency)  # Lower is better
                })

        if not candidates:
            return None

        # Select candidate with lowest score (best energy efficiency)
        best = min(candidates, key=lambda x: x['score'])

        reason = (
            f"Selected {best['hw_type_name']} in Cell {best['cell_id']} "
            f"for optimal energy efficiency (Est: {best['energy_cost']:.4f} kWh)"
        )

        return (best['cell_id'], best['hw_type_id'], best['energy_cost'], reason)

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

        # Calculate total resources for this HW type
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

    def get_statistics(self) -> dict:
        """Get allocator statistics."""
        return {
            "total_allocations": self.allocation_count,
            "rejections": self.rejection_count,
            "success_rate": (
                (self.allocation_count - self.rejection_count) / max(self.allocation_count, 1)
            ) * 100
        }
