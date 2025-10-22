import random
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .pswitch import PSwitch
    from .resource import Resource
    from .network import Network
    from .statistics import Statistics
    from .task import Task


class PRouter:

    def __init__(self, start: int = 0, end: int = 0, resource_type: int = 0,
                 pswitches_list: Optional[List[List['PSwitch']]] = None,
                 poll_interval_prouter: float = 0.0, c: float = 0.0, p: float = 0.0,
                 pi: float = 0.0, num_functions: int = 0,
                 weights: Optional[List[float]] = None):

        self.alloc: int = 0
        self.number_of_pswitches: int = 0
        self.number_of_functions: int = num_functions
        self.poll_interval_prouter: float = poll_interval_prouter
        self.pswitches: List['PSwitch'] = []
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
        self.sis: List[float] = []
        self.si: float = 0.0
        self.c: float = c
        self.p: float = p
        self.pi: float = pi

        if pswitches_list is not None and end > start:
            self._initialize(start, end, resource_type, pswitches_list)

    def _initialize(self, start: int, end: int, resource_type: int,
                    pswitches_list: List[List['PSwitch']]) -> None:
        self.alloc = 1
        self.number_of_pswitches = end - start

        for i in range(start, end):
            self.pswitches.append(pswitches_list[resource_type][i])

        self.available_processors = [0.0] * self.number_of_pswitches
        self.total_processors = [0.0] * self.number_of_pswitches
        self.available_memory = [0.0] * self.number_of_pswitches
        self.total_memory = [0.0] * self.number_of_pswitches
        self.available_accelerators = [0.0] * self.number_of_pswitches
        self.total_accelerators = [0.0] * self.number_of_pswitches
        self.available_storage = [0.0] * self.number_of_pswitches
        self.total_storage = [0.0] * self.number_of_pswitches
        self.sis = [0.0] * self.number_of_pswitches

        self.update_state_info(0.0)

    def compute_fs(self) -> None:
        if self.alloc:
            self.fs = [0.0] * self.number_of_functions

            for pswitch in self.pswitches:
                pswitch_fs = pswitch.get_fs()
                for j in range(self.number_of_functions):
                    self.fs[j] += pswitch_fs[j]

            for j in range(self.number_of_functions):
                self.fs[j] /= self.number_of_pswitches

    def compute_si(self) -> None:
        if self.alloc:
            self.si = 1e-4 * random.random()
            for i in range(self.number_of_functions):
                self.si += self.ws[i] * self.fs[i]

    def probe(self, proc: float, mem: float, sto: float, acc: int) -> int:
        if (proc <= self.spmsa[0] and mem <= self.spmsa[2] and
            sto <= self.spmsa[4] and acc <= int(self.spmsa[6])):
            return 1
        else:
            return -1

    def deploy(self, resources: List[List['Resource']], network: 'Network',
               stats: List['Statistics'], task: 'Task') -> None:
        if not self.alloc:
            return

        l_number_of_vms = task.get_number_of_vms()
        l_req_pmns = task.get_req_pmns()
        l_av_acc = task.get_av_acc()[0]

        req_proc = l_number_of_vms * l_req_pmns[0]
        req_mem = l_number_of_vms * l_req_pmns[1]
        req_sto = l_number_of_vms * l_req_pmns[3]
        req_acc = l_number_of_vms * l_av_acc

        choice = -1
        max_si = 0.0

        for i in range(self.number_of_pswitches):
            if (max_si < self.sis[i] and req_proc <= self.available_processors[i] and
                req_mem <= self.available_memory[i] and req_sto <= self.available_storage[i] and
                req_acc <= self.available_accelerators[i]):
                max_si = self.sis[i]
                choice = i

        if choice == -1:
            stats[task.get_available_implementations()[0]].rejected_tasks += 1
            return

        self.available_processors[choice] -= req_proc
        self.available_memory[choice] -= req_mem
        self.available_storage[choice] -= req_sto
        self.available_accelerators[choice] -= req_acc
        self.spmsa[0] -= req_proc
        self.spmsa[2] -= req_mem
        self.spmsa[4] -= req_sto
        self.spmsa[6] -= float(req_acc)

        ssum = 0.0
        if req_acc > 0:
            for i in range(4):
                ssum += self.ws[i] * self.deassessment_functions(
                    -float(req_acc), self.spmsa[7], -req_mem, self.spmsa[3], i)
        else:
            for i in range(4):
                ssum += self.ws[i] * self.deassessment_functions(
                    -req_proc, self.spmsa[1], -req_mem, self.spmsa[3], i)

        self.si += ssum

        ssum = 0.0
        if self.spmsa[7] > 0:
            for i in range(4):
                ssum += self.ws[i] * self.deassessment_functions(
                    -float(req_acc), self.total_accelerators[choice],
                    -req_mem, self.total_memory[choice], i)
        else:
            for i in range(4):
                ssum += self.ws[i] * self.deassessment_functions(
                    -req_proc, self.total_processors[choice],
                    -req_mem, self.total_memory[choice], i)

        self.sis[choice] += ssum

        self.pswitches[choice].deploy(resources, network, stats, task)

    def update_state_info(self, tstep: float) -> None:
        if self.alloc:
            if int(tstep) % int(self.poll_interval_prouter) == 0 if self.poll_interval_prouter > 0 else True:
                self.spmsa = [0.0] * 8

                for i, pswitch in enumerate(self.pswitches):
                    pswitch_spmsa = pswitch.get_spmsa()
                    self.available_processors[i] = pswitch_spmsa[0]
                    self.total_processors[i] = pswitch_spmsa[1]
                    self.available_memory[i] = pswitch_spmsa[2]
                    self.total_memory[i] = pswitch_spmsa[3]
                    self.available_storage[i] = pswitch_spmsa[4]
                    self.total_storage[i] = pswitch_spmsa[5]
                    self.available_accelerators[i] = pswitch_spmsa[6]
                    self.total_accelerators[i] = pswitch_spmsa[7]
                    self.sis[i] = pswitch.get_si()

                for i in range(len(self.pswitches)):
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

    def deassessment_functions(self, dnu: float, tot_nu: float, dnmem: float,
                              total_memory: float, choice: int) -> float:
        if choice == 0:
            return dnu * self.c / tot_nu if tot_nu > 0 else 0.0
        elif choice == 1:
            return dnmem / total_memory if total_memory > 0 else 0.0
        elif choice == 2:
            denom = (self.p * (tot_nu - dnu) + self.pi * dnu)
            return (dnu * self.pi * self.p * tot_nu) / (denom * denom) if denom > 0 else 0.0
        elif choice == 3:
            return 0.2 * dnu / tot_nu if tot_nu > 0 else 0.0
        else:
            return 0.0

    def print(self) -> None:
        if self.alloc:
            print("pRouter Stats")
            print(f"Available Processing Units: {self.spmsa[0]}")
            print(f"Total Processing Units: {self.spmsa[1]}")
            print(f"Available Memory: {self.spmsa[2]}")
            print(f"Total Memory: {self.spmsa[3]}")
            print(f"Available Storage: {self.spmsa[4]}")
            print(f"Total Storage: {self.spmsa[5]}")
            print(f"Available Accelerators: {self.spmsa[6]}")
            print(f"Total Accelerators: {self.spmsa[7]}")

    def get_alloc(self) -> int:
        return self.alloc

    def get_number_of_pswitches(self) -> int:
        return self.number_of_pswitches

    def get_number_of_functions(self) -> int:
        return self.number_of_functions

    def get_poll_interval_prouter(self) -> float:
        return self.poll_interval_prouter

    def get_pswitches(self) -> List['PSwitch']:
        return self.pswitches

    def get_fs(self) -> List[float]:
        return self.fs

    def get_ws(self) -> List[float]:
        return self.ws

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

    def get_sis(self) -> List[float]:
        return self.sis

    def get_si(self) -> float:
        return self.si

    def get_c(self) -> float:
        return self.c

    def get_p(self) -> float:
        return self.p

    def get_pi(self) -> float:
        return self.pi
