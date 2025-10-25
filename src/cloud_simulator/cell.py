from typing import List, Optional
from .resource import Resource, ResourceConfig
from .network import Network
from .statistics import Statistics
from .power import Power
from .inputs import CellInputs


class Cell:

    def __init__(self, cell_inputs: CellInputs):
        self.cell_id = cell_inputs.cell_id
        self.number_of_types = cell_inputs.number_of_types
        self.types = cell_inputs.types[:]
        self.number_of_resources_per_type = cell_inputs.number_of_resources_per_type[:]

        self.resources: List[List[Resource]] = []
        self.power_consumption: List[Power] = []
        self.statistics: List[Statistics] = []
        self.network: Optional[Network] = None
        self.broker = None

        for i in range(self.number_of_types):
            res_input = cell_inputs.resource_inputs[i]
            pow_input = cell_inputs.power_inputs[i]

            res_config = ResourceConfig(
                total_processors=res_input.num_of_proc_units,
                total_memory=res_input.total_memory,
                total_storage=res_input.total_storage,
                total_accelerators=res_input.total_accelerators,
                comp_cap_per_proc=res_input.compute_capability,
                comp_cap_per_acc=res_input.accelerator_compute_capability,
                overcommitment_processors=res_input.overcommitment_processors
            )

            resources_of_type = []
            for j in range(self.number_of_resources_per_type[i]):
                resource = Resource(j, self.types[i], res_config)
                resources_of_type.append(resource)

            self.resources.append(resources_of_type)

            power = Power(pow_input)
            self.power_consumption.append(power)

            stats = Statistics()
            self.statistics.append(stats)

        if cell_inputs.network_inputs:
            self.network = Network(cell_inputs.network_inputs.net_bw)

    def get_cell_id(self) -> int:
        return self.cell_id

    def get_number_of_types(self) -> int:
        return self.number_of_types

    def get_types(self) -> List[int]:
        return self.types

    def get_number_of_resources_per_type(self) -> List[int]:
        return self.number_of_resources_per_type

    def get_resources(self) -> List[List[Resource]]:
        return self.resources

    def get_power_consumption(self) -> List[Power]:
        return self.power_consumption

    def get_network(self) -> Network:
        return self.network

    def get_stats(self) -> List[Statistics]:
        return self.statistics

    def set_broker(self, broker) -> None:
        self.broker = broker

    def get_broker(self):
        return self.broker

    def create_broker(self, broker_type: int):
        if broker_type == 0:
            from .traditional_broker import TraditionalBroker
            return TraditionalBroker()
        elif broker_type == 1:
            from .sosm_broker import SOSMBroker
            return SOSMBroker()
        elif broker_type == 2:
            from .improved_sosm_broker import ImprovedSOSMBroker
            return ImprovedSOSMBroker()
        else:
            raise ValueError(f"Unknown broker type: {broker_type}")

    def get_state(self) -> dict:
        resource_summary = []
        for type_idx, resources_of_type in enumerate(self.resources):
            total_resources = len(resources_of_type)
            active_resources = sum(1 for r in resources_of_type if r.active)
            total_procs = sum(r.total_processors for r in resources_of_type)
            avail_procs = sum(r.get_available_processors() for r in resources_of_type)
            total_mem = sum(r.total_memory for r in resources_of_type)
            avail_mem = sum(r.get_available_memory() for r in resources_of_type)

            resource_summary.append({
                "type_id": self.types[type_idx],
                "total_resources": total_resources,
                "active_resources": active_resources,
                "total_processors": total_procs,
                "available_processors": avail_procs,
                "total_memory": total_mem,
                "available_memory": avail_mem,
            })

        return {
            "cell_id": self.cell_id,
            "number_of_types": self.number_of_types,
            "resource_summary": resource_summary,
            "network": self.network.get_state() if self.network else {},
            "statistics": [stats.get_summary() for stats in self.statistics],
        }
