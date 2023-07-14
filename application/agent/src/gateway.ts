/*
 * Copyright IBM Corp. All Rights Reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import * as grpc from '@grpc/grpc-js';
import { connect, Contract, Gateway, Network, Identity, Signer, signers } from '@hyperledger/fabric-gateway';
import * as crypto from 'crypto';
import { promises as fs } from 'fs';
import * as path from 'path';
import { TextDecoder } from 'util';
import { ConnectionProfile, ClientProfile } from './gatewayOptions'

const utf8Decoder = new TextDecoder();

async function newGrpcConnection(tlsCertPath: string, peerEndpoint: string, peerHostAlias: string): Promise<grpc.Client> {
    const tlsRootCert = await fs.readFile(tlsCertPath);
    const tlsCredentials = grpc.credentials.createSsl(tlsRootCert);
    return new grpc.Client(peerEndpoint, tlsCredentials, {
        'grpc.ssl_target_name_override': peerHostAlias,
    });
}

async function newIdentity(mspId: string, certPath: string): Promise<Identity> {
    const credentials = await fs.readFile(certPath);
    return { mspId, credentials };
}

async function newSigner(keyDirectoryPath: string): Promise<Signer> {
    const files = await fs.readdir(keyDirectoryPath);
    const keyPath = path.resolve(keyDirectoryPath, files[0]);
    const privateKeyPem = await fs.readFile(keyPath);
    const privateKey = crypto.createPrivateKey(privateKeyPem);
    return signers.newPrivateKeySigner(privateKey);
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
export async function getAllmodels(contract: Contract): Promise<void> {
    console.log('\n--> Evaluate Transaction: GetAllmodels, function returns all the current models on the ledger');

    const resultBytes = await contract.evaluateTransaction('GetAllmodels');

    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    console.log('*** Result:', result);
}

/**
 * Submit a transaction synchronously, blocking until it has been committed to the ledger.
 */
export async function createModel(contract: Contract, id: string, hash: string, url: string, owner: string, round: number, accuracy: number, loss: number): Promise<void> {
    console.log('\n--> Submit Transaction: CreateModel, creates new model with ID, Color, Hash, URL, Owner, Round, Accuracy and Loss arguments');

    await contract.submitTransaction(
        'CreateModel',
        id,
        hash,
        url,
        owner,
        round,
        accuracy,
        loss
    );

    console.log('*** Transaction committed successfully');
}

export async function readModelByID(contract: Contract): Promise<any> {
    console.log('\n--> Evaluate Transaction: Readmodel, function returns model attributes');

    const resultBytes = await contract.evaluateTransaction('ReadModel', modelId);

    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    return result;
}

/**
 * submitTransaction() will throw an error containing details of any error responses from the smart contract.
 */
async function updateNonExistentmodel(contract: Contract): Promise<void>{
    console.log('\n--> Submit Transaction: Updatemodel model70, model70 does not exist and should return an error');

    try {
        await contract.submitTransaction(
            'Updatemodel',
            'model70',
            'blue',
            '5',
            'Tomoko',
            '300',
        );
        console.log('******** FAILED to return an error');
    } catch (error) {
        console.log('*** Successfully caught the error: \n', error);
    }
}

export const getNetwork = async (gateway: Gateway, channelName: string) => {
    const network = await gateway.getNetwork(channelName);
    return network;
}

export const getContract = async (network: Network, chaincodeName: string) => {
    const contract = await network.getContract(chaincodeName);
    return contract;
}

export const getGateway = async (connectionProfile: ConnectionProfile, clientProfile: ClientProfile) => {
    const client = await newGrpcConnection(connectionProfile.tlsCertPath, clientProfile.peerEndpoint, clientProfile.peerHostAlias);

    const gateway = connect({
        client,
        identity: await newIdentity(clientProfile.mspId, connectionProfile.certPath),
        signer: await newSigner(connectionProfile.keyPath),
        // Default timeouts for different gRPC calls
        evaluateOptions: () => {
            return { deadline: Date.now() + 5000 }; // 5 seconds
        },
        endorseOptions: () => {
            return { deadline: Date.now() + 15000 }; // 15 seconds
        },
        submitOptions: () => {
            return { deadline: Date.now() + 5000 }; // 5 seconds
        },
        commitStatusOptions: () => {
            return { deadline: Date.now() + 60000 }; // 1 minute
        },
    });

    return gateway;
}