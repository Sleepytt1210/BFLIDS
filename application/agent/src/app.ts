import express, { Request, Response } from 'express';
import * as config from './utils/config'
import { Contract, Gateway, Network } from 'fabric-network';
import { getContract, getNetwork, getGateway, createCheckpoint, readCheckpointByID, getAllCheckpoints, getLatestCheckpoint } from './gateway';
import { ClientProfile, KeysProfile } from './gatewayOptions';
import { getReasonPhrase, StatusCodes } from 'http-status-codes';
import { CheckpointNotFoundError, handleError } from './errors';
import { RequestArgs } from './interface';

const main = async () => {
    const router = express();
    router.use(express.json())

    const { OK, ACCEPTED, BAD_REQUEST, INTERNAL_SERVER_ERROR, NOT_FOUND } = StatusCodes

    router.post('/transactions/checkpoint/create', async (req: Request, resp: Response) => {

        try {
            const {channelName, chaincodeName, contractName, clientName, checkpointData} = req.body as RequestArgs;
            console.log(`Creating new checkpoint with args ${JSON.stringify(checkpointData)} from client ${clientName}`);
            
            const {gateway, network, contract} = await setupConnection(clientName, channelName, chaincodeName, contractName);
            isConnected(gateway, network, contract);
            console.log('Gateway connection is setup.')
            await createCheckpoint(contract, checkpointData.id, checkpointData.hash, checkpointData.url, checkpointData.owner, checkpointData.algorithm, checkpointData.cAccuracy, checkpointData.loss, checkpointData.round, checkpointData.fedSession);
            return resp.status(ACCEPTED).json({
                status: {
                    code: ACCEPTED,
                    message: getReasonPhrase(ACCEPTED)
                },
                result: `Model ${checkpointData.id} created at ${contractName}`,
                timestamp: new Date().toISOString()
            });
        } catch (err) {
            console.error(err);
            const parsedErr = handleError(err);
            if (parsedErr instanceof CheckpointNotFoundError) {
                return resp.status(BAD_REQUEST).json({
                    status: {
                        code: BAD_REQUEST,
                        message: getReasonPhrase(BAD_REQUEST)
                    },
                    reason: `${err.name}: ${err.message}`,
                    details: err?.details || 'none',
                    timestamp: new Date().toISOString()
                })
            }

            if (String(err.message).includes('Conversion')) {
                return resp.status(BAD_REQUEST).json({
                    status: {
                        code: BAD_REQUEST,
                        message: getReasonPhrase(BAD_REQUEST)
                    },
                    reason: 'Invalid arguments!',
                    details: err?.details || 'none',
                    timestamp: new Date().toISOString()
                })
            }

            return resp.status(INTERNAL_SERVER_ERROR).json({
                status: {
                    code: INTERNAL_SERVER_ERROR,
                    message: getReasonPhrase(INTERNAL_SERVER_ERROR)
                },
                reason: `${err.name}: ${err.message}`,
                details: err?.details || 'none',
                timestamp: new Date().toISOString()
            })
        }
    })

    router.get('/query/checkpoint/:cpID', async (req: Request, resp: Response) => {
        const cpID = req.params.cpID;
        const channelName = req.query.chn as string;
        const chaincodeName = req.query.ccn as string;
        const contractName = req.query.ctn as string;
        const clientName = req.query.clID as string;
    
        console.log(`Requesting checkpoint ${cpID} by client ${clientName}`);

        try {
            const {gateway, network, contract} = await setupConnection(clientName, channelName, chaincodeName, contractName);
            isConnected(gateway, network, contract);
            let data; 
            switch (cpID) {
                case 'all':{
                    data = await getAllCheckpoints(contract);
                    break;
                }
                case 'latest':{
                    data = await getLatestCheckpoint(contract);
                    break;
                }
                case 'latestcheckpoint': {
                    data = await getLatestCheckpoint(contract);
                    break;
                }
                default:{
                    data = await readCheckpointByID(contract, cpID);
                    break;
                }
            } 
            return resp.status(OK).json({
                status: {
                    code: OK,
                    message: getReasonPhrase(OK)
                },
                result: data
            });
        } catch (err) {
            console.error(err);
            const parsedErr = handleError(err);
            if (parsedErr instanceof CheckpointNotFoundError) {
                return resp.status(NOT_FOUND).json({
                    status: {
                        code: NOT_FOUND,
                        message: getReasonPhrase(NOT_FOUND)
                    },
                    reason: `${err.name}: ${err.message}`,
                    details: err?.details || 'none',
                    timestamp: new Date().toISOString()
                })
            }

            return resp.status(INTERNAL_SERVER_ERROR).json({
                status: {
                    code: INTERNAL_SERVER_ERROR,
                    message: getReasonPhrase(INTERNAL_SERVER_ERROR)
                },
                reason: `${err.name}: ${err.message}`,
                details: err?.details || 'none',
                timestamp: new Date().toISOString()
            })
        }
    })

    router.get('/health', (req: Request, resp: Response) => {
        return resp.status(OK).json({
            status: {
                code: OK,
                message: getReasonPhrase(OK)
            }
        })
    })

    async function setupConnection(clientName: string, channelName: string, chaincodeName: string, contractName: string): Promise<{gateway: Gateway, network: Network, contract: Contract}> {
        const clientProfile: ClientProfile = config.getClientProfile(clientName)

        const keysProfile: KeysProfile = config.getKeysProfile(clientName) 

        const gateway = await getGateway(keysProfile, clientProfile);

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
        console.log(`Started Fabric Rest API at localhost:${config.expressPort}`)
    })

}

main()