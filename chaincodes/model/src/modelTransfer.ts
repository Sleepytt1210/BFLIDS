import { Contract, Info, Transaction, Context, Returns } from "fabric-contract-api"
import stringify from "json-stringify-deterministic"
import sortKeysRecursive from "sort-keys-recursive"
import { Model } from "./model"
import { ModelNotFoundError, ModelExistsError } from './errors'

@Info({title: "Model Transfer", description: "Exchange model"})
export class ModelTransferContract extends Contract {
    
    @Transaction()
    public async InitLedger(ctx: Context): Promise<void> {
        const models: Model[] = [
            {
                "ID": "01H4FSMAHZW9VGYZFVFNKK7VJH",
                "URL": "https://ipfs.com/?query=7b3ca5f2f5870bca98265e9d8bd4e87f4dfe006b480be2fe7606ac8b7a87bbd0",
                "Hash": "7b3ca5f2f5870bca98265e9d8bd4e87f4dfe006b480be2fe7606ac8b7a87bbd0",
                "Owner": "CS.manchester.ac.uk",
                "Round": 1,
                "Accuracy": 97.6,
                "Loss": 0.07
            }

        ]

        for (const model of models) {
            model.docType = 'model';
            // example of how to write to world state deterministically
            // use convetion of alphabetic order
            // we insert data in alphabetic order using 'json-stringify-deterministic' and 'sort-keys-recursive'
            // when retrieving data, in any lang, the order of data will be the same and consequently also the corresonding hash
            await ctx.stub.putState(model.ID, Buffer.from(stringify(sortKeysRecursive(model))));
            console.info(`Asset ${model.ID} initialized`);
        }
    }

    @Transaction()
    public async CreateModel(ctx: Context, id: string, hash: string, url: string, owner: string, round: number, accuracy: number, loss: number) {
        const exists = await this.ModelExists(ctx, id);

        if(exists) {
            throw new ModelExistsError(`The model ${id} already exists!`)
        }

        const model: Model = {
            ID: id,
            Hash: hash,
            URL: url,
            Owner: owner,
            Round: round,
            Accuracy: accuracy,
            Loss: loss
        }

        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(model))))
    
    }

    @Transaction(false)
    public async ReadModel(ctx: Context, id: string) {
        const modelJSON = await ctx.stub.getState(id);
        if (!modelJSON || modelJSON.length == 0){
            throw new ModelNotFoundError(`The asset ${id} does not exist!`)
        }

        return modelJSON.toString()
    }

    @Transaction()
    public async UpdateModel(ctx: Context, id: string, hash: string, url: string, owner: string, round: number, accuracy: number, loss: number) {
        const exists = await this.ModelExists(ctx, id);

        if(!exists) {
            throw new ModelNotFoundError(`The model ${id} does not exist!`)
        }

        const model: Model = {
            ID: id,
            Hash: hash,
            URL: url,
            Owner: owner,
            Round: round,
            Accuracy: accuracy,
            Loss: loss
        }

        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(model))))

    }

    @Transaction()
    public async DeleteModel(ctx: Context, id: string) {
        const exists = this.ModelExists(ctx, id);
        if(!exists) {
            throw new ModelNotFoundError(`The model ${id} does not exist!`)
        }

        await ctx.stub.deleteState(id);
    }

    @Transaction(false)
    @Returns('boolean')
    public async ModelExists(ctx: Context, id: string) {
        const modelJSON = await ctx.stub.getState(id);
        return modelJSON && modelJSON.length > 0;
    }

    @Transaction(false)
    @Returns('string')
    public async GetAllModel(ctx: Context) {
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
