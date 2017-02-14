import chainer.optimizer


class MultiNodeOptimizer(chainer.optimizer.Optimizer):

    # TODO(akiba): write why this class inherits Optimizer

    def __init__(self, actual_optimizer, communicator):
        super(MultiNodeOptimizer, self).__setattr__(
            'communicator', communicator)
        super(MultiNodeOptimizer, self).__setattr__(
            'actual_optimizer', actual_optimizer)

    def setup(self, link):
        self.actual_optimizer.setup(link)
        self.communicator.broadcast_data(link)

    def update(self, lossfun=None, *args, **kwds):
        if lossfun is not None:
            use_cleargrads = getattr(self, '_use_cleargrads', False)
            loss = lossfun(*args, **kwds)
            if use_cleargrads:
                self.target.cleargrads()
            else:
                self.target.zerograds()
            loss.backward()
            del loss

        self.communicator.allreduce_grad(self.actual_optimizer.target)
        self.actual_optimizer.update(None, *args, **kwds)

    def __getattr__(self, attr_name):
        return getattr(self.actual_optimizer, attr_name)

    def __setattr__(self, attr_name, value):
        setattr(self.actual_optimizer, attr_name, value)
