import time

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from twisted.internet.defer import Deferred
from twisted.python import log

import random


class PongBall(object):

  def __init__(self):
    self.a = 0
    self.velocity_x = 0
    self.velocity_y = 0
    self.pos_x = 0
    self.pos_y = 0
    self.reset_ball()

  def reset_ball(self):
    self.pos_x = 0.5
    self.pos_y = 0.5
    a = random.randint(0, 1)
    if a == 0:
      self.velocity_x = 0.01
    else:
      self.velocity_x = -0.01
    self.velocity_y = random.uniform(-0.004, 0.004)

  def move(self, dt):
    self.pos_x = self.pos_x + self.velocity_x * dt * 60
    self.pos_y = self.pos_y + self.velocity_y * dt * 60
    if self.pos_x < 1.0 / 30.0:
      if self.interact_with_pad(self.match.player1.pad):
        self.bounce(self.match.player1.pad)
      else:
        self.match.player2_score += 1
        self.match.goal("p2")
        self.reset_ball()
    elif self.pos_x > 29.0 / 30.0:
      if self.interact_with_pad(self.match.player2.pad):
        self.bounce(self.match.player2.pad)
      else:
        self.match.player1_score += 1
        self.match.goal("p1")
        self.reset_ball()
    if self.pos_y < 0 or self.pos_y > 1:
      self.velocity_y = -self.velocity_y

  def bounce(self, pad):
    offset = (self.pos_y - pad.center) / 0.214285
    # bounced = (-1 * vx, vy)
    self.velocity_x = -self.velocity_x
    if self.velocity_x < 0.1:
      self.velocity_x = self.velocity_x + 0.001

    if self.velocity_y + offset / 500 > 0.004:
      self.velocity_y = 0.004
    elif self.velocity_y + offset / 500 < -0.004:
      self.velocity_y = -0.004
    else:
      self.velocity_y = self.velocity_y + offset / 500

  def get_position1(self):
    return f"{self.pos_x},{self.pos_y}"

  def get_position2(self):
    return f"{1 - self.pos_x},{self.pos_y}"

  def interact_with_pad(self, player_pad):
    player_start, player_end = player_pad.get_start_and_end()
    if player_start > self.pos_y > player_end:
      return True
    return False


class PlayerPad(object):
  center = 0.5

  def get_start_and_end(self):
    return self.center + 1.1 / 7.0, self.center - 1.1 / 7.0


class PongMatch(object):

  def __init__(self):
    self.player1 = None
    self.player2 = None
    self.player1_score = 0
    self.player2_score = 0

    self.ball = PongBall()
    self.ball.match = self

    self.last_time = 0
    
  def add_player(self, player):
    if not self.player1:
      self.player1 = player
    else:
      self.player2 = player
      
  def ready_to_start(self):
    return self.player1 is not None and self.player2 is not None
      

  def start(self):
    print("A MATCH STARTED")
    self.player1.enemy = self.player2
    self.player2.enemy = self.player1
    
    self.player1.transport.write(f'ename:{self.player2.name}_'.encode())
    self.player2.transport.write(f'ename:{self.player1.name}_'.encode())
    
    data = 'match is starting_'.encode()
    self.player1.transport.write(data)
    self.player2.transport.write(data)

    self.player1.playing = True
    self.player2.playing = True

    self.player1.pad = PlayerPad()
    self.player2.pad = PlayerPad()

    def sleep(secs):
      d = Deferred()
      reactor.callLater(secs, d.callback, None)
      return d

    # sleep(2)
    self.start_set()

  def start_set(self):
    self.serve_ball()

  def serve_ball(self):
    self.l = task.LoopingCall(self.update_ball)
    self.l.start(1.0 / 60.0).addErrback(log.err)

  def update_ball(self):
    if self.last_time != 0:
      dt = time.time() - self.last_time
      self.last_time = time.time()
    else:
      self.last_time = time.time()
      dt = 0

    self.ball.move(dt)
    data_1 = f'ball:{self.ball.get_position1()}_'.encode()
    data_2 = f'ball:{self.ball.get_position2()}_'.encode()
    self.player1.transport.write(data_1)
    self.player2.transport.write(data_2)

  def end_set(self):
    self.l.stop()

  def goal(self, player):
    if player == "p1":
      self.player1.transport.write(b'upoint_')
      self.player2.transport.write(b'epoint_')
    elif player == "p2":
      self.player2.transport.write(b'upoint_')
      self.player1.transport.write(b'epoint_')


class GameServerProtocol(protocol.Protocol):

  def __init__(self, factory):
    self.factory = factory
    self.name = ''
    self.disc_position = 0.0
    self.playing = False
    self.match = None
    self.enemy = None

  def connectionMade(self):
    print('New connection')
    self.factory.numConnections += 1

  def dataReceived(self, data: bytes):
    data = data.decode()
    if self.playing:
      self.pad.center = float(data.split('_')[-2])
      self.update_match(data)
    elif self.playing == False:
      try:
        data = data.split('_')[-2]
        data = data.split(':')
        if data[0] == "find a match":
          self.name = data[1]
          self.find_match()
      except:
        print('wtf2')
    else:
      print('wtf')

  def find_match(self):
    self.match = self.factory.get_match()
    self.match.add_player(self)
    self.factory.start_match(self.match)
    

  def update_match(self, data):
    data = data.split('_')
    data = data[-2]
    self.enemy.transport.write(f"enemy:{data}_".encode())
    self.disc_position = float(data)

  def connectionLost(self, reason):
    if not self.playing:
      self.factory.looking_for_opponent.remove(self.match)
    self.factory.numConnections -= 1
    try:
      self.enemy.transport.write('enemy left the match_'.encode())
      self.enemy.loseConnection()
    except:
      pass
    try:
      self.match.end_set()
      self.factory.finished_matches.append(self.match)
      self.factory.online_matches.remove(self.match)
    except:
      print("already removed")
    print(len(self.factory.finished_matches))
