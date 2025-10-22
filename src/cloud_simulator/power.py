import math
from typing import List, Optional
from .inputs import PowerInputs


class Power:

    def __init__(self, power_inputs: Optional[PowerInputs] = None):
        self.type_cpu: int = 0
        self.type_acc: int = 0
        self.accelerator: int = 0
        self.cpu_pmin: float = 0.0
        self.cpu_pmax: float = 0.0
        self.cpu_c: float = 0.0
        self.num_of_points: int = 0
        self.cpu_bins: List[float] = []
        self.cpu_p: List[float] = []
        self.acc_pmin: float = 0.0
        self.acc_pmax: float = 0.0
        self.acc_c: float = 0.0
        self.a: List[float] = []
        self.b: List[float] = []
        self.c_coeff: List[float] = []
        self.d: List[float] = []

        if power_inputs:
            self._init_from_inputs(power_inputs)

    def _init_from_inputs(self, t: PowerInputs) -> None:
        self.type_cpu = t.type_cpu
        self.cpu_pmin = t.cpu_pmin
        self.cpu_pmax = t.cpu_pmax
        self.cpu_c = t.cpu_c

        if self.type_cpu < 0:
            self.num_of_points = 0
        elif self.type_cpu > 0:
            self.num_of_points = t.num_of_points
            self.cpu_bins = list(t.cpu_bins)
            self.cpu_p = list(t.cpu_p)

            if self.type_cpu == 2:
                self._compute_cubic_spline()

        self.accelerator = t.accelerator
        self.type_acc = t.type_acc
        self.acc_pmin = t.acc_pmin
        self.acc_pmax = t.acc_pmax
        self.acc_c = t.acc_c

    def _compute_cubic_spline(self) -> None:
        n = self.num_of_points
        self.a = [self.cpu_p[i] for i in range(n - 1)]
        self.b = [0.0] * (n - 1)
        self.c_coeff = [0.0] * n
        self.d = [0.0] * (n - 1)

        h = [self.cpu_bins[i + 1] - self.cpu_bins[i] for i in range(n - 1)]

        s = [0.0] * n
        for i in range(1, n - 1):
            s[i] = (3.0 * (self.cpu_p[i + 1] - self.cpu_p[i]) / h[i] -
                    3.0 * (self.cpu_p[i] - self.cpu_p[i - 1]) / h[i - 1])
        s[0] = -h[0] * s[1]
        s[n - 1] = -h[n - 2] * s[n - 2]

        tb = [0.0] * n
        tb[0] = h[1] * h[1] - h[0] * h[0]
        for i in range(1, n - 1):
            tb[i] = 2.0 * (h[i - 1] + h[i])
        tb[n - 1] = h[n - 3] * h[n - 3] - h[n - 2] * h[n - 2]

        tc = [0.0] * n
        tc[0] = -2.0 * h[0] * h[0] - 3.0 * h[0] * h[1] - h[1] * h[1]
        for i in range(1, n - 1):
            tc[i] = h[i]

        ta = [0.0] * n
        for i in range(1, n - 1):
            ta[i] = h[i - 1]
        ta[n - 1] = (-2.0 * h[n - 2] * h[n - 2] -
                     3.0 * h[n - 3] * h[n - 2] - h[n - 3] * h[n - 3])

        tc[0] = tc[0] / tb[0]
        for i in range(1, n - 1):
            tc[i] = tc[i] / (tb[i] - ta[i] * tc[i - 1])

        s[0] = s[0] / tb[0]
        for i in range(1, n):
            s[i] = (s[i] - ta[i] * s[i - 1]) / (tb[i] - ta[i] * tc[i - 1])

        self.c_coeff[n - 1] = s[n - 1]
        for i in range(n - 2, -1, -1):
            self.c_coeff[i] = s[i] - tc[i] * self.c_coeff[i + 1]

        for i in range(n - 1):
            self.d[i] = (self.c_coeff[i + 1] - self.c_coeff[i]) / (3.0 * h[i])

        for i in range(n - 1):
            self.b[i] = ((self.cpu_p[i + 1] - self.cpu_p[i]) / h[i] -
                         self.c_coeff[i] * h[i] - self.d[i] * h[i] * h[i])

    def model_cpu(self, u: float) -> float:
        pcons = 0.0

        if self.type_cpu == -1:
            pcons = self.cpu_pmin + (self.cpu_pmax - self.cpu_pmin) * u
        elif self.type_cpu == -2:
            pcons = self.cpu_pmin + (self.cpu_pmax - self.cpu_pmin) * u * u
        elif self.type_cpu == -3:
            pcons = self.cpu_pmin + (self.cpu_pmax - self.cpu_pmin) * u * u * u
        elif self.type_cpu == -4:
            pmid = self.cpu_pmin + (self.cpu_pmax - self.cpu_pmin) / 2
            pcons = ((4.0 / 3.0 * pmid - self.cpu_pmin / 6.0 - self.cpu_pmax / 3.0) +
                     (4.0 / 3.0 * pmid - 2.0 * self.cpu_pmin / 3.0 - self.cpu_pmax / 3.0) * u +
                     (2.0 * self.cpu_pmax + 2.0 * self.cpu_pmin - 4.0 * pmid) * u * u +
                     (4.0 / 3.0 * pmid - 7.0 / 6.0 * self.cpu_pmin - self.cpu_pmax / 3.0) *
                     (2.0 * u - 1.0) * (2.0 * u - 1.0) * (2.0 * u - 1.0))
        elif self.type_cpu == -5:
            pmid = 5.0 * self.cpu_pmax / 9.0
            pcons = ((4.0 / 3.0 * pmid - self.cpu_pmin / 6.0 - self.cpu_pmax / 3.0) +
                     (4.0 / 3.0 * pmid - 2.0 * self.cpu_pmin / 3.0 - self.cpu_pmax / 3.0) * u +
                     (2.0 * self.cpu_pmax + 2.0 * self.cpu_pmin - 4.0 * pmid) * u * u +
                     (4.0 / 3.0 * pmid - 7.0 / 6.0 * self.cpu_pmin - self.cpu_pmax / 3.0) *
                     (2.0 * u - 1.0) * (2.0 * u - 1.0) * (2.0 * u - 1.0))
        elif self.type_cpu == 1:
            if u < self.cpu_bins[0]:
                pcons = (self.cpu_p[0] + (self.cpu_p[1] - self.cpu_p[0]) *
                         (u - self.cpu_bins[0]) / (self.cpu_bins[1] - self.cpu_bins[0]))
            elif u > self.cpu_bins[self.num_of_points - 1]:
                n = self.num_of_points
                pcons = (self.cpu_p[n - 2] + (self.cpu_p[n - 1] - self.cpu_p[n - 2]) *
                         (u - self.cpu_bins[n - 2]) / (self.cpu_bins[n - 1] - self.cpu_bins[n - 2]))
            else:
                i = 1
                for idx in range(1, self.num_of_points):
                    if u <= self.cpu_bins[idx]:
                        i = idx
                        break
                pcons = (self.cpu_p[i - 1] + (self.cpu_p[i] - self.cpu_p[i - 1]) *
                         (u - self.cpu_bins[i - 1]) / (self.cpu_bins[i] - self.cpu_bins[i - 1]))
        elif self.type_cpu == 2:
            if u < self.cpu_bins[0]:
                du = u - self.cpu_bins[0]
                pcons = self.a[0] + self.b[0] * du + self.c_coeff[0] * du * du + self.d[0] * du * du * du
            elif u > self.cpu_bins[self.num_of_points - 1]:
                n = self.num_of_points
                du = u - self.cpu_bins[n - 2]
                pcons = (self.a[n - 2] + self.b[n - 2] * du +
                         self.c_coeff[n - 2] * du * du + self.d[n - 2] * du * du * du)
            else:
                i = 0
                for idx in range(1, self.num_of_points):
                    if u <= self.cpu_bins[idx]:
                        i = idx - 1
                        break
                du = u - self.cpu_bins[i]
                pcons = self.a[i] + self.b[i] * du + self.c_coeff[i] * du * du + self.d[i] * du * du * du
        elif self.type_cpu == 3:
            ii = math.floor(u * 10)
            if ii >= self.num_of_points - 1:
                ii = self.num_of_points - 2
            pcons = (self.cpu_p[ii] + (self.cpu_p[ii + 1] - self.cpu_p[ii]) *
                     (u - 0.1 * ii) / (0.1 * (ii + 1) - 0.1 * ii))

        return pcons

    def model_acc(self, rho: float, num_acc: int) -> float:
        pcons = 0.0
        if self.type_acc == -1:
            pcons = self.acc_pmin * num_acc + rho * (self.acc_pmax - self.acc_pmin) * num_acc
        return pcons

    def consumption(self, u: float, rho: float, active: int, num_acc: int) -> float:
        if active:
            return (self.model_cpu(u) + self.model_acc(rho, num_acc)) * (1.0e-9) / 3600
        else:
            return (self.cpu_c + num_acc * self.acc_c) * (1.0e-9) / 3600

    def print(self) -> None:
        print(f"         CPU Power Consumption model: {self.type_cpu}")
        if self.type_cpu < 0:
            print(f"            CPU Idle Power Consumption: {self.cpu_pmin} Watts")
            print(f"            CPU Max Power Consumption: {self.cpu_pmax} Watts")
        elif self.type_cpu > 0:
            print(f"            CPU Number of Points for Interpolation: {self.num_of_points}")
            print(f"            CPU Utilization Bins: {self.cpu_bins}")
            print(f"            CPU Power Consumption: {self.cpu_p}")
        print(f"            CPU Sleep Power Consumption: {self.cpu_c} Watts")
        print(f"         ACC Power Consumption model: {self.type_acc}")
        if self.accelerator:
            print(f"            ACC Idle Power Consumption: {self.acc_pmin} Watts")
            print(f"            ACC Max Power Consumption: {self.acc_pmax} Watts")
            print(f"            ACC Sleep Power Consumption: {self.acc_c} Watts")
