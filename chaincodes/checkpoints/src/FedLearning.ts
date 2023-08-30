import { Contract, Info, Transaction, Context, Returns, Param } from "fabric-contract-api";
import stringify from "json-stringify-deterministic";
import sortKeysRecursive from "sort-keys-recursive";
import { CheckpointNotFoundError, CheckpointExistsError, BadCheckpointError } from "./errors";
import { Checkpoint, CheckpointTypes } from "./Checkpoint";

export class LearningContract extends Contract {
	private _docType: CheckpointTypes;

	get docType() {
		return this._docType;
	}

	constructor(name?: string, docType?: CheckpointTypes) {
		super(name);
		this._docType = docType;
	}

	@Transaction()
	public async InitLedger(ctx: Context): Promise<void> {
		const logger = ctx.logging.getLogger(this.getName());
		logger.warn("Nothing to do, method InitLedger is not implemented.");
	}

	@Transaction()
	public async CreateCheckpoint(
		ctx: Context,
		id: string,
		hash: string,
		url: string,
		algorithm: string,
		cAccuracy: number,
		cLoss: number,
		round: number,
		fedSession: number
	) {
		this.ValidIdentity(ctx);

		const exists = await this.CheckpointExists(ctx, id);

		if (exists) {
			throw new CheckpointExistsError(`The checkpoint ${id} already exists!`);
		}

		const thresholdResult = await ctx.stub.invokeChaincode("accuracyT", ["ReadThreshold"], "fedlearn");
		const strValue = Buffer.from(thresholdResult.payload).toString("utf-8");
		const threshold = Number(JSON.parse(strValue)["Threshold"]);

		let oldHAccuracy: number = 0;

		if (this.docType == "globalCheckpoint") {
			const highestAccCp = await this.GetHighestAccCheckpoint(ctx, cAccuracy);
			if (highestAccCp && JSON.parse(highestAccCp)) oldHAccuracy = JSON.parse(highestAccCp)["HighestAccuracy"];

			if (cAccuracy < oldHAccuracy - threshold)
				throw new BadCheckpointError(
					`**Transaction REJECTED**! The current accuracy for this model (${cAccuracy}) 
					is lower than the tolerable value ${oldHAccuracy - threshold}`
				);
		}

		const newHAccuracy = Math.max(oldHAccuracy, cAccuracy);

		const checkpoint: Checkpoint = {
			ID: id,
			Hash: hash,
			URL: url,
			Owner: this.GetOwnerNameFromCtx(ctx),
			Algorithm: algorithm,
			HighestAccuracy: newHAccuracy,
			CurAccuracy: cAccuracy,
			Loss: cLoss,
			Round: round,
			FedSession: fedSession,
			docType: this._docType,
		};

		await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(checkpoint))));
	}

	@Transaction(false)
	public async ReadCheckpoint(ctx: Context, id: string): Promise<string> {
		const cpJSON = await ctx.stub.getState(id);
		if (!cpJSON || cpJSON.length == 0) {
			throw new CheckpointNotFoundError(`The checkpoint ${id} does not exist!`);
		}

		return cpJSON.toString();
	}

	@Transaction()
	public async UpdateCheckpoint(
		ctx: Context,
		id: string,
		hash: string,
		url: string,
		owner: string,
		algorithm: string,
		cAccuracy: number,
		cLoss: number,
		round: number,
		fedSession: number
	) {
		const exists = await this.CheckpointExists(ctx, id);

		if (!exists) {
			throw new CheckpointNotFoundError(`The checkpoint ${id} does not exist!`);
		}

		this.ValidIdentity(ctx, true, (JSON.parse(await this.ReadCheckpoint(ctx, id)) as Checkpoint).Owner);

		const thresholdResult = await ctx.stub.invokeChaincode("accuracyT", ["ReadThreshold"], "fedlearn");
		const strValue = Buffer.from(thresholdResult.payload).toString("utf-8");
		const threshold = Number(JSON.parse(strValue)["Threshold"]);

		let oldHAccuracy: number = 0;

		if (this.docType == "globalCheckpoint") {
			const highestAccCp = await this.GetHighestAccCheckpoint(ctx, cAccuracy);
			if (highestAccCp && JSON.parse(highestAccCp)) oldHAccuracy = JSON.parse(highestAccCp)["HighestAccuracy"];

			if (cAccuracy < oldHAccuracy - threshold)
				throw new BadCheckpointError(
					`**Transaction REJECTED**! The current accuracy for this model (${cAccuracy}) 
					is lower than the tolerable value ${oldHAccuracy - threshold}`
				);
		}

		const newHAccuracy = Math.max(oldHAccuracy, cAccuracy);

		const checkpoint: Checkpoint = {
			ID: id,
			URL: url,
			Hash: hash,
			Owner: owner,
			Algorithm: algorithm,
			HighestAccuracy: newHAccuracy,
			CurAccuracy: cAccuracy,
			Loss: cLoss,
			Round: round,
			FedSession: fedSession,
			docType: this._docType,
		};

		await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(checkpoint))));
	}

	@Transaction()
	public async DeleteCheckpoint(ctx: Context, id: string) {
		this.ValidIdentity(ctx, true, (JSON.parse(await this.ReadCheckpoint(ctx, id)) as Checkpoint).Owner);
		const exists = this.CheckpointExists(ctx, id);
		if (!exists) {
			throw new CheckpointNotFoundError(`The checkpoint ${id} does not exist!`);
		}

		await ctx.stub.deleteState(id);
	}

	@Transaction(false)
	@Returns("boolean")
	public async CheckpointExists(ctx: Context, id: string): Promise<boolean> {
		const cpJSON = await ctx.stub.getState(id);
		return cpJSON && cpJSON.length > 0;
	}

	@Transaction(false)
	@Returns("string")
	public async GetAllCheckpoints(ctx: Context) {
		const iterator = await ctx.stub.getQueryResult(JSON.stringify({ selector: { docType: this.docType } }));
		const allResults: any[] = [];

		let result = await iterator.next();
		while (!result.done) {
			const strValue = Buffer.from(result.value.value.toString()).toString("utf8");
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

	@Transaction(true)
	public async DeleteAllCheckpoints(ctx: Context) {
		const iterator = await ctx.stub.getQueryResult(JSON.stringify({ selector: { docType: this.docType } }));
		const allResults: any[] = [];

		let result = await iterator.next();
		while (!result.done) {
			const strValue = Buffer.from(result.value.value.toString()).toString("utf8");
			let record;
			try {
				record = JSON.parse(strValue);
				await ctx.stub.deleteState(record["ID"]);
			} catch (err) {
				console.log(err);
			}
			result = await iterator.next();
		}
	}

	@Transaction(false)
	@Returns("string")
	public async QueryCheckpointsByOwner(ctx: Context, owner: string): Promise<string> {
		let queryString = {
			selector: {
				docType: this._docType,
				Owner: owner,
			},
		};

		return await this.GetQueryResultForQueryString(ctx, JSON.stringify(queryString));
	}

	@Transaction(false)
	public async GetLatestCheckpoint(ctx: Context) {
		const queryString = {
			selector: {
				docType: this._docType,
				FedSession: {
					$gt: null,
				},
				Round: {
					$gt: null,
				},
			},
			sort: [
				{
					FedSession: "desc",
				},
				{
					Round: "desc",
				},
			],
			limit: 1,
		};
		return await this.GetQueryResultForQueryString(ctx, JSON.stringify(queryString), 1);
	}

	@Transaction(false)
	public async GetHighestAccCheckpoint(ctx: Context, curAcc: number) {
		const queryString = {
			selector: {
				docType: this._docType,
				HighestAccuracy: {
					$gt: curAcc,
				},
			},
			sort: [
				{
					HighestAccuracy: "desc",
				},
			],
			limit: 1,
		};
		return await this.GetQueryResultForQueryString(ctx, JSON.stringify(queryString), 1);
	}

	@Transaction(false)
	private async GetQueryResultForQueryString(ctx: Context, queryString: string, limit?: number): Promise<string> {
		const iterator = await ctx.stub.getQueryResult(queryString);
		const allResults: any[] = [];

		let result = await iterator.next();
		while (!result.done) {
			const strValue = Buffer.from(result.value.value.toString()).toString("utf8");
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
		limit = limit || allResults.length;
		return JSON.stringify(allResults.length == 0 ? [] : limit == 1 ? allResults[0] : allResults.slice(0, limit));
	}

	@Transaction(false)
	public ValidIdentity(ctx: Context, requireOwner: boolean = false, ownerName?: string): void {
		if (!ctx.clientIdentity.assertAttributeValue("trainer", "true")) {
			throw Error(`Identity ${ctx.clientIdentity.getID()} is not authorised to perform this action!`);
		}
		if (this._docType == "globalCheckpoint" && !ctx.clientIdentity.assertAttributeValue("verifier", "true")) {
			throw Error(`Identity ${ctx.clientIdentity.getID()} is not authorised to perform this action!`);
		}

		if (requireOwner) {
			if (!ownerName) throw Error(`Owner's name to verify against was not provided!`);
			else if (ownerName != this.GetOwnerNameFromCtx(ctx))
				throw Error(`Identity ${ctx.clientIdentity.getID()} is not authorised to perform this action`);
		}
	}

	@Transaction(false)
	public GetOwnerNameFromCtx(ctx: Context): string {
		return (
			ctx.clientIdentity.getMSPID() +
			ctx.clientIdentity.getID().substring(ctx.clientIdentity.getID().indexOf("::"))
		);
	}
}

@Info({
	title: "Global Learning",
	description: "Smart Contract to record the results of each round of global learning.",
})
export class GlobalLearningContract extends LearningContract {
	constructor() {
		super("GlobalLearningContract", "globalCheckpoint");
	}

	@Transaction()
	public async InitLedger(ctx: Context): Promise<void> {
		this.ValidIdentity(ctx);
		const checkpoints: Checkpoint[] = [
			{
				Algorithm: "BiLSTM",
				CurAccuracy: 81.85,
				FedSession: 1,
				Hash: "a71073aab977d93a350fa0f37e10ece715857e285091f0a3eb847836c1123723",
				HighestAccuracy: 81.85,
				ID: "gmodel_fs1_r1_a71073aab977d93a350fa0f37e10ece715857e285091f0a3eb847836c1123723",
				Loss: 0.874645,
				Owner:
					"Org1MSP::/C=US/ST=North Carolina/O=Hyperledger/OU=client/CN=user1::/C=UK/ST=Greater Manchester" +
					"/L=Manchester/O=org1.example.com/CN=ca.org1.example.com",
				Round: 1,
				URL: "/ipfs/QmaqHD8SwiM9accixFPutbNKxXtKVzp8NHxBrJ73Af2osp",
				docType: "globalCheckpoint",
			},
		];

		for (const checkpoint of checkpoints) {
			checkpoint.docType = super.docType;
			const exists = await this.CheckpointExists(ctx, checkpoint.ID);

			if (exists) {
				throw new CheckpointExistsError(`The checkpoint ${checkpoint.ID} already exists!`);
			}
			await ctx.stub.putState(checkpoint.ID, Buffer.from(stringify(sortKeysRecursive(checkpoint))));
			console.info(`Checkpoint ${checkpoint.ID} initialized`);
		}
	}
}

@Info({
	title: "Local Learning",
	description: "Smart Contract to record the results of each client's local learning.",
})
export class LocalLearningContract extends LearningContract {
	constructor() {
		super("LocalLearningContract", "localCheckpoint");
	}

	@Transaction()
	public async InitLedger(ctx: Context): Promise<void> {
		this.ValidIdentity(ctx);
		const checkpoints: Checkpoint[] = [
			{
				Algorithm: "BiLSTM",
				CurAccuracy: 0.924558,
				FedSession: 1,
				Hash: "5742110b0d45132f130be6f9495b2d6551851da58c7df305e2530f141025b0ae",
				HighestAccuracy: 0.924558,
				ID: "model_fs1_r1_c1_5742110b0d45132f130be6f9495b2d6551851da58c7df305e2530f141025b0ae",
				Loss: 0.154124,
				Owner: "Org1MSP::/C=US/ST=North Carolina/O=Hyperledger/OU=client/CN=user1::/C=UK/ST=Greater Manchester/L=Manchester/O=org1.example.com/CN=ca.org1.example.com",
				Round: 1,
				URL: "/ipfs/QmYiocQ6k2zoXwsRJGeFdZkZmFLJyfoubT2D6P3yqhvpyp",
				docType: "localCheckpoint",
			},
			{
				Algorithm: "BiLSTM",
				CurAccuracy: 0.965021,
				FedSession: 1,
				Hash: "61e69da40b818f2cd79dc88494b715f3356c8f3d0ea4f5adc0a5ad85084a00ef",
				HighestAccuracy: 0.965021,
				ID: "model_fs1_r1_c2_61e69da40b818f2cd79dc88494b715f3356c8f3d0ea4f5adc0a5ad85084a00ef",
				Loss: 0.088593,
				Owner: "Org2MSP::/C=US/ST=North Carolina/O=Hyperledger/OU=client/CN=user1::/C=UK/ST=Greater Manchester/L=Manchester/O=org2.example.com/CN=ca.org2.example.com",
				Round: 1,
				URL: "/ipfs/Qmc9V9t5zguQs6BAN9Y2PUsG1avuKoDufWUkaHffyrJWAj",
				docType: "localCheckpoint",
			},
			{
				Algorithm: "BiLSTM",
				CurAccuracy: 0.942616,
				FedSession: 1,
				Hash: "a0baf66faf2bdd39d276c05b8471f219815a5ab89a6de3fecf2b9dbea8170574",
				HighestAccuracy: 0.942616,
				ID: "model_fs1_r1_c3_a0baf66faf2bdd39d276c05b8471f219815a5ab89a6de3fecf2b9dbea8170574",
				Loss: 0.131221,
				Owner: "Org3MSP::/C=US/ST=North Carolina/O=Hyperledger/OU=client/CN=user1::/C=UK/ST=Greater Manchester/L=Manchester/O=org3.example.com/CN=ca.org3.example.com",
				Round: 1,
				URL: "/ipfs/QmdR634jkG8wgg9URb161YWWiT3KRDsXw1PDjQHrHgsubU",
				docType: "localCheckpoint",
			},
		];

		for (const checkpoint of checkpoints) {
			checkpoint.docType = super.docType;
			const exists = await this.CheckpointExists(ctx, checkpoint.ID);

			if (exists) {
				throw new CheckpointExistsError(`The checkpoint ${checkpoint.ID} already exists!`);
			}
			await ctx.stub.putState(checkpoint.ID, Buffer.from(stringify(sortKeysRecursive(checkpoint))));
			console.info(`Checkpoint ${checkpoint.ID} initialized`);
		}
	}
}
