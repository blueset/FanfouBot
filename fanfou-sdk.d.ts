
import { Fanfou } from "fanfou-sdk";

declare module "fanfou-sdk" {
    declare namespace Fanfou {
        export interface FanfouOptions {
            consumerKey: string,
            consumerSecret: string,
            oauthToken?: string,
            oauthTokenSecret?: string,
            username?: string,
            password?: string,
            protocol?: string,
            fakeHttps?: boolean,
            apiDomain?: string,
            oauthDomain?: string,
            hooks?: {
                baseString?: (str: string) => any;
            }
        }
    }

    interface DirectMessage {
        id: string;
        text: string;
        sender_id: string;
        recipient_id: string;
        created_at: string;
        sender_screen_name: string;
        recipient_screen_name: string;
        sender: User;
        recipient: User;
        in_reply_to?: DirectMessage;
    }

    interface Conversation {
        dm: DirectMessage;
        otherid: string;
        msg_num: number;
        new_conv: boolean;
    }

    interface User {
        id: string;
        name: string;
        screen_name: string;
        unique_id: string;
        location: string;
        gender: string;
        birthday: string;
        description: string;
        profile_image_url: string;
        profile_image_url_large: string;
        url: string;
        protected: boolean;
        followers_count: number;
        friends_count: number;
        favourites_count: number;
        statuses_count: number;
        photo_count: number;
        following: boolean;
        notifications: boolean;
        created_at: string;
        utc_offset: number;
        profile_background_color: string;
        profile_text_color: string;
        profile_link_color: string;
        profile_sidebar_fill_color: string;
        profile_sidebar_border_color: string;
        profile_background_image_url: string;
        profile_background_tile: boolean;
        status?: object;
        profile_image_origin: string;
        profile_image_origin_large: string;
    }

    interface Photo {
        url: string;
        imageurl: string;
        thumburl: string;
        largeurl: string;
        originurl: string;
        type: string;
        isGif(): boolean;
    }

    interface Status {
        created_at: string;
        id: string;
        rawid: string;
        text: string;
        source: string;
        truncated: string;
        in_reply_to_status_id: string;
        in_reply_to_user_id: string;
        favorited: boolean;
        in_reply_to_screen_name: string;
        is_self: string;
        location: string;
        repost_status_id?: string;
        repost_user_id?: string;
        repost_screen_name?: string;
        repost_status?: Status;
        user?: User;
        photo?: Photo;
        isReply(): boolean;
        isRepost(): boolean;
        isOrigin(): boolean;
        isOriginRepost(): boolean;
        type: "reply" | "repost" | "origin" | "unknown";
        source_url: string;
        source_name: string;
        txt: string;
        plain_text: string;
    }

    type TimelineURLs = "/search/public_timeline" | "/search/user_timeline" | "/photos/user_timeline" | "/statuses/friends_timeine" | "/statuses/home_timeline" | "/statuses/public_timeline" | "/statuses/replies" | "/statuses/user_timeline" | "/statuses/context_timeline" | "/statuses/mentions" | "/favorites";
    type StatusURLs = "/statuses/update" | "/statuses/show" | "/favorites/destroy" | "/favorites/create" | "/photos/upload";
    type UsersURLs = "/users/tagged" | "/users/followers" | "/users/friends" | "/friendships/requests";
    type UserURLs = "/users/show" | "/friendships/create" | "/friendships/destroy" | "/account/verify_credentials";
    type ConversationURLs = "/direct_messages/conversation" | "/direct_messages/inbox" | "/direct_messages/sent";
    type ConversationListURLs = "/direct_messages/conversation_list";
    type DirectMessageURLs = "/direct_messages/new" | "/direct_messages/destroy";

    type ParsedData<T> =
        T extends TimelineURLs ? Status[] :
        T extends UsersURLs ? User[] :
        T extends ConversationURLs ? DirectMessage[] :
        T extends ConversationListURLs ? Conversation[] :
        T extends StatusURLs ? Status :
        T extends UserURLs ? User :
        T extends DirectMessageURLs ? DirectMessage :
        object;

    export default class Fanfou {
        constructor(opt?: Fanfou.FanfouOptions)
        getRequestToken(): this;
        getAccessToken(token: {
            oauthToken: string,
            oauthTokenSecret: string
        }): this;
        xauth(): this;
        get<T extends string>(uri: T, params: object): ParsedData<T>;
        post<T extends string>(uri: T, params: object): ParsedData<T>;
        oauthEndPoint?: string;
        apiEndPoint?: string;
        consumerKey?: string;
        consumerSecret?: string;
        oauthToken?: string;
        oauthTokenSecret?: string;
        username?: string;
        password?: string;
        protocol?: string;
        apiDomain?: string;
        oauthDomain?: string;
    }
}
