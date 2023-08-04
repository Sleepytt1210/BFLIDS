# BFLIDS
Blockchain-based Federated Learning Intrusion Detection (BFLIDS) is a collaborative IDS to detect attacks across foreign domains using federated learning. 

## Prerequisites
### Operating System
This project is to recommended to be run on **WSL2**.
To install **WSL2**, refer to [Windows guide](https://learn.microsoft.com/en-us/windows/wsl/install).

### Python packages
Install miniconda and start the terminal in a conda environment.

`pip install requirements.txt`

### IPFS Installation
- IPFS Kubo
```sh
cd ~/Downloads
wget https://dist.ipfs.tech/kubo/v0.21.0/kubo_v0.21.0_linux-amd64.tar.gz
tar -xvzf kubo_v0.21.0_linux-amd64.tar.gz
cd kubo
sudo bash install.sh
```
Test installation
```sh
ipfs --version
```
The default home path for ipfs is `~/.ipfs`

*Refer to the [official guide](https://docs.ipfs.tech/install/command-line/#system-requirements) for installation on other platforms.* 

### Local Swarm Key Setup
- Using Go

Install the following package
```sh 
go install github.com/Kubuxu/go-ipfs-swarm-key-gen/ipfs-swarm-key-gen
```
Run it and store the generated key to your IPFS path
```sh
`go env GOPATH`/bin/ipfs-swarm-key-gen > "~/.ipfs/swarm.key"
```
Any peer with the same key can now connect to you to form a private IPFS network.

### Node.js
```sh
cd ~/Downloads
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - &&\
sudo apt-get install -y nodejs
```

### Docker
Follow the [official instructions](https://docs.docker.com/get-docker/) to install Docker on your machine.

### Hyperledger Fabric

At the root working directory of this project (The same directory where this README.md) is located, run 
```sh
curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh && chmod +x install-fabric.sh

./install-fabric.sh --fabric-version 2.5.0 docker binary
```

#### CouchDB
CouchDB is a powerful database system that allows more complicated queries to be performed on world states of the ledger. It is recommended to install and enable CouchDB by specifying `ledger.state.stateDatabase = CouchDB` in [core.yaml](config/core.yaml).

The default address used by couchDB is `127.0.0.1:5984`.

#### jq \[Optional\]
This command is required to perform JSON operations in a Linux shell. The installation is very simple.
```sh

```


#### Others
Follow the instructions on Hyperledger Fabric Docs to install other tools if things are not working. Click (here)[https://hyperledger-fabric.readthedocs.io/en/latest/prereqs.html].

### Done
There we go, the prerequisites has been successfully setup!

## Configurations