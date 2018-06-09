import pymysql.cursors
from user import User

class IPDB:
    def __init__(self):
      self.conn = pymysql.connect(host='localhost',
                                  user='root',
                                  db='ipdb',
                                  charset='utf8mb4',
                                  cursorclass=pymysql.cursors.DictCursor
      )
      self.dbMeta = {
        "ip": {
          "property": "ip",
          "tableName": "ips",
        },
        "name": {
          "property": "name",
          "tableName": "names",
        },
        "steamid": {
          "property": "steamid",
          "tableName": "steamids",
        },
        "hwid": {
          "property": "hwid",
          "tableName": "hwids",
        },
        "hostname": {
          "property": "hostname",
          "tableName": "hostnames",
        }
      }
      self.innerJoin = 'INNER JOIN names ON users.name_id = names.id ' \
                       'INNER JOIN steamids ON users.steamid_id = steamids.id ' \
                       'INNER JOIN ips ON users.ip_id = ips.id ' \
                       'INNER JOIN hwids on users.hwid_id = hwids.id ' \
                       'INNER JOIN hostnames ON users.hostname_id = hostnames.id'
      self.dateFormats = "DATE_FORMAT(users.last_seen, '%Y-%m-%d %H:%i') AS last_seen, DATE_FORMAT(users.first_seen, '%Y-%m-%d %H:%i') AS first_seen"
      self.selectFields = "users.id, hwids.hwid, INET_NTOA(ips.ip) as ip, names.name, hostnames.hostname, steamids.steamid, {}".format(self.dateFormats)

    def isNewUser(self, user):
      cursor = self.conn.cursor()

      sql = 'SELECT count(*) as count from users {} WHERE ips.ip=INET_ATON(%s) AND names.name=%s AND steamids.steamid=%s AND hwids.hwid=%s AND hostnames.hostname=%s'.format(self.innerJoin)
      cursor.execute(sql,(user.string_ip, user.name, user.steamid, user.hwid, user.hostname))

      if cursor.fetchone()['count'] == 0:
        return True
      return False

    def isNewProperty(self, value, property, tableName):
      cursor = self.conn.cursor()
      sql = 'SELECT count(*) as count FROM {} WHERE {}=%s'.format(tableName, property)
      cursor.execute(sql, (value,))

      if cursor.fetchone()['count'] == 0:
          return True
      return False

    def addProperty(self, value, property, tableName):
      cursor = self.conn.cursor()
      sql = "INSERT IGNORE INTO {} ({}) VALUES('{}')".format(tableName, property, value)
      cursor.execute(sql)
      self.conn.commit()

    def addUser(self, data):
      cursor = self.conn.cursor()
      sql = 'INSERT IGNORE INTO users (name_id,ip_id,hwid_id,hostname_id,steamid_id) VALUES({},{},{},{},{})'.format(data['name'], data['ip'],data['hwid'],data['hostname'],data['steamid'])
      cursor.execute(sql)
      self.conn.commit()

    def getPropertyID(self, value, property, tableName):
      cursor = self.conn.cursor()
      sql = "SELECT id FROM {} WHERE {}='{}'".format(tableName, property, value)
      cursor.execute(sql)
      result = cursor.fetchone()
      if result:
        return result['id']
      return False

    def getByIP(self, start, end):
      cursor = self.conn.cursor()
      sql = "SELECT {} FROM users {} WHERE ips.ip BETWEEN {} AND {}".format(self.selectFields, self.innerJoin, start, end)
      cursor.execute(sql)
      result = cursor.fetchall()
      if result:
        return result
      return False

    def getByHost(self, input):
      cursor = self.conn.cursor()
      sql = "SELECT {} FROM users {} WHERE hostnames.hostname LIKE '%{}%'".format(self.selectFields, self.innerJoin, input)
      cursor.execute(sql)
      result = cursor.fetchall()
      if result:
        return result
      return False

    def getUsers(self, value, property, tableName):
      cursor = self.conn.cursor()
      foreign_key = tableName + '.' + property
      sql = "SELECT {} FROM users {} WHERE {} LIKE '%{}%'".format(self.selectFields, self.innerJoin, foreign_key, value)
      cursor.execute(sql)
      result = cursor.fetchall()
      if result:
        return result
      return False

    def getUserID(self, name, ip, hwid, steamid, hostname):
      cursor = self.conn.cursor()
      sql = "SELECT users.id FROM users {} WHERE names.name='{}' AND ips.ip={} AND hwids.hwid='{}' AND steamids.steamid='{}' AND hostnames.hostname='{}'".format(self.innerJoin,name,ip,hwid,steamid,hostname)
      print(sql)
      cursor.execute(sql)
      result = cursor.fetchone()
      if result:
        return result['id']
      return False

    def checkUser(self, user):
      userID = self.getUserID(user.name, user.ip, user.hwid, user.steamid, user.hostname)
      print(userID)
      if not userID:
        print('User is new')
        keys = {}
        for prop in self.dbMeta.values():
          field = prop['property']
          value = getattr(user, field)

          if self.isNewProperty(value, **prop):
            print("prop {} is new".format(field))
            self.addProperty(value, **prop)
          else:
            print("prop {} is not new".format(field))

          keys[field] = self.getPropertyID(value, **prop)
        self.addUser(keys)
      else:
        print('Player not new, updating last seen')
        self.updateLastSeen('users', userID)

    def updateLastSeen(self, tableName, id):
      cursor = self.conn.cursor()
      sql = "UPDATE {} SET last_seen=CURRENT_TIMESTAMP WHERE id={}".format(tableName, id)
      cursor.execute(sql)
      self.conn.commit()
