"""
ImprovedSOSMBroker (Improved Self-Organizing Self-Management Broker) for CloudLightning Simulator

Copyright 2017 The CloudLightning Simulation Framework Authors.
Translated from C++ to Python.
"""

from typing import List, Optional
from .base_broker import BaseBroker
from .improved_vrm import ImprovedVRM
from .improved_pswitch import ImprovedPSwitch
from .improved_prouter import ImprovedPRouter


class ImprovedSOSMBroker(BaseBroker):
    def __init__(self):
        super().__init__()
        self.number_of_vrms = 0
        self.number_of_pswitches = 0
        self.number_of_prouters = 0
        self.poll_interval_cell_m = 0.0
        self.poll_interval_prouter = 0.0
        self.poll_interval_pswitch = 0.0
        self.poll_interval_vrm = 0.0
        self.s_pmsa: List[List[float]] = []
        self.vrms: List[List[ImprovedVRM]] = []
        self.sis: List[float] = []
        self.pswitches: List[List[ImprovedPSwitch]] = []
        self.prouters: List[List[ImprovedPRouter]] = []
        self.cs: List[float] = []
        self.ps: List[float] = []
        self.pis: List[float] = []
        self.caccs: List[float] = []
        self.paccs: List[float] = []
        self.piaccs: List[float] = []
        self.ws: List[float] = []
        self.number_of_functions = 0

    def init_with_inputs(self, cl_cell, si):
        self.alloc = 1
        self.number_of_types = cl_cell.get_number_of_types()
        self.types = cl_cell.get_types()[:]
        self.number_of_resources_per_type = cl_cell.get_number_of_resources_per_type()[:]

        self.poll_interval_cell_m = si.cell_inputs[0].broker_inputs.poll_interval_cell_m
        self.poll_interval_prouter = si.cell_inputs[0].broker_inputs.poll_interval_prouter
        self.poll_interval_pswitch = si.cell_inputs[0].broker_inputs.poll_interval_pswitch
        self.poll_interval_vrm = si.cell_inputs[0].broker_inputs.poll_interval_vrm

        temp_c = [0.0] * self.number_of_types
        temp_p = [0.0] * self.number_of_types
        temp_pi = [0.0] * self.number_of_types
        temp_c_acc = [0.0] * self.number_of_types
        temp_p_acc = [0.0] * self.number_of_types
        temp_pi_acc = [0.0] * self.number_of_types

        resources = cl_cell.get_resources()
        power_consumption = cl_cell.get_power_consumption()

        for i in range(self.number_of_types):
            temp_c[i] = (resources[i][0].get_compute_capability() /
                        resources[i][0].total_processors)
            temp_c_acc[i] = resources[i][0].get_accelerator_compute_capability()

            oz = 1.0
            temp_p[i] = (power_consumption[i].model_cpu(oz) /
                        resources[i][0].total_processors)
            temp_p_acc[i] = power_consumption[i].acc_pmax

            oz = 0.0
            temp_pi[i] = (power_consumption[i].model_cpu(oz) /
                         resources[i][0].total_processors)
            temp_pi_acc[i] = power_consumption[i].acc_pmin

        self.number_of_functions = si.cell_inputs[0].broker_inputs.number_of_functions
        self.ws = list(si.cell_inputs[0].broker_inputs.weights)

        self.number_of_prouters = self.number_of_types
        self.number_of_vrms = 0
        self.number_of_pswitches = 0
        self.vrms = [[] for _ in range(self.number_of_types)]
        self.pswitches = [[] for _ in range(self.number_of_types)]
        self.prouters = [[] for _ in range(self.number_of_types)]

        for i in range(self.number_of_types):
            temp = self.number_of_resources_per_type[i] // si.cell_inputs[0].broker_inputs.init_res_per_vrm
            for j in range(temp):
                vrm = ImprovedVRM(
                    j * si.cell_inputs[0].broker_inputs.init_res_per_vrm,
                    (j + 1) * si.cell_inputs[0].broker_inputs.init_res_per_vrm,
                    i,
                    resources,
                    self.poll_interval_vrm,
                    temp_c[i], temp_c_acc[i],
                    temp_p[i], temp_p_acc[i],
                    temp_pi[i], temp_pi_acc[i],
                    si.cell_inputs[0].broker_inputs.init_res_per_vrm,
                    si.cell_inputs[0].broker_inputs.number_of_functions,
                    si.cell_inputs[0].broker_inputs.weights,
                    si.cell_inputs[0].broker_inputs.vrm_deploy_strategy
                )
                self.vrms[i].append(vrm)
            self.number_of_vrms += temp

            if temp * si.cell_inputs[0].broker_inputs.init_res_per_vrm != self.number_of_resources_per_type[i]:
                vrm = ImprovedVRM(
                    temp * si.cell_inputs[0].broker_inputs.init_res_per_vrm,
                    self.number_of_resources_per_type[i],
                    i,
                    resources,
                    self.poll_interval_vrm,
                    temp_c[i], temp_c_acc[i],
                    temp_p[i], temp_p_acc[i],
                    temp_pi[i], temp_pi_acc[i],
                    si.cell_inputs[0].broker_inputs.init_res_per_vrm,
                    si.cell_inputs[0].broker_inputs.number_of_functions,
                    si.cell_inputs[0].broker_inputs.weights,
                    si.cell_inputs[0].broker_inputs.vrm_deploy_strategy
                )
                self.vrms[i].append(vrm)
                self.number_of_vrms += 1

        for i in range(self.number_of_types):
            temp = len(self.vrms[i]) // si.cell_inputs[0].broker_inputs.init_vrm_per_pswitch
            for j in range(temp):
                pswitch = ImprovedPSwitch(
                    j * si.cell_inputs[0].broker_inputs.init_vrm_per_pswitch,
                    (j + 1) * si.cell_inputs[0].broker_inputs.init_vrm_per_pswitch,
                    i,
                    self.vrms,
                    self.poll_interval_pswitch,
                    temp_c[i], temp_c_acc[i],
                    temp_p[i], temp_p_acc[i],
                    temp_pi[i], temp_pi_acc[i],
                    si.cell_inputs[0].broker_inputs.number_of_functions,
                    si.cell_inputs[0].broker_inputs.weights
                )
                self.pswitches[i].append(pswitch)
            self.number_of_pswitches += temp

            if temp * si.cell_inputs[0].broker_inputs.init_vrm_per_pswitch != len(self.vrms[i]):
                pswitch = ImprovedPSwitch(
                    temp * si.cell_inputs[0].broker_inputs.init_vrm_per_pswitch,
                    len(self.vrms[i]),
                    i,
                    self.vrms,
                    self.poll_interval_pswitch,
                    temp_c[i], temp_c_acc[i],
                    temp_p[i], temp_p_acc[i],
                    temp_pi[i], temp_pi_acc[i],
                    si.cell_inputs[0].broker_inputs.number_of_functions,
                    si.cell_inputs[0].broker_inputs.weights
                )
                self.pswitches[i].append(pswitch)
                self.number_of_pswitches += 1

        for i in range(self.number_of_types):
            prouter = ImprovedPRouter(
                0,
                len(self.pswitches[i]),
                i,
                self.pswitches,
                self.poll_interval_prouter,
                temp_c[i], temp_c_acc[i],
                temp_p[i], temp_p_acc[i],
                temp_pi[i], temp_pi_acc[i],
                si.cell_inputs[0].broker_inputs.number_of_functions,
                si.cell_inputs[0].broker_inputs.weights
            )
            self.prouters[i].append(prouter)

        self.s_pmsa = [[0.0] * 8 for _ in range(self.number_of_types)]

        for i in range(self.number_of_types):
            for prouter in self.prouters[i]:
                for j in range(8):
                    self.s_pmsa[i][j] = prouter.get_s_pmsa()[j]

        network = cl_cell.get_network()
        self.available_network = network.available_bandwidth
        self.total_network = network.total_bandwidth
        self.sis = [0.0] * self.number_of_types

        self.cs = temp_c
        self.caccs = temp_c_acc
        self.ps = temp_p
        self.paccs = temp_p_acc
        self.pis = temp_pi
        self.piaccs = temp_pi_acc

    def print(self):
        if self.alloc:
            for i in range(self.number_of_types):
                print(f"No of Type: {i}")
                print(f"     Number of available processing units: {self.s_pmsa[i][0]}")
                print(f"     Number of total processing units: {self.s_pmsa[i][1]}")
                print(f"     Number of available memory: {self.s_pmsa[i][2]}")
                print(f"     Number of total memory: {self.s_pmsa[i][3]}")
                print(f"     Number of available storage: {self.s_pmsa[i][4]}")
                print(f"     Number of total storage: {self.s_pmsa[i][5]}")
                print(f"     Number of available accelerators: {self.s_pmsa[i][6]}")
                print(f"     Number of total accelerators: {self.s_pmsa[i][7]}")
            print(f"Available network bandwidth: {self.available_network}")
            print(f"Total network bandwidth: {self.total_network}")

    def deassessment_functions(self, d_nu: float, d_acc: float, choice: int, type_: int) -> float:
        if choice == 0:
            ln = (self.pis[type_] * self.s_pmsa[type_][1] +
                  (self.ps[type_] - self.pis[type_]) * (self.s_pmsa[type_][1] - self.s_pmsa[type_][0]) +
                  self.piaccs[type_] * self.s_pmsa[type_][6] +
                  self.paccs[type_] * (self.s_pmsa[type_][7] - self.s_pmsa[type_][6]))
            kn = self.cs[type_] * self.s_pmsa[type_][1] + self.caccs[type_] * self.s_pmsa[type_][7]
            return (kn * (d_nu * (self.ps[type_] - self.pis[type_]) + d_acc * self.paccs[type_])) / (ln * ln) if ln != 0 else 0.0
        else:
            return 0.0

    def update_state_info(self, cl_cell, tstep: float):
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
                    for j in range(8):
                        self.s_pmsa[i][j] = prouter.get_s_pmsa()[j]
                    self.sis[i] = prouter.get_si()

        network = cl_cell.get_network()
        self.available_network = network.available_bandwidth
        self.total_network = network.total_bandwidth

    def deploy(self, resources, network, stats, task):
        task.comp_c_util_pmnr()

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

        if count == 0:
            return

        if self.available_network < task.get_req_pmns()[2]:
            stats[rem[0]].rejected_tasks += 1
            return

        self.available_network -= task.get_req_pmns()[2]

        max_si = 0.0
        type_ = -1

        for i in range(count):
            if (max_si < self.sis[rem[i]] and
                task.get_number_of_vms() * task.get_req_pmns()[0] <= self.s_pmsa[rem[i]][0] and
                task.get_number_of_vms() * task.get_req_pmns()[1] <= self.s_pmsa[rem[i]][2] and
                task.get_number_of_vms() * task.get_req_pmns()[3] <= self.s_pmsa[rem[i]][4] and
                task.get_number_of_vms() * task.get_av_acc()[rem2[i]] <= self.s_pmsa[rem[i]][6]):

                if self.prouters[rem[i]][0].probe(
                    task.get_number_of_vms() * task.get_req_pmns()[0],
                    task.get_number_of_vms() * task.get_req_pmns()[1],
                    task.get_number_of_vms() * task.get_req_pmns()[3],
                    task.get_number_of_vms() * task.get_av_acc()[rem2[i]]) != -1:
                    max_si = self.sis[rem[i]]
                    type_ = i

            weighted_si = ((self.cs[rem[i]] * task.get_req_pmns()[0] +
                          task.get_av_acc()[rem2[i]] * self.caccs[rem[i]]) /
                          (self.cs[rem[i]] * task.get_req_pmns()[0] + self.caccs[rem[i]])) * self.sis[rem[i]]

            if (max_si < weighted_si and
                task.get_number_of_vms() * task.get_req_pmns()[0] <= self.s_pmsa[rem[i]][0] and
                task.get_number_of_vms() * task.get_req_pmns()[1] <= self.s_pmsa[rem[i]][2] and
                task.get_number_of_vms() * task.get_req_pmns()[3] <= self.s_pmsa[rem[i]][4] and
                task.get_number_of_vms() * task.get_av_acc()[rem2[i]] <= self.s_pmsa[rem[i]][6]):

                if self.prouters[rem[i]][0].probe(
                    task.get_number_of_vms() * task.get_req_pmns()[0],
                    task.get_number_of_vms() * task.get_req_pmns()[1],
                    task.get_number_of_vms() * task.get_req_pmns()[3],
                    task.get_number_of_vms() * task.get_av_acc()[rem2[i]]) != -1:
                    max_si = weighted_si
                    type_ = i

        if type_ == -1:
            stats[rem[0]].rejected_tasks += 1
            return

        task.reduce_impl(rem2[type_])
        task.remap_type(rem[type_], 1)
        type_ = rem[type_]

        for i in range(4):
            self.sis[type_] += self.ws[i] * self.deassessment_functions(
                -task.get_number_of_vms() * task.get_req_pmns()[0],
                -task.get_number_of_vms() * task.get_av_acc()[0],
                i, type_)

        self.s_pmsa[type_][0] -= task.get_number_of_vms() * task.get_req_pmns()[0]
        self.s_pmsa[type_][2] -= task.get_number_of_vms() * task.get_req_pmns()[1]
        self.s_pmsa[type_][4] -= task.get_number_of_vms() * task.get_req_pmns()[3]
        self.s_pmsa[type_][6] -= task.get_number_of_vms() * task.get_av_acc()[0]

        self.prouters[type_][0].deploy(resources, [network], stats, task)

    def timestep(self, cl_cell):
        if not self.alloc:
            return

        resources = cl_cell.get_resources()
        network = cl_cell.get_network()
        power_consumption = cl_cell.get_power_consumption()
        stats = cl_cell.get_stats()

        for i in range(self.number_of_types):
            for j in range(self.number_of_resources_per_type[i]):
                if resources[i][j].running_vms > 0:
                    resources[i][j].initialize_running_quantities()

        network.initialize_running_quantities()

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
                        resources[i][r_id].increment_running_quantities(gc_u[0], gc_u[1], gc_u[3])

        network.increment_running_quantities(l_net)

        for i in range(self.number_of_types):
            for j in range(self.number_of_resources_per_type[i]):
                if resources[i][j].running_vms > 0:
                    resources[i][j].comp_current_comp_cap_per_proc()
                    resources[i][j].comp_current_comp_cap_per_acc()

        for i in range(self.number_of_types):
            l_total_power_consumption = 0.0
            for j in range(self.number_of_resources_per_type[i]):
                proc_util = (resources[i][j].get_actual_utilized_processors() /
                           resources[i][j].total_processors)
                rho_acc = resources[i][j].get_actual_rho_accelerators()
                active = resources[i][j].active
                total_acc = resources[i][j].total_accelerators
                l_total_power_consumption += power_consumption[i].consumption(proc_util, rho_acc, active, total_acc)
            stats[i].total_power_consumption += l_total_power_consumption

        for i in range(self.number_of_types):
            oc_p = resources[i][0].overcommitment_processors
            for vrm in self.vrms[i]:
                for task in vrm.get_queue():
                    r_id = task.get_resource_ids()[0]
                    ins_r = resources[i][r_id].get_current_comp_cap_per_proc()
                    ins_ra = resources[i][r_id].get_current_comp_cap_per_acc()
                    l_number_of_vms = task.get_number_of_vms()
                    l_v_cpu = task.get_req_pmns()[0]

                    for j in range(1, l_number_of_vms):
                        r_id = task.get_resource_ids()[j]
                        ins_r = min(ins_r, resources[i][r_id].get_current_comp_cap_per_proc())
                        ins_ra = min(ins_ra, resources[i][r_id].get_current_comp_cap_per_acc())

                    task.reduce_ins(
                        l_number_of_vms * ins_r * min(task.get_c_util_pmnr()[0] / l_v_cpu * oc_p, 1.0) * l_v_cpu +
                        l_number_of_vms * ins_ra * task.get_c_util_pmnr()[3]
                    )

        for i in range(self.number_of_types):
            av_au = [0.0, 0.0]
            number_of_tasks = 0

            for vrm in self.vrms[i]:
                tasks_to_remove = []
                for idx, task in enumerate(vrm.get_queue()):
                    if task.get_requested_instructions() <= 0.0:
                        l_number_of_vms = task.get_number_of_vms()
                        for j in range(l_number_of_vms):
                            r_id = task.get_resource_ids()[j]
                            resources[i][r_id].unload(task)
                        number_of_tasks += 1
                        av_au[0] += task.get_req_pmns()[2]
                        av_au[1] += task.get_c_util_pmnr()[2]
                        tasks_to_remove.append(idx)

                for idx in reversed(tasks_to_remove):
                    vrm.get_queue().pop(idx)

            network.unload(av_au[0], av_au[1], number_of_tasks)

    def get_number_of_vrms(self) -> int:
        return self.number_of_vrms

    def get_number_of_pswitches(self) -> int:
        return self.number_of_pswitches

    def get_number_of_prouters(self) -> int:
        return self.number_of_prouters

    def get_poll_interval_cell_m(self) -> float:
        return self.poll_interval_cell_m

    def get_poll_interval_prouter(self) -> float:
        return self.poll_interval_prouter

    def get_poll_interval_pswitch(self) -> float:
        return self.poll_interval_pswitch

    def get_poll_interval_vrm(self) -> float:
        return self.poll_interval_vrm

    def get_s_pmsa(self) -> List[List[float]]:
        return self.s_pmsa

    def get_sis(self) -> List[float]:
        return self.sis

    def get_cs(self) -> List[float]:
        return self.cs

    def get_ps(self) -> List[float]:
        return self.ps

    def get_pis(self) -> List[float]:
        return self.pis

    def get_ws(self) -> List[float]:
        return self.ws

    def get_caccs(self) -> List[float]:
        return self.caccs

    def get_paccs(self) -> List[float]:
        return self.paccs

    def get_piaccs(self) -> List[float]:
        return self.piaccs

    def get_number_of_functions(self) -> int:
        return self.number_of_functions

    def get_vrms(self) -> List[List[ImprovedVRM]]:
        return self.vrms

    def get_pswitches(self) -> List[List[ImprovedPSwitch]]:
        return self.pswitches

    def get_prouters(self) -> List[List[ImprovedPRouter]]:
        return self.prouters
