import telegram
import telegram.ext
import config
import shelve
import requests
import time
from requests_oauthlib import OAuth1Session, oauth1_session


class CONST:
    AUTH = 0x10


def s_get(key, val):
    with shelve.open("storage") as s:
        return s.get(str(key), val)


def s_put(key, val):
    with shelve.open("storage") as s:
        s[str(key)] = val


def pastebin(text):
    r = requests.post("https://cfp.vim-cn.com/", {"vimcn": text}).text.strip()
    return text[:138 - len(r)] + "… " + r


def start(bot, update):
    bot.sendMessage(update.message.from_user.id,
                    "欢迎使用电磁炉。一只发<a href=\"http://fanfou.com/\">饭</a>用 Bot。\n"
                    "来自<a href=\"http://fanfou.com/blueset\">蓝色之风.py3</a>。\n\n"
                    "发送 /login 以登陆。发送 /logout 以退出。\n"
                    "直接发送消息即可发饭。"
                    "意见与反馈请<a href=\"https://github.com/blueset/FanfouBot/issues\">戳此</a>。\n"
                    "友情联动：<a href=\"https://t.me/joinchat/AAAAAAbHdr-JkfRdeHI5Yw\">饭友 Telegram 交流群</a>\n\n"
                    "<i>Icon by shashank singh from the Noun Project.</i>",
                    parse_mode="HTML")


def cancel(bot, update):
    bot.sendMessage(update.message.from_user.id,
                    "进程已取消。",
                    reply_markup=telegram.forcereply.ForceReply(False))
    return telegram.ext.ConversationHandler.END


def login(bot, update):

    user = update.message.from_user.id

    if s_get((user, "up"), False):

        bot.sendMessage(update.message.from_user.id,
                        "您已登录。请使用 /logout 以登出。")
        return telegram.ext.ConversationHandler.END
    else:
        try:

            o = OAuth1Session(config.client_key, config.client_secret)
            req = o.fetch_request_token("http://fanfou.com/oauth/request_token")

            s_put((user, "req"), req)
            auth = o.authorization_url("http://m.fanfou.com/oauth/authorize", oauth_callback="oob")

            bot.sendMessage(update.message.from_user.id,
                            "请访问下面的链接授权。将获得的授权码发送至此，或回复 /cancel 取消。\n\n%s" % auth,
                            reply_markup=telegram.forcereply.ForceReply())
            return CONST.AUTH
        except:
            bot.sendMessage(update.message.from_user.id,
                            "网络连接异常。请发送 /login 重试。")
            return telegram.ext.ConversationHandler.END


def authorize(bot, update):
    user = update.message.from_user.id
    try:
        if update.message.text.isalnum() and update.message.text == update.message.text.lower() \
            and len(update.message.text) == 10:
            req = s_get((user, "req"), None)
            if req is None:
                bot.sendMessage(update.message.from_user.id,
                                "登录信息已过期。请发送 /login 登陆。")
                return telegram.ext.ConversationHandler.END
            o = OAuth1Session(config.client_key,
                              config.client_secret,
                              req['oauth_token'],
                              req['oauth_token_secret'],
                              verifier=update.message.text)
            ac = o.fetch_access_token("http://fanfou.com/oauth/access_token")
            s_put((user, "req"), ac)
            s_put((user, "up"), True)
            bot.sendMessage(update.message.from_user.id, "登陆成功。", reply_markup=telegram.forcereply.ForceReply(False))
            return telegram.ext.ConversationHandler.END
    except oauth1_session.TokenRequestDenied as e:
        pass
    except requests.exceptions.ConnectionError as e:
        pass
    except Exception as e:
        bot.sendMessage(update.message.from_user.id,
                        "网络连接异常。请发送 /login 重试。 (%s)" % e)
        return telegram.ext.ConversationHandler.END
    o = OAuth1Session(config.client_key, config.client_secret)
    req = o.fetch_request_token("http://fanfou.com/oauth/request_token")
    s_put((user, "req"), req)
    auth = o.authorization_url("http://m.fanfou.com/oauth/authorize", oauth_callback="oob")
    bot.sendMessage(update.message.from_user.id,
                    "验证失败。\n请重新访问下面的链接授权。将获得的授权码发送至此，或回复 /cancel 取消。\n\n%s" % auth,
                    reply_markup=telegram.forcereply.ForceReply())
    return CONST.AUTH

def logout(bot, update):
    user = update.message.from_user.id
    if s_get((user, "up"), False):
        s_put((user, "up"), False)
        bot.sendMessage(update.message.from_user.id,
                        "您已登出。")
    else:
        bot.sendMessage(update.message.from_user.id,
                        "您尚未登录。")


