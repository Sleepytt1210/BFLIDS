export enum ErrorCode {
    MODEL_BAD_REQUEST = 'TR400',
    MODEL_NOT_FOUND = 'TR404',
    MODEL_EXISTS = 'TR409',
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
 * Represents the error which occurs in the basic asset transfer smart contract
 * implementation when an model already exists.
 */
export class ModelExistsError extends ContractError {
    constructor(message: string) {
        super(message);
        Object.setPrototypeOf(this, ModelExistsError.prototype);

        this.name = 'ModelExistsError';
    }
}

/**
 * Represents the error which occurs in the basic model transfer smart contract
 * implementation when an model does not exist.
 */
export class ModelNotFoundError extends ContractError {
    constructor(message: string) {
        super(message);
        Object.setPrototypeOf(this, ModelNotFoundError.prototype);

        this.name = 'ModelNotFoundError';
    }
}


/**
 * Represents the error which occurs in the local learning smart contract
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
 * Represents the error which occurs in the local learning smart contract
 * implementation when a checkpoint does not exist.
 */
export class CheckpointNotFoundError extends ContractError {
    constructor(message: string) {
        super(message);
        Object.setPrototypeOf(this, CheckpointNotFoundError.prototype);

        this.name = 'CheckpointNotFoundError';
    }
}


export const handleError = (e: Error) => {
    const msg = e.message;
    if (msg.startsWith(ErrorCode.MODEL_NOT_FOUND)) {
        return new ModelNotFoundError(msg);
    } else if (msg.startsWith(ErrorCode.MODEL_EXISTS)) {
        return new ModelExistsError(msg);
    } else if (msg.startsWith(ErrorCode.CP_NOT_FOUND)) {
        return new CheckpointNotFoundError(msg);
    } else if (msg.startsWith(ErrorCode.CP_EXISTS)) {
        return new CheckpointExistsError(msg);
    }

    return e;
} 
