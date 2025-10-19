"""
Statistics module for cloud simulator.

Tracks and aggregates simulation metrics for analysis.
"""

from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class PowerModel:
    idle_power: float
    peak_power_cpu: float
    peak_power_acc: float


class Statistics:
    def __init__(self, resource_type: int, power_model: PowerModel):
        self.resource_type = resource_type
        self.power_model = power_model

        self.accepted_tasks = 0
        self.rejected_tasks = 0
        self.total_power_consumption = 0.0

        self.task_completion_times: List[float] = []
        self.task_waiting_times: List[float] = []
        self.task_response_times: List[float] = []

    def calculate_power_consumption(
        self,
        processor_utilization: float,
        accelerator_utilization: float,
        is_active: int,
        total_accelerators: int
    ) -> float:
        if is_active == 0:
            return 0.0

        cpu_power = (
            self.power_model.idle_power +
            (self.power_model.peak_power_cpu - self.power_model.idle_power) *
            processor_utilization
        )

        acc_power = 0.0
        if total_accelerators > 0:
            acc_power = (
                self.power_model.peak_power_acc *
                accelerator_utilization *
                total_accelerators
            )

        return cpu_power + acc_power

    def record_task_completion(
        self,
        arrival_time: float,
        start_time: float,
        completion_time: float
    ) -> None:
        waiting_time = start_time - arrival_time
        response_time = completion_time - arrival_time
        execution_time = completion_time - start_time

        self.task_waiting_times.append(waiting_time)
        self.task_response_times.append(response_time)
        self.task_completion_times.append(execution_time)

    def get_summary(self) -> Dict:
        total_tasks = self.accepted_tasks + self.rejected_tasks
        acceptance_rate = (
            self.accepted_tasks / total_tasks if total_tasks > 0 else 0.0
        )

        avg_waiting_time = (
            sum(self.task_waiting_times) / len(self.task_waiting_times)
            if self.task_waiting_times else 0.0
        )

        avg_response_time = (
            sum(self.task_response_times) / len(self.task_response_times)
            if self.task_response_times else 0.0
        )

        avg_completion_time = (
            sum(self.task_completion_times) / len(self.task_completion_times)
            if self.task_completion_times else 0.0
        )

        return {
            "resource_type": self.resource_type,
            "total_tasks": total_tasks,
            "accepted_tasks": self.accepted_tasks,
            "rejected_tasks": self.rejected_tasks,
            "acceptance_rate": acceptance_rate,
            "rejection_rate": 1.0 - acceptance_rate,
            "total_power_consumption": self.total_power_consumption,
            "avg_waiting_time": avg_waiting_time,
            "avg_response_time": avg_response_time,
            "avg_execution_time": avg_completion_time,
        }
