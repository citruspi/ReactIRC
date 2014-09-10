import socket
import ssl

class Connection (object):

    connection = None

    ssl_ports = [6697, 7000, 7070]

    def __init__ (self, host, port):

        self.connection = socket.socket()

        # If the port is used for SSL, wrap the socket in SSL/TLS
        if port in self.ssl_ports:

            self.connection = ssl.wrap_socket(self.connection)

        # Initiate a connection to the server
        self.connection.connect((host, port))

    def send (self, string):

        self.connection.send(string)

    def receive (self, size):

        return self.connection.recv(size)
