import { Contract, Info, Transaction, Context, Returns, Param } from "fabric-contract-api"
import stringify from "json-stringify-deterministic"
import sortKeysRecursive from "sort-keys-recursive"
import { CheckpointNotFoundError, CheckpointExistsError, BadCheckpointError } from './errors'
import { Checkpoint } from "./Checkpoint"

class LearningContract extends Contract {

    private _docType: "localCheckpoint" | "globalCheckpoint";

    get docType() {
        return this._docType;
    }

    constructor(name?: string, docType?: "localCheckpoint" | "globalCheckpoint") {
        super(name)
        this._docType = docType
    }

    @Transaction()
    public async InitLedger(ctx: Context): Promise<void> {
        const logger = ctx.logging.getLogger(this.getName())
        logger.warn("Nothing to do, method InitLedger is not implemented.")
    }

    @Transaction()
    public async CreateCheckpoint(ctx: Context, id: string, hash: string, url: string, owner: string, algorithm: string, cAccuracy: number, cLoss: number, round: number, fedSession: number) {
        const exists = await this.CheckpointExists(ctx, id);

        if (exists) {
            throw new CheckpointExistsError(`The checkpoint ${id} already exists!`)
        }

        let newHAccuracy: number, oldHAccuracy: number = 0

        const latestCP = await this.GetHighestAccCheckpoint(ctx, cAccuracy)
        if (latestCP && JSON.parse(latestCP).length > 0)
            oldHAccuracy = JSON.parse(latestCP)[0].HighestAccuracy
        
        const thresholdResult = await ctx.stub.invokeChaincode("accuracyT", ["ReadThreshold"], "fedlearn")
        const strValue = Buffer.from(thresholdResult.payload).toString('utf-8')
        const threshold = Number(JSON.parse(strValue)['Threshold'])

        if (this._docType == 'globalCheckpoint' && cAccuracy < oldHAccuracy - threshold)
            throw new BadCheckpointError(`**Transaction REJECTED**! The current accuracy for this model (${cAccuracy}) is lower than the tolerable value ${oldHAccuracy - threshold}`)

        const checkpoint: Checkpoint = {
            ID: id,
            Hash: hash,
            URL: url,
            Owner: owner,
            Algorithm: algorithm,
            HighestAccuracy: newHAccuracy,
            CurAccuracy: cAccuracy,
            Loss: cLoss,
            Round: round,
            FedSession: fedSession,
            docType: this._docType
        }

        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(checkpoint))))

    }

    @Transaction(false)
    public async ReadCheckpoint(ctx: Context, id: string) {
        const cpJSON = await ctx.stub.getState(id);
        if (!cpJSON || cpJSON.length == 0) {
            throw new Error(`The checkpoint ${id} does not exist!`)
        }

        return cpJSON.toString()
    }

    @Transaction()
    public async UpdateCheckpoint(ctx: Context, id: string, hash: string, url: string, owner: string, algorithm: string, cAccuracy: number, cLoss: number, round: number, fedSession: number) {
        const exists = await this.CheckpointExists(ctx, id);

        if (!exists) {
            throw new CheckpointNotFoundError(`The checkpoint ${id} does not exist!`)
        }

        const allCheckpoints: Checkpoint[] = JSON.parse(await this.GetAllCheckpoints(ctx))
        const hAccuracy = allCheckpoints.reduce((max_acc, cur_max) => Math.max(max_acc, cur_max.HighestAccuracy), 0)

        const checkpoint: Checkpoint = {
            ID: id,
            URL: url,
            Hash: hash,
            Owner: owner,
            Algorithm: algorithm,
            HighestAccuracy: hAccuracy,
            CurAccuracy: cAccuracy,
            Loss: cLoss,
            Round: round,
            FedSession: fedSession,
            docType: this._docType
        }

        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(checkpoint))))

    }

    @Transaction()
    public async DeleteCheckpoint(ctx: Context, id: string) {
        const exists = this.CheckpointExists(ctx, id);
        if (!exists) {
            throw new CheckpointNotFoundError(`The checkpoint ${id} does not exist!`)
        }

        await ctx.stub.deleteState(id);
    }

    @Transaction(false)
    @Returns('boolean')
    public async CheckpointExists(ctx: Context, id: string) {
        const cpJSON = await ctx.stub.getState(id);
        return cpJSON && cpJSON.length > 0;
    }

    @Transaction(false)
    @Returns('string')
    public async GetAllCheckpoints(ctx: Context) {

        const iterator = await ctx.stub.getQueryResult(JSON.stringify({selector: {"docType": this.docType}}));
        const allResults: any[] = []

        let result = await iterator.next();
        while (!result.done) {
            const strValue = Buffer.from(result.value.value.toString()).toString('utf8');
            let record;
            try {
                record = JSON.parse(strValue);
            } catch (err) {
                console.log(err);
                record = strValue;
            }
            allResults.push(record);
            result = await iterator.next();
        }

        return JSON.stringify(allResults);
    }

    @Transaction(false)
    @Returns('string')
    public async QueryCheckpointsByOwner(ctx: Context, owner: string) {
        let queryString = {
            "selector": {
                "docType": this._docType,
                "Owner": owner
            }
        };

        return await this.GetQueryResultForQueryString(ctx, JSON.stringify(queryString)); //shim.success(queryResults);
    }

    @Transaction(false)
    public async GetLatestCheckpoint(ctx: Context) {
        const queryString = {
            "selector": {
               "docType":  this._docType,
               "FedSession": {
                  "$gt": null
               },
               "Round": {
                  "$gt": null
               }
            },
            "sort": [
               {
                  "FedSession": "desc"
               },
               {
                  "Round": "desc"
               }
            ],
            "limit": 1
         }
        return await this.GetQueryResultForQueryString(ctx, JSON.stringify(queryString), 1);
    }

    @Transaction(false)
    public async GetHighestAccCheckpoint(ctx: Context, curAcc: number) {
        const queryString = {
            "selector": {
               "docType": "globalCheckpoint",
               "HighestAccuracy": {
                  "$gt": curAcc
               }
            },
            "sort": [
               {
                  "HighestAccuracy": "desc"
               }
            ],
            "limit": 1
         }
        return await this.GetQueryResultForQueryString(ctx, JSON.stringify(queryString), 1);
    }


    @Transaction(false)
    private async GetQueryResultForQueryString(ctx: Context, queryString: string, limit?: number) {

        const iterator = await ctx.stub.getQueryResult(queryString);
        const allResults: any[] = []

        let result = await iterator.next();
        while(!result.done){
            const strValue = Buffer.from(result.value.value.toString()).toString('utf8');
            let record;
            try {
                record = JSON.parse(strValue);
            } catch (err) {
                console.log(err);
                record = strValue;
            }
            allResults.push(record);
            result = await iterator.next();
        }
        limit = limit || allResults.length
        return JSON.stringify(allResults.length == 0 ? [] : limit == 1 ? allResults[0] : allResults.slice(0, limit));
    }
}


