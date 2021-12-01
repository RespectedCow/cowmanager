# Import libraries
import socket
import threading
import pickle

# Import scripts
from src import database
from src import interpreter
from src import commons

# Classes
class Server:
    
    def __init__(self, address, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((address, port))
        
        sock.listen(5)
        
        # Class variables
        self.address = address
        self.port = port
        self.sock = sock
        self.shouldRun = False
        self.threadCount = 0
        
        self.onlineUsers = {}
        
        # Init database
        self.database = database.UserDatabase("./database.sqlite")
        self.database.setup()
        
    def run(self):
        self.shouldRun = True
        
        while self.shouldRun:
            client, address = self.sock.accept()
            print("Connection from " + address[0])
            threading.Thread(target=self.client_thread(client)).start()
            self.threadCount += 1
            
        self.sock.close()
        
    def stop(self):
        self.shouldRun = False
        
    def client_thread(self, client):
        # Identification
        identification = pickle.loads(client.recv(2048))
        username = identification['username']
        password = identification['password']
        
        # Check if returned data is valid
        if username == None or password == None:
            client.send(pickle.dumps("Incorrect"))
            client.close()
            
        # Init the interpreter
        newInterpreter = interpreter.Interpreter(self.database, username, client)
        
        if self.database.check_if_exist("users", 0, username) and self.database.check_row_column(self.database.get_user("users", username), 1, password) and commons.check_dict(self.onlineUsers, username, True) == False:
            print(f"User {username} logged in.")
            client.send(pickle.dumps("Success"))
            
            # Add user to online user list
            self.onlineUsers[username] = True
            
            while True:
                try:
                    message = pickle.loads(client.recv(2048))
                    print(message)
                    
                    try:
                        return_message = newInterpreter.check_message(message)
                        print(return_message)
                        client.send(pickle.dumps(return_message))
                    except socket.error:
                        print(f"User {username} disconnected.")
                        client.close()
                        self.onlineUsers.pop(username)
                        break                 
                except:
                    print(f"User {username} disconnected.")
                    client.close()
                    self.onlineUsers.pop(username)
                    break
                    
        elif self.database.check_if_exist("users", 0, username) and self.database.check_row_column(self.database.get_user("users", username), 1, password) and commons.check_dict(self.onlineUsers, username, True):
            client.send(pickle.dumps("Same user already logged in."))
            client.close()
        else:
            client.send(pickle.dumps("Incorrect username or password."))
            client.close()