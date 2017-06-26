#!/usr/bin/env python

# This file is part of the Printrun suite.
#
# Printrun is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Printrun is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Printrun.  If not, see <http://www.gnu.org/licenses/>.

from printrun.eventhandler import PrinterEventHandler

from Queue import Queue, Empty as QueueEmpty
import threading
import traceback as tr
import time
import serial

class LedStatus(PrinterEventHandler):
    '''
    LED status representation via arduino using /dev/ttyACM0 to
    send out status numbers.
    '''
    STATUS_OFF = 0
    STATUS_ON = 1
    STATUS_ANIM = 2
    
#     PRINT_OFF = 0
#     PRINT_PREHEAT = 1
#     PRINT_ON = 2
    
    def __init__(self):
        self._queue = Queue(0)
        self._loop = True
        self._printing = False
        self._printanim = 4
        self._light_status = LedStatus.STATUS_ANIM
        self._thread = None
        self._port = serial.Serial('/dev/ttyACM0')

#     def on_init(self):
#         self.__enqueue(self.__light_on)
#         
#     def on_send(self, command, gline):
#         self.__write("on_send", command)
#
#     def on_recv(self, line):
#         self.__write("on_recv", line)
#     
#     def on_connect(self):
#         if not self._thread.is_alive():
#             self._loop = True
#             self._queue = Queue()
#             self._thread.start()
#             print "thread started"
#         self.__enqueue(self.__light_on)

    def on_disconnect(self):
        self.__enqueue(self.__light_off)
        self._loop = False
        if self._thread:
            self._thread.join(10.0)
            self._thread = None
     
#     def on_error(self, error):
#         self.__write("on_error", error)
#         
    def on_online(self):
        if not self._thread:
            self._loop = True
            self._queue = Queue()
            self.__enqueue(self.__light_on)
            self._thread = threading.Thread(target = self.__queue_thread)
            self._thread.start()
        self.__enqueue(self.__light_on)
         
#     def on_temp(self, line):
#         self.__write("on_temp", line)

    def on_start(self, resume):
        self.__enqueue(self.__light_off)
        self._printing = True
        self.__enqueue(self.__next_printanim)
         
    def on_end(self):
        self.__enqueue(self.__light_on)
        self._printing = False
         
    def on_layerchange(self, layer):
        if self._printing:
            self.__enqueue(self.__next_printanim)
 
#     def on_preprintsend(self, gline, index, mainqueue):
#         self.__write("on_preprintsend", gline)
#     
#     def on_printsend(self, gline):
#         self.__write("on_printsend", gline)

    def __serial_write(self, data):
        '''
        Writes some bytes of binary data out to the serial port.
        '''
        print ">>> out: %s <<<" % (data)
        self._port.write(data)
        self._port.flush()
        
    def __enqueue(self, function):
        try:
            self._queue.put_nowait(function)
        except:
            tr.print_exc()

    def __handle_queue(self):
        try:
            entry = self._queue.get(True, timeout = 1)
            entry()
        except QueueEmpty:
            pass
    
    def __queue_thread(self):
        print "led-thread started"
        while self._loop:
            self.__handle_queue()
            #data = self._port.read_all()
            #if len(data) > 0:
            #    print ">>> %s <<<" % (data.strip())
        print "led-thread ended"

    def __light_on(self):
        '''
        Turns the lights on.
        
        Light on means white light.
        
        This blocks until the light has been turned on.
        '''
        if self._light_status == LedStatus.STATUS_ON:
            return
        self._light_status = LedStatus.STATUS_ON
        self.__serial_write("9")
        time.sleep(2.5)
    
    def __light_off(self):
        '''
        Turns the lights off.
        
        Lights off means fading to black. This blocks
        until the lights are turned off.
        '''
        if self._light_status == LedStatus.STATUS_OFF:
            return
        self._light_status = LedStatus.STATUS_OFF
        self.__serial_write("0")
        time.sleep(2.5)
    
    def __next_printanim(self):
        '''
        Starts playing the next printing animation.
        '''
        self._printanim += 1
        self._printanim %= 4
        self._light_status = LedStatus.STATUS_ANIM
        self.__serial_write("%c" % (self._printanim + 1 + 0x30))

