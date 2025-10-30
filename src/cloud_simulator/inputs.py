import json
from typing import List, Optional
from dataclasses import dataclass, field


IntegrationMap = ["Traditional", "SOSM", "Improved SOSM"]

@dataclass
class BrokerInputs:
    number_of_functions: int = 0
    weights: List[float] = field(default_factory=list)
    init_res_per_vrm: int = 0
    init_vrm_per_pswitch: int = 0
    init_pswitch_per_prouter: int = 0
    poll_interval_cell_m: float = 0.0
    poll_interval_prouter: float = 0.0
    poll_interval_pswitch: float = 0.0
    poll_interval_vrm: float = 0.0
    vrm_deploy_strategy: int = 0

    def parse(self, filename: str, cell_id: int) -> None:
        with open(filename, 'r') as f:
            data = json.load(f)

        broker = data['Brokers'][cell_id]
        self.number_of_functions = broker['Number of functions']
        self.weights = broker['Weights of functions']
        self.init_res_per_vrm = broker['Number of Resources per vRM']
        self.init_vrm_per_pswitch = broker['Number of vRMs per pSwitch']
        self.init_pswitch_per_prouter = broker['Number of pSwitch per pRouter']
        self.poll_interval_cell_m = broker['Poll Interval Cell Manager']
        self.poll_interval_prouter = broker['Poll Interval pRouter']
        self.poll_interval_pswitch = broker['Poll Interval pSwitch']
        self.poll_interval_vrm = broker['Poll Interval vRM']
        self.vrm_deploy_strategy = broker['vRM deployment strategy']

    def print(self) -> None:
        print("    =========== Broker ===========")
        print(f"        Number of Assessment Functions: {self.number_of_functions}")
        print(f"        Weights: {self.weights}")
        print(f"        Initial number of Resources per vRM: {self.init_res_per_vrm}")
        print(f"        Initial number of vRMs per pSwitch: {self.init_vrm_per_pswitch}")
        print(f"        Initial number of pSwitches per pRouter: {self.init_pswitch_per_prouter}")
        print(f"        Poll Interval for the Cell Manager: {self.poll_interval_cell_m}")
        print(f"        Poll Interval for the pRouters: {self.poll_interval_prouter}")
        print(f"        Poll Interval for the pSwitches: {self.poll_interval_pswitch}")
        print(f"        Poll Interval for the vRMs: {self.poll_interval_vrm}")
        print(f"        vRM deployment strategy: {self.vrm_deploy_strategy}")


@dataclass
class AppInputs:
    min_max_jobs_per_sec: List[float] = field(default_factory=list)
    num_of_apps: int = 0
    number_of_available_implementations_per_app: List[int] = field(default_factory=list)
    available_implementations_per_app: List[List[int]] = field(default_factory=list)
    min_max_vm_per_app: List[List[int]] = field(default_factory=list)
    min_max_ins_per_app: List[List[float]] = field(default_factory=list)
    min_max_proc_per_vm: List[List[float]] = field(default_factory=list)
    min_max_mem_per_vm: List[List[float]] = field(default_factory=list)
    min_max_sto_per_vm: List[List[float]] = field(default_factory=list)
    min_max_net_per_app: List[List[float]] = field(default_factory=list)
    type_of_act_p: List[int] = field(default_factory=list)
    type_of_act_m: List[int] = field(default_factory=list)
    type_of_act_n: List[int] = field(default_factory=list)
    min_max_act_p: List[List[float]] = field(default_factory=list)
    min_max_act_m: List[List[float]] = field(default_factory=list)
    min_max_act_n: List[List[float]] = field(default_factory=list)
    accelerator: List[List[int]] = field(default_factory=list)
    rho_acc: List[List[float]] = field(default_factory=list)

    def parse(self, filename: str) -> None:
        with open(filename, 'r') as f:
            data = json.load(f)

        apps = data.get('Applications', [])
        self.num_of_apps = len(apps)


    def print(self) -> None:
        print(f"Number of Applications: {self.num_of_apps}")


@dataclass
class NetworkInputs:
    net_bw: float = 0.0
    overcommitment_network: float = 1.0

    def print(self) -> None:
        print(f"Network Bandwidth: {self.net_bw}")
        print(f"Overcommitment: {self.overcommitment_network}")


@dataclass
class PowerInputs:
    type_cpu: int = 0
    type_acc: int = 0
    cpu_pmin: float = 0.0
    cpu_pmax: float = 0.0
    cpu_c: float = 0.0
    num_of_points: int = 0
    cpu_bins: List[float] = field(default_factory=list)
    cpu_p: List[float] = field(default_factory=list)
    accelerator: int = 0
    acc_pmin: float = 0.0
    acc_pmax: float = 0.0
    acc_c: float = 0.0

    def print(self) -> None:
        print(f"CPU Power Model Type: {self.type_cpu}")
        print(f"CPU Min Power: {self.cpu_pmin}, Max Power: {self.cpu_pmax}")
        if self.accelerator:
            print(f"Accelerator Power Model Type: {self.type_acc}")
            print(f"Accelerator Min Power: {self.acc_pmin}, Max Power: {self.acc_pmax}")