def tweet_text(bot, update):
    user = update.message.from_user.id
    if s_get((user, "up"), False):
        try:
            req = s_get((user, "req"), None)
            if req is None:
                s_set((user, "up"), False)
                return bot.sendMessage(update.message.from_user.id,
                                "登录信息已过期。请发送 /login 登陆。")
            text = update.message.text
            if len(text) > 140:
                text = pastebin(text)
            o = OAuth1Session(config.client_key, config.client_secret, req['oauth_token'], req['oauth_token_secret'])
            res = o.post("http://api.fanfou.com/statuses/update.json", data={
                "status": text
            })

            if res.status_code == 200:
                return bot.sendMessage(update.message.from_user.id,
                                "消息发送成功。",
                                reply_to_message_id=update.message.message_id)
            elif res.status_code == 401:
                s_set((user, "up"), False)
                return bot.sendMessage(update.message.from_user.id,
                                "登录信息已过期。请发送 /login 登陆。")
            else:
                err = str(res.status_code)
                try:
                    err += ", %s" % res.json().get("error")
                except:
                    pass
                return bot.sendMessage(update.message.from_user.id,
                                "发送失败。(%s)" % err,
                                reply_to_message_id=update.message.message_id)
        except oauth1_session.TokenRequestDenied:
            s_set((user, "up"), False)
            return bot.sendMessage(update.message.from_user.id,
                            "登录信息已过期。请发送 /login 登陆。")
        except requests.exceptions.ConnectionError:
            bot.sendMessage(update.message.from_user.id,
                            "网络连接出错，请重试。",
                            reply_to_message_id=update.message.message_id)
    else:
        bot.sendMessage(update.message.from_user.id,
                        "您尚未登录。请发送 /login 登陆。")


def tweet_photo(bot, update):
    user = update.message.from_user.id
    if s_get((user, "up"), False):
        try:
            req = s_get((user, "req"), None)
            if req is None:
                s_set((user, "up"), False)
                return bot.sendMessage(update.message.from_user.id,
                                "登录信息已过期。请发送 /login 登陆。")
            fn = "downloads/%s" % str(int(time.time()))
            photo = bot.getFile(update.message.photo[-1].file_id).download(fn)
            text = update.message.caption or "发送了图片。"
            if len(text) > 140:
                text = pastebin(text)
            o = OAuth1Session(config.client_key, config.client_secret, req['oauth_token'], req['oauth_token_secret'])
            res = o.post("http://api.fanfou.com/photos/upload.json", data={
                "status": text
            }, files={"photo": open(fn, 'rb')})

            if res.status_code == 200:
                bot.sendMessage(update.message.from_user.id,
                                "消息发送成功。",
                                reply_to_message_id=update.message.message_id)
            elif res.status_code == 401:
                s_set((user, "up"), False)
                bot.sendMessage(update.message.from_user.id,
                                "登录信息已过期。请发送 /login 登陆。")
            else:
                err = str(res.status_code)
                try:
                    err += ", %s" % res.json().get("error")
                except:
                    pass
                bot.sendMessage(update.message.from_user.id,
                                "发送失败。(%s)" % err,
                                reply_to_message_id=update.message.message_id)
            os.remove(fn)
        except oauth1_session.TokenRequestDenied:
            s_set((user, "up"), False)
            return bot.sendMessage(update.message.from_user.id,
                            "登录信息已过期。请发送 /login 登陆。")
        except requests.exceptions.ConnectionError:
            bot.sendMessage(update.message.from_user.id,
                            "网络连接出错，请重试。",
                            reply_to_message_id=update.message.message_id)
    else:
        bot.sendMessage(update.message.from_user.id,
                        "您尚未登录。请发送 /login 登陆。")


def error(bot, update, error):
    estr = 'Error! Update %s caused error %s.' % (update, error)

    bot.sendMessage(config.admin, estr)


if __name__ == "__main__":
    bot = telegram.ext.Updater(config.token)
    bot.dispatcher.add_handler(telegram.ext.CommandHandler("start", start))
    bot.dispatcher.add_handler(telegram.ext.CommandHandler("logout", logout))
    bot.dispatcher.add_handler(telegram.ext.ConversationHandler(
        entry_points=[telegram.ext.CommandHandler('login', login)],
        states={
            CONST.AUTH: [telegram.ext.CommandHandler("cancel", cancel),
                         telegram.ext.MessageHandler(telegram.ext.Filters.text, authorize)]
        },
        fallbacks=[telegram.ext.CommandHandler("cancel", cancel)]
    ))
    bot.dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text, tweet_text))
    bot.dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.photo, tweet_photo))
    bot.dispatcher.add_error_handler(error)
    bot.start_polling(network_delay=10, timeout=10)
