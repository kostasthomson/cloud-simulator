from typing import List, Optional, TYPE_CHECKING
from .base_broker import BaseBroker
from .vrm import VRM
from .pswitch import PSwitch
from .prouter import PRouter

if TYPE_CHECKING:
    from .cell import Cell
    from .inputs import SimulationInputs
    from .resource import Resource
    from .network import Network
    from .statistics import Statistics
    from .task import Task


class SOSMBroker(BaseBroker):

    def __init__(self):
        super().__init__()
        self.number_of_vrms: int = 0
        self.number_of_pswitches: int = 0
        self.number_of_prouters: int = 0
        self.poll_interval_cell_m: float = 0.0
        self.poll_interval_prouter: float = 0.0
        self.poll_interval_pswitch: float = 0.0
        self.poll_interval_vrm: float = 0.0
        self.spmsa: List[List[float]] = []
        self.vrms: List[List[VRM]] = []
        self.sis: List[float] = []
        self.pswitches: List[List[PSwitch]] = []
        self.prouters: List[List[PRouter]] = []
        self.cs: List[float] = []
        self.ps: List[float] = []
        self.pis: List[float] = []
        self.ws: List[float] = []
        self.number_of_functions: int = 0

    def init_with_inputs(self, cell: 'Cell', sim_inputs: 'SimulationInputs') -> None:
        self.alloc = 1
        self.number_of_types = cell.get_number_of_types()
        self.types = cell.get_types()[:]
        self.number_of_resources_per_type = cell.get_number_of_resources_per_type()[:]

        cell_input = None
        for ci in sim_inputs.cell_inputs:
            if ci.cell_id == cell.get_cell_id():
                cell_input = ci
                break

        if cell_input is None or cell_input.broker_inputs is None:
            raise ValueError("SOSM Broker requires broker configuration")

        broker_inputs = cell_input.broker_inputs

        self.poll_interval_cell_m = broker_inputs.poll_interval_cell_m
        self.poll_interval_prouter = broker_inputs.poll_interval_prouter
        self.poll_interval_pswitch = broker_inputs.poll_interval_pswitch
        self.poll_interval_vrm = broker_inputs.poll_interval_vrm

        temp_c = [0.0] * self.number_of_types
        temp_p = [0.0] * self.number_of_types
        temp_pi = [0.0] * self.number_of_types

        for i in range(self.number_of_types):
            resources = cell.get_resources()
            temp_c[i] = (resources[i][0].get_compute_capability() +
                        resources[i][0].get_accelerator_compute_capability())
            oz = 1.0
            active = resources[i][0].get_active()
            total_accelerators = resources[i][0].get_total_accelerators()
            power_consumption = cell.get_power_consumption()
            temp_p[i] = power_consumption[i].consumption(oz, oz, active, total_accelerators)
            oz = 0.0
            temp_pi[i] = power_consumption[i].consumption(oz, oz, active, total_accelerators)

        tmin_c = 0
        tmin_p = 0
        for i in range(1, self.number_of_types):
            if temp_c[tmin_c] > temp_c[i]:
                tmin_c = i
            if temp_p[tmin_p] > temp_p[i]:
                tmin_p = i

        min_c = temp_c[tmin_c]
        min_p = temp_p[tmin_p]

        for i in range(self.number_of_types):
            temp_pi[i] = temp_pi[i] / temp_p[i] if temp_p[i] > 0 else 0.0

        for i in range(self.number_of_types):
            temp_c[i] /= min_c if min_c > 0 else 1.0
            temp_p[i] /= min_p if min_p > 0 else 1.0

        self.number_of_functions = broker_inputs.number_of_functions
        self.ws = list(broker_inputs.weights)

        self.number_of_prouters = self.number_of_types
        self.number_of_vrms = 0
        self.number_of_pswitches = 0

        self.vrms = [[] for _ in range(self.number_of_types)]
        self.pswitches = [[] for _ in range(self.number_of_types)]
        self.prouters = [[] for _ in range(self.number_of_types)]

        for i in range(self.number_of_types):
            temp = self.number_of_resources_per_type[i] // broker_inputs.init_res_per_vrm
            for j in range(temp):
                start_idx = j * broker_inputs.init_res_per_vrm
                end_idx = (j + 1) * broker_inputs.init_res_per_vrm
                vrm = VRM(start_idx, end_idx, i, cell.get_resources(),
                         self.poll_interval_vrm, temp_c[i], temp_p[i], temp_pi[i],
                         broker_inputs.init_res_per_vrm, broker_inputs.number_of_functions,
                         broker_inputs.weights, broker_inputs.vrm_deploy_strategy)
                self.vrms[i].append(vrm)
            self.number_of_vrms += temp

            if temp * broker_inputs.init_res_per_vrm != self.number_of_resources_per_type[i]:
                start_idx = temp * broker_inputs.init_res_per_vrm
                end_idx = self.number_of_resources_per_type[i]
                vrm = VRM(start_idx, end_idx, i, cell.get_resources(),
                         self.poll_interval_vrm, temp_c[i], temp_p[i], temp_pi[i],
                         broker_inputs.init_res_per_vrm, broker_inputs.number_of_functions,
                         broker_inputs.weights, broker_inputs.vrm_deploy_strategy)
                self.vrms[i].append(vrm)
                self.number_of_vrms += 1

        for i in range(self.number_of_types):
            temp = len(self.vrms[i]) // broker_inputs.init_vrm_per_pswitch
            for j in range(temp):
                start_idx = j * broker_inputs.init_vrm_per_pswitch
                end_idx = (j + 1) * broker_inputs.init_vrm_per_pswitch
                pswitch = PSwitch(start_idx, end_idx, i, self.vrms,
                                 self.poll_interval_pswitch, temp_c[i], temp_p[i], temp_pi[i],
                                 broker_inputs.number_of_functions, broker_inputs.weights)
                self.pswitches[i].append(pswitch)
            self.number_of_pswitches += temp

            if temp * broker_inputs.init_vrm_per_pswitch != len(self.vrms[i]):
                start_idx = temp * broker_inputs.init_vrm_per_pswitch
                end_idx = len(self.vrms[i])
                pswitch = PSwitch(start_idx, end_idx, i, self.vrms,
                                 self.poll_interval_pswitch, temp_c[i], temp_p[i], temp_pi[i],
                                 broker_inputs.number_of_functions, broker_inputs.weights)
                self.pswitches[i].append(pswitch)
                self.number_of_pswitches += 1

        for i in range(self.number_of_types):
            prouter = PRouter(0, len(self.pswitches[i]), i, self.pswitches,
                            self.poll_interval_prouter, temp_c[i], temp_p[i], temp_pi[i],
                            broker_inputs.number_of_functions, broker_inputs.weights)
            self.prouters[i].append(prouter)

        self.spmsa = [[0.0] * 8 for _ in range(self.number_of_types)]

        for i in range(self.number_of_types):
            for prouter in self.prouters[i]:
                prouter_spmsa = prouter.get_spmsa()
                for j in range(8):
                    self.spmsa[i][j] = prouter_spmsa[j]

        self.available_network = cell.get_network().get_available_network()
        self.total_network = cell.get_network().get_total_network()
        self.sis = [0.0] * self.number_of_types
        self.cs = temp_c
        self.ps = temp_p
        self.pis = temp_pi

    def print(self) -> None:
        if self.alloc:
            for i in range(self.number_of_types):
                print(f"No of Type: {i}")
                print(f"     Number of available processing units: {self.spmsa[i][0]}")
                print(f"     Number of total processing units: {self.spmsa[i][1]}")
                print(f"     Number of available memory: {self.spmsa[i][2]}")
                print(f"     Number of total memory: {self.spmsa[i][3]}")
                print(f"     Number of available storage: {self.spmsa[i][4]}")
                print(f"     Number of total storage: {self.spmsa[i][5]}")
                print(f"     Number of available accelerators: {self.spmsa[i][6]}")
                print(f"     Number of total accelerators: {self.spmsa[i][7]}")
            print(f"Available network bandwidth: {self.available_network}")
            print(f"Total network bandwidth: {self.total_network}")

    def deassessment_functions(self, dnu: float, dnmem: float, choice: int, res_type: int) -> float:
        if self.spmsa[res_type][7] > 0:
            if choice == 0:
                return (dnu * self.cs[res_type] / self.spmsa[res_type][7]
                       if self.spmsa[res_type][7] > 0 else 0.0)
            elif choice == 1:
                return dnmem / self.spmsa[res_type][3] if self.spmsa[res_type][3] > 0 else 0.0
            elif choice == 2:
                denom = (self.ps[res_type] * (self.spmsa[res_type][7] - self.spmsa[res_type][6]) +
                        self.pis[res_type] * self.spmsa[res_type][6])
                return ((dnu * self.pis[res_type] * self.ps[res_type] * self.spmsa[res_type][7]) /
                       (denom * denom) if denom > 0 else 0.0)
            elif choice == 3:
                return 0.2 * dnu / self.spmsa[res_type][7] if self.spmsa[res_type][7] > 0 else 0.0
            else:
                return 0.0
        else:
            if choice == 0:
                return (dnu * self.cs[res_type] / self.spmsa[res_type][1]
                       if self.spmsa[res_type][1] > 0 else 0.0)
            elif choice == 1:
                return dnmem / self.spmsa[res_type][3] if self.spmsa[res_type][3] > 0 else 0.0
            elif choice == 2:
                denom = (self.ps[res_type] * (self.spmsa[res_type][1] - self.spmsa[res_type][0]) +
                        self.pis[res_type] * self.spmsa[res_type][0])
                return ((dnu * self.pis[res_type] * self.ps[res_type] * self.spmsa[res_type][1]) /
                       (denom * denom) if denom > 0 else 0.0)
            elif choice == 3:
                return 0.2 * dnu / self.spmsa[res_type][1] if self.spmsa[res_type][1] > 0 else 0.0
            else:
                return 0.0

    def update_state_info(self, cell: 'Cell', tstep: float) -> None:
        if not self.alloc:
            return

        if int(tstep) % int(self.poll_interval_vrm) == 0 if self.poll_interval_vrm > 0 else True:
            for i in range(self.number_of_types):
                for vrm in self.vrms[i]:
                    vrm.update_state_info(tstep)

        if int(tstep) % int(self.poll_interval_pswitch) == 0 if self.poll_interval_pswitch > 0 else True:
            for i in range(self.number_of_types):
                for pswitch in self.pswitches[i]:
                    pswitch.update_state_info(tstep)

        if int(tstep) % int(self.poll_interval_prouter) == 0 if self.poll_interval_prouter > 0 else True:
            for i in range(self.number_of_types):
                for prouter in self.prouters[i]:
                    prouter.update_state_info(tstep)

        if int(tstep) % int(self.poll_interval_cell_m) == 0 if self.poll_interval_cell_m > 0 else True:
            for i in range(self.number_of_types):
                for prouter in self.prouters[i]:
                    prouter_spmsa = prouter.get_spmsa()
                    for j in range(8):
                        self.spmsa[i][j] = prouter_spmsa[j]
                    self.sis[i] = prouter.get_si()

        self.available_network = cell.get_network().get_available_network()
        self.total_network = cell.get_network().get_total_network()

    def deploy(self, resources: List[List['Resource']], network: 'Network',
               stats: List['Statistics'], task: 'Task') -> None:
        rem = []
        rem2 = []
        count = 0

        for j in range(task.get_number_of_available_implementations()):
            for i in range(self.number_of_types):
                if self.types[i] == task.get_available_implementations()[j]:
                    rem.append(i)
                    rem2.append(j)
                    count += 1
                    break

        if self.available_network < task.get_req_pmns()[2]:
            stats[rem[0]].rejected_tasks += 1
            return

        self.available_network -= task.get_req_pmns()[2]

        max_si = 0.0
        selected_type = -1

        for i in range(count):
            req_proc = task.get_number_of_vms() * task.get_req_pmns()[0]
            req_mem = task.get_number_of_vms() * task.get_req_pmns()[1]
            req_sto = task.get_number_of_vms() * task.get_req_pmns()[3]
            req_acc = task.get_number_of_vms() * task.get_av_acc()[rem2[i]]

            if (max_si < self.sis[rem[i]] and
                req_proc <= self.spmsa[rem[i]][0] and
                req_mem <= self.spmsa[rem[i]][2] and
                req_sto <= self.spmsa[rem[i]][4] and
                req_acc <= self.spmsa[rem[i]][6]):

                if self.prouters[rem[i]][0].probe(req_proc, req_mem, req_sto, int(req_acc)) != -1:
                    max_si = self.sis[rem[i]]
                    selected_type = i

        if selected_type == -1:
            stats[rem[0]].rejected_tasks += 1
            return

        task.reduce_impl(rem2[selected_type])
        task.remap_type(rem[selected_type], 1)
        res_type = rem[selected_type]

        self.spmsa[res_type][0] -= task.get_number_of_vms() * task.get_req_pmns()[0]
        self.spmsa[res_type][2] -= task.get_number_of_vms() * task.get_req_pmns()[1]
        self.spmsa[res_type][4] -= task.get_number_of_vms() * task.get_req_pmns()[3]
        self.spmsa[res_type][6] -= task.get_number_of_vms() * task.get_av_acc()[0]

        for i in range(4):
            self.sis[res_type] += self.ws[i] * self.deassessment_functions(
                -task.get_number_of_vms() * task.get_req_pmns()[0],
                -task.get_number_of_vms() * task.get_req_pmns()[1],
                i, res_type)

        self.prouters[res_type][0].deploy(resources, network, stats, task)

    def timestep(self, cell: 'Cell') -> None:
        if not self.alloc:
            return

        for i in range(self.number_of_types):
            for j in range(self.number_of_resources_per_type[i]):
                resources = cell.get_resources()
                if resources[i][j].get_running_vms() > 0:
                    resources[i][j].initialize_running_quantities()

        cell.get_network().initialize_running_quantities()

        l_net = 0.0

        for i in range(self.number_of_types):
            for vrm in self.vrms[i]:
                for task in vrm.get_queue():
                    task.comp_c_util_pmnr()
                    gc_u = task.get_c_util_pmnr()
                    gr = task.get_resource_ids()
                    l_net += gc_u[2]
                    l_number_of_vms = task.get_number_of_vms()

                    for j in range(l_number_of_vms):
                        r_id = gr[j]
                        cell.get_resources()[i][r_id].increment_running_quantities(
                            gc_u[0], gc_u[1], gc_u[3])

        cell.get_network().increment_running_quantities(l_net)

        for i in range(self.number_of_types):
            for j in range(self.number_of_resources_per_type[i]):
                resources = cell.get_resources()
                if resources[i][j].get_running_vms() > 0:
                    resources[i][j].comp_current_comp_cap_per_proc()
                    resources[i][j].comp_current_comp_cap_per_acc()

        for i in range(self.number_of_types):
            l_total_power_consumption = 0.0
            for j in range(self.number_of_resources_per_type[i]):
                resources = cell.get_resources()
                proc_util = (resources[i][j].get_actual_utilized_processors() /
                           resources[i][j].get_total_processors()
                           if resources[i][j].get_total_processors() > 0 else 0.0)
                rho_acc = resources[i][j].get_actual_rho_accelerators()
                active = resources[i][j].get_active()
                total_acc = resources[i][j].get_total_accelerators()
                l_total_power_consumption += cell.get_power_consumption()[i].consumption(
                    proc_util, rho_acc, active, total_acc)

            cell.get_stats()[i].total_power_consumption += l_total_power_consumption

        for i in range(self.number_of_types):
            oc_p = cell.get_resources()[i][0].get_overcommitment_processors()

            for vrm in self.vrms[i]:
                for task in vrm.get_queue():
                    r_id = task.get_resource_ids()[0]
                    ins_r = cell.get_resources()[i][r_id].get_current_comp_cap_per_proc()
                    ins_ra = cell.get_resources()[i][r_id].get_current_comp_cap_per_acc()
                    l_number_of_vms = task.get_number_of_vms()
                    l_vcpu = task.get_req_pmns()[0]

                    for j in range(1, l_number_of_vms):
                        r_id = task.get_resource_ids()[j]
                        ins_r = min(ins_r, cell.get_resources()[i][r_id].get_current_comp_cap_per_proc())
                        ins_ra = min(ins_ra, cell.get_resources()[i][r_id].get_current_comp_cap_per_acc())

                    reduction = (l_number_of_vms * ins_r *
                               min(task.get_c_util_pmnr()[0] * oc_p / l_vcpu if l_vcpu > 0 else 0.0, 1.0) * l_vcpu +
                               l_number_of_vms * ins_ra * task.get_c_util_pmnr()[3])
                    task.reduce_ins(reduction)

        for i in range(self.number_of_types):
            avau = [0.0, 0.0]
            number_of_tasks = 0

            for vrm in self.vrms[i]:
                tasks_to_remove = []
                for idx, task in enumerate(vrm.get_queue()):
                    if task.get_requested_instructions() <= 0.0:
                        l_number_of_vms = task.get_number_of_vms()
                        for j in range(l_number_of_vms):
                            r_id = task.get_resource_ids()[j]
                            cell.get_resources()[i][r_id].unload(task)

                        number_of_tasks += 1
                        avau[0] += task.get_req_pmns()[2]
                        avau[1] += task.get_c_util_pmnr()[2]
                        tasks_to_remove.append(idx)

                for idx in reversed(tasks_to_remove):
                    vrm.get_queue().pop(idx)

            cell.get_network().unload(avau[0], avau[1], number_of_tasks)
