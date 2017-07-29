import chainer
import chainermn
import chainermn.communicators
import chainermn.functions
import chainermn.functions.point_to_point_communication


class MultiNodeChainList(chainer.ChainList):
    """Combining multiple non-connected components of computational graph.

    This class combines each ``chainer.Chain``, which represents one of the
    non-connected component in compuational graph. In ``__call__()``,
    the returned object of ``chainer.Chain`` (which represents pointer)
    are passed to the next ``chainer.Chain``, in order to retain the
    computational graph connected and make backprop work properly.

    Users add each ``chainer.Chain`` by ``add_link()`` method. Each chain
    is invoked in forward computation according to the order they are added,
    and in backward computation according to the reversed order.

    .. admonition:: Example

        This is a simple example of the model which sends its outputs to
        rank=1 machine::

            import chainer
            import chainer.functions as F
            import chainermn


            class SimpleModelSub(chainer.Chain):

                def __init__(self, n_in, n_hidden, n_out):
                    super(SimpleModelSub, self).__init__(
                        l1=L.Linear(n_in, n_hidden),
                        l2=L.Linear(n_hidden, n_out))

                def __call__(self, x):
                    h1 = F.relu(self.l1(x))
                    return self.l2(h1)


            class SimpleModel(chainermn.MultiNodeChainList):

                def __init__(self, comm, n_in, n_hidden, n_out):
                    super(SimpleModel, self).__init__(comm)
                    self.add_link(
                        SimpleModelSub(n_in, n_hidden, n_out),
                        rank_in=None,
                        rank_out=1)

    .. admonition:: Example

        This is the other example of two models interacting each other::

            import chainer
            import chainer.functions as F
            import chainermn


            class MLP(chainer.Chain):

                def __init__(self, n_in, n_hidden, n_out):
                    super(MLP, self).__init__(
                        l1=L.Linear(n_in, n_hidden),
                        l2=L.Linear(n_hidden, n_hidden),
                        l3=L.Linear(n_hidden, n_out))

                def __call__(self, x):
                    h1 = F.relu(self.l1(x))
                    h2 = F.relu(self.l2(h1))
                    return self.l3(h2)


            class Model0(chainermn.MultiNodeChainList):

                def __init__(self, comm):
                    super(Model0, self).__init__(comm)
                    self.add_link(
                        MLP(10000, 5000, 2000),
                        rank_in=None,
                        rank_out=1)
                    self.add_link(
                        MLP(100, 50, 10),
                        rank_in=1,
                        rank_out=None)


            class Model1(chainermn.MultiNodeChainList):

                def __init__(self, comm):
                    super(Model1, self).__init__(comm)
                    self.add_link(MLP(2000, 500, 100), rank_in=0, rank_out=0)


        ``Model0`` is expected to be on rank=0, and ``Model1`` is expected to
        be on rank=1. The first ``MLP`` in ``Model0`` will send its outputs
        to ``Model1``, then ``MLP`` in ``Model1`` will receive it and send
        its outputs to the second ``MLP`` in ``Model0``.

    Args:
        comm (chainermn.communicators._base.CommunicatorBase):
            ChainerMN communicator.
    """

    def __init__(self, comm):
        chainer.utils.experimental('chainermn.MultiNodeChainList')
        super(MultiNodeChainList, self).__init__()
        self._comm = comm
        self._rank_inouts = []

    def add_link(self, link, rank_in=None, rank_out=None):
        """Register one connected link with its inout rank.

        Args:
            link (chainer.Link): The link object to be registered.
            rank_in (int or list):
                Ranks from which it receives data. If None is specified,
                the model does not receive from any machines.
            rank_out (int or list):
                Ranks to which it sends data. If None is specified,
                the model will not send to any machine.
        """
        super(MultiNodeChainList, self).add_link(link)
        if isinstance(rank_in, int):
            rank_in = [rank_in]
        if isinstance(rank_out, int):
            rank_out = [rank_out]

        assert rank_in is None or self._comm.rank not in rank_in,\
            "cannot specify self rank for rank_in"
        assert rank_out is None or self._comm.rank not in rank_out,\
            "cannot specify self rank for rank_out"

        self._rank_inouts.append((rank_in, rank_out))

    def __call__(self, *inputs):
        y = None
        backward_pointer = None

        for f, (rank_in, rank_out) in zip(self._children, self._rank_inouts):
            x = None

            if rank_in is None:
                x = f(*inputs)
            else:
                # Preprocess: receiving inputs from the other machine.
                for _rank_in in rank_in:
                    _x = chainermn.functions.recv(
                        self._comm,
                        rank=_rank_in,
                        backward_pointer=backward_pointer,
                        device=self._device_id)

                    # Guarantee the backward path to the previous graph
                    # component to be executed in the last to avoid dead-lock.
                    if backward_pointer is not None and _x.creator is not None:
                        _x.creator.rank = -1

                    x = _x if x is None else x + _x

                    # Prevent "double-backwarding," i.e., backprop
                    # the same edge more than twice.
                    backward_pointer = None

                # Actual forward.
                x = f(x)

            if rank_out is None:
                assert y is None, "MultiNodeChainList cannot have more than "\
                    "two computational graph component whose rank_out is None"
                y = x  # model output
                backward_pointer = y
            else:
                for _rank_out in rank_out:
                    backward_pointer = chainermn.functions.send(
                        x, self._comm,
                        rank=_rank_out,
                        backward_pointer=backward_pointer)

        # Return.
        if y is backward_pointer:
            # The last computational graph component returns model output.
            return y
        elif y is not None:
            # The intermediate graph component returns model output.
            return chainermn.functions.point_to_point_communication.merge(
                backward_pointer, y.data)
        else:
            # Do not have any model output.
            return backward_pointer
