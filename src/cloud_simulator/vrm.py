import math
import random
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .resource import Resource
    from .network import Network
    from .statistics import Statistics
    from .task import Task


class VRM:

    def __init__(self, start: int = 0, end: int = 0, resource_type: int = 0,
                 resources: Optional[List[List['Resource']]] = None,
                 poll_interval_vrm: float = 0.0, c: float = 0.0, p: float = 0.0,
                 pi: float = 0.0, opt_num_of_res: int = 0, num_functions: int = 0,
                 weights: Optional[List[float]] = None, deploy_strategy: int = 0):

        self.alloc: int = 0
        self.number_of_resources: int = 0
        self.number_of_functions: int = num_functions
        self.opt_num_of_res: int = opt_num_of_res
        self.poll_interval_vrm: float = poll_interval_vrm
        self.queue: List['Task'] = []
        self.resources: List['Resource'] = []
        self.fs: List[float] = [0.0] * num_functions
        self.ws: List[float] = list(weights) if weights else [0.0] * num_functions
        self.available_processors: List[float] = []
        self.total_processors: List[float] = []
        self.available_memory: List[float] = []
        self.total_memory: List[float] = []
        self.available_accelerators: List[float] = []
        self.total_accelerators: List[float] = []
        self.available_storage: List[float] = []
        self.total_storage: List[float] = []
        self.spmsa: List[float] = [0.0] * 8
        self.c: float = c
        self.p: float = p
        self.pi: float = pi
        self.si: float = 0.0
        self.dep_strategy: int = deploy_strategy

        if resources is not None and end > start:
            self._initialize(start, end, resource_type, resources)

    def _initialize(self, start: int, end: int, resource_type: int,
                    resources: List[List['Resource']]) -> None:
        self.alloc = 1
        self.number_of_resources = end - start

        for i in range(start, end):
            self.resources.append(resources[resource_type][i])

        self.available_processors = [0.0] * self.number_of_resources
        self.total_processors = [0.0] * self.number_of_resources
        self.available_memory = [0.0] * self.number_of_resources
        self.total_memory = [0.0] * self.number_of_resources
        self.available_accelerators = [0.0] * self.number_of_resources
        self.total_accelerators = [0.0] * self.number_of_resources
        self.available_storage = [0.0] * self.number_of_resources
        self.total_storage = [0.0] * self.number_of_resources

        self.update_state_info(0.0)

    def print(self) -> None:
        if self.alloc:
            for resource in self.resources:
                resource.print()

    def compute_fs(self) -> None:
        if self.alloc:
            for i in range(self.number_of_functions):
                self.fs[i] = self.assess_funcs(i)

    def compute_si(self) -> None:
        if self.alloc:
            self.si = 1e-4 * random.random()
            for i in range(self.number_of_functions):
                self.si += self.ws[i] * self.fs[i]

    def assess_funcs(self, choice: int) -> float:
        if self.spmsa[7] > 0:
            if choice == 0:
                return self.c * self.spmsa[6] / self.spmsa[7]
            elif choice == 1:
                return self.spmsa[2] / self.spmsa[3]
            elif choice == 2:
                return (self.pi * self.spmsa[6]) / (self.pi * self.spmsa[6] +
                        self.p * (self.spmsa[7] - self.spmsa[6]))
            elif choice == 3:
                return 1.0 - 0.2 * (self.spmsa[7] - self.spmsa[6]) / self.spmsa[7]
            elif choice == 4:
                return 2.0 / (1.0 + math.exp(-6.0 + 6.0 * self.number_of_resources / self.opt_num_of_res))
            else:
                return 0.0
        else:
            if choice == 0:
                return self.c * self.spmsa[0] / self.spmsa[1]
            elif choice == 1:
                return self.spmsa[2] / self.spmsa[3]
            elif choice == 2:
                return (self.pi * self.spmsa[0]) / (self.pi * self.spmsa[0] +
                        self.p * (self.spmsa[1] - self.spmsa[0]))
            elif choice == 3:
                return 1.0 - 0.2 * (self.spmsa[1] - self.spmsa[0]) / self.spmsa[1]
            elif choice == 4:
                return 2.0 / (1.0 + math.exp(-6.0 + 6.0 * self.number_of_resources / self.opt_num_of_res))
            else:
                return 0.0

    def deassessment_functions(self, dnu: float, dnmem: float, choice: int) -> float:
        if self.spmsa[7] > 0:
            if choice == 0:
                return dnu * self.c / self.spmsa[7]
            elif choice == 1:
                return dnmem / self.spmsa[3]
            elif choice == 2:
                denom = (self.p * (self.spmsa[7] - self.spmsa[6]) + self.pi * self.spmsa[6])
                return (dnu * self.pi * self.p * self.spmsa[7]) / (denom * denom)
            elif choice == 3:
                return 0.2 * dnu / self.spmsa[7]
            else:
                return 0.0
        else:
            if choice == 0:
                return dnu * self.c / self.spmsa[1]
            elif choice == 1:
                return dnmem / self.spmsa[3]
            elif choice == 2:
                denom = (self.p * (self.spmsa[1] - self.spmsa[0]) + self.pi * self.spmsa[0])
                return (dnu * self.pi * self.p * self.spmsa[1]) / (denom * denom)
            elif choice == 3:
                return 0.2 * dnu / self.spmsa[1]
            else:
                return 0.0

    def update_state_info(self, tstep: float) -> None:
        if self.alloc:
            if int(tstep) % int(self.poll_interval_vrm) == 0 if self.poll_interval_vrm > 0 else True:
                self.spmsa = [0.0] * 8

                for i, resource in enumerate(self.resources):
                    self.available_processors[i] = resource.get_available_processors()
                    self.total_processors[i] = resource.get_total_processors()
                    self.available_memory[i] = resource.get_available_memory()
                    self.total_memory[i] = resource.get_total_memory()
                    self.available_accelerators[i] = float(resource.get_available_accelerators())
                    self.total_accelerators[i] = float(resource.get_total_accelerators())
                    self.available_storage[i] = resource.get_available_storage()
                    self.total_storage[i] = resource.get_total_storage()

                for i in range(len(self.resources)):
                    self.spmsa[0] += self.available_processors[i]
                    self.spmsa[1] += self.total_processors[i]
                    self.spmsa[2] += self.available_memory[i]
                    self.spmsa[3] += self.total_memory[i]
                    self.spmsa[4] += self.available_storage[i]
                    self.spmsa[5] += self.total_storage[i]
                    self.spmsa[6] += self.available_accelerators[i]
                    self.spmsa[7] += self.total_accelerators[i]

                self.compute_fs()
                self.compute_si()

    def obtain_resources(self, ores: List['Resource'], rem_proc: float,
                        rem_mem: float, rem_sto: float, rem_acc: float) -> tuple:
        if not self.alloc:
            return rem_proc, rem_mem, rem_sto, rem_acc

        if rem_proc <= 0.0 and rem_mem <= 0.0 and rem_sto <= 0.0 and rem_acc <= 0:
            return rem_proc, rem_mem, rem_sto, rem_acc

        resources_to_remove = []
        i = 0
        for resource in self.resources:
            if resource.get_movable() == 1:
                ores.append(resource)
                resources_to_remove.append(i)
                self.number_of_resources -= 1
                rem_proc -= self.total_processors[i]
                rem_mem -= self.total_memory[i]
                rem_sto -= self.total_storage[i]
                rem_acc -= self.total_accelerators[i]
                self.spmsa[0] -= self.total_processors[i]
                self.spmsa[1] -= self.total_processors[i]
                self.spmsa[2] -= self.total_memory[i]
                self.spmsa[3] -= self.total_memory[i]
                self.spmsa[4] -= self.total_storage[i]
                self.spmsa[5] -= self.total_storage[i]
                self.spmsa[6] -= self.total_accelerators[i]
                self.spmsa[7] -= self.total_accelerators[i]

                if rem_proc <= 0.0 and rem_mem <= 0.0 and rem_sto <= 0.0 and rem_acc <= 0:
                    break
            i += 1

        for idx in reversed(resources_to_remove):
            del self.resources[idx]
            del self.available_processors[idx]
            del self.total_processors[idx]
            del self.available_memory[idx]
            del self.total_memory[idx]
            del self.available_accelerators[idx]
            del self.total_accelerators[idx]
            del self.available_storage[idx]
            del self.total_storage[idx]

        if resources_to_remove:
            self.compute_fs()
            self.compute_si()

        return rem_proc, rem_mem, rem_sto, rem_acc

    def attach_resources(self, ores: List['Resource']) -> None:
        if not self.alloc:
            return

        nar = len(ores)
        if nar <= 0:
            return

        for resource in ores:
            self.spmsa[0] += resource.get_total_processors()
            self.spmsa[1] += resource.get_total_processors()
            self.spmsa[2] += resource.get_total_memory()
            self.spmsa[3] += resource.get_total_memory()
            self.spmsa[4] += resource.get_total_storage()
            self.spmsa[5] += resource.get_total_storage()
            self.spmsa[6] += float(resource.get_total_accelerators())
            self.spmsa[7] += float(resource.get_total_accelerators())

            self.available_processors.append(resource.get_total_processors())
            self.total_processors.append(resource.get_total_processors())
            self.available_memory.append(resource.get_total_memory())
            self.total_memory.append(resource.get_total_memory())
            self.available_accelerators.append(float(resource.get_total_accelerators()))
            self.total_accelerators.append(float(resource.get_total_accelerators()))
            self.available_storage.append(resource.get_total_storage())
            self.total_storage.append(resource.get_total_storage())

            self.resources.append(resource)

        self.number_of_resources += nar
        self.compute_fs()
        self.compute_si()

    def deploy_strategy_impl(self, n_vms: int, proc: float, mem: float,
                            sto: float, acc: int) -> tuple:
        ids = [-1] * n_vms
        resource_refs = [None] * n_vms

        if self.dep_strategy == 1:
            for i in range(n_vms):
                l_id = -1
                for j in range(self.number_of_resources):
                    if (self.available_processors[j] >= proc and
                        self.available_memory[j] >= mem and
                        self.available_storage[j] >= sto and
                        self.available_accelerators[j] >= acc):

                        l_id = self.resources[j].probe(proc, mem, sto, acc)
                        if l_id != -1:
                            ids[i] = j
                            resource_refs[i] = self.resources[j]
                            break

                if l_id == -1:
                    break
                else:
                    self.available_processors[j] -= proc
                    self.available_memory[j] -= mem
                    self.available_storage[j] -= sto
                    self.available_accelerators[j] -= acc

            if l_id == -1:
                for i in range(n_vms):
                    if ids[i] == -1:
                        break
                    self.available_processors[ids[i]] += proc
                    self.available_memory[ids[i]] += mem
                    self.available_storage[ids[i]] += sto
                    self.available_accelerators[ids[i]] += acc
                return -1, ids, resource_refs

            return 1, ids, resource_refs

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

                        l_id = self.resources[j].probe(proc, mem, sto, acc)
                        if l_id != -1:
                            idx = n_vms - rem
                            ids[idx] = j
                            resource_refs[idx] = self.resources[j]
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
                for i in range(n_vms):
                    if ids[i] == -1:
                        break
                    self.available_processors[ids[i]] += proc
                    self.available_memory[ids[i]] += mem
                    self.available_storage[ids[i]] += sto
                    self.available_accelerators[ids[i]] += acc
                return -1, ids, resource_refs

            return 1, ids, resource_refs

        return 0, ids, resource_refs

    def deploy(self, resources: List[List['Resource']], network: 'Network',
               stats: List['Statistics'], task: 'Task') -> None:
        if not self.alloc:
            return

        l_number_of_vms = task.get_number_of_vms()
        impl_type = task.get_available_implementations()[0]
        l_req_pmns = task.get_req_pmns()
        l_av_acc = task.get_av_acc()[0]

        l_id = network.probe(l_req_pmns[2])

        if l_id == -1:
            stats[impl_type].rejected_tasks += 1
            return

        l_id, ids, resource_refs = self.deploy_strategy_impl(
            l_number_of_vms, l_req_pmns[0], l_req_pmns[1], l_req_pmns[3], l_av_acc)

        if l_id == -1:
            stats[impl_type].rejected_tasks += 1
        else:
            for i in range(l_number_of_vms):
                resource_refs[i].deploy(task)
                ids[i] = resource_refs[i].get_id()

            network.deploy(task)
            task.attach_resources(ids)
            self.enque(task)

            stats[impl_type].accepted_tasks += 1

            self.spmsa[0] -= l_number_of_vms * l_req_pmns[0]
            self.spmsa[2] -= l_number_of_vms * l_req_pmns[1]
            self.spmsa[4] -= l_number_of_vms * l_req_pmns[3]
            self.spmsa[6] -= float(l_number_of_vms * l_av_acc)

            ssum = 0.0
            for i in range(4):
                ssum += self.ws[i] * self.deassessment_functions(
                    -l_number_of_vms * l_req_pmns[0],
                    -l_number_of_vms * l_req_pmns[1], i)

            self.si += ssum

    def probe(self, proc: float, mem: float, sto: float, acc: int) -> int:
        if (proc <= self.spmsa[0] and mem <= self.spmsa[2] and
            sto <= self.spmsa[4] and acc <= int(self.spmsa[6])):
            return 1
        else:
            return -1

    def enque(self, task: 'Task') -> None:
        if self.alloc:
            self.queue.append(task)

    def get_alloc(self) -> int:
        return self.alloc

    def get_number_of_resources(self) -> int:
        return self.number_of_resources

    def get_opt_num_of_res(self) -> int:
        return self.opt_num_of_res

    def get_poll_interval_vrm(self) -> float:
        return self.poll_interval_vrm

    def get_queue(self) -> List['Task']:
        return self.queue

    def get_resources(self) -> List['Resource']:
        return self.resources

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

    def get_spmsa(self) -> List[float]:
        return self.spmsa

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

    def get_si(self) -> float:
        return self.si

    def get_dep_strategy(self) -> int:
        return self.dep_strategy

    def get_number_of_functions(self) -> int:
        return self.number_of_functions
