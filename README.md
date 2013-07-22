pyEPS
=====

## An LTE EPS Emulation ##
  - pyEPS is a Long Term Evolution (LTE) Evolved Packet System (EPS) Emulation software written in Python
  - The software implements the signalling procedures of LTE EPS.
  - The following nodes are implemented: UE, eNB, MME, SGW/PGW, and HSS
  - The initial goal is to implement the signaling procedures to enable a UE to login to an LTE system (LTE Initial Attach).
  - Additional procedures will be added as the project progresses.

  
## Overview ##
  - One objective of the project is to be educational 
      - to enable the developer to write code quickly and in a step wise fashion from specifications. Hence, the use of Python
      - to enable new enterants into LTE to understand the signalling procedures of LTE system: the messages passed, the paramters used and underlying state-transition logic.
      - to act as a software supplement for people wanting to understand 3GPP LTE Specifications.

## Software Overview ##
 - Each node is a software module that communicate using UDP sockets. 
 - The messages use simple Python dictionary. (ASN.1 encoding is not required).
 - The software consists of the following key directories:
     - *messages*: Describes the messages and the paramters used in the messages.
     - *nodes*: Contains the logic of each node (ue, enb, mme, hss, sgwpgw)
     - *procedures*: Contains logic for elementary procedures on a per-node basis.
     - *utils*: Most important directory containing the main procedures used for communication and state transition. `io.py` is the key file to look at.