@dataclass
class ResourceInputs:
    num_of_proc_units: float = 0.0
    total_memory: float = 0.0
    total_storage: float = 0.0
    overcommitment_processors: float = 1.0
    overcommitment_memory: float = 1.0
    compute_capability: float = 0.0
    accelerator: int = 0
    accelerator_compute_capability: float = 0.0
    total_accelerators: int = 0
    resource_type: int = 0

    def print(self) -> None:
        print(f"Resource Type: {self.resource_type}")
        print(f"Processors: {self.num_of_proc_units}, Memory: {self.total_memory}, Storage: {self.total_storage}")
        if self.accelerator:
            print(f"Accelerators: {self.total_accelerators}")


@dataclass
class CellInputs:
    cell_id: int = 0
    resource_inputs: List[ResourceInputs] = field(default_factory=list)
    power_inputs: List[PowerInputs] = field(default_factory=list)
    network_inputs: Optional[NetworkInputs] = None
    broker_inputs: Optional[BrokerInputs] = None
    number_of_types: int = 0
    types: List[int] = field(default_factory=list)
    number_of_resources_per_type: List[int] = field(default_factory=list)

    def print(self) -> None:
        print(f"=== Cell {self.cell_id} ===")
        print(f"Number of Types: {self.number_of_types}")
        print(f"Types: {self.types}")
        print(f"Resources per Type: {self.number_of_resources_per_type}")


class SimulationInputs:

    def __init__(self):
        self.cell_inputs: List[CellInputs] = []
        self.num_of_cells: int = 0
        self.max_time: float = 0.0
        self.update_interval: float = 0.0
        self.sosm_integration: int = 0

    def parse(self, cell_data_file: str, broker_data_file: str) -> None:
        with open(cell_data_file, 'r') as f:
            cell_data = json.load(f)

        with open(broker_data_file, 'r') as f:
            broker_data = json.load(f)

        self.max_time = cell_data['Maximum simulation time']
        self.update_interval = cell_data['Update interval']
        self.num_of_cells = cell_data['Number of Cells']

        mechanism = broker_data.get('Resource allocation mechanism', 'Traditional')
        self.sosm_integration = IntegrationMap.index(mechanism)

        for i, cell in enumerate(cell_data['Cells']):
            cell_input = CellInputs()
            cell_input.cell_id = cell['Cell ID']

            net_input = NetworkInputs()
            net_input.net_bw = cell['Cell interconnection bandwidth']
            net_input.overcommitment_network = cell.get('Network bandwidth overcommitment ratio', 1.0)
            cell_input.network_inputs = net_input

            cell_input.number_of_types = cell['Number of hardware(HW) types']

            for hw_type in cell['HW types']:
                res_input = ResourceInputs()
                res_input.resource_type = hw_type['HW type ID']
                res_input.num_of_proc_units = hw_type['Number of CPUs per server']
                res_input.total_memory = hw_type['Memory per server']
                res_input.total_storage = hw_type['Storage per server']
                res_input.overcommitment_processors = hw_type['Processors overcommitment ratio']
                res_input.overcommitment_memory = hw_type.get('Memory overcommitment ratio', 1.0)
                res_input.compute_capability = hw_type['Compute capability']
                res_input.accelerator = hw_type['Accelerators']
                res_input.total_accelerators = hw_type['Number of accelerators per server']
                res_input.accelerator_compute_capability = hw_type['Accelerator compute capability']

                cell_input.resource_inputs.append(res_input)
                cell_input.types.append(res_input.resource_type)
                cell_input.number_of_resources_per_type.append(hw_type['Number of servers'])

                pow_input = PowerInputs()
                pow_input.type_cpu = hw_type['Type of CPU model']
                pow_input.cpu_pmin = hw_type['CPU idle power consumption']
                pow_input.cpu_pmax = hw_type['CPU max power consumption']
                pow_input.cpu_c = hw_type['CPU sleep power consumption']
                pow_input.num_of_points = hw_type.get('CPU number of points for interpolation', 0)
                pow_input.cpu_bins = hw_type.get('CPU utilization bins', [])
                pow_input.cpu_p = hw_type.get('CPU power consumption', [])
                pow_input.type_acc = hw_type.get('Type of accelerator model', 0)
                pow_input.accelerator = hw_type['Accelerators']
                pow_input.acc_pmin = hw_type['Accelerator idle power consumption']
                pow_input.acc_pmax = hw_type['Accelerator max power consumption']
                pow_input.acc_c = hw_type['Accelerator sleep power consumption']

                cell_input.power_inputs.append(pow_input)

            if self.sosm_integration > 0:
                broker_input = BrokerInputs()
                broker_input.parse(broker_data_file, i)
                cell_input.broker_inputs = broker_input

            self.cell_inputs.append(cell_input)

    def print(self) -> None:
        print(f"Maximum Simulation Time: {self.max_time}")
        print(f"Update Interval: {self.update_interval}")
        print(f"Number of Cells: {self.num_of_cells}")
        print(f"SOSM Integration: {self.sosm_integration}")
        for cell_input in self.cell_inputs:
            cell_input.print()

    def get_broker(self) -> str:
        return IntegrationMap[self.sosm_integration]
