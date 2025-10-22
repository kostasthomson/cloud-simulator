import logging
from typing import List, Dict
from pathlib import Path

from .inputs import SimulationInputs
from .cell import Cell
from .task import Task, TaskConfig

logger = logging.getLogger(__name__)


class Simulator:

    def __init__(self, cell_data_file: str, broker_data_file: str, task_data_file: str = None):
        self.sim_inputs = SimulationInputs()
        self.sim_inputs.parse(cell_data_file, broker_data_file)

        self.max_time = self.sim_inputs.max_time
        self.update_interval = self.sim_inputs.update_interval

        self.cells: List[Cell] = []
        for cell_input in self.sim_inputs.cell_inputs:
            cell = Cell(cell_input)
            broker_type = self.sim_inputs.sosm_integration
            broker = cell.create_broker(broker_type)
            broker.init_with_inputs(cell, self.sim_inputs)
            cell.set_broker(broker)
            self.cells.append(cell)

        self.tasks: List[Task] = []
        self.pending_tasks: List[Task] = []
        self.current_time = 0.0

        if task_data_file:
            self._initialize_tasks(task_data_file)

        logger.info(f"Simulator initialized: {len(self.cells)} cells, broker_type={self.sim_inputs.sosm_integration}")

    def _initialize_tasks(self, task_data_file: str) -> None:
        import json
        with open(task_data_file, 'r') as f:
            task_data = json.load(f)

        task_id = 0
        for task_dict in task_data.get("tasks", []):
            task_config = TaskConfig(
                processors_per_vm=task_dict["processors_per_vm"],
                memory_per_vm=task_dict["memory_per_vm"],
                network_bandwidth=task_dict["network_bandwidth"],
                storage_per_vm=task_dict["storage_per_vm"],
                accelerators_per_vm=task_dict.get("accelerators_per_vm", 0),
                num_vms=task_dict["num_vms"],
                total_instructions=task_dict["total_instructions"],
                processor_utilization=task_dict.get("processor_utilization", 1.0),
                memory_utilization=task_dict.get("memory_utilization", 1.0),
                storage_utilization=task_dict.get("storage_utilization", 0.0),
                accelerator_utilization=task_dict.get("accelerator_utilization", 0.0),
                available_implementations=task_dict["available_implementations"],
                arrival_time=task_dict["arrival_time"],
            )
            self.tasks.append(Task(task_id, task_config))
            task_id += 1

        self.tasks.sort(key=lambda t: t.arrival_time)
        self.pending_tasks = self.tasks.copy()
        logger.info(f"Initialized {len(self.tasks)} tasks")

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)
        if task.arrival_time >= self.current_time:
            self.pending_tasks.append(task)
            self.pending_tasks.sort(key=lambda t: t.arrival_time)

    def run(self, cell_id: int = 0) -> Dict:
        logger.info(f"Starting simulation: max_time={self.max_time}, update_interval={self.update_interval}")

        if cell_id >= len(self.cells):
            raise ValueError(f"Invalid cell_id {cell_id}, only {len(self.cells)} cells available")

        cell = self.cells[cell_id]
        broker = cell.get_broker()

        while self.current_time <= self.max_time:
            if int(self.current_time) % 100 == 0:
                logger.debug(f"Timestep: {self.current_time}")

            arriving_tasks = [
                t for t in self.pending_tasks
                if t.arrival_time <= self.current_time
            ]

            for task in arriving_tasks:
                task.start_time = self.current_time
                broker.deploy(cell.get_resources(), cell.get_network(), cell.get_stats(), task)
                self.pending_tasks.remove(task)
                logger.debug(f"Time {self.current_time}: Task {task.id} deployed")

            broker.update_state_info(cell, self.current_time)
            broker.timestep(cell)

            self.current_time += self.update_interval

            if len(self.pending_tasks) == 0:
                active_tasks = self._count_active_tasks(broker)
                if active_tasks == 0:
                    logger.info(f"All tasks completed at time {self.current_time}")
                    break

        logger.info("Simulation complete")
        return self._generate_results(cell)

    def _count_active_tasks(self, broker) -> int:
        if hasattr(broker, 'vrms'):
            count = 0
            for type_vrms in broker.vrms:
                for vrm in type_vrms:
                    count += len(vrm.get_queue())
            return count
        elif hasattr(broker, 'get_queue_length'):
            return broker.get_queue_length()
        return 0

    def _generate_results(self, cell: Cell) -> Dict:
        results = {
            "simulation_config": {
                "max_time": self.max_time,
                "update_interval": self.update_interval,
                "actual_end_time": self.current_time,
            },
            "cell_state": cell.get_state(),
            "statistics": {
                i: stats.get_summary()
                for i, stats in enumerate(cell.get_stats())
            }
        }
        return results

    def save_results(self, output_path: str, cell_id: int = 0) -> None:
        results = self._generate_results(self.cells[cell_id])
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_path}")
