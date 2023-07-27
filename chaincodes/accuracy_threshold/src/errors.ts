enum ErrorCode {
    BAD_REQUEST = "TH400",
    ASSET_NOT_FOUND = "TH404",
    EXISTS = "TH409",
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
 * implementation when a threshold already exists.
 */
export class ThresholdExistsError extends ContractError {
    constructor(message: string) {
        super(message, ErrorCode.EXISTS);
        Object.setPrototypeOf(this, ThresholdExistsError.prototype);

        this.name = 'ThresholdExistsError';
    }
}

/**
 * Represents the error which occurs in the local learning smart contract
 * implementation when a threshold does not exist.
 */
export class ThresholdNotFoundError extends ContractError {
    constructor(message: string) {
        super(message, ErrorCode.ASSET_NOT_FOUND);
        Object.setPrototypeOf(this, ThresholdNotFoundError.prototype);

        this.name = 'ThresholdNotFoundError';
    }
}
