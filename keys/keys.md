# Keys Directory

This directory contains the private/public key pairs (`.pem` files) used by IPv8 peers for secure communication.

The `.pem` files are generated automatically when running the application and are gitignored to prevent committing sensitive cryptographic material.

The keys are used to:

1. Uniquely identify peers in the network
2. Sign messages to prove authenticity
3. Enable encrypted communication between peers

Note: Never commit .pem files to version control. They should remain private to each peer.
