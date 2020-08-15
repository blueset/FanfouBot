import { Telegraf } from 'telegraf'
import ProxyAgent from "simple-proxy-agent";
import { TelegrafOptions } from 'telegraf/typings/telegraf';
import { TelegrafContext } from 'telegraf/typings/context';
import { MongoClient } from "mongodb";
import got from "got";
import { TelegrafMongoSession } from "telegraf-session-mongodb";
import { StorageDoc } from './dbModel';
import Fanfou, { ParsedData } from "fanfou-sdk";
import queryString from "query-string";
import FormData from "form-data";

const PROXY =
    process.env.http_proxy ||
    process.env.HTTP_PROXY ||
    process.env.https_proxy ||
    process.env.HTTPS_PROXY || null;

const telegrafOptions: TelegrafOptions = {};
let gotInst = got;

if (PROXY) {
    const agent = new ProxyAgent(PROXY)
    telegrafOptions.telegram = { agent: agent };
    gotInst = got.extend({
        agent: {
            https: agent
        }
    });
}

async function post<T extends string>(uri: T, parameters: Object): Promise<ParsedData<T>> {
    const url = `${this.apiEndPoint}${uri}.json`;
    const oAuthUrl = `http://api.fanfou.com${uri}.json`;
    const token = { key: this.oauthToken, secret: this.oauthTokenSecret };
    const isUpload = ['/photos/upload', '/account/update_profile_image'].includes(uri);
    const { Authorization } = this.o.toHeader(this.o.authorize({ url: oAuthUrl, method: 'POST', data: isUpload ? null : parameters }, token));
    let form = null;
    const headers = { Authorization, 'Content-Type': 'application/x-www-form-urlencoded' };
    if (isUpload) {
        form = new FormData();
        Object.keys(parameters).forEach(key => {
            form.append(key, parameters[key]);
        });
        delete headers['Content-Type'];
    }

    try {
        const { body } = await got.post(url, {
            headers,
            body: isUpload ? form : queryString.stringify(parameters)
        });
        const response = JSON.parse(body);
        // @ts-ignore
        const result: ParsedData<T> = Fanfou._parseData(response, Fanfou._uriType(uri));
        return result;
    } catch (error) {
        throw new Error(error);
    }
}
Fanfou.prototype.post = post;

const client: MongoClient = new MongoClient(process.env.MONGO_URL, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
});

const bot = new Telegraf(process.env.BOT_TOKEN, telegrafOptions);

bot.use(async (ctx: TelegrafContext, next) => {
    if (!client.isConnected()) await client.connect();
    ctx.dbClient = client;
    ctx.db = client.db();

    const user = ctx.from.id;
    const collection = ctx.db.collection<StorageDoc>("storage");
    const userDoc = await collection.findOne({ id: user });
    ctx.state = {
        storageCollection: collection,
        user: userDoc
    };

    const session = new TelegrafMongoSession(ctx.db, {
        collectionName: 'sessions',
        sessionName: 'session'
    });
    await session.middleware(ctx, next);
});

async function pastebin(text: string): Promise<string> {
    try {
        const resp = await gotInst.post("https://cfp.vim-cn.com/", {
            form: {
                vimcn: text
            },
        });
        const url = resp.body.trim();
        return `${text.substring(0, 138 - url.length)}… ${url}`;
    } catch {
        return `${text.substring(138)}…`;
    }
}

async function printHelp(context: TelegrafContext) {
    await context.reply(
        `欢迎使用电磁炉。一只发<a href="https://fanfou.com/">饭</a>用 Bot。
来自<a href="https://fanfou.com/blueset">Eana.Hufwe.0</a>。

发送 /login 以登录。发送 /logout 以退出。
直接发送消息即可发饭。
意见与反馈请<a href="https://github.com/blueset/FanfouBot/issues">戳此</a>。
<i>Icon by shashank singh from the Noun Project.</i>`,
        { parse_mode: "HTML" });
}

bot.start(printHelp);
bot.help(printHelp);

bot.command("logout", async (context) => {
    const user = context.from.id;
    const userDoc = context.state.user;
    const collection = context.state.storageCollection;
    if (userDoc?.up !== true) {
        await context.reply("您尚未登录。");
        return;
    } else if (userDoc !== null) {
        await collection.updateOne({ id: user }, {
            $set: {
                up: false
            }
        });
    }
    await context.reply("您现已登出。");
});

bot.command("login", async (context) => {
    const user = context.from.id;
    const userDoc = context.state.user;
    const collection = context.state.storageCollection;
    if (userDoc?.up === true) {
        await context.reply("您已登录。请使用 /logout 以登出。");
        context.session.status = null;
        return;
    }
    try {
        const ff = new Fanfou({
            consumerKey: process.env.CLIENT_KEY,
            consumerSecret: process.env.CLIENT_SECRET,
        });
        await ff.getRequestToken();
        const url = `https://m.fanfou.com/oauth/authorize?oauth_token=${ff.oauthToken}&oauth_callback=https://labs.1a23.com/fanfou_auth`;
        await collection.updateOne({ id: user }, {
            $set: {
                req: {
                    oauth_token: ff.oauthToken,
                    oauth_token_secret: ff.oauthTokenSecret,
                },
                up: false
            }
        }, { upsert: true });

        await context.reply(
            `请访问下面的链接授权，或回复 /cancel 取消。\n\n${url}`,
            {
                reply_markup: {
                    keyboard: [[{ text: "我已授权。" }], [{ text: "/cancel" }]],
                    one_time_keyboard: true
                }
            }
        );

        context.session.status = "auth";
    } catch (e) {
        console.error(e);
        await context.reply(`网络连接异常。(${e}) 请发送 /login 重试。`);
        context.session.status = null;
        return;
    }
});

