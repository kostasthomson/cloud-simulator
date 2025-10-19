"""
Simulator module for cloud simulator.

Main orchestration class that runs the simulation loop.
"""

import json
import logging
from typing import List, Dict
from pathlib import Path

from .resource import Resource, ResourceConfig
from .network import Network
from .task import Task, TaskConfig
from .statistics import Statistics, PowerModel
from .cell import Cell
from .traditional_broker import TraditionalBroker

logger = logging.getLogger(__name__)


class Simulator:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()

        self.max_time = self.config["simulation"]["max_time"]
        self.update_interval = self.config["simulation"]["update_interval"]

        self.cell = Cell()
        self.broker = TraditionalBroker(
            poll_interval=self.config["broker"]["poll_interval"]
        )

        self.tasks: List[Task] = []
        self.pending_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []

        self.current_time = 0.0

        self._initialize_cell()
        self._initialize_tasks()

    def _load_config(self) -> dict:
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _initialize_cell(self) -> None:
        network_config = self.config["network"]
        self.cell.set_network(Network(network_config["total_bandwidth"]))

        for res_type_config in self.config["resource_types"]:
            res_type = res_type_config["type"]
            num_resources = res_type_config["num_resources"]

            power_model = PowerModel(
                idle_power=res_type_config["power"]["idle_power"],
                peak_power_cpu=res_type_config["power"]["peak_power_cpu"],
                peak_power_acc=res_type_config["power"]["peak_power_acc"],
            )

            resources = []
            for i in range(num_resources):
                resource_config = ResourceConfig(
                    total_processors=res_type_config["total_processors"],
                    total_memory=res_type_config["total_memory"],
                    total_storage=res_type_config["total_storage"],
                    total_accelerators=res_type_config["total_accelerators"],
                    comp_cap_per_proc=res_type_config["comp_cap_per_proc"],
                    comp_cap_per_acc=res_type_config["comp_cap_per_acc"],
                    overcommitment_processors=res_type_config.get(
                        "overcommitment_processors", 1.0
                    ),
                )
                resources.append(Resource(i, res_type, resource_config))

            self.cell.add_resource_type(res_type, resources)
            self.cell.add_statistics(res_type, Statistics(res_type, power_model))

        self.broker.initialize(self.cell)
        logger.info(f"Cell initialized with {len(self.cell.resources)} resource types")

    def _initialize_tasks(self) -> None:
        task_id = 0
        for task_config_dict in self.config["tasks"]:
            task_config = TaskConfig(
                processors_per_vm=task_config_dict["processors_per_vm"],
                memory_per_vm=task_config_dict["memory_per_vm"],
                network_bandwidth=task_config_dict["network_bandwidth"],
                storage_per_vm=task_config_dict["storage_per_vm"],
                accelerators_per_vm=task_config_dict.get("accelerators_per_vm", 0),
                num_vms=task_config_dict["num_vms"],
                total_instructions=task_config_dict["total_instructions"],
                processor_utilization=task_config_dict.get("processor_utilization", 1.0),
                memory_utilization=task_config_dict.get("memory_utilization", 1.0),
                storage_utilization=task_config_dict.get("storage_utilization", 0.0),
                accelerator_utilization=task_config_dict.get("accelerator_utilization", 0.0),
                available_implementations=task_config_dict["available_implementations"],
                arrival_time=task_config_dict["arrival_time"],
            )
            self.tasks.append(Task(task_id, task_config))
            task_id += 1

        self.tasks.sort(key=lambda t: t.arrival_time)
        self.pending_tasks = self.tasks.copy()
        logger.info(f"Initialized {len(self.tasks)} tasks")

    def run(self) -> Dict:
        logger.info(f"Starting simulation: max_time={self.max_time}, update_interval={self.update_interval}")

        while self.current_time <= self.max_time:
            logger.debug(f"Timestep: {self.current_time}")

            arriving_tasks = [
                t for t in self.pending_tasks
                if t.arrival_time <= self.current_time
            ]

            for task in arriving_tasks:
                task.start_time = self.current_time
                deployed = self.broker.deploy(self.cell, task)
                if deployed:
                    logger.info(f"Time {self.current_time}: Task {task.id} deployed")
                else:
                    logger.info(f"Time {self.current_time}: Task {task.id} rejected")
                self.pending_tasks.remove(task)

            self.broker.update_state_info(self.cell, self.current_time)

            self.broker.timestep(self.cell, self.current_time)

            self.current_time += self.update_interval

            if len(self.pending_tasks) == 0 and self.broker.get_queue_length() == 0:
                logger.info(f"All tasks completed at time {self.current_time}")
                break

        logger.info("Simulation complete")
        return self._generate_results()

    def _generate_results(self) -> Dict:
        results = {
            "simulation_config": {
                "max_time": self.max_time,
                "update_interval": self.update_interval,
                "actual_end_time": self.current_time,
            },
            "cell_state": self.cell.get_state(),
            "broker": {
                "queue_length": self.broker.get_queue_length(),
                "poll_interval": self.broker.poll_interval,
            },
        }
        return results

    def save_results(self, output_path: str) -> None:
        results = self._generate_results()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_path}")
