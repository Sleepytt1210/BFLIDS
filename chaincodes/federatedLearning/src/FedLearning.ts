import { Contract, Info, Transaction, Context, Returns } from "fabric-contract-api"
import stringify from "json-stringify-deterministic"
import sortKeysRecursive from "sort-keys-recursive"
import { CheckpointNotFoundError, CheckpointExistsError } from './errors'
import { Checkpoint } from "./Checkpoint"

@Info({title: "Global Learning", description: "Smart Contract to record the results of each round of global learning."})
export class GlobalLearningContract extends Contract {
    
    constructor() {
        super('GlobalLearningContract')
    }

    @Transaction()
    public async InitLedger(ctx: Context): Promise<void> {
        const checkpoints: Checkpoint[] = [
            {
                "ID":"01H4FSMAHZW9VGYZFVFNKK7VJH",
                "URL":"https://ipfs.com/?query=7b3ca5f2f5870bca98265e9d8bd4e87f4dfe006b480be2fe7606ac8b7a87bbd0",
                "Hash":"7b3ca5f2f5870bca98265e9d8bd4e87f4dfe006b480be2fe7606ac8b7a87bbd0",
                "Owner": "CS.manchester.ac.uk",
                "Algorithm": "RandomForestClassifier",
                "HighestAccuracy": 97.6,
                "CurAccuracy": 97.6,
                "Loss": 0.003,
                "Round": 1
            }

        ]

        for (const checkpoint of checkpoints) {
            checkpoint.docType = 'checkpoint';
            await ctx.stub.putState(checkpoint.ID, Buffer.from(stringify(sortKeysRecursive(checkpoint))));
            console.info(`Asset ${checkpoint.ID} initialized`);
        }
    }

    @Transaction()
    public async CreateCheckpoint(ctx: Context, id: string, hash: string, url: string, owner: string, algorithm: string, cAccuracy: number, cLoss: number, round: number) {
        const exists = await this.CheckpointExists(ctx, id);

        if(exists) {
            throw new CheckpointExistsError(`The checkpoint ${id} already exists!`)
        }

        const allCheckpoints: Checkpoint[] = JSON.parse(await this.GetAllCheckpoints(ctx))
        const hAccuracy = allCheckpoints.reduce((max_acc, cur_max) => Math.max(max_acc, cur_max.HighestAccuracy), 0)        

        const checkpoint: Checkpoint = {
            ID: id,
            Hash: hash,
            URL: url,
            Owner: owner,
            Algorithm: algorithm,
            HighestAccuracy: hAccuracy,
            CurAccuracy: cAccuracy,
            Loss: cLoss,
            Round: round
        }

        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(checkpoint))))
    
    }

    @Transaction(false)
    public async ReadCheckpoint(ctx: Context, id: string) {
        const cpJSON = await ctx.stub.getState(id);
        if (!cpJSON || cpJSON.length == 0){
            throw new Error(`The checkpoint ${id} does not exist!`)
        }

        return cpJSON.toString()
    }

    @Transaction()
    public async UpdateCheckpoint(ctx: Context, id: string, hash: string, url: string, owner: string, algorithm: string, cAccuracy: number, cLoss: number, round: number) {
        const exists = await this.CheckpointExists(ctx, id);

        if(!exists) {
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
            Round: round
        }

        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(checkpoint))))

    }

    @Transaction()
    public async DeleteCheckpoint(ctx: Context, id: string) {
        const exists = this.CheckpointExists(ctx, id);
        if(!exists) {
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
        const allResults: any[] = []

        const iterator = await ctx.stub.getStateByRange('', '');
        let result = await iterator.next();
        while(!result.done) {
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
}

@Info({title: "Local Learning", description: "Smart Contract to record the results of each client's local learning."})
export class LocalLearningContract extends Contract {
    
    constructor() {
        super('LocalLearningContract')
    }

    @Transaction()
    public async InitLedger(ctx: Context): Promise<void> {
        const checkpoints: Checkpoint[] = [
            {
                "ID":"01H4FSMAHZW9VGYZFVFNKK7VJH",
                "URL":"https://ipfs.com/?query=7b3ca5f2f5870bca98265e9d8bd4e87f4dfe006b480be2fe7606ac8b7a87bbd0",
                "Hash":"7b3ca5f2f5870bca98265e9d8bd4e87f4dfe006b480be2fe7606ac8b7a87bbd0",
                "Owner": "CS.manchester.ac.uk",
                "Algorithm": "RandomForestClassifier",
                "HighestAccuracy": 97.6,
                "CurAccuracy": 97.6,
                "Loss": 0.003,
                "Round": 1
            }

        ]

        for (const checkpoint of checkpoints) {
            checkpoint.docType = 'checkpoint';
            await ctx.stub.putState(checkpoint.ID, Buffer.from(stringify(sortKeysRecursive(checkpoint))));
            console.info(`Asset ${checkpoint.ID} initialized`);
        }
    }

    @Transaction()
    public async CreateCheckpoint(ctx: Context, id: string, hash: string, url: string, owner: string, algorithm: string, cAccuracy: number, cLoss: number, round: number) {
        const exists = await this.CheckpointExists(ctx, id);

        if(exists) {
            throw new CheckpointExistsError(`The checkpoint ${id} already exists!`)
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
            Round: round
        }

        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(checkpoint))))
    
    }

    @Transaction(false)
    public async ReadCheckpoint(ctx: Context, id: string) {
        const cpJSON = await ctx.stub.getState(id);
        if (!cpJSON || cpJSON.length == 0){
            throw new Error(`The checkpoint ${id} does not exist!`)
        }

        return cpJSON.toString()
    }

    @Transaction()
    public async UpdateCheckpoint(ctx: Context, id: string, hash: string, url: string, owner: string, algorithm: string, cAccuracy: number, cLoss: number, round: number) {
        const exists = await this.CheckpointExists(ctx, id);

        if(!exists) {
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
            Round: round
        }

        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(checkpoint))))

    }

    @Transaction()
    public async DeleteCheckpoint(ctx: Context, id: string) {
        const exists = this.CheckpointExists(ctx, id);
        if(!exists) {
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
        const allResults: any[] = []

        const iterator = await ctx.stub.getStateByRange('', '');
        let result = await iterator.next();
        while(!result.done) {
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

}
