export enum ErrorCode {
    CP_BAD_REQUEST = 'CP400',
    CP_NOT_FOUND = 'CP404',
    CP_EXISTS = 'CP409'
}

/**
 * Base type for errors from the smart contract.
 *
 */
export class ContractError extends Error {
    transactionId: string;

    constructor(message: string) {
        super(message);
        Object.setPrototypeOf(this, ContractError.prototype);

        this.name = 'TransactionError';
    }
}

/**
 * Represents the error which occurs when the transaction being submitted or
 * evaluated is not implemented in a smart contract.
 */
export class TransactionNotFoundError extends ContractError {
    constructor(message: string) {
        super(message);
        Object.setPrototypeOf(this, TransactionNotFoundError.prototype);

        this.name = 'TransactionNotFoundError';
    }
}

/**
 * Represents the error which occurs in the learning smart contract
 * implementation when a checkpoint already exists.
 */
export class CheckpointExistsError extends ContractError {
    constructor(message: string) {
        super(message);
        Object.setPrototypeOf(this, CheckpointExistsError.prototype);

        this.name = 'CheckpointExistsError';
    }
}

/**
 * Represents the error which occurs in the learning smart contract
 * implementation when a checkpoint does not exist.
 */
export class CheckpointNotFoundError extends ContractError {
    constructor(message: string) {
        super(message);
        Object.setPrototypeOf(this, CheckpointNotFoundError.prototype);

        this.name = 'CheckpointNotFoundError';
    }
}

/**
 * Represents the error which occurs in the local learning smart contract
 * implementation when a checkpoint submitted is unacceptable.
 */
export class BadCheckpointError extends ContractError {
    constructor(message: string) {
        super(message);
        Object.setPrototypeOf(this, CheckpointNotFoundError.prototype);

        this.name = 'BadCheckpointError';
    }
}


export const handleError = (e: Error) => {
    const msg = e.message;
    if (msg.startsWith(ErrorCode.CP_NOT_FOUND)) {
        return new CheckpointNotFoundError(msg);
    } else if (msg.startsWith(ErrorCode.CP_EXISTS)) {
        return new CheckpointExistsError(msg);
    } else if (msg.startsWith(ErrorCode.CP_BAD_REQUEST)) {
        return new BadCheckpointError(msg)
    }

    return e;
} 
