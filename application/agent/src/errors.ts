export enum ErrorCode {
    BAD_REQUEST = 'TR400',
    ASSET_NOT_FOUND = 'TR404',
    EXISTS = 'TR409',
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

export const handleError = (e: Error) => {
    const msg = e.message;
    if (msg.startsWith(ErrorCode.ASSET_NOT_FOUND)) {
        return new ModelNotFoundError(msg);
    } else if (msg.startsWith(ErrorCode.EXISTS)) {
        return new ModelExistsError(msg);
    } 

    return e;
} 
