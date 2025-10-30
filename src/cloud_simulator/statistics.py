"""
Statistics module for cloud simulator.

Matches the C++ stat.h/stat.cpp implementation exactly.
"""

from typing import Dict


class Statistics:
    def __init__(self):
        self.processors_over_active_servers: int = 0
        self.memory_over_active_servers: float = 0.0
        self.storage_over_active_servers: float = 0.0
        self.accelerators_over_active_servers: int = 0
        self.alloc: int = 0
        self.current_timestep: float = 0.0
        self.physical_memory: float = 0.0
        self.physical_processors: float = 0.0
        self.physical_storage: float = 0.0
        self.physical_network: float = 0.0
        self.total_memory: float = 0.0
        self.total_processors: float = 0.0
        self.available_processors: float = 0.0
        self.available_memory: float = 0.0
        self.utilized_processors: float = 0.0
        self.utilized_memory: float = 0.0
        self.total_storage: float = 0.0
        self.available_storage: float = 0.0
        self.utilized_storage: float = 0.0
        self.total_network: float = 0.0
        self.available_network: float = 0.0
        self.utilized_network: float = 0.0
        self.total_power_consumption: float = 0.0

        self.total_accelerators: int = 0
        self.available_accelerators: int = 0
        self.utilized_accelerators: int = 0
        self.active_servers: int = 0
        self.running_vms: int = 0
        self.rejected_tasks: int = 0
        self.accepted_tasks: int = 0

        self.actual_utilized_processors: float = 0.0
        self.actual_utilized_memory: float = 0.0
        self.actual_utilized_network: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "Time Step": self.current_timestep,
            "Active Servers": self.active_servers,
            "Actual Utilized Memory": self.actual_utilized_memory,
            "Actual Utilized Network": self.actual_utilized_network,
            "Actual Utilized Processors": self.actual_utilized_processors,
            "Available Accelerators": self.available_accelerators,
            "Available Memory": self.available_memory,
            "Available Network": self.available_network,
            "Available Processors": self.available_processors,
            "Available Storage": self.available_storage,
            "Running VMs": self.running_vms,
            "Total Accelerators": self.total_accelerators,
            "Total Accelerators over Active Servers": self.accelerators_over_active_servers,
            "Total Energy Consumption": self.total_power_consumption,
            "Total Memory": self.total_memory,
            "Total Memory over Active Servers": self.memory_over_active_servers,
            "Total Network": self.total_network,
            "Total Number of accepted Tasks": self.accepted_tasks,
            "Total Number of rejected Tasks": self.rejected_tasks,
            "Total Physical Memory": self.physical_memory,
            "Total Physical Network": self.physical_network,
            "Total Physical Processors": self.physical_processors,
            "Total Physical Storage": self.physical_storage,
            "Total Processors": self.total_processors,
            "Total Processors over Active Servers": self.processors_over_active_servers,
            "Total Storage": self.total_storage,
            "Total Storage over Active Servers": self.storage_over_active_servers,
            "Utilized Accelerators": self.utilized_accelerators,
            "Utilized Memory": self.utilized_memory,
            "Utilized Network": self.utilized_network,
            "Utilized Processors": self.utilized_processors,
            "Utilized Storage": self.utilized_storage
        }

    def print_stats(self) -> None:
        if self.alloc:
            print(f"         Active Servers: {self.active_servers}")
            print(f"         Time Step: {self.current_timestep}")
            print(f"         Total Processors over Active Servers: {self.processors_over_active_servers}")
            print(f"         Total Memory over Active Servers: {self.memory_over_active_servers}")
            print(f"         Total Storage over Active Servers: {self.storage_over_active_servers}")
            print(f"         Total Accelerators over Active Servers: {self.accelerators_over_active_servers}")
            print(f"         Running VMs: {self.running_vms}")
            print(f"         Total Number of accepted Tasks: {self.accepted_tasks}")
            print(f"         Total Number of rejected Tasks: {self.rejected_tasks}")
            print(f"         Total Physical Processors: {self.physical_processors} Proc. Units")
            print(f"         Total Processors: {self.total_processors} Proc. Units")
            print(f"         Utilized Processors: {self.utilized_processors} Proc. Units")
            print(f"         Actual Utilized Processors: {self.actual_utilized_processors} Proc. Units")
            print(f"         Available Processors: {self.available_processors} Proc. Units")
            print(f"         Total Physical Memory: {self.physical_memory} GBytes")
            print(f"         Total Memory: {self.total_memory} GBytes")
            print(f"         Utilized Memory: {self.utilized_memory} GBytes")
            print(f"         Actual Utilized Memory: {self.actual_utilized_memory} Proc. Units")
            print(f"         Available Memory: {self.available_memory} GBytes")
            print(f"         Total Physical Storage: {self.physical_storage} TBytes")
            print(f"         Total Storage: {self.total_storage} TBytes")
            print(f"         Utilized Storage: {self.utilized_storage} TBytes")
            print(f"         Available Storage: {self.available_storage} TBytes")
            print(f"         Total Physical Network: {self.physical_network} Gbps")
            print(f"         Total Network: {self.total_network} Gbps")
            print(f"         Utilized Network: {self.utilized_network} Gbps")
            print(f"         Actual Utilized Network: {self.actual_utilized_network} Gbps")
            print(f"         Available Network: {self.available_network} Gbps")
            print(f"         Total Energy Consumption: {self.total_power_consumption} GWh")
            print(f"         Total Accelerators: {self.total_accelerators}")
            print(f"         Utilized Accelerators: {self.utilized_accelerators}")
            print(f"         Available Accelerators: {self.available_accelerators}")
