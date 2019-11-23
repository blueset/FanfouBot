import telegram
import telegram.ext
import config
import shelve
import requests
import time
import urllib
import json
from tempfile import NamedTemporaryFile
# from requests_oauthlib import OAuth1Session, oauth1_session
import fanfou


class CONST:
    AUTH = 0x10


CONSUMER = {"key": config.client_key, "secret": config.client_secret}


def s_get(key, val):
    with shelve.open("storage") as s:
        return s.get(str(key), val)


def s_put(key, val):
    with shelve.open("storage") as s:
        s[str(key)] = val


def pastebin(text):
    try:
        r = requests.post("https://cfp.vim-cn.com/",
                          {"vimcn": text}).text.strip()
        return text[:138 - len(r)] + "… " + r
    except:
        return text[:138] + "…"


def start(bot, update):
    bot.sendMessage(update.message.from_user.id,
                    "欢迎使用电磁炉。一只发<a href=\"https://fanfou.com/\">饭</a>用 Bot。\n"
                    "来自<a href=\"https://fanfou.com/blueset\">Eana.Hufwe.0</a>。\n\n"
                    "发送 /login 以登录。发送 /logout 以退出。\n"
                    "直接发送消息即可发饭。"
                    "意见与反馈请<a href=\"https://github.com/blueset/FanfouBot/issues\">戳此</a>。\n"
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
            c = fanfou.OAuth(
                CONSUMER, callback="https://labs.1a23.com/fanfou_auth")
            req = c.request_token()
            req = {"oauth_token": req['key'],
                   "oauth_token_secret": req['secret']}

            s_put((user, "req"), req)
            auth = c.authorize_url

            bot.sendMessage(update.message.from_user.id,
                            # "请访问下面的链接授权。将获得的授权码发送至此，或回复 /cancel 取消。\n\n%s" % auth,
                            "请访问下面的链接授权，或回复 /cancel 取消。\n\n%s" % auth,
                            reply_markup=telegram.ReplyKeyboardMarkup(
                                [["我已授权。"], ["/cancel"]],
                                one_time_keyboard=True
                            ))
            return CONST.AUTH
        except:
            bot.sendMessage(update.message.from_user.id,
                            "网络连接异常。请发送 /login 重试。")
            return telegram.ext.ConversationHandler.END


def authorize(bot, update):
    user = update.message.from_user.id
    try:
        if update.message.text == "我已授权。":  # update.message.text.isalnum() and update.message.text == update.message.text.lower() \
            # and len(update.message.text) == 10:
            req = s_get((user, "req"), None)
            if req is None:
                bot.sendMessage(update.message.from_user.id,
                                "登录信息已过期。请发送 /login 登录。")
                return telegram.ext.ConversationHandler.END

            c = fanfou.OAuth(CONSUMER, {
                "key": req['oauth_token'],
                "secret": req['oauth_token_secret']
            })
            ac = c.access_token()
            s_put((user, "req"), {
                "oauth_token": ac['key'], "oauth_token_secret": ac['secret']
            })
            s_put((user, "up"), True)
            bot.sendMessage(update.message.from_user.id, "登录成功。",
                            reply_markup=telegram.forcereply.ForceReply(False))
            return telegram.ext.ConversationHandler.END
    except oauth1_session.TokenRequestDenied as e:
        pass
    except requests.exceptions.ConnectionError as e:
        pass
    except Exception as e:
        bot.sendMessage(update.message.from_user.id,
                        "网络连接异常。请发送 /login 重试。 (%s)" % e)
        return telegram.ext.ConversationHandler.END
    c = fanfou.OAuth(CONSUMER, callback="https://labs.1a23.com/fanfou_auth")
    req = c.request_token()
    req = {"oauth_token": req['key'], "oauth_token_secret": req['secret']}
    s_put((user, "req"), req)
    auth = c.authorize_url
    bot.sendMessage(update.message.from_user.id,
                    "验证失败。\n请重新访问下面的链接授权，或回复 /cancel 取消。\n\n%s" % auth,
                    reply_markup=telegram.ReplyKeyboardMarkup(
                        [["我已授权。"], ["/cancel"]],
                        one_time_keyboard=True
                    ))
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
                s_put((user, "up"), False)
                return bot.sendMessage(update.message.from_user.id,
                                       "登录信息已过期。请发送 /login 登录。")
            text = update.message.text
            if len(text) > 140:
                text = pastebin(text)
            c = fanfou.OAuth(CONSUMER, {
                "key": req['oauth_token'],
                "secret": req['oauth_token_secret']
            })
            res = c.request("/statuses/update", 'POST', {
                "status": text
            })
            print(res.code)
            result = res.json()
            response = f"消息发送成功。\n\n{result.get('text')}\nhttps://fanfou.com/statuses/{result.get('id')}"
            return bot.sendMessage(update.message.from_user.id,
                                   response,
                                   reply_to_message_id=update.message.message_id)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                s_put((user, "up"), False)
                err_msg = json.loads(e.fp.read().decode())
                return bot.sendMessage(update.message.from_user.id,
                                       f"登录信息已过期。请发送 /login 登录。\n\n{err_msg.get('error')}")
            else:
                err = str(e.code)
                try:
                    err += ", %s" % json.loads(e.fp.read().decode()
                                               ).get('error')
                except:
                    pass
                return bot.sendMessage(update.message.from_user.id,
                                       "发送失败。(%s)" % err,
                                       reply_to_message_id=update.message.message_id)
        except requests.exceptions.ConnectionError:
            bot.sendMessage(update.message.from_user.id,
                            "网络连接出错，请重试。",
                            reply_to_message_id=update.message.message_id)
    else:
        bot.sendMessage(update.message.from_user.id,
                        "您尚未登录。请发送 /login 登录。")


def tweet_photo(bot, update):
    user = update.message.from_user.id
    if s_get((user, "up"), False):
        f = NamedTemporaryFile()
        try:
            req = s_get((user, "req"), None)
            if req is None:
                s_put((user, "up"), False)
                return bot.sendMessage(update.message.from_user.id,
                                       "登录信息已过期。请发送 /login 登录。")
            # fn = "downloads/%s" % str(int(time.time()))
            fn = f.name
            photo = bot.getFile(update.message.photo[-1].file_id).download(fn)
            text = update.message.caption or "发送了图片。"
            if len(text) > 140:
                text = pastebin(text)
            c = fanfou.OAuth(CONSUMER, {
                "key": req['oauth_token'],
                "secret": req['oauth_token_secret']
            })
            body, headers = fanfou.pack_image({
                "status": text,
                "photo": fn
            })
            res = c.request("/photos/upload", 'POST', body, headers)

            if res.code == 200:
                result = res.json()
                response = f"消息发送成功。\n\n{result.get('text')}\nhttps://fanfou.com/statuses/{result.get('id')}"
                bot.sendMessage(update.message.from_user.id,
                                response,
                                reply_to_message_id=update.message.message_id)
            elif res.code == 401:
                s_put((user, "up"), False)
                err_msg = json.loads(e.fp.read().decode())
                return bot.sendMessage(update.message.from_user.id,
                                       f"登录信息已过期。请发送 /login 登录。\n\n{err_msg.get('error')}")
            else:
                err = str(e.code)
                try:
                    err += ", %s" % json.loads(e.fp.read().decode()
                                               ).get('error')
                except:
                    pass
                bot.sendMessage(update.message.from_user.id,
                                "发送失败。(%s)" % err,
                                reply_to_message_id=update.message.message_id)

        except oauth1_session.TokenRequestDenied:
            s_put((user, "up"), False)
            return bot.sendMessage(update.message.from_user.id,
                                   "登录信息已过期。请发送 /login 登录。")
        except requests.exceptions.ConnectionError:
            bot.sendMessage(update.message.from_user.id,
                            "网络连接出错，请重试。",
                            reply_to_message_id=update.message.message_id)
        finally:
            f.close()
    else:
        bot.sendMessage(update.message.from_user.id,
                        "您尚未登录。请发送 /login 登录。")


def error(bot, update, error):
    estr = 'Error! Update %s caused error %s.' % (update, error)
    bot.sendMessage(config.admin, estr)
    bot.sendMessage(update.message.from_user.id, "网络连接超时 (%s)，请重试。" % error)


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
    bot.dispatcher.add_handler(telegram.ext.MessageHandler(
        telegram.ext.Filters.text, tweet_text))
    bot.dispatcher.add_handler(telegram.ext.MessageHandler(
        telegram.ext.Filters.photo, tweet_photo))
    bot.dispatcher.add_error_handler(error)

    bot.start_polling()
    # bot.start_webhook(listen='0.0.0.0', port=8080,
    #                   url_path='telegram/' + config.token)
    # bot.bot.setWebhook(url='https://example.com/telegram/' + config.token)
