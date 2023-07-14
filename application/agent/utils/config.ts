import * as  env from 'env-var';

export const org: string = env.get('ORG').required().asString();
export const mspId: string = env.get('MSP_ID').default(`${org}MSP`).asString();

export const certPath: string = env.get('CERT_PATH').required().asString();
export const keyPath: string = env.get('KEY_DIRECTORY_PATH').required().asString();
export const tlsCertPath: string = env.get('TLS_CERT_PATH').required().asString();

export const peerHost: string = env.get('HOST').required().asString();
export const peerHostAlias: string = env.get('PEER_HOST_ALIAS').required().asString();
export const port: number = env.get('PORT').required().asPortNumber();
export const peerEndpoint = `${peerHost}:${port}`

export const channelName: string = env.get('CHANNEL_NAME').default('fedlearn').asString();
export const chaincodeName: string = env.get('CHAINCODE_NAME').required().asString();

export const expressPort: number = env.get('EXPRESS_PORT').required().asPortNumber()
