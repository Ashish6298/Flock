# Known Limitations - Milestone A

As of Milestone A completion, the framework has the following boundaries:
1. **No Autodiscovery**: Nodes cannot dynamically find each other. Senders must explicitly know the `NodeInfo` (host/port) of target nodes.
2. **Local Loopback Verification Only**: All tests run inside loopback (`127.0.0.1`). Cross-machine routing has not been validated.
3. **No Encryption/TLS**: Transport payload bytes are sent over cleartext TCP connections.
4. **No Cluster Consensus**: There is no concept of leader nodes, cluster members, or distributed consensus.
5. **No Task Scheduling or Queueing**: Distributing and executing background python tasks is not yet implemented.
