import express, { Request, Response } from 'express';
import * as config from '../utils/config'
import { Contract, Gateway, Network } from '@hyperledger/fabric-gateway';
import { getContract, getNetwork, getGateway, createCheckpoint, readCheckpointByID } from './gateway';
import { ClientProfile, ConnectionProfile } from './gatewayOptions';
import { getReasonPhrase, StatusCodes } from 'http-status-codes';
import { CheckpointNotFoundError, handleError } from './errors';
import { RequestArgs } from './interface';

const main = async () => {
    const router = express();
    router.use(express.json())

    const { OK, ACCEPTED, BAD_REQUEST, INTERNAL_SERVER_ERROR, NOT_FOUND } = StatusCodes

    router.post('/transactions/checkpoint/create', async (req: Request, resp: Response) => {

        try {
            console.log(req.body)
            const {channelName, chaincodeName, contractName, client, checkpointData} = req.body as RequestArgs;
            console.log(`Creating new checkpoint with args ${JSON.stringify(checkpointData)} from client ${client}`);
            
            const {gateway, network, contract} = await setupConnection(channelName, chaincodeName, contractName);
            isConnected(gateway, network, contract);
            console.log("Gateway connection is setup.")
            await createCheckpoint(contract, checkpointData.id, checkpointData.hash, checkpointData.url, checkpointData.owner, checkpointData.algorithm, checkpointData.cAccuracy, checkpointData.loss, checkpointData.round);
            return resp.status(ACCEPTED).json({
                status: getReasonPhrase(ACCEPTED),
                modelID: checkpointData.id,
                timestamp: new Date().toISOString()
            });
        } catch (err) {
            console.error(err);
            const parsedErr = handleError(err);
            if (parsedErr instanceof CheckpointNotFoundError) {
                return resp.status(BAD_REQUEST).json({
                    status: getReasonPhrase(BAD_REQUEST),
                    timestamp: new Date().toISOString()
                })
            }

            if (String(err.message).includes('Conversion')) {
                return resp.status(BAD_REQUEST).json({
                    status: getReasonPhrase(BAD_REQUEST),
                    reason: 'Invalid arguments!',
                    timestamp: new Date().toISOString()
                })
            }

            return resp.status(INTERNAL_SERVER_ERROR).json({
                status: getReasonPhrase(INTERNAL_SERVER_ERROR),
                details: `${err.name}: ${err.message}`,
                timestamp: new Date().toISOString()
            })
        }
    })

    router.get('/transactions/checkpoint/query/:cpID', async (req: Request, resp: Response) => {
        const cpID = req.params.cpID;
        const channelName = req.query.chn as string;
        const chaincodeName = req.query.ccn as string;
        const contractName = req.query.ctn as string;
        const clientID = req.query.clID as string;
    
        console.log(`Requesting checkpoint ${cpID} of client ${clientID}`);

        try {
            const {gateway, network, contract} = await setupConnection(channelName, chaincodeName, contractName);
            isConnected(gateway, network, contract);
            const data = await readCheckpointByID(contract, cpID);
            resp.status(OK).json(data);
        } catch (err) {
            console.error(err);
            const parsedErr = handleError(err);
            if (parsedErr instanceof CheckpointNotFoundError) {
                return resp.status(NOT_FOUND).json({
                    status: getReasonPhrase(NOT_FOUND),
                    timestamp: new Date().toISOString()
                })
            }

            return resp.status(INTERNAL_SERVER_ERROR).json({
                status: getReasonPhrase(INTERNAL_SERVER_ERROR),
                details: err.message,
                timestamp: new Date().toISOString()
            })
        }
    })

    async function setupConnection(channelName: string, chaincodeName: string, contractName: string): Promise<{gateway: Gateway, network: Network, contract: Contract}> {
        const clientProfile: ClientProfile = {
            org: config.org,
            mspID: config.mspID,
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

        const gateway = await getGateway(connectionProfile, clientProfile);

        const network = await getNetwork(gateway, channelName);

        const contract = await getContract(network, chaincodeName, contractName);

        return {gateway: gateway, network: network, contract: contract}
    }

    function isConnected(gateway: Gateway, network: Network, contract: Contract) {
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

    router.listen(config.expressPort, () => {
        console.log(`Starting Fabric Rest API at localhost:${config.expressPort}`)
    })

}

main()