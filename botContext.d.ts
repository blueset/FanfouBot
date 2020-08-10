import { TelegrafContext } from "telegraf/typings/context";
import { MongoClient, Db, Collection } from "mongodb";
import { StorageDoc } from "../../dbModel";

declare module "telegraf/typings/context" {
    export interface TelegrafContext {
        dbClient?: MongoClient;
        db?: Db;
        session?: {
            status: null | "auth";
        },
        state?: {
            storageCollection: Collection<StorageDoc>;
            user?: StorageDoc;
        }
    }
}