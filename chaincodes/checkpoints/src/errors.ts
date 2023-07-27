enum ErrorCode {
    BAD_REQUEST = "CP400",
    ASSET_NOT_FOUND = "CP404",
    EXISTS = "CP409",
}

/**
 * Base type for errors from the smart contract.
 *
 */
export class ContractError extends Error {
    transactionId: string;

    constructor(message: string, errorCode: string) {
        const codedMsg = `${errorCode}:${message}` 
        super(codedMsg);
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
        super(message, ErrorCode.BAD_REQUEST);
        Object.setPrototypeOf(this, TransactionNotFoundError.prototype);

        this.name = 'TransactionNotFoundError';
    }
}

/**
 * Represents the error which occurs in the local learning smart contract
 * implementation when a checkpoint already exists.
 */
export class CheckpointExistsError extends ContractError {
    constructor(message: string) {
        super(message, ErrorCode.EXISTS);
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
        super(message, ErrorCode.ASSET_NOT_FOUND);
        Object.setPrototypeOf(this, CheckpointNotFoundError.prototype);

        this.name = 'CheckpointNotFoundError';
    }
}
