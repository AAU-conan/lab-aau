from lab.environments import SlurmEnvironment
import platform
import re
from lab.compress_step import CompressStep

class DEISSlurmEnvironment(SlurmEnvironment):
    """Environment for DEIS cluster."""

    DEFAULT_PARTITION = "naples"
    DEFAULT_QOS = "normal"
    DEFAULT_MEMORY_PER_CPU = "4096M"
    MAX_TASKS = 1000 - 1  # see slurm.conf

    DEFAULT_EXPORT = []


    @classmethod
    def is_cluster_main(cls):
        node = platform.node()
        return re.match(r"deis-mcc3-fe\d+", node)

    @classmethod
    def is_cluster_rome(cls):
        node = platform.node()
        return re.match(r"a1024-gc1-\d+", node)

    @classmethod
    def is_cluster_naples(cls):
        node = platform.node()
        return re.match(r"a512-ib1-a-\d+", node)

    @classmethod
    def is_cluster_dhabi(cls):
        node = platform.node()
        return re.match(r"a512-ib1-a-\d+", node)

    @classmethod
    def is_cluster(cls):
        return cls.is_cluster_main() or cls.is_cluster_dhabi() or cls.is_cluster_naples() or cls.is_cluster_rome()

    @classmethod
    def compress_step(cls, lab_experiment, username):
        return CompressStep(lab_experiment,f'/nfs/home/cs.aau.dk/{username}', '/scratch/username/')

