"""
ImprovedVRM (Improved Virtual Resource Manager) for CloudLightning Simulator

Copyright 2017 The CloudLightning Simulation Framework Authors.
Translated from C++ to Python.
"""

from typing import List, Optional
import random


class ImprovedVRM:
    def __init__(self, start: int = 0, end: int = 0, type_: int = 0,
                 resources: Optional[List[List]] = None,
                 poll_interval_vrm: float = 0.0,
                 c: float = 0.0, c_acc: float = 0.0,
                 p: float = 0.0, p_acc: float = 0.0,
                 pi: float = 0.0, pi_acc: float = 0.0,
                 opt_num_of_res: int = 0,
                 number_of_functions: int = 0,
                 ws: Optional[List[float]] = None,
                 dep_strategy: int = 0):

        if resources is None:
            self.alloc = 0
            self.number_of_resources = 0
            self.number_of_functions = 0
            self.opt_num_of_res = 0
            self.poll_interval_vrm = 0.0
            self.queue: List = []
            self.res: List = []
            self.available_processors: List[float] = []
            self.total_processors: List[float] = []
            self.available_memory: List[float] = []
            self.total_memory: List[float] = []
            self.available_accelerators: List[float] = []
            self.total_accelerators: List[float] = []
            self.available_storage: List[float] = []
            self.total_storage: List[float] = []
            self.s_pmsa: List[float] = [0.0] * 8
            self.fs: List[float] = []
            self.ws: List[float] = []
            self.c = 0.0
            self.p = 0.0
            self.pi = 0.0
            self.c_acc = 0.0
            self.p_acc = 0.0
            self.pi_acc = 0.0
            self.si = 0.0
            self.dep_strategy = 0
        else:
            self.alloc = 1
            self.number_of_resources = end - start
            self.opt_num_of_res = opt_num_of_res
            self.number_of_functions = number_of_functions
            self.poll_interval_vrm = poll_interval_vrm
            self.c = c
            self.p = p
            self.pi = pi
            self.c_acc = c_acc
            self.p_acc = p_acc
            self.pi_acc = pi_acc
            self.queue: List = []
            self.res: List = []

            for i in range(start, end):
                self.res.append(resources[type_][i])

            self.available_processors = [0.0] * self.number_of_resources
            self.total_processors = [0.0] * self.number_of_resources
            self.available_memory = [0.0] * self.number_of_resources
            self.total_memory = [0.0] * self.number_of_resources
            self.available_accelerators = [0.0] * self.number_of_resources
            self.total_accelerators = [0.0] * self.number_of_resources
            self.available_storage = [0.0] * self.number_of_resources
            self.total_storage = [0.0] * self.number_of_resources
            self.s_pmsa = [0.0] * 8

            self.fs = [0.0] * number_of_functions
            self.ws = list(ws) if ws else [0.0] * number_of_functions

            self.si = 0.0
            self.dep_strategy = dep_strategy
            self.update_state_info(0.0)

    def obtain_resources(self, ores: List, rem_proc: List[float], rem_mem: List[float],
                        rem_sto: List[float], rem_acc: List[float]) -> None:
        if not self.alloc:
            return

        if rem_proc[0] <= 0.0 and rem_mem[0] <= 0.0 and rem_sto[0] <= 0.0 and rem_acc[0] <= 0:
            return

        i = 0
        while i < len(self.res):
            resource = self.res[i]
            if resource.get_movable() == 1:
                ores.append(resource)
                self.number_of_resources -= 1
                rem_proc[0] -= self.total_processors[i]
                rem_mem[0] -= self.total_memory[i]
                rem_sto[0] -= self.total_storage[i]
                rem_acc[0] -= self.total_accelerators[i]
                self.s_pmsa[0] -= self.total_processors[i]
                self.s_pmsa[1] -= self.total_processors[i]
                self.s_pmsa[2] -= self.total_memory[i]
                self.s_pmsa[3] -= self.total_memory[i]
                self.s_pmsa[4] -= self.total_storage[i]
                self.s_pmsa[5] -= self.total_storage[i]
                self.s_pmsa[6] -= self.total_accelerators[i]
                self.s_pmsa[7] -= self.total_accelerators[i]

                self.available_processors.pop(i)
                self.total_processors.pop(i)
                self.available_memory.pop(i)
                self.total_memory.pop(i)
                self.available_accelerators.pop(i)
                self.total_accelerators.pop(i)
                self.available_storage.pop(i)
                self.total_storage.pop(i)

                self.compute_fs()
                self.compute_si()
                self.res.pop(i)

                if rem_proc[0] <= 0.0 and rem_mem[0] <= 0.0 and rem_sto[0] <= 0.0 and rem_acc[0] <= 0:
                    break
            else:
                i += 1

    def attach_resources(self, ores: List) -> None:
        if not self.alloc:
            return

        nar = len(ores)
        if nar <= 0:
            return

        i = self.number_of_resources
        self.number_of_resources += nar

        for resource in ores:
            self.s_pmsa[0] += resource.get_total_processors()
            self.s_pmsa[1] += resource.get_total_processors()
            self.s_pmsa[2] += resource.get_total_memory()
            self.s_pmsa[3] += resource.get_total_memory()
            self.s_pmsa[4] += resource.get_total_storage()
            self.s_pmsa[5] += resource.get_total_storage()
            self.s_pmsa[6] += float(resource.get_total_accelerators())
            self.s_pmsa[7] += float(resource.get_total_accelerators())

            self.available_processors.append(resource.get_total_processors())
            self.total_processors.append(resource.get_total_processors())
            self.available_memory.append(resource.get_total_memory())
            self.total_memory.append(resource.get_total_memory())
            self.available_accelerators.append(float(resource.get_total_accelerators()))
            self.total_accelerators.append(float(resource.get_total_accelerators()))
            self.available_storage.append(resource.get_total_storage())
            self.total_storage.append(resource.get_total_storage())

            self.res.append(resource)

        self.compute_fs()
        self.compute_si()

    def update_state_info(self, tstep: float) -> None:
        if not self.alloc:
            return

        if int(tstep) % int(self.poll_interval_vrm) == 0 if self.poll_interval_vrm > 0 else True:
            for i in range(8):
                self.s_pmsa[i] = 0.0

            i = 0
            for resource in self.res:
                self.available_processors[i] = resource.get_available_processors()
                self.total_processors[i] = resource.get_total_processors()
                self.available_memory[i] = resource.get_available_memory()
                self.total_memory[i] = resource.get_total_memory()
                self.available_accelerators[i] = float(resource.get_available_accelerators())
                self.total_accelerators[i] = float(resource.get_total_accelerators())
                self.available_storage[i] = resource.get_available_storage()
                self.total_storage[i] = resource.get_total_storage()
                i += 1

            for i in range(len(self.res)):
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

    def compute_fs(self) -> None:
        if not self.alloc:
            return

        for i in range(self.number_of_functions):
            self.fs[i] = self.assess_funcs(i)

    def compute_si(self) -> None:
        if not self.alloc:
            return

        self.si = 1e-4 * random.random()
        for i in range(self.number_of_functions):
            self.si += self.ws[i] * self.fs[i]

    def assess_funcs(self, choice: int) -> float:
        if choice == 0:
            numerator = self.c * self.s_pmsa[1] + self.c_acc * self.s_pmsa[7]
            denominator = (self.pi * self.s_pmsa[1] +
                          (self.p - self.pi) * (self.s_pmsa[1] - self.s_pmsa[0]) +
                          self.pi_acc * self.s_pmsa[6] +
                          self.p_acc * (self.s_pmsa[7] - self.s_pmsa[6]))
            return numerator / denominator if denominator != 0 else 0.0
        else:
            return 0.0

    def deassessment_functions(self, d_nu: float, d_acc: float, choice: int) -> float:
        if choice == 0:
            ln = (self.pi * self.s_pmsa[1] +
                  (self.p - self.pi) * (self.s_pmsa[1] - self.s_pmsa[0]) +
                  self.pi_acc * self.s_pmsa[6] +
                  self.p_acc * (self.s_pmsa[7] - self.s_pmsa[6]))
            kn = self.c * self.s_pmsa[1] + self.c_acc * self.s_pmsa[7]
            return (kn * (d_nu * (self.p - self.pi) + d_acc * self.p_acc)) / (ln * ln) if ln != 0 else 0.0
        else:
            return 0.0

    def deploy_strategy(self, proc: float, mem: float, sto: float, acc: int, n_vms: int) -> tuple:
        if not self.alloc:
            return -1, [], []

        ids = [-1] * n_vms
        iterators = [None] * n_vms

        if self.dep_strategy == 1:
            for i in range(n_vms):
                l_id = -1
                for j in range(self.number_of_resources):
                    if (self.available_processors[j] >= proc and
                        self.available_memory[j] >= mem and
                        self.available_storage[j] >= sto and
                        self.available_accelerators[j] >= acc):

                        l_id = self.res[j].probe(proc, mem, sto, acc)
                        if l_id != -1:
                            ids[i] = j
                            iterators[i] = j
                            break

                if l_id == -1:
                    for k in range(i):
                        if ids[k] != -1:
                            self.available_processors[ids[k]] += proc
                            self.available_memory[ids[k]] += mem
                            self.available_storage[ids[k]] += sto
                            self.available_accelerators[ids[k]] += acc
                    return -1, [], []
                else:
                    self.available_processors[j] -= proc
                    self.available_memory[j] -= mem
                    self.available_storage[j] -= sto
                    self.available_accelerators[j] -= acc

            return 1, ids, iterators

        elif self.dep_strategy == 2:
            rem = n_vms
            i = 0
            while rem != 0 and i < n_vms:
                j = 0
                while j < self.number_of_resources:
                    if (self.available_processors[j] >= proc and
                        self.available_memory[j] >= mem and
                        self.available_storage[j] >= sto and
                        self.available_accelerators[j] >= acc):

                        l_id = self.res[j].probe(proc, mem, sto, acc)
                        if l_id != -1:
                            ids[n_vms - rem] = j
                            iterators[n_vms - rem] = j
                            self.available_processors[j] -= proc
                            self.available_memory[j] -= mem
                            self.available_storage[j] -= sto
                            self.available_accelerators[j] -= acc
                            rem -= 1

                    if rem == 0:
                        break
                    j += 1
                i += 1

            if rem != 0:
                for k in range(n_vms):
                    if ids[k] == -1:
                        break
                    self.available_processors[ids[k]] += proc
                    self.available_memory[ids[k]] += mem
                    self.available_storage[ids[k]] += sto
                    self.available_accelerators[ids[k]] += acc
                return -1, [], []

            return 1, ids, iterators

        return 0, [], []

    def deploy(self, resources, network, stats, task) -> None:
        if not self.alloc:
            return

        l_number_of_vms = task.get_number_of_vms()
        type_ = task.get_available_implementations()[0]
        l_req_pmns = task.get_req_pmns()
        l_av_acc = task.get_av_acc()[0]

        l_id = network[0].probe(l_req_pmns[2])

        if l_id == -1:
            stats[type_].rejected_tasks += 1
            return

        ids = [-1] * l_number_of_vms

        l_id, ids, iterators = self.deploy_strategy(l_req_pmns[0], l_req_pmns[1],
                                                     l_req_pmns[3], l_av_acc, l_number_of_vms)

        if l_id == -1:
            stats[type_].rejected_tasks += 1
        else:
            for i in range(l_number_of_vms):
                self.res[iterators[i]].deploy(task)
                ids[i] = self.res[iterators[i]].get_id()

            network[0].deploy(task)
            task.attach_resources(ids)
            self.enque(task)
            stats[type_].accepted_tasks += 1

            ssum = 0.0
            for i in range(1):
                ssum += self.ws[i] * self.deassessment_functions(
                    -l_number_of_vms * l_req_pmns[0],
                    -float(l_number_of_vms * l_av_acc),
                    i
                )
            self.si += ssum

            self.s_pmsa[0] -= l_number_of_vms * l_req_pmns[0]
            self.s_pmsa[2] -= l_number_of_vms * l_req_pmns[1]
            self.s_pmsa[4] -= l_number_of_vms * l_req_pmns[3]
            self.s_pmsa[6] -= float(l_number_of_vms * l_av_acc)

    def probe(self, proc: float, mem: float, sto: float, acc: int) -> int:
        if (proc <= self.s_pmsa[0] and mem <= self.s_pmsa[2] and
            sto <= self.s_pmsa[4] and acc <= int(self.s_pmsa[6])):
            return 1
        else:
            return -1

    def enque(self, task) -> None:
        if self.alloc:
            self.queue.append(task)

    def print(self) -> None:
        if self.alloc:
            for resource in self.res:
                resource.print()

    def get_alloc(self) -> int:
        return self.alloc

    def get_number_of_resources(self) -> int:
        return self.number_of_resources

    def get_opt_num_of_res(self) -> int:
        return self.opt_num_of_res

    def get_poll_interval_vrm(self) -> float:
        return self.poll_interval_vrm

    def get_queue(self) -> List:
        return self.queue

    def get_res(self) -> List:
        return self.res

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

    def get_fs(self) -> List[float]:
        return self.fs

    def get_ws(self) -> List[float]:
        return self.ws

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

    def get_si(self) -> float:
        return self.si

    def get_dep_strategy(self) -> int:
        return self.dep_strategy

    def get_number_of_functions(self) -> int:
        return self.number_of_functions
