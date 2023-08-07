export interface KeysProfile {
    certPath: string;
    keyPath: string;
    tlsCertPath: string;
}

export interface ClientProfile {
    identity: string;
    mspID: string;
    peerHost: string;
    peerHostAlias: string;
    port: number;
    peerEndpoint: string;
    peerDomain: string;
}