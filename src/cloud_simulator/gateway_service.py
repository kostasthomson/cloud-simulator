"""
Gateway Service (GS) for CloudLightning Simulator

Copyright 2017 The CloudLightning Simulation Framework Authors.
Translated from C++ to Python.
"""

from typing import List, Optional
import json


class GatewayService:
    def __init__(self, cell_data: Optional[str] = None,
                 app_data: Optional[str] = None,
                 broker_data: Optional[str] = None,
                 app_inputs=None,
                 sim_inputs=None):
        if cell_data is None:
            self.alloc = 0
            self.ai = None
            self.si = None
            self.stats = []
        else:
            self.alloc = 1

            if app_inputs is not None and sim_inputs is not None:
                self.ai = app_inputs
                self.si = sim_inputs
            else:
                from .inputs import AppInputs, SimulationInputs
                self.ai = AppInputs()
                self.ai.parse(app_data)
                self.si = SimulationInputs()
                self.si.parse(cell_data, broker_data)

            self.stats = []
            for i in range(self.si.num_of_cells):
                cell_stats = []
                for j in range(self.si.cell_inputs[i].number_of_types):
                    from .statistics import Statistics
                    cell_stats.append(Statistics())
                self.stats.append(cell_stats)

    def find_cell(self, r_impl: List[int], num_impl: int, r_vm: int,
                 rv_proc: float, r_mem: float, r_net: float,
                 r_sto: float, r_acc: List[int]) -> int:
        choice = -1
        choice2 = -1
        r_ind = -1
        fr_ind = -1
        weight = 0.0

        for i in range(self.si.num_of_cells):
            for k in range(num_impl):
                r_ind = -1
                for j in range(self.si.cell_inputs[i].number_of_types):
                    if r_impl[k] == self.si.cell_inputs[i].types[j]:
                        r_ind = j

                if r_ind == -1:
                    continue

                if (self.stats[i][r_ind].available_processors >= float(r_vm) * rv_proc and
                    self.stats[i][r_ind].available_memory >= float(r_vm) * r_mem and
                    self.stats[i][r_ind].available_network >= r_net and
                    self.stats[i][r_ind].available_storage >= float(r_vm) * r_sto and
                    self.stats[i][r_ind].available_accelerators >= float(r_vm) * r_acc[k]):

                    lweight = (
                        (self.stats[i][r_ind].available_processors - float(r_vm) * rv_proc) /
                        (self.stats[i][r_ind].available_processors + 1) +
                        (self.stats[i][r_ind].available_memory - float(r_vm) * r_mem) /
                        (self.stats[i][r_ind].available_memory + 1) +
                        (self.stats[i][r_ind].available_network - r_net) /
                        (self.stats[i][r_ind].available_network + 1) +
                        (self.stats[i][r_ind].available_storage - float(r_vm) * r_sto) /
                        (self.stats[i][r_ind].available_storage + 1) +
                        (self.stats[i][r_ind].available_accelerators - float(r_vm) * r_acc[k]) /
                        (self.stats[i][r_ind].available_accelerators + 1)
                    )

                    if lweight > weight:
                        weight = lweight
                        choice = i + 1
                        choice2 = k
                        fr_ind = r_ind

        if fr_ind != -1 and choice != -1:
            self.stats[choice - 1][fr_ind].available_processors -= float(r_vm) * rv_proc
            self.stats[choice - 1][fr_ind].available_memory -= float(r_vm) * r_mem
            self.stats[choice - 1][fr_ind].available_network -= r_net
            self.stats[choice - 1][fr_ind].available_storage -= float(r_vm) * r_sto
            self.stats[choice - 1][fr_ind].available_accelerators -= float(r_vm) * r_acc[choice2]

        return choice

    def print(self):
        if self.alloc:
            self.si.print()
            self.ai.print()

    def print_file(self, outfile: str, mode: str = 'w'):
        if self.alloc:
            with open(outfile, mode) as f:
                pass
            self.si.print_file(outfile, 'a')
            self.ai.print_file(outfile, 'a')

    def num_2_str(self, num: int) -> str:
        return str(num)

    def print_stats(self):
        if self.alloc:
            for i in range(self.si.num_of_cells):
                for j in range(self.si.cell_inputs[i].number_of_types):
                    self.stats[i][j].print()

    def print_stats_file(self, outfile: str, mode: str = 'w'):
        if self.alloc:
            for i in range(self.si.num_of_cells):
                for j in range(self.si.cell_inputs[i].number_of_types):
                    tmp = outfile + self.num_2_str(self.si.cell_inputs[i].cell_id) + \
                          self.num_2_str(self.si.cell_inputs[i].types[j])
                    self.stats[i][j].print_file(tmp, mode)

    def print_stats_json(self, outfile: str, mode: str, end_time: int,
                        update_interval: int, sosm_integration: int, all_tasks: int):
        overall_records = (end_time // update_interval) + 1
        if self.alloc:
            for i in range(self.si.num_of_cells):
                for j in range(self.si.cell_inputs[i].number_of_types):
                    tmp = outfile + self.num_2_str(self.si.cell_inputs[i].cell_id) + \
                          self.num_2_str(self.si.cell_inputs[i].types[j])
                    temp = outfile + "CLSim.json"
                    self.stats[i][j].print_file_json(
                        temp, tmp, mode,
                        self.si.cell_inputs[i].cell_id,
                        self.si.cell_inputs[i].types[j],
                        overall_records,
                        self.si.num_of_cells,
                        self.si.cell_inputs[i].number_of_types,
                        j + 1,
                        sosm_integration,
                        all_tasks
                    )

    def print_stats_to_json_direct(self, outfile: str, mode: str, end_time: int,
                                  update_interval: int, sosm_integration: int,
                                  all_tasks: int, current_time: int):
        if not hasattr(self, '_flag'):
            self._flag = 0

        if update_interval == 1 and self._flag == 0:
            time_step = (current_time + 1) // (update_interval + 1)
            self._flag += 1
        else:
            time_step = (current_time + 1) // update_interval

        k = 0
        if self.alloc:
            for i in range(self.si.num_of_cells):
                for j in range(self.si.cell_inputs[i].number_of_types):
                    temp = outfile + "CLSim.json"
                    self.stats[i][j].print_file_json_direct(
                        temp, mode,
                        self.si.cell_inputs[i].cell_id,
                        self.si.cell_inputs[i].types[j],
                        self.si.num_of_cells,
                        self.si.cell_inputs[i].number_of_types,
                        j + 1,
                        sosm_integration,
                        all_tasks,
                        k,
                        time_step
                    )
                    k += 1

    def get_alloc(self) -> int:
        return self.alloc

    def get_ai(self):
        return self.ai

    def get_si(self):
        return self.si

    def get_stats(self) -> List[List]:
        return self.stats
