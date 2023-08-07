export interface CheckpointArgs {

    id: string;

    url: string;

    hash: string;

    algorithm: string;

    owner: string;

    round: string;

    cAccuracy: string;

    loss: string;

    fedSession: string;
}

export interface RequestArgs {
    channelName: string;
    
    chaincodeName: string;

    contractName: string;

    clientName: string;

    checkpointData: CheckpointArgs;
}