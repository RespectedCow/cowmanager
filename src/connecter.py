'''
Helps the program connect to the server.
'''

# Importing libraries
import socket, time, yaml, pickle
from PyQt5 import QtWidgets, QtGui, QtCore, uic

# Scripts
from src import login
from src import interpreter

# Classes
class ConnectingWindow(QtWidgets.QMainWindow):
    messageReceived = QtCore.pyqtSignal(str)
    connectionLost = QtCore.pyqtSignal()
    connected = QtCore.pyqtSignal()
    
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        
        # Load UI
        uic.loadUi("./lib/uis/connectToServer.ui", self)
        
        # Set icon and title
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("cowicon.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        
        self.setWindowTitle("Connecting to server")
        
        # Class variables
        self.loginWindow = login.LoginWindow()
        
        # Start Thread
        self.connection = ConnectToServer()
        
        # Connect to signals
        self.connection.setProgress.connect(self.progressBar.setValue)
        self.connection.finishedProgress.connect(self.hide)
        self.connection.connectionLost.connect(self.connectionRefused)
        self.connection.createLoginWindow.connect(self.login)
        self.connection.hide.connect(self.hide)
        self.connection.show.connect(self.show)
        self.connection.setLabel.connect(self.label.setText)
        
        # Start thread
        self.connection.start()
        
    def connectionRefused(self, int):
        if int == 1:
            self.label.setText("Connection refused. Server might be down.")
        elif int == 2:
            self.label.setText("You may not be connected to the internet.")
        else:
            self.label.setText("Unexplained error.")     
            
    def login(self):
        if self.loginWindow == None:
            self.loginWindow = login.LoginWindow()
            self.loginWindow.logEvent.connect(self.loggedIn)
            self.loginWindow.show()
        else:
            self.loginWindow.logEvent.connect(self.loggedIn)
            self.loginWindow.show()
            
    def loggedIn(self):
        self.loginWindow.hide()
        self.connection.start()
        
        
class ConnectToServer(QtCore.QThread):
    setProgress = QtCore.pyqtSignal(int)
    finishedProgress = QtCore.pyqtSignal()
    setLabel = QtCore.pyqtSignal(str)
    messageReceived = QtCore.pyqtSignal(str)
    connectionLost = QtCore.pyqtSignal(int)
    connected = QtCore.pyqtSignal()
    createLoginWindow = QtCore.pyqtSignal()
    hide = QtCore.pyqtSignal()
    show = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.server = "192.168.0.165"
        self.port = 3333
        
    def reconnect(self):
        time.sleep(3)
        # Attempt a reconnect
        self.setLabel.emit("Reconnecting")
        time.sleep(2)
        self.run()

    def run(self):
        self.show.emit()
        self.setProgress.emit(0)
        self.setLabel.emit("Connecting to server")
        
        # For visual effects
        for i in range(26):
            self.setProgress.emit(i)
            time.sleep(0.005)
            
        # Check if user entered login credentials
        with open("./data/login.yaml", 'r') as stream:
            loginCres = yaml.safe_load(stream)
        
        if loginCres == None or loginCres['username'] == None and loginCres['password'] == None:
            self.setLabel.emit("User needs to enter login credentials")
            time.sleep(2)
            self.hide.emit()
            self.createLoginWindow.emit()
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            try:
                self.socket.connect((self.server, self.port))
            except ConnectionRefusedError:
                self.connectionLost.emit(1)
                
                self.reconnect()
            except OSError:
                self.connectionLost.emit(2)
                
                self.reconnect()
            except:
                self.reconnect()
            
            # If successfully connected, send identification
            username = loginCres['username'] # Get it
            password = loginCres['password']

            self.socket.send(pickle.dumps({
                'username': username,
                'password': password
            }))
            
            # Get results
            results = pickle.loads(self.socket.recv(2048))
            print(results)
            
            if results == "Success":
                self.setProgress.emit(100)
                self.setLabel.emit("Connected")
                time.sleep(1)
                self.hide.emit()
            else:
                self.setLabel.emit("Incorrect username or password")
                time.sleep(1)
                self.hide.emit()
                self.createLoginWindow.emit()
                
            # Init interpreter
            sage = interpreter.Interpreter()
                
            # Main loop
            while True:
                message = pickle.loads(self.socket.recv(2048))
                
                if not message:
                    self.connectionLost.emit()
                    time.sleep(2)
                    self.run()
                
                response = sage.get_interpretation()
                
                try:
                    self.socket.send(pickle.dumps(response))
                except socket.error:
                    self.connectionLost.emit()
                    time.sleep(2)
                    self.run()