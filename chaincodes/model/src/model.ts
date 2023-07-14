import { Object, Property } from "fabric-contract-api"

type ModelTypes = "model";

@Object()
export class Model{
    @Property()
    public docType?: ModelTypes = "model";

    @Property()
    public ID!: string;

    @Property()
    public URL!: string;

    @Property()
    public Hash!: string;

    @Property()
    public Owner: string;

    @Property()
    public Round: number;

    @Property()
    public Accuracy: number;

    @Property()
    public Loss: number;
}