.. module:: chainermn

API Reference
=============


Communicators
~~~~~~~~~~~~~

.. autofunction:: create_communicator


Links
~~~~~

.. autoclass:: MultiNodeChainGroup
    :members: add_link


Optimizers and Evaluators
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: create_multi_node_optimizer
.. autofunction:: create_multi_node_evaluator


Point-to-Point Communications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: chainermn.functions.send
.. autofunction:: chainermn.functions.recv


Dataset Utilities
~~~~~~~~~~~~~~~~~

.. autofunction:: scatter_dataset
.. autofunction:: chainermn.datasets.get_empty_dataset