@Info({ title: "Global Learning", description: "Smart Contract to record the results of each round of global learning." })
export class GlobalLearningContract extends LearningContract {

    constructor() {
        super('GlobalLearningContract', "globalCheckpoint")
    }

    public async InitLedger(ctx: Context): Promise<void> {
        const checkpoints: Checkpoint[] = [{
            "ID": "model_fs1_r1_75b9212074bee60e9876b53ffd170429187b51c493e2f19272a49caf327ac389",
            "URL": "/ipfs/QmR1X8CKFirUgZDHEUCVxmUvsUCwhonJqSrgCLEMzVKaGx",
            "Hash": "75b9212074bee60e9876b53ffd170429187b51c493e2f19272a49caf327ac389",
            "Owner": "org1.example.com",
            "Algorithm": "BiLSTM",
            "HighestAccuracy": 95.7,
            "CurAccuracy": 95.7,
            "Loss": 0.0015,
            "Round": 1,
            "FedSession": 1
          }, {
            "ID": "model_fs1_r2_da697d10927d9e0b4b7d6511d6fa0a2fe5bda146e4e9d819f27ede33b2477c84",
            "URL": "/ipfs/QmQ65etrCGR75uuKZpwD21cR1hAgDNnhmNFGiGcVjDhD75",
            "Hash": "da697d10927d9e0b4b7d6511d6fa0a2fe5bda146e4e9d819f27ede33b2477c84",
            "Owner": "org1.example.com",
            "Algorithm": "BiLSTM",
            "HighestAccuracy": 96.5,
            "CurAccuracy": 96.5,
            "Loss": 0.0009,
            "Round": 2,
            "FedSession": 1
          }, {
            "ID": "model_fs1_r3_80f298f00b4dc58a9ce9b5d8a400c03eeeb2fe82ad19b3c393dc8cc1a27d8327",
            "URL": "/ipfs/QmUzSm44TeR4TCFVi4k2yFU6wnidywaa8QTzTErZizEcLY",
            "Hash": "80f298f00b4dc58a9ce9b5d8a400c03eeeb2fe82ad19b3c393dc8cc1a27d8327",
            "Owner": "org1.example.com",
            "Algorithm": "BiLSTM",
            "HighestAccuracy": 97.6,
            "CurAccuracy": 97.6,
            "Loss": 0.0001,
            "Round": 3,
            "FedSession": 1
          }]

        for (const checkpoint of checkpoints) {
            checkpoint.docType = super.docType;
            await ctx.stub.putState(checkpoint.ID, Buffer.from(stringify(sortKeysRecursive(checkpoint))));
            console.info(`Asset ${checkpoint.ID} initialized`);
        }
    }

}

