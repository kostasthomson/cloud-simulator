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
            raise NotImplementedError("Improved SOSM not yet implemented")
        else:
            raise ValueError(f"Unknown broker type: {broker_type}")

    def get_state(self) -> dict:
        return {
            "cell_id": self.cell_id,
            "number_of_types": self.number_of_types,
            "resources": [
                [r.get_state() for r in resources_of_type]
                for resources_of_type in self.resources
            ],
            "network": self.network.get_state() if self.network else {},
            "statistics": [stats.get_summary() for stats in self.statistics],
        }
