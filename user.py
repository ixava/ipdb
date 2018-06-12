from socket import inet_aton, inet_ntoa
from struct import unpack

class User:
  def __init__(self, ip, hostname, steamid, name, hwid, **seen):
    self.string_ip = ip if type(ip) == str else self.stringIP(ip)
    self.ip = ip if type(ip) == str else self.longIP(ip)
    self.hostname = hostname
    self.steamid = steamid
    self.name = name
    self.name_escaped = name.replace("'","\\'")
    self.hwid = hwid

  @staticmethod
  def longIP(ip):
    pack = inet_aton(ip)
    value = unpack("!L", pack)[0]
    return value

  @staticmethod
  def stringIP(long):
    pack = struct.pack('!I', long)
    addr = inet_ntoa(pack)
    return addr