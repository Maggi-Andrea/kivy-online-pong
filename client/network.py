
#A simple Client that send messages to the echo server
from twisted.internet import protocol




class GameNetworkClient(protocol.Protocol):

    def connectionMade(self):
        self.factory.app.on_connection(self.transport)
        name = str(self.factory.app.player1_name)
        data = f"find a match:{name}_".encode()
        self.transport.write(data)

    def dataReceived(self, data: bytes):
        data = data.decode()
        print(data)
        try:
            data_list = data.split('_')
        except:
            pass
        while data_list != []:
            what = data_list.pop(0)

            if self.factory.app.state == "in_que":
                if self.factory.app.player2_name or self.factory.app.player2_name == "":
                    if what == "match is starting":
                        self.factory.app.start_game()
                else:
                    what = what.split(':')
                    if what[0] == "ename":
                        self.factory.app.player2_name = what[1]
                    else:
                        print('wtf data')
                        print(what)

            elif self.factory.app.state == "in_game":
                if what == "epoint":
                    self.factory.app.game.player2.score += 1
                elif what == "upoint":
                    self.factory.app.game.player1.score += 1
                elif what == "enemy left the match":
                    self.factory.app.exit_popup()
                else:
                    what = what.split(':')
                    if what[0] == "ball":
                        ball_position = what[1].split(',')
                        self.factory.app.game.update_ball(float(ball_position[0]), float(ball_position[1]))
                    elif what[0] == "enemy":
                        self.factory.app.game.update_enemy(float(what[1]))


class GameNetworkFactory(protocol.ClientFactory):

    protocol = GameNetworkClient

    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        print("connection lost")

    def clientConnectionFailed(self, conn, reason):
        print("connection failed")
        print(reason)
