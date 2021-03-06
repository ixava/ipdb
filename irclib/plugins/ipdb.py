# -*- coding: utf-8 -*-
from irc3.plugins.command import command
import irc3, re, socket, queue, time
from db import IPDB
from user import User
from tabulate import tabulate

CFG = irc3.utils.parse_config('ipdb', 'ipdb.ini')
MSG_QUEUE = queue.Queue()

@irc3.plugin
class Plugin:

    def __init__(self, bot):
        self.bot = bot
        self.ipdb = IPDB(CFG["db"])

    @irc3.event(irc3.rfc.CONNECTED)
    def initialize(self, **kwargs):
        """get oper and nickserv authenticated"""
        self.bot.part('#hangout')
        if 'pass' in CFG:
            self.bot.send('PASS %s' % CFG['pass'])
        if 'oper' in CFG:
            self.bot.send('OPER %s' % CFG['oper'])

    @command(permission='view')
    def hostsearch(self, mask, target, args):
      """Hostsearch

         %%hostsearch <input>...
      """
      input = ' '.join(args['<input>'])
      result = self.ipdb.getByProperty(input, 'hostname', 'hostnames')
      if result:
        table = self.makeTable(result)
        for msg in table:
          self.bot.privmsg(target, msg)
      else:
        self.bot.privmsg(target, 'No records matched the query')

    @command(permission="view")
    def help(self, mask, target, args):
      """Help
         %%help
      """
      self.bot.notice(mask.nick, 'Commands: .ipdb, .hostsearch, .help')

    @command(permission='view')
    def ipdb(self, mask, target, args):
        """Ipdb

           %%ipdb <input>...
        """
        input = ' '.join(args['<input>'])
        ip_regex = re.compile('(\d{1,3}\.){1,3}(\d{1,3})?')
        steamid_regex = re.compile('0[xX][0-9a-fA-F]+')
        hwid_regex = re.compile('[0-9a-fA-F]{16}')

        if ip_regex.match(input):
            [start, end] = self.getIPRange(input)
            result = self.ipdb.getByIP(User.longIP(start), User.longIP(end))
        elif steamid_regex.match(input):
            result = self.ipdb.getByProperty(input, 'steamid', 'steamids')
        elif hwid_regex.match(input):
            result = self.ipdb.getByProperty(input, 'hwid', 'hwids')
        else:
            result = self.ipdb.getByProperty(self.ipdb.conn.escape_string(input), 'name', 'names')

        if result:
          table = self.makeTable(result)
          for msg in table:
            self.bot.privmsg(target, msg)
        else:
          self.bot.privmsg(target, 'No results matched')

    @irc3.event(irc3.rfc.PRIVMSG)
    def parseData(self, target, data, mask, event):
        if target == self.bot.nick:
            print("privmsg from %s: %s" % (mask.nick, data))
        elif mask.nick == CFG['botName'] and target.lower() == CFG['adminChannel'].lower():

            color_regex = re.compile("\x1f|\x02|\x12|\x0f|\x16|\x03(?:\d{1,2}(?:,\d{1,2})?)?", re.UNICODE)
            noMarkup = color_regex.sub("", data)

            join_regex = re.compile("^\[Join\] (?:\[Mod\]|\[Manager\]|\[Admin\]|\[Half Mod\]|\[Temp Mod\]|\[Owner\])?(.+) joined.+from ([\d\.]+)(?:,| )[^0]+(0x[^\.]+)?")
            playerjoin = join_regex.search(noMarkup)
            if playerjoin:
                joinData = {}
                joinData['name'] = playerjoin.group(1)
                joinData['ip']= playerjoin.group(2)
                try:
                    joinData['hostname'] = socket.gethostbyaddr(joinData['ip'])[0]
                except:
                    joinData['hostname'] = '-'
                joinData['steamid'] = playerjoin.group(3)
                if not joinData['steamid']:
                    joinData['steamid'] = "-"
                MSG_QUEUE.put([joinData,time.time()])

            else:
                hwid_regex = re.compile("^\[Player\].*[\d]{1,5},(.+)hwid(.*)")
                hwinfo = hwid_regex.search(noMarkup)
                if hwinfo:
                    if MSG_QUEUE.qsize() < 1:
                        return
                    nick = hwinfo.group(1).encode().decode('unicode-escape')
                    hwid = hwinfo.group(2)
                    for x in range(MSG_QUEUE.qsize()):
                        [joinData,enterTime] = MSG_QUEUE.get(block=True) if not MSG_QUEUE.empty() else False
                        if not joinData:
                            break
                        if nick == joinData['name']:
                            joinData['hwid'] = hwid
                        elif (time.time() - enterTime) > 10:
                            joinData['hwid']  = '-'
                        else:
                            MSG_QUEUE.put([joinData,enterTime])
                            continue
                        userObj = User(**joinData)
                        if userObj.string_ip == '82.31.137.26' or userObj.hwid == 'C19950D00000A8ED':
                          continue
                        self.checkUser(userObj)

    def checkUser(self, user):
      userID = self.ipdb.getUserID(user.name_escaped, user.ip, user.hwid, user.steamid, user.hostname)
      print(userID)
      if not userID:
        print('User is new')
        keys = {}
        for prop in self.ipdb.dbMeta.values():
          field = prop['property']
          value = getattr(user, field)
          if type(value) == str:
            value = self.ipdb.conn.escape_string(value)
          if self.ipdb.isNewProperty(value, **prop):
            print("prop {} is new".format(field))
            self.ipdb.addProperty(value, **prop)
          else:
            print("prop {} is not new".format(field))

          keys[field] = self.ipdb.getPropertyID(value, **prop)
        user = User(**keys)
        self.ipdb.addUser(user)
      else:
        print('Player not new, updating last seen')
        self.ipdb.updateLastSeen('users', userID)

    def getIPRange(self, input):
      input = input.rstrip('.')
      start = input.split('.')
      end = input.split('.')
      for addOctetCount in range(4 - len(start)):
        start.append('0')
        end.append('255')
      return ['.'.join(start), '.'.join(end)]

    def makeTable(self, data):
      tableData = []
      tableHeaders = ["ID","Nick", "IP", "steamid", "hwid", "Hostname", "last_seen"]
      for user in data:
        tableData.append([user['id'],user['name'], user['ip'], user['steamid'], user['hwid'], user['hostname'],user['last_seen']])
      table = tabulate(tableData, tableHeaders)
      return table.split('\n')

