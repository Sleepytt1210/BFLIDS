import express, { Request, Response } from 'express';
import * as config from '../utils/config'
import { Contract, Gateway, Network } from '@hyperledger/fabric-gateway';
import { getContract, getNetwork, getGateway, readModelByID, createModel } from './gateway';
import { ClientProfile, ConnectionProfile } from './gatewayOptions';
import { getReasonPhrase, StatusCodes } from 'http-status-codes';
import { ModelExistsError, ModelNotFoundError, handleError } from './errors';
import { ModelArgs } from './interface';

const main = async () => {
    const router = express();
    let gateway: Gateway, network: Network, contract: Contract;

    const { OK, ACCEPTED, BAD_REQUEST, INTERNAL_SERVER_ERROR, NOT_FOUND } = StatusCodes

    router.post('/transactions/create', async (req: Request, resp: Response) => {

        try {
            const args = req.body() as ModelArgs;
            console.log(`Creating new model with args ${args}`);
            
            await setupConnection();
            isConnected();
            await createModel(contract, args.id, args.hash, args.url, args.owner, args.round, args.accuracy, args.loss);
            return resp.status(ACCEPTED).json({
                status: getReasonPhrase(ACCEPTED),
                modelId: args.id,
                timestamp: new Date().toISOString()
            });
        } catch (err) {
            console.error(err);
            const parsedErr = handleError(err);
            if (parsedErr instanceof ModelExistsError) {
                return resp.status(BAD_REQUEST).json({
                    status: getReasonPhrase(BAD_REQUEST),
                    timestamp: new Date().toISOString()
                })
            }

            if (String(err.message).includes('Conversion')) {
                return resp.status(BAD_REQUEST).json({
                    status: getReasonPhrase(BAD_REQUEST),
                    reason: 'Invalid argmuments!',
                    timestamp: new Date().toISOString()
                })
            }

            return resp.status(INTERNAL_SERVER_ERROR).json({
                status: getReasonPhrase(INTERNAL_SERVER_ERROR),
                timestamp: new Date().toISOString()
            })
        }
    })

    router.get('/transactions/query/:modelId', async (req: Request, resp: Response) => {
        const modelId = req.params.modelId;
        console.log(`Requesting model ${modelId}`);

        try {
            await setupConnection();
            isConnected();
            const data = await readModelByID(contract);
            resp.status(OK).json(data);
        } catch (err) {
            console.error(err);
            const parsedErr = handleError(err);
            if (parsedErr instanceof ModelNotFoundError) {
                return resp.status(NOT_FOUND).json({
                    status: getReasonPhrase(NOT_FOUND),
                    timestamp: new Date().toISOString()
                })
            }

            return resp.status(INTERNAL_SERVER_ERROR).json({
                status: getReasonPhrase(INTERNAL_SERVER_ERROR),
                timestamp: new Date().toISOString()
            })
        }

        router.listen(config.expressPort, () => {
            console.log(`Starting Fabric Rest API at localhost:${config.expressPort}`)
        })
    })

    async function setupConnection() {
        const clientProfile: ClientProfile = {
            org: config.org,
            mspId: config.mspId,
            peerHost: config.peerHost,
            peerHostAlias: config.peerHostAlias,
            port: config.port,
            peerEndpoint: config.peerEndpoint
        }

        const connectionProfile: ConnectionProfile = {
            certPath: config.certPath,
            keyPath: config.keyPath,
            tlsCertPath: config.tlsCertPath
        }

        gateway = await getGateway(connectionProfile, clientProfile);

        network = await getNetwork(gateway, config.channelName);

        contract = await getContract(network, config.chaincodeName);
    }

    function isConnected() {
        if (!gateway) {
            throw new Error('Gateway is not connected!');
        }
        if (!network) {
            throw new Error('Channel is not connected!');
        }
        if (!contract) {
            throw new Error('Contract is not selected!');
        }
        return true;
    }

}