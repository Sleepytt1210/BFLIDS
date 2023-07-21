import { Object, Property } from "fabric-contract-api"

type CheckpointTypes = "checkpoint";

@Object()
export class Checkpoint{
    @Property()
    public docType?: CheckpointTypes = "checkpoint";

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
}