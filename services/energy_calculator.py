"""
Energy calculation utilities for estimating power consumption.
Based on server power profiles and utilization levels.
"""
from typing import List, Dict
import numpy as np


class EnergyCalculator:
    """
    Calculates energy consumption based on CPU/GPU utilization and power profiles.
    Uses interpolation from power consumption bins.
    """

    @staticmethod
    def interpolate_power_consumption(
        utilization: float,
        utilization_bins: List[float],
        power_values: List[float]
    ) -> float:
        """
        Interpolate power consumption based on utilization level.

        Args:
            utilization: Current utilization (0.0 to 1.0)
            utilization_bins: Utilization bin boundaries
            power_values: Power consumption at each bin

        Returns:
            Interpolated power consumption (Watts)
        """
        if not utilization_bins or not power_values:
            return 0.0

        # Clamp utilization to valid range
        utilization = max(0.0, min(1.0, utilization))

        # Use numpy for efficient interpolation
        return float(np.interp(utilization, utilization_bins, power_values))

    @staticmethod
    def estimate_task_energy(
        task_vcpus: int,
        task_duration: float,
        cpu_utilization: float,
        utilization_bins: List[float],
        power_values: List[float],
        has_accelerator: bool = False,
        accelerator_utilization: float = 0.0,
        accelerator_idle_power: float = 0.0,
        accelerator_max_power: float = 0.0
    ) -> float:
        """
        Estimate total energy consumption for a task.

        Args:
            task_vcpus: Number of vCPUs used by task
            task_duration: Task duration in seconds
            cpu_utilization: Expected CPU utilization (0.0 to 1.0)
            utilization_bins: CPU utilization bins
            power_values: CPU power consumption values
            has_accelerator: Whether task uses accelerator
            accelerator_utilization: Accelerator utilization ratio
            accelerator_idle_power: Accelerator idle power (W)
            accelerator_max_power: Accelerator max power (W)

        Returns:
            Estimated energy consumption in kWh
        """
        # Calculate CPU power
        cpu_power = EnergyCalculator.interpolate_power_consumption(
            cpu_utilization, utilization_bins, power_values
        )

        # Calculate accelerator power if applicable
        accelerator_power = 0.0
        if has_accelerator:
            # Linear interpolation between idle and max power based on utilization
            accelerator_power = (
                accelerator_idle_power + 
                accelerator_utilization * (accelerator_max_power - accelerator_idle_power)
            )

        # Total power in Watts
        total_power = cpu_power + accelerator_power

        # Convert to kWh: (Watts * seconds) / (3600 * 1000)
        energy_kwh = (total_power * task_duration) / 3_600_000.0

        return energy_kwh

    @staticmethod
    def calculate_server_efficiency(
        available_cpus: int,
        total_cpus: int,
        available_memory: float,
        total_memory: float,
        available_accelerators: int,
        total_accelerators: int
    ) -> float:
        """
        Calculate server efficiency score based on resource availability.
        Higher score means more available resources (better for new tasks).

        Args:
            available_cpus: Available CPU cores
            total_cpus: Total CPU cores
            available_memory: Available memory
            total_memory: Total memory
            available_accelerators: Available accelerators
            total_accelerators: Total accelerators

        Returns:
            Efficiency score (0.0 to 1.0)
        """
        # Calculate utilization ratios
        cpu_available_ratio = available_cpus / max(total_cpus, 1)
        memory_available_ratio = available_memory / max(total_memory, 1)

        # Weight CPU and memory equally
        base_score = (cpu_available_ratio + memory_available_ratio) / 2.0

        # Adjust for accelerator availability if relevant
        if total_accelerators > 0:
            accel_available_ratio = available_accelerators / total_accelerators
            # Weighted average: 40% CPU, 40% memory, 20% accelerator
            base_score = (
                0.4 * cpu_available_ratio + 
                0.4 * memory_available_ratio + 
                0.2 * accel_available_ratio
            )

        return base_score
