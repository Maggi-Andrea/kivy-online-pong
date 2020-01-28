

from core.factory import GameServerFactory
from unittest.mock import MagicMock, call

PLAYER_1 = 'Player1'
PLAYER_2 = 'Player1'

def test_handshaking():
  gsf = GameServerFactory()
  assert gsf.numConnections == 0
  assert len(gsf.looking_for_opponent) == 0
  
  protocol_1 = gsf.buildProtocol(addr=None)
  protocol_1.transport = MagicMock()
  
  protocol_1.connectionMade()
  assert gsf.numConnections == 1
  assert len(gsf.looking_for_opponent) == 0
  
  assert protocol_1.playing == False
  assert protocol_1.match == None
  assert protocol_1.enemy == None
  assert protocol_1.name == ''
  
  protocol_1.dataReceived(f'find a match:{PLAYER_1}_'.encode())
  assert gsf.numConnections == 1
  assert len(gsf.looking_for_opponent) == 1
  assert protocol_1.playing == False
  assert protocol_1.match
  assert protocol_1.enemy == None
  assert protocol_1.name == PLAYER_1
  
  protocol_2 = gsf.buildProtocol(addr=None)
  protocol_2.transport = MagicMock()
  protocol_2.connectionMade()
  assert gsf.numConnections == 2
  assert len(gsf.looking_for_opponent) == 1
  
  assert protocol_2.playing == False
  assert protocol_2.match == None
  assert protocol_2.enemy == None
  assert protocol_2.name == ''
  
  protocol_2.dataReceived(f'find a match:{PLAYER_2}_'.encode())
  assert gsf.numConnections == 2
  assert len(gsf.looking_for_opponent) == 0
  
  assert protocol_2.playing == True
  assert protocol_2.match
  assert protocol_2.enemy
  assert protocol_2.name == PLAYER_2
  
  assert protocol_1.playing == True
  assert protocol_1.match
  assert protocol_1.enemy
  assert protocol_1.name == PLAYER_1
  
  assert protocol_1.transport.write.call_args_list == [
    call(f'ename:{PLAYER_2}_'.encode()),
    call(f'match is starting_'.encode()),
    call(f'ball:0.5,0.5_'.encode())
  ]
  
  assert protocol_2.transport.write.call_args_list == [
    call(f'ename:{PLAYER_1}_'.encode()),
    call(f'match is starting_'.encode()),
    call(f'ball:0.5,0.5_'.encode())
  ]
  
  assert protocol_1.match == protocol_2.match
  assert protocol_1.enemy == protocol_2
  assert protocol_2.enemy == protocol_1
  
  
  
  
  
  
  