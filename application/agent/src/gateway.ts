/*
 * Copyright IBM Corp. All Rights Reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { Gateway, Wallets, GatewayOptions, X509Identity, Network, Contract } from 'fabric-network';
import { promises as fs } from 'fs';
import * as path from 'path';
import { TextDecoder } from 'util';
import { KeysProfile, ClientProfile } from './gatewayOptions'
import { getConnectionProfile } from './utils/config';

const utf8Decoder = new TextDecoder();
const walletPath = path.resolve("./wallets")

async function newIdentity(mspId: string, certPath: string, keyDirectoryPath: string): Promise<X509Identity> {
    const files = await fs.readdir(keyDirectoryPath);
    const keyPath = path.resolve(keyDirectoryPath, files[0]);
    const privateKeyPem = await fs.readFile(keyPath);
    
    const identity: X509Identity = {
        credentials: {
            certificate: (await fs.readFile(certPath)).toString('utf-8'),
            privateKey: privateKeyPem.toString('utf-8'),
        },
        mspId: mspId,
        type: 'X.509',
    };
    return identity
}

/**
 * This type of transaction would typically only be run once by an application the first time it was started after its
 * initial deployment. A new version of the chaincode deployed later would likely not need to run an "init" function.
 */
export async function initLedger(contract: Contract): Promise<void> {
    console.log('\n--> Submit Transaction: InitLedger, function creates the initial set of models on the ledger');

    await contract.submitTransaction('InitLedger');

    console.log('*** Transaction committed successfully');
}

/**
 * Evaluate a transaction to query ledger state.
 */
export async function getAllCheckpoints(contract: Contract): Promise<void> {
    console.log('\n--> Evaluate Transaction: GetAllCheckpoints, function returns all the current checkpoints on the ledger');

    const resultBytes = await contract.evaluateTransaction('GetAllCheckpoints');

    const resultJson = resultBytes.toString('utf-8');
    const result = JSON.parse(resultJson);
    return result;
}

/**
 * Submit a transaction synchronously, blocking until it has been committed to the ledger.
 */
export async function createCheckpoint(contract: Contract, id: string, hash: string, url: string, owner: string, algorithm: string, cAccuracy: string, loss: string, round: string, fedSession: string): Promise<void> {
    console.log('\n--> Submit Transaction: CreateCheckpoint, creates new model with ID, Hash, URL, Owner, Algorithm, Current Accuracy, Loss, Round and FedSession arguments');

    await contract.submitTransaction(
        'CreateCheckpoint',
        id,
        hash,
        url,
        owner,
        algorithm,
        cAccuracy,
        loss,
        round,
        fedSession
    );

    console.log('*** Transaction committed successfully');
}

export async function readCheckpointByID(contract: Contract, id: string): Promise<any> {
    console.log('\n--> Evaluate Transaction: ReadCheckpoint, function returns checkpoint info of a client');

    const resultBytes = await contract.evaluateTransaction('ReadCheckpoint', id);

    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    return result;
}

export async function getLatestCheckpoint(contract: Contract): Promise<any> {
    console.log('\n--> Evaluate Transaction: GetLatestCheckpoint, function returns latest checkpoint info of a client');

    const resultBytes = await contract.evaluateTransaction('GetLatestCheckpoint');

    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    return result;
}


export const getNetwork = async (gateway: Gateway, channelName: string) => {
    const network = await gateway.getNetwork(channelName);
    return network;
}

export const getContract = async (network: Network, chaincodeName: string, contractName: string) => {
    const contract = await network.getContract(chaincodeName, contractName);
    return contract;
}

export const getGateway = async (keysProfile: KeysProfile, clientProfile: ClientProfile) => {
    
    const wallet = await Wallets.newFileSystemWallet(walletPath);
    const clientName = clientProfile.identity
    const connectionProfile = await getConnectionProfile(clientProfile.peerDomain)

    if (! (await wallet.get(clientName))) {
        await wallet.put(clientName, await newIdentity(clientProfile.mspID, keysProfile.certPath, keysProfile.keyPath))
    }

    const gatewayOptions: GatewayOptions = {
        identity: clientName,
        wallet,
    };

    const gateway = new Gateway();
    await gateway.connect(connectionProfile, gatewayOptions)

    return gateway;
}