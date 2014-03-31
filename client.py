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

class IRC(socket.socket):
    """Main Class"""
    def __init__(self, config):
        socket.socket.__init__(self)
        self.nick = config.get('Configuration', 'nick')
        self.host = config.get('Configuration', 'host')
        self.port = config.getint('Configuration', 'port')
        self.verbose = config.getboolean('Configuration', 'verbose')
        self.channel = None
        
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
        self.channel = channel
        
    def privmsg(self, recipient, message):
        self.send_irc('PRIVMSG %s :%s' % (recipient, message))
        
class Input(threading.Thread):
    """Get user input"""
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        #self.start()
        
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
            elif client.channel is not None:
                client.privmsg(client.channel, message)
                print '<%s(%s)> %s' % (client.nick, client.channel, message)
            else:
                print 'You need to join a channel first.'
                print 'Use /join [#channel] to join one.'
            time.sleep(1)
        
def configuration():
    config = ConfigParser.ConfigParser()
    config.read('config.cfg')
    return config
    
def process_command(client, command, args): 

    if command == 'join':
        if len(args) > 0:
            client.join(args[0])
        else:
            print 'Insufficient arguments.'
            print 'Usage: /join [#channel]'
            
    elif command == 'msg':
        if len(args) > 1:
            client.privmsg(args[0], ' '.join(args[1:]))
            print '<YOU(-->%s)> %s' % (args[0], ' '.join(args[1:]))
        else:
            print 'Insufficient arguments.'
            print 'Usage: /msg [user] [message...]'
            
    elif command == 'help':
        print 'Basic commands:'
        print '\tMSG [USER] [MESSAGE...] > Private message a user'
        print '\tJOIN [#CHANNEL] > Join/switch to the specified channel'
        print '\tPART > Part (leave) the current channel'
        print '\tQUIT > Close the session. May take a moment to fully exit.',
        print 'CTRL+C will terminate the script quickly once /quit is executed.'
        print '\tRAW [ARGS...] > Send raw arguments to the server.',
        print 'Only use if you know what you\'re doing.'
        
    elif command == 'raw':
        client.send_irc(' '.join(args))
        
    elif command == 'part':
        client.send_irc('PART %s' % client.channel)
        
    elif command == 'quit':
        client.send_irc('QUIT')
        print 'Stopping client...'
        sys.exit()
        
    else:
        print 'Unknown command'
    
def main():
    config = configuration()
    client = IRC(config)
    client.start()
    
    input = Input(client)
    input.start()
    
    read_buffer = ''
    
    RUNNING = True
    while RUNNING:
        try:
            read_buffer += client.recv(1024)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            traceback.print_exc()
            
        temp = read_buffer.split('\n')
        read_buffer = temp.pop()
        
        for line in temp:
            #print line
            
            if line.startswith('PING'):
                client.pong(line.replace('PING :', ''))
                break
            
            line_separated = line.split(' ')
            
            if not '!' in line_separated[0]:
                if '353' in line_separated[1]:
                    line_separated[4] = line_separated[4].replace(':', '')
                    print 'Users in session: %s' % ' '.join(line_separated[4:])
                else:
                    print 'SERVER: %s' % ' '.join(line_separated[1:])
            else:
                nick = line_separated[0].split('!', 1)[0].replace(':', '')
                type = line_separated[1]
                recipient = line_separated[2]
                if type == 'PRIVMSG' and recipient.startswith('#'):
                    message = ' '.join(line_separated[3:])
                    print '<%s(%s)> %s' % (nick, recipient, message)
                elif type == 'PRIVMSG':
                    message = ' '.join(line_separated[3:])
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
    main()