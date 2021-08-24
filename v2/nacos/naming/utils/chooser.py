import math
import random

from nacos import NacosException
from v2.nacos.naming.utils.generic_poller import GenericPoller


class Chooser:
    def __init__(self, unique_key, pairs=None):
        if not pairs:
            pairs = []
            ref = Chooser.Ref(pairs)
            ref.refresh()
            self.unique_key = unique_key
            self.ref = ref

    def random(self):
        items = self.ref.items
        if len(items) == 0:
            return None

        if len(items) == 1:
            return items[0]

        return items[random.randint(0, len(items)-1)]

    def random_with_weight(self):
        def search_insert(nums, target):
            if target in nums:
                return True, nums.index(target)
            else:
                for i, value in enumerate(nums):
                    if value > target:
                        return i
                return False, len(nums)

        ref = self.ref
        random_double = random.random()
        flag, index = search_insert(ref.weights, random_double)
        if flag:
            return ref.items[index]

        if index < len(ref.weights):
            if random_double < ref.weights[index]:
                return ref.items[index]

        return ref.items[len(ref.items) - 1]

    def get_unique_key(self):
        return self.unique_key

    def get_ref(self):
        return self.ref

    def get_hash_code(self):
        return hash(self.unique_key)

    def refresh(self, items_with_weight: list):
        new_ref = Chooser.Ref(items_with_weight)
        new_ref.refresh()
        new_ref.poller = self.ref.poller.refresh(new_ref.items)
        self.ref = new_ref

    class Ref:
        def __init__(self, items_with_weight):
            self.items_with_weight = items_with_weight
            self.items = []
            self.poller = GenericPoller(self.items)
            self.weights = []

        def refresh(self):
            origin_weight_sum = 0

            for item in self.items_with_weight:
                weight = item["weight"]
                if weight <= 0:
                    continue

                self.items.append(item["item"])

                if math.isinf(weight):
                    weight = 10000
                if math.isnan(weight):
                    weight = 1

                origin_weight_sum += weight

            exact_weight = []
            for item in self.items_with_weight:
                single_weight = item["weight"]
                if single_weight <= 0:
                    continue
                exact_weight.append(single_weight/origin_weight_sum)

            random_range = 0
            for i in range(len(exact_weight)):
                self.weights.append(random_range + exact_weight[i])
                random_range += exact_weight[i]

            double_precision_delta = 0.0001

            if not self.weights or abs(self.weights[-1] - 1) < double_precision_delta:
                return
            raise NacosException("Cumulative Weight calculate wrong , the sum of probabilities does not equals 1.")

        def get_hash_code(self):
            return hash(self.items_with_weight)
