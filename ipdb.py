from irc3 import IrcBot, utils
import sys
from threading import Thread

CFG = utils.parse_config('ipdb', 'ipdb.ini')

IRC_CFG = {
    **utils.parse_config('bot', 'irclib/config.ini'),
    **CFG['irc'],
    'autojoins': [
        CFG['adminChannel']
    ]
}

bot = server = None

if __name__ == "__main__":
    bot = IrcBot(**IRC_CFG)
    bot.include('irc3.plugins.command')
    bot.include('irclib.plugins.ipdb')
    # bot.run()
    bot_thread = Thread(target=bot.run)
    bot_thread.daemon = True
    bot_thread.start()
    while 1:
        raw_input = input('INPUT:')
        try:
            eval(raw_input)
        except:
            print("Unexpected error:", sys.exc_info()[0])





