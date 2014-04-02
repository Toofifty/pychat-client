'''
PyChat Client
Acts as a makeshift client for a
low-scale IRC server

Currently limited to one channel at a time.

@author: Alex Matheson
'''

import socket
import ConfigParser
import threading
import traceback
import sys
import time
import Tkinter
from threading import Thread

class ChatBox(Tkinter.Tk):
    def __init__(self, parent, client):
        Tkinter.Tk.__init__(self, parent)
        self.parent = parent
        self.client = client
        self.initialize()
        
    def initialize(self):
        self.grid()
        
        self.entry_variable = Tkinter.StringVar()
        self.entry = Tkinter.Entry(self, textvariable=self.entry_variable)
        self.entry.grid(column=0, row=1, sticky='EW')
        self.entry.bind('<Return>', self.on_press_enter)
        
        button = Tkinter.Button(self, text=u'Send',
                                command=self.on_button_click)
        button.grid(column=1, row=1)
        
        self.label_variable = Tkinter.StringVar()
        #chat = Tkinter.Listbox(self, fg='white', bg='blue')
        #chat.grid(column=0, row=0, columnspan=2, sticky='EW')
        
        #scrollbar = Tkinter.Scrollbar(self, orient=Tkinter.VERTICAL)
        #scrollbar.pack(side='left', fill='y')
        
        self.grid_columnconfigure(0, weight=1)
        self.resizable(True, False)
        self.update()
        self.geometry(self.geometry())
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

    def on_button_click(self):
        self.label_variable.set(self.entry_variable.get())
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)
        process_message(self.client, self.entry_variable.get())
        self.entry_variable.set('')
        
    def on_press_enter(self, event):
        self.label_variable.set(self.entry_variable.get())
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)
        process_message(self.client, self.entry_variable.get())
        self.entry_variable.set('')
        
class IRC(socket.socket):
    """Main Class"""
    def __init__(self, config):
        socket.socket.__init__(self)
        self.nick = raw_input('Please enter a nickname: ')
        print 'Thanks! Name set to \'%s\'.\n' % self.nick
        print 'Use the pop-up box to chat.\n'
        time.sleep(2)
        self.name = self.nick
        self.host = config.get('Configuration', 'host')
        self.port = config.getint('Configuration', 'port')
        self.verbose = config.getboolean('Configuration', 'verbose')
        self.channels = []
        self.current_channel = None
        
    def send_irc(self, message):
        # May want to add other things here
        if self.verbose:
            print '...', message
        self.send('%s\r\n' % message)
        
    def start(self):
        try:
            self.connect((self.host, self.port))
            self.send_irc('NICK %s' % self.nick)
            self.send_irc('USER %s %s bla :CLIENT' % (self.nick, self.host))
        except Exception, e:
            print e
            raise
            
    def pong(self, id):
        self.send_irc('PONG :%s' % id)
        
    def join(self, channel):
        self.send_irc('JOIN %s' % channel)
        self.channels.append(channel)
        self.current_channel = channel
        
    def privmsg(self, recipient, message):
        self.send_irc('PRIVMSG %s :%s' % (recipient, message))
        
    def set_nick(self, nick):
        self.send_irc('NICK %s' % nick)
        self.nick = nick
        
    def get_users(self):
        self.send_irc('LUSERS')
        
    def get_channels(self):
        return self.channels
        
class Input(threading.Thread):
    """Get user input"""
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        
    def run(self):
        self.get_input(self.client)        
        
    def get_input(self, client):
        while True:
            message = raw_input('>>')
            if message.startswith('/'):
                message = message.replace('/', '')
                command = message.split(' ', 1)[0]
                try:
                    args = message.split(' ')[1:]
                except Exception, e:
                    traceback.print_exc()
                    args = []
                process_command(client, command, args)
            elif message.startswith('#'):
                channel, message = message.split(' ', 1)
                client.privmsg(channel, message)
                print '<%s(%s)> %s' % (client.nick, channel, message)
            elif client.channel is not None:
                client.privmsg(client.current_channel, message)
                print '<%s(%s)> %s' % (client.nick, client.current_channel, message)
            else:
                print 'You need to join a channel first.'
                print 'Use /join [#channel] to join one.'
            time.sleep(1)
        
def configuration():
    config = ConfigParser.ConfigParser()
    config.read('config.cfg')
    return config
    
def process_message(client, message):
    if message.startswith('/'):
        message = message.replace('/', '')
        command = message.split(' ', 1)[0]
        try:
            args = message.split(' ')[1:]
        except Exception, e:
            traceback.print_exc()
            args = []
        process_command(client, command, args)
    elif client.channel is not None:
        client.privmsg(client.channel, message)
        print '<%s(%s)> %s' % (client.nick, client.current_channel, message)
    else:
        print 'You need to join a channel first.'
        print 'Use /join [#channel] to join one.'
    
