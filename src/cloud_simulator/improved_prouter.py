"""
ImprovedPRouter (Improved Physical Router) for CloudLightning Simulator

Copyright 2017 The CloudLightning Simulation Framework Authors.
Translated from C++ to Python.
"""

from typing import List, Optional
import random


class ImprovedPRouter:
    def __init__(self, start: int = 0, end: int = 0, type_: int = 0,
                 pswitches: Optional[List[List]] = None,
                 poll_interval_prouter: float = 0.0,
                 c: float = 0.0, c_acc: float = 0.0,
                 p: float = 0.0, p_acc: float = 0.0,
                 pi: float = 0.0, pi_acc: float = 0.0,
                 number_of_functions: int = 0,
                 ws: Optional[List[float]] = None):

        if pswitches is None:
            self.alloc = 0
            self.number_of_pswitches = 0
            self.number_of_functions = 0
            self.poll_interval_prouter = 0.0
            self.pswitches: List = []
            self.fs: List[float] = []
            self.ws: List[float] = []
            self.available_processors: List[float] = []
            self.total_processors: List[float] = []
            self.available_memory: List[float] = []
            self.total_memory: List[float] = []
            self.available_accelerators: List[float] = []
            self.total_accelerators: List[float] = []
            self.available_storage: List[float] = []
            self.total_storage: List[float] = []
            self.s_pmsa: List[float] = [0.0] * 8
            self.sis: List[float] = []
            self.si = 0.0
            self.c = 0.0
            self.p = 0.0
            self.pi = 0.0
            self.c_acc = 0.0
            self.p_acc = 0.0
            self.pi_acc = 0.0
        else:
            self.alloc = 1
            self.number_of_pswitches = end - start
            self.number_of_functions = number_of_functions
            self.poll_interval_prouter = poll_interval_prouter

            self.pswitches: List = []
            for i in range(start, end):
                self.pswitches.append(pswitches[type_][i])

            self.ws = list(ws) if ws else [0.0] * number_of_functions
            self.fs = [0.0] * number_of_functions

            self.available_processors = [0.0] * self.number_of_pswitches
            self.total_processors = [0.0] * self.number_of_pswitches
            self.available_memory = [0.0] * self.number_of_pswitches
            self.total_memory = [0.0] * self.number_of_pswitches
            self.available_accelerators = [0.0] * self.number_of_pswitches
            self.total_accelerators = [0.0] * self.number_of_pswitches
            self.available_storage = [0.0] * self.number_of_pswitches
            self.total_storage = [0.0] * self.number_of_pswitches
            self.sis = [0.0] * self.number_of_pswitches

            self.si = 0.0
            self.s_pmsa = [0.0] * 8

            self.c = c
            self.p = p
            self.pi = pi
            self.c_acc = c_acc
            self.p_acc = p_acc
            self.pi_acc = pi_acc
            self.update_state_info(0.0)

    def compute_fs(self) -> None:
        if not self.alloc:
            return

        for i in range(self.number_of_functions):
            self.fs[i] = 0.0

        for pswitch in self.pswitches:
            for j in range(self.number_of_functions):
                self.fs[j] += pswitch.get_fs()[j]

        for j in range(self.number_of_functions):
            self.fs[j] /= self.number_of_pswitches if self.number_of_pswitches > 0 else 1

    def compute_si(self) -> None:
        if not self.alloc:
            return

        self.si = 1e-4 * random.random()
        for i in range(self.number_of_functions):
            self.si += self.ws[i] * self.fs[i]

    def probe(self, proc: float, mem: float, sto: float, acc: int) -> int:
        if (proc <= self.s_pmsa[0] and mem <= self.s_pmsa[2] and
            sto <= self.s_pmsa[4] and acc <= int(self.s_pmsa[6])):
            return 1
        else:
            return -1

    def deploy(self, resources, network, stats, task) -> None:
        if not self.alloc:
            return

        l_number_of_vms = task.get_number_of_vms()
        l_req_pmns = task.get_req_pmns()
        max_si = 0.0
        l_av_acc = task.get_av_acc()[0]
        choice = -1

        req_proc = l_number_of_vms * l_req_pmns[0]
        req_mem = l_number_of_vms * l_req_pmns[1]
        req_sto = l_number_of_vms * l_req_pmns[3]
        req_acc = l_number_of_vms * l_av_acc

        for i in range(self.number_of_pswitches):
            if (max_si < self.sis[i] and
                req_proc <= self.available_processors[i] and
                req_mem <= self.available_memory[i] and
                req_sto <= self.available_storage[i] and
                req_acc <= self.available_accelerators[i]):
                max_si = self.sis[i]
                choice = i

        if choice == -1:
            stats[task.get_available_implementations()[0]].rejected_tasks += 1
            return

        ssum = 0.0
        for i in range(1):
            ssum += self.ws[i] * self.deassessment_functions(
                -req_proc, self.s_pmsa[0], self.s_pmsa[1],
                -float(req_acc), self.s_pmsa[6], self.s_pmsa[7], i)
        self.si += ssum

        ssum = 0.0
        for i in range(1):
            ssum += self.ws[i] * self.deassessment_functions(
                -req_proc, self.available_processors[choice], self.total_processors[choice],
                -float(req_acc), float(self.available_accelerators[choice]),
                float(self.total_accelerators[choice]), i)
        self.sis[choice] += ssum

        self.available_processors[choice] -= req_proc
        self.available_memory[choice] -= req_mem
        self.available_storage[choice] -= req_sto
        self.available_accelerators[choice] -= req_acc
        self.s_pmsa[0] -= req_proc
        self.s_pmsa[2] -= req_mem
        self.s_pmsa[4] -= req_sto
        self.s_pmsa[6] -= float(req_acc)

        self.pswitches[choice].deploy(resources, network, stats, task)

    def update_state_info(self, tstep: float) -> None:
        if not self.alloc:
            return

        if int(tstep) % int(self.poll_interval_prouter) == 0 if self.poll_interval_prouter > 0 else True:
            len_ = len(self.pswitches)

            for i in range(8):
                self.s_pmsa[i] = 0.0

            i = 0
            for pswitch in self.pswitches:
                pswitch_pmsa = pswitch.get_s_pmsa()
                self.available_processors[i] = pswitch_pmsa[0]
                self.total_processors[i] = pswitch_pmsa[1]
                self.available_memory[i] = pswitch_pmsa[2]
                self.total_memory[i] = pswitch_pmsa[3]
                self.available_storage[i] = pswitch_pmsa[4]
                self.total_storage[i] = pswitch_pmsa[5]
                self.available_accelerators[i] = pswitch_pmsa[6]
                self.total_accelerators[i] = pswitch_pmsa[7]
                self.sis[i] = pswitch.get_si()
                i += 1

            for i in range(len_):
                self.s_pmsa[0] += self.available_processors[i]
                self.s_pmsa[1] += self.total_processors[i]
                self.s_pmsa[2] += self.available_memory[i]
                self.s_pmsa[3] += self.total_memory[i]
                self.s_pmsa[4] += self.available_storage[i]
                self.s_pmsa[5] += self.total_storage[i]
                self.s_pmsa[6] += self.available_accelerators[i]
                self.s_pmsa[7] += self.total_accelerators[i]

            self.compute_fs()
            self.compute_si()

    def deassessment_functions(self, d_nu: float, avail_nu: float, tot_nu: float,
                              d_acc: float, available_accelerators: float,
                              total_accelerators: float, choice: int) -> float:
        if choice == 0:
            ln = (self.pi * tot_nu +
                  (self.p - self.pi) * (tot_nu - avail_nu) +
                  self.pi_acc * available_accelerators +
                  self.p_acc * (total_accelerators - available_accelerators))
            kn = self.c * tot_nu + self.c_acc * total_accelerators
            return (kn * (d_nu * (self.p - self.pi) + d_acc * self.p_acc)) / (ln * ln) if ln != 0 else 0.0
        else:
            return 0.0

    def print(self) -> None:
        if self.alloc:
            print("ImprovedPRouter Stats")
            print(f"Available Processing Units: {self.s_pmsa[0]}")
            print(f"Total Processing Units: {self.s_pmsa[1]}")
            print(f"Available Memory: {self.s_pmsa[2]}")
            print(f"Total Memory: {self.s_pmsa[3]}")
            print(f"Available Storage: {self.s_pmsa[4]}")
            print(f"Total Storage: {self.s_pmsa[5]}")
            print(f"Available Accelerators: {self.s_pmsa[6]}")
            print(f"Total Accelerators: {self.s_pmsa[7]}")

    def get_alloc(self) -> int:
        return self.alloc

    def get_number_of_pswitches(self) -> int:
        return self.number_of_pswitches

    def get_number_of_functions(self) -> int:
        return self.number_of_functions

    def get_poll_interval_prouter(self) -> float:
        return self.poll_interval_prouter

    def get_pswitches(self) -> List:
        return self.pswitches

    def get_available_processors(self) -> List[float]:
        return self.available_processors

    def get_total_processors(self) -> List[float]:
        return self.total_processors

    def get_available_memory(self) -> List[float]:
        return self.available_memory

    def get_total_memory(self) -> List[float]:
        return self.total_memory

    def get_available_accelerators(self) -> List[float]:
        return self.available_accelerators

    def get_total_accelerators(self) -> List[float]:
        return self.total_accelerators

    def get_available_storage(self) -> List[float]:
        return self.available_storage

    def get_total_storage(self) -> List[float]:
        return self.total_storage

    def get_s_pmsa(self) -> List[float]:
        return self.s_pmsa

    def get_ws(self) -> List[float]:
        return self.ws

    def get_fs(self) -> List[float]:
        return self.fs

    def get_si(self) -> float:
        return self.si

    def get_sis(self) -> List[float]:
        return self.sis

    def get_c(self) -> float:
        return self.c

    def get_p(self) -> float:
        return self.p

    def get_pi(self) -> float:
        return self.pi

    def get_c_acc(self) -> float:
        return self.c_acc

    def get_p_acc(self) -> float:
        return self.p_acc

    def get_pi_acc(self) -> float:
        return self.pi_acc
