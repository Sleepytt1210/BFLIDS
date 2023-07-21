export interface ConnectionProfile {
    certPath: string;
    keyPath: string;
    tlsCertPath: string;
}

export interface ClientProfile {
    org: string;
    mspID: string;
    peerHost: string;
    peerHostAlias: string;
    port: number;
    peerEndpoint: string;
}