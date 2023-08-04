import { Object, Property } from "fabric-contract-api"

type CheckpointTypes = "localCheckpoint" | "globalCheckpoint";

@Object()
export class Checkpoint{
    @Property()
    public docType?: CheckpointTypes = "globalCheckpoint";

    @Property()
    public ID!: string;

    @Property()
    public Hash!: string;

    @Property()
    public URL!: string;

    @Property()
    public Owner: string;

    @Property()
    public Algorithm: string;

    @Property()
    public HighestAccuracy: number;

    @Property()
    public CurAccuracy: number;

    @Property()
    public Loss: number;

    @Property()
    public Round: number;

    @Property()
    public FedSession: number;
}