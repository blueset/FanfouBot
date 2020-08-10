export interface StorageDoc {
    id: number;
    up: boolean;
    req?: {
        oauth_token: string;
        oauth_token_secret: string;
    }
}