def process_command(client, command, args): 

    if command == 'join' or command == 'channel':
        if len(args) > 0:
            client.join(args[0])
        else:
            print 'Insufficient parameters.'
            print 'Usage: /join [#channel]'
            
    elif command == 'msg':
        if len(args) > 1:
            client.privmsg(args[0], ' '.join(args[1:]))
            print '<YOU(-->%s)> %s' % (args[0], ' '.join(args[1:]))
        else:
            print 'Insufficient parameters.'
            print 'Usage: /msg [user] [message...]'
            
    elif command == 'help':
        help_list = [
            ('MSG [USER] [MESSAGE...]',
             'Private message a user'),
            ('JOIN [#CHANNEL]',
             'Join/switch to specified channel'),
            ('PART <#CHANNEL>',
             'Part (leave) current or specific channel'),
            ('NICK [NICK]',
             'Change your nick'),
            ('TOPIC [MESSAGE...]',
             'Set the topic of your current channel'),
            ('GETCHANNEL',
             'Return the current channel you are speaking in'),
            ('QUIT',
             'Close the session - may take a moment to fully exit.'),
            ('.',
             'Throw some errors and shit so it looks like an errored program'),
            ('RAW [ARGS...]',
             'Send raw arguments to the server - only use if you know what'
             'you\'re doing')
        ]
        print 'Basic commands:'
        
        for help in help_list:
            p_1 = help[0].ljust(25)
            p_2 = help[1]
            print '\t%s > %s' % (p_1, p_2)
        
    elif command == 'raw':
        client.send_irc(' '.join(args))
        
    elif command == 'part':
        client.send_irc('PART %s' % client.channel)
        
    elif command == 'quit':
        client.send_irc('QUIT')
        print 'Stopping client...'
        raise SystemExit
        
    elif command == 'nick':
        if len(args) > 0:
            client.set_nick(args[0])
            print 'Nick changed to', args[0]
        else:
            print 'Insufficient parameters'
            print 'Usage: /nick [nick]'
            
    elif command == 'users':
        pass
        
    elif command == 'topic':
        if len(args) > 0:
            client.send_irc('TOPIC %s :%s' % (client.channel, ' '.join(args)))
        else:
            print 'Insufficient parameters'
            print 'Usage: /topic [message...]'
            
    elif command == 'broadcast':
        for c in client.get_channels():
            client.privmsg(c, ' '.join(args)
    
    elif command == 'getchannel':
        print 'Current channel:', client.channel
    
    elif command == '.':
        if len(args) > 0:
            amount = int(args[0])
        else:
            amount = 5
        for i in range(amount):
            try:
                raise WindowsError
            except:
                traceback.print_exc()
        
    else:
        print 'Unknown command'
    
def start_input(client):
    app = ChatBox(None, client)
    app.title('Chat - DO NOT CLOSE ME')
    app.mainloop()
    
def main(client):    
    #input = Input(client)
    #input.start()
    
    read_buffer = ''
    
    RUNNING = True
    while RUNNING:
        try:
            read_buffer += client.recv(32)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            traceback.print_exc()
            
        temp = read_buffer.split('\n')
        read_buffer = temp.pop()
        
        for line in temp:
            #print line
            if 'MOTD' in line:
                client.joinchannel
            
            if line.startswith('PING'):
                client.pong(line.replace('PING :', ''))
                break
            
            line_separated = line.split(' ')
            
            if not '!' in line_separated[0]:
                if '353' in line_separated[1]:
                    line_separated[4] = line_separated[4].replace(':', '')
                    print 'Users in session: %s' % ' '.join(line_separated[4:])
                else:
                    out = ' '.join(line_separated[3:]).split(':', 1)[1]
                    print 'SERVER: %s' % out
            else:
                nick = line_separated[0].split('!', 1)[0].replace(':', '')
                type = line_separated[1]
                recipient = line_separated[2]
                if type == 'PRIVMSG' and recipient.startswith('#'):
                    message = ' '.join(line_separated[3:]).replace(':', '')
                    print '<%s(%s)> %s' % (nick, recipient, message)
                elif type == 'PRIVMSG':
                    message = ' '.join(line_separated[3:]).replace(':', '')
                    print '<%s(-->YOU)> %s' % (nick, message)
                elif type == 'JOIN':
                    print '== %s has joined %s' % (nick, recipient)
                elif type == 'PART':
                    print '== %s has left %s' % (nick, recipient)
                elif type == 'NICK':
                    print '== %s has changed nick to %s' % (nick, recipient.replace(':', ''))
                elif type == 'QUIT':
                    print '== %s has quit' % nick
                else:
                    print line

if __name__ == '__main__':
    config = configuration()
    client = IRC(config)
    client.start()
    
    p1 = Thread(target=main, args=(client,))
    p1.start()
    p2 = Thread(target=start_input, args=(client,))
    p2.start()
    p1.join()
    p2.join()