@Info({ title: "Local Learning", description: "Smart Contract to record the results of each client's local learning." })
export class LocalLearningContract extends LearningContract {

    constructor() {
        super("LocalLearningContract", "localCheckpoint")
    }

    public async InitLedger(ctx: Context): Promise<void> {
        const checkpoints: Checkpoint[] = [{
            "ID": "model_fs1_r1_75b9212074bee60e9876b53ffd170429187b51c493e2f19272a49caf327ac389",
            "URL": "/ipfs/QmR1X8CKFirUgZDHEUCVxmUvsUCwhonJqSrgCLEMzVKaGx",
            "Hash": "75b9212074bee60e9876b53ffd170429187b51c493e2f19272a49caf327ac389",
            "Owner": "org2.example.com",
            "Algorithm": "BiLSTM",
            "HighestAccuracy": 95.7,
            "CurAccuracy": 95.7,
            "Loss": 0.0015,
            "Round": 1,
            "FedSession": 1
          }, {
            "ID": "model_fs1_r2_da697d10927d9e0b4b7d6511d6fa0a2fe5bda146e4e9d819f27ede33b2477c84",
            "URL": "/ipfs/QmQ65etrCGR75uuKZpwD21cR1hAgDNnhmNFGiGcVjDhD75",
            "Hash": "da697d10927d9e0b4b7d6511d6fa0a2fe5bda146e4e9d819f27ede33b2477c84",
            "Owner": "org1.example.com",
            "Algorithm": "BiLSTM",
            "HighestAccuracy": 96.5,
            "CurAccuracy": 96.5,
            "Loss": 0.0009,
            "Round": 2,
            "FedSession": 1
          }, {
            "ID": "model_fs1_r3_80f298f00b4dc58a9ce9b5d8a400c03eeeb2fe82ad19b3c393dc8cc1a27d8327",
            "URL": "/ipfs/QmUzSm44TeR4TCFVi4k2yFU6wnidywaa8QTzTErZizEcLY",
            "Hash": "80f298f00b4dc58a9ce9b5d8a400c03eeeb2fe82ad19b3c393dc8cc1a27d8327",
            "Owner": "org1.example.com",
            "Algorithm": "BiLSTM",
            "HighestAccuracy": 97.6,
            "CurAccuracy": 97.6,
            "Loss": 0.0001,
            "Round": 3,
            "FedSession": 1
          }]

        for (const checkpoint of checkpoints) {
            checkpoint.docType = super.docType;
            await ctx.stub.putState(checkpoint.ID, Buffer.from(stringify(sortKeysRecursive(checkpoint))));
            console.info(`Asset ${checkpoint.ID} initialized`);
        }
    }
}
