Tips and FAQs
=============


Using MultiprocessIterator
~~~~~~~~~~~~~~~~~~~~~~~~~~
If you are using ``MultiprocessIterator`` and communication goes through InfiniBand,
you would probably face crash problems.
This is because ``MultiprocessIterator`` creates child processes by ``fork`` system call,
which has `problems with the design of MPI and InfiniBand <https://www.open-mpi.org/faq/?category=tuning#fork-warning>`_.
To cope with this issue, we can use ``multiprocessing.set_start_method``
to change the way to start child processes::

  multiprocessing.set_start_method('forkserver')

Both ``forkserver`` mode and ``spawn`` mode should work.
Please also refer to our ImageNet example, where ``MultiprocessIterator`` is used.


Using Your Own Evaluator
~~~~~~~~~~~~~~~~~~~~~~~~
Method ``create_multi_node_evaluator`` can also be used for customized evaluator classes
that inherits ``chainer.training.extensions.Evaluator``.
Specifically, it wraps ``evaluate`` method and returns the averaged values over all workers.
Please also refer to our ImageNet example, where a customized evaluator is used.


Using MPI4py Communicator
~~~~~~~~~~~~~~~~~~~~~~~~~
ChainerMN is based on MPI4py. For advanced users
(e.g., those who want to parallelize preprocessing, create custom extension, etc.),
we encourage to make use of MPI4py communicators.
Let ``comm`` be a ChainerMN communicator,
then you can obtain MPI4py communicator by ``comm.mpi_comm``.
Please refer to `MPI4py API reference <http://pythonhosted.org/mpi4py/apiref/mpi4py.MPI.Comm-class.html>`_.

Using FP16
~~~~~~~~~~
FP16 (16-bit half precision floating point) is not supported in ChainerMN as of now.

