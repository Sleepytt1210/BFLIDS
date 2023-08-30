import { Contract, Info, Transaction, Context, Returns } from "fabric-contract-api"
import stringify from "json-stringify-deterministic"
import sortKeysRecursive from "sort-keys-recursive"
import { ThresholdExistsError, ThresholdNotFoundError } from './errors'
import { AccuracyT } from "./AccuracyT"

const THRESHOLD_ID = '1'

@Info({title: "Accuracy Threshold", description: "Smart Contract to store the accuracy threshold allowed from the highest global accuracy."})
export class AccuracyThreshold extends Contract {
    
    constructor() {
        super('AccuracyThreshold')
    }

    @Transaction()
    public async InitLedger(ctx: Context): Promise<void> {
        if (ctx.clientIdentity.assertAttributeValue("verifier", "false")) {
            throw Error(`Identity ${ctx.clientIdentity.getID()} is not authorised to perform this action!`)
        }
    
        const exists = await this.ThresholdExists(ctx);

        if(exists) {
            throw new ThresholdExistsError(`The threshold ${THRESHOLD_ID} already exist!`)
        } 

        const threshold: AccuracyT = {
                ID: THRESHOLD_ID,
                Requestor: this.GetOwnerNameFromCtx(ctx),
                Threshold: 4
            }

        threshold.docType = 'accuracyT';
        await ctx.stub.putState(threshold.ID, Buffer.from(stringify(sortKeysRecursive(threshold))));
        console.info(`Threshold ${threshold.ID} initialized`);
    }

    @Transaction(false)
    public async ReadThreshold(ctx: Context) {
        const cpJSON = await ctx.stub.getState(THRESHOLD_ID);
        if (!cpJSON || cpJSON.length == 0){
            throw new Error(`Error retrieving threshold ID ${THRESHOLD_ID}`)
        }

        return cpJSON.toString()
    }

    @Transaction()
    public async UpdateThreshold(ctx: Context, threshold_val: number) {
        if (ctx.clientIdentity.assertAttributeValue("verifier", "false")) {
            throw Error(`Identity ${ctx.clientIdentity.getID()} is not authorised to perform this action!`)
        }
        
        const exists = await this.ThresholdExists(ctx);

        if(!exists) {
            throw new ThresholdNotFoundError(`The threshold ${THRESHOLD_ID} does not exist!`)
        }

        const threshold: AccuracyT = {
            ID: THRESHOLD_ID,
            Requestor: this.GetOwnerNameFromCtx(ctx),
            Threshold: threshold_val
        }

        await ctx.stub.putState(THRESHOLD_ID, Buffer.from(stringify(sortKeysRecursive(threshold))))

    }

    @Transaction(false)
    @Returns('boolean')
    public async ThresholdExists(ctx: Context) {
        const cpJSON = await ctx.stub.getState(THRESHOLD_ID);
        return cpJSON && cpJSON.length > 0;
    }

    @Transaction(false)
    @Returns('string')
    public async GetThresholdHistories(ctx: Context) {
        const allResults: any[] = []

        const iterator = await ctx.stub.getHistoryForKey(THRESHOLD_ID);
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

    @Transaction(false)
	public GetOwnerNameFromCtx(ctx: Context): string {
		return (
			ctx.clientIdentity.getMSPID() +
			ctx.clientIdentity.getID().substring(ctx.clientIdentity.getID().indexOf("::"))
		);
	}

}
