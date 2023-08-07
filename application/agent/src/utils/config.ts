import * as  env from 'env-var';
import path from 'path';
import { promises as fs } from 'fs';
import { extractOrg, extractPeerDomain } from './utils';
import { ClientProfile, KeysProfile } from '../gatewayOptions';

export const getKeysProfile = (clientName: string): KeysProfile => {
    const peerDomain = extractPeerDomain(clientName)
    const cryptoPath = path.resolve(`../../network/organizations/peerOrganizations/${peerDomain}`)
    const KEY_DIRECTORY_PATH = path.join(cryptoPath, 'users', clientName, 'msp', 'keystore')
    const CERT_PATH = path.join(cryptoPath, 'users', clientName, 'msp', 'signcerts', 'cert.pem')
    const TLS_CERT_PATH = path.join(cryptoPath, 'peers', `peer0.${peerDomain}`, 'tls', 'ca.crt')
    return { keyPath: KEY_DIRECTORY_PATH, certPath: CERT_PATH, tlsCertPath: TLS_CERT_PATH }
}

export const getClientProfile = (clientName: string): ClientProfile => {
    const peerDomain = extractPeerDomain(clientName)
    const org = extractOrg(clientName)
    const mspID = org.charAt(0).toUpperCase() + org.substring(1) + "MSP"
    const peerHost = 'localhost'
    const port = 7051 + ((Number((org.match(/\d+/g)?.[0])) - 1) * 2000)
    const peerEndpoint = `${peerHost}:${port}`
    return { identity: clientName, mspID: mspID, peerHost: peerHost, port: port, peerEndpoint: peerEndpoint, peerDomain: peerDomain, peerHostAlias: `peer0.${peerDomain}` }
}

export const getConnectionProfile = async (peerDomain: string) => {
    const org = extractOrg(peerDomain)
    const connectionProfileFileName = path.resolve(`../../network/organizations/peerOrganizations/${peerDomain}/connection-${org}.json`)
    const connectionProfileJson = (await fs.readFile(connectionProfileFileName)).toString('utf-8');
    return JSON.parse(connectionProfileJson);
}


export const channelName: string = env.get('CHANNEL_NAME').default('fedlearn').asString();

export const expressPort: number = env.get('EXPRESS_PORT').required().asPortNumber()
