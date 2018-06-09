from socket import inet_aton
from struct import unpack

class User:
  def __init__(self, ip, hostname, steamid, name, hwid, **seen):
    self.string_ip = ip
    self.ip = self.longIP(ip)
    self.hostname = hostname
    self.steamid = steamid
    self.name = name
    self.hwid = hwid

  @staticmethod
  def longIP(ip):
    pack = inet_aton(ip)
    value = unpack("!L", pack)[0]
    return value