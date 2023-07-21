import * as  env from 'env-var';
import path from 'path';

export const org: string = env.get('ORG').required().asString();
export const mspID: string = env.get('MSP_ID').default(`${org}MSP`).asString();

export const certPath: string = path.resolve(env.get('CERT_PATH').required().asString());
export const keyPath: string = path.resolve(env.get('KEY_DIRECTORY_PATH').required().asString());
export const tlsCertPath: string = path.resolve(env.get('TLS_CERT_PATH').required().asString());

export const peerHost: string = env.get('HOST').required().asString();
export const peerHostAlias: string = env.get('PEER_HOST_ALIAS').required().asString();
export const port: number = env.get('PORT').required().asPortNumber();
export const peerEndpoint = `${peerHost}:${port}`

export const channelName: string = env.get('CHANNEL_NAME').default('fedlearn').asString();

export const expressPort: number = env.get('EXPRESS_PORT').required().asPortNumber()