async function authorize(context: TelegrafContext, next: () => Promise<void>) {
    if (context.session.status !== "auth") {
        return await next();
    }
    const user = context.from.id;
    const collection = context.state.storageCollection;
    try {
        if (context.message.text === "我已授权。") {
            const req = context.state?.user?.req;
            if (!req) {
                await context.reply("登录信息已过期。请发送 /login 登录。");
                context.session.status = null;
                return;
            }
            const ff = new Fanfou({
                consumerKey: process.env.CLIENT_KEY,
                consumerSecret: process.env.CLIENT_SECRET,
            });
            await ff.getAccessToken({ oauthToken: req.oauth_token, oauthTokenSecret: req.oauth_token_secret });
            const ac = {
                oauth_token: ff.oauthToken,
                oauth_token_secret: ff.oauthTokenSecret
            };
            await collection.updateOne({ id: user }, {
                $set: {
                    req: ac,
                    up: true
                }
            }, { upsert: true });
            await context.reply("登录成功。", { reply_markup: { remove_keyboard: true } });
            context.session.status = null;
        }
    } catch (e) {
        await context.reply(`网络连接异常。请发送 /login 重试。 (${e})`);
        context.session.status = null;
    }
}

bot.command("cancel", async (context) => {
    await context.reply("进程已取消。", { reply_markup: { remove_keyboard: true } });
    context.session.status = null;
});

async function requireAuth(context: TelegrafContext, next: () => Promise<void>) {
    if (context.state.user?.up !== true) {
        return await context.reply("您尚未登录。请发送 /login 登录。");
    }
    return await next();
}

bot.on("text", authorize, requireAuth, async (context) => {
    try {
        const req = context.state.user?.req;
        let text = context.message.text;
        if (text.length > 140) {
            text = await pastebin(text);
        }

        const ff = new Fanfou({
            consumerKey: process.env.CLIENT_KEY,
            consumerSecret: process.env.CLIENT_SECRET,
            oauthToken: req.oauth_token,
            oauthTokenSecret: req.oauth_token_secret,
        });
        const res = await ff.post("/statuses/update", {
            status: text
        });
        const response = `消息发送成功。\n\n${res.plain_text}\nhttps://fanfou.com/statuses/${res.id}`;
        return await context.reply(
            response,
            { reply_to_message_id: context.message.message_id }
        )
    } catch (e) {
        console.error(e);
        return await context.reply(
            `出现错误，请重试。 ${e}`,
            { reply_to_message_id: context.message.message_id }
        );
    }
});


bot.on("photo", requireAuth, async (context) => {
    const start = process.hrtime();
    try {
        const req = context.state.user?.req;
        let text = context.message?.caption || "发送了图片。";
        if (text.length > 140) {
            text = await pastebin(text);
        }

        let stop = process.hrtime(start);
        console.log(`text: ${stop[0]}s, ${stop[1] / 1000000}ms.`);

        const photos = context.message.photo;
        const photo = photos[photos.length - 1];
        const photoURL = await context.telegram.getFileLink(photo.file_id);
        const photoBuffer = (await gotInst.get(photoURL)).rawBody;
        // @ts-ignore
        photoBuffer.name = "image.jpg";

        stop = process.hrtime(start);
        console.log(`download photo: ${stop[0]}s, ${stop[1] / 1000000}ms.`);

        const ff = new Fanfou({
            consumerKey: process.env.CLIENT_KEY,
            consumerSecret: process.env.CLIENT_SECRET,
            oauthToken: req.oauth_token,
            oauthTokenSecret: req.oauth_token_secret,
            apiDomain: "cors.fanfou.pro",
        });
        const res = await ff.post("/photos/upload", {
            status: text,
            photo: photoBuffer,
        });

        stop = process.hrtime(start);
        console.log(`send photo: ${stop[0]}s, ${stop[1] / 1000000}ms.`);

        const response = `消息发送成功。\n\n${res.plain_text}\nhttps://fanfou.com/statuses/${res.id}`;
        await context.reply(
            response,
            { reply_to_message_id: context.message.message_id }
        )

        stop = process.hrtime(start);
        console.log(`respond: ${stop[0]}s, ${stop[1] / 1000000}ms.`);
        return;
    } catch (e) {
        console.error(e);
        return await context.reply(
            `出现错误，请重试。 ${e}`,
            { reply_to_message_id: context.message.message_id }
        );
    }
});

bot.catch(async (error: any, context: TelegrafContext) => {
    const estr = `Error! Update ${context.update} caused error ${error}.`;
    await context.telegram.sendMessage(process.env.ADMIN, estr);
    await context.reply(`网络连接超时 (${error})，请重试。`);
});

export default bot;