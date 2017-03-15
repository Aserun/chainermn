def get_communicator(communicator_name='node_aware', *args, **kwargs):
    if communicator_name == 'naive':
        from chainermn.communicators.naive_communicator \
            import NaiveCommunicator
        return NaiveCommunicator(*args, **kwargs)
    elif communicator_name == 'hierarchical':
        from chainermn.communicators.hierarchical_communicator \
            import HierarchicalCommunicator
        return HierarchicalCommunicator(*args, **kwargs)
    elif communicator_name == 'single_node':
        from chainermn.communicators.single_node_communicator \
            import SingleNodeCommunicator
        return SingleNodeCommunicator(*args, **kwargs)
    else:
        raise ValueError(
            'Unrecognized communicator: "{}"'.format(communicator_name))
