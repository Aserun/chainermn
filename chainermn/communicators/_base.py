from chainermn.communicators import _communication_utility
from chainermn import nccl


class NodeAwareCommunicatorBase(object):

    def __init__(self, mpi_comm, use_nccl = None):
        # Automatically enable NCCL if not specified
        if use_nccl is None and nccl._available:
            use_nccl = True
            
        if use_nccl and not nccl._available:
            raise RuntimeError('use_nccl is specified but ' +
                               'ChainerMN is not built with NCCL')

        self.mpi_comm = mpi_comm
        self.use_nccl = use_nccl

        self._init_ranks()

        # TODO(akiba): write why we delay initializing comms
        self.inter_mpi_comm = None
        self.intra_mpi_comm = None
        if self.use_nccl:
            self.intra_nccl_comm = None

    @property
    def rank(self):
        return self.mpi_comm.rank

    @property
    def size(self):
        return self.mpi_comm.size

    def _init_ranks(self):
        my_ranks = _communication_utility.init_ranks(self.mpi_comm)
        assert my_ranks[0] == self.mpi_comm.rank
        self.intra_rank = my_ranks[1]
        self.intra_size = my_ranks[2]
        self.inter_rank = my_ranks[3]
        self.inter_size = my_ranks[4]

    def _init_comms(self):
        if self.inter_mpi_comm is not None:
            assert self.intra_mpi_comm is not None
            assert self.intra_nccl_comm is not None
            return

        comms = _communication_utility.init_comms(
            self.mpi_comm, self.intra_rank, self.intra_size, self.inter_rank,
            use_nccl=self.use_nccl)
        self.intra_mpi_comm = comms[0]
        self.inter_mpi_comm = comms[1]
        if self.use_nccl:
            self.intra_nccl_comm = comms[2]

    def broadcast_data(self, model):
        raise NotImplementedError()

    def allreduce_grad(self, model):
        raise NotImplementedError()
