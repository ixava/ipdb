import pymysql.cursors

class IPDB:
    def __init__(self, cfg):
      self.conn = pymysql.connect(host=cfg["host"],
                                  user=cfg["user"],
                                  password= cfg['password'] if 'password' in cfg else '',
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

    def addUser(self, user):
      cursor = self.conn.cursor()
      sql = 'INSERT IGNORE INTO users (name_id,ip_id,hwid_id,hostname_id,steamid_id) VALUES({},{},{},{},{})'.format(user.name_escaped,user.ip,user.hwid,user.hostname,user.steamid)
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

    def getByProperty(self, value, property, tableName):
      cursor = self.conn.cursor()
      foreign_key = tableName + '.' + property
      sql = "SELECT {} FROM users {} WHERE {} LIKE '%{}%'".format(self.selectFields, self.innerJoin, foreign_key, value)
      cursor.execute(sql)
      result = cursor.fetchall()
      if result:
        return result
      return False

    def getUserID(self, name_escaped, ip, hwid, steamid, hostname):
      cursor = self.conn.cursor()
      sql = "SELECT users.id FROM users {} WHERE names.name='{}' AND ips.ip={} AND hwids.hwid='{}' AND steamids.steamid='{}' AND hostnames.hostname='{}'".format(self.innerJoin,name_escaped,ip,hwid,steamid,hostname)
      print(sql)
      cursor.execute(sql)
      result = cursor.fetchone()
      if result:
        return result['id']
      return False

    def updateLastSeen(self, tableName, id):
      cursor = self.conn.cursor()
      sql = "UPDATE {} SET last_seen=CURRENT_TIMESTAMP WHERE id={}".format(tableName, id)
      cursor.execute(sql)
      self.conn.commit()
