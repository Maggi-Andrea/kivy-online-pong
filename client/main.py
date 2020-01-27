#install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

from network import GameNetworkFactory
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout

from kivy.properties import NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.uix.popup import Popup

from twisted.internet import reactor


class PongBall(Widget):

    def move(self, x, y):
        x = x * self.pong_game.width - self.width/2
        y = y * self.pong_game.height - self.height/2
        self.pos = (x, y)


class PongPaddle(Widget):
    score = NumericProperty(0)


class PongGame(Widget):
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)

    def __init__(self, connection, **kwargs):
        super(PongGame, self).__init__(**kwargs)
        self.connection = connection

    def serve_ball(self, vel=(4, 0)):
        self.ball.center = self.center
        self.ball.velocity = vel
        self.ball.pong_game = self

    def on_touch_move(self, touch):
        self.player1.center_y = touch.y
        data = self.player1.center_y / float(self.height)
        data = "%f_" % data
        self.connection.write(data.encode())

    def update_enemy(self, position):
        location = position * self.height
        self.player2.center_y = location

    def update_ball(self, x, y):
        self.ball.move(x, y)


def exit_game(dt):
    import sys
    sys.exit(0)

class PongApp(App):
    connection = None
    state = None

    player1_name = ""
    player2_name = None

    game = None

    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.button = Button(text="Que for A Game", on_press=self.que_for_game)
        self.textinput = TextInput(hint_text="Enter Your Name")
        self.layout.add_widget(self.textinput)
        self.layout.add_widget(self.button)
        return self.layout

    def que_for_game(self, what):
        self.state = "in_que"
        self.player1_name = self.textinput.text
        self.connect_to_server()
        self.layout.remove_widget(self.button)
        self.label = Label(text="Wait For A Player")
        self.layout.add_widget(self.label)

    def start_game(self):        
        self.state = "in_game"
        self.layout.clear_widgets()
        self.game = PongGame(self.connection)
        self.game.serve_ball()
        # Clock.schedule_interval(self.game.update, 1.0 / 60.0)
        self.layout.add_widget(self.game)

    def clientConnectionFailed(self):
        self.textbox = TextInput(size_hint_y=.1, multiline=False)
        self.textbox.bind(on_text_validate=self.send_message)
        self.label = Label(text='connecting...\n')
        self.layout = BoxLayout(orientation='vertical')
        self.layout.add_widget(self.label)
        self.layout.add_widget(self.textbox)
        return self.layout

    def connect_to_server(self):
        reactor.connectTCP('localhost', 8000, GameNetworkFactory(self))

    def on_connection(self, connection):
        self.connection = connection

    def exit_popup():
        pu = Popup(title='Game Notification',
                   content=Label(text='The Enemy Ran Away !'),
                   size_hint=(0.5, 0.5), auto_dismiss=False)
        pu.open()
        Clock.schedule_once(exit_game, 4)

    def send_message(self):
        pass


if __name__ == '__main__':
    PongApp().run()