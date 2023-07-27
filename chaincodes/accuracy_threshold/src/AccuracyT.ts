import { Object, Property } from "fabric-contract-api"

type AccuracyTTypes = "accuracyT";

@Object()
export class AccuracyT{
    @Property()
    public docType?: AccuracyTTypes = "accuracyT";

    @Property()
    public ID: string;

    @Property()
    public Requestor: string;

    @Property()
    public Threshold: number;
}