from .protocol import GameServerProtocol, PongMatch


from twisted.internet.protocol import Factory


class GameServerFactory(Factory):
  numConnections = 0

  looking_for_opponent = []
  online_matches = []

  finished_matches = []

  def __init__(self):
    print("Server is Running...")

  def buildProtocol(self, addr):
    return GameServerProtocol(self)
  
  def get_match(self):
    if len(self.looking_for_opponent) == 0:
      match = PongMatch()
      self.looking_for_opponent.append(match)
    else:
      match = self.looking_for_opponent.pop()
    return match
    
  def start_match(self, match):
    if match.ready_to_start():
      self.online_matches.append(match)
      match.start()
    
