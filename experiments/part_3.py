'''
Created on 18 ott 2019

@author: Andrea
'''
from twisted.internet import reactor
import traceback
from time import sleep
import threading

def hello():
  print(f"Hello from the reactor loop! - in {threading.get_ident()}'")
  print("Lately I feel like I'm stuck in a rut.")
  
def raiseError():
  print("raiseError in 3")
  sleep(3)
  raise Exception('I fall down.')
  
class Countdown(object):
 
    counter = 5
    
    def __call__(self):
        if self.counter == 0:
            reactor.stop()
            print(f'stop called ...')
        else:
            print(f'{self.counter} ...')
            self.counter -= 1
            reactor.callLater(1, self)


def callThread_(message):
  for i in range(10):
    print(f'call{message}Thread_{i} - in {threading.get_ident()}')
    sleep(1)


reactor.callWhenRunning(hello)
reactor.callWhenRunning(Countdown())

    
reactor.callFromThread(callThread_, "From")
reactor.callInThread(callThread_, "In")
reactor.callInThread(callThread_, "In2")

print(f"Start - in {threading.get_ident()}")
reactor.run()
print(f"Stop - in {threading.get_ident()}")