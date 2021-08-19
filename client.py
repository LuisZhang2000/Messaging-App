#Python 3
#Usage: python3 client.py localhost 12000
#coding: utf-8
from socket import *
from select import *
from helper import *
import sys
import errno
import threading

if len(sys.argv) != 3:
    print(f"Wrong number of arguments. Usage: python3 client.py localhost (port number)")
    sys.exit(1)

serverName = sys.argv[1]
serverPort = int(sys.argv[2])

# Initialise TCP client socket 
clientSocket = socket(AF_INET, SOCK_STREAM)

# Connect TCP client socket to server socket
try:
    clientSocket.connect((serverName, serverPort))
except Exception:
    print("Connection failed")
    sys.exit(1)

print(f"TCP Connection established with server {serverName} and port no. {serverPort}")

# Intialise UDP socket (for p2p connection)
UDPsocket = socket(AF_INET, SOCK_DGRAM)
UDPsocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

clientAddr = clientSocket.getsockname()[0]
clientPortNum = clientSocket.getsockname()[1]

UDPsocket.bind((clientAddr, clientPortNum))

# List of client_ socket and p2p_socket sockets for select()
socket_list = [clientSocket, UDPsocket]

# List of p2p client sockets created
# contains client-owner, server-owner
online_p2p_clients = {}

while 1:
    # get the user to input their login details and remove any whitespace
    username = input("> Username: ").strip()
    password = input("> Password: ").strip()
    credentials = username + " " + password

    clientSocket.send(credentials.encode('utf-8'))

    serverMessage = clientSocket.recv(1024)
    print(serverMessage.decode('utf-8'))
    
    if 'Welcome' in serverMessage.decode('utf-8'):
        break

    if 'Your account has been blocked' in serverMessage.decode('utf-8'):
        clientSocket.close()
        sys.exit(1)

# After client has successfully logged in, start an infinite loop and await for commands from user input
while 1:
    userInput = input("> Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD): ")
    userInputStrings = userInput.split()
    command = userInputStrings[0]
    
    # Ensure that the command entered is either MSG, DLT, EDT, RDM, ATU, OUT or UPD
    if (command != "MSG" and command != "DLT" and command != "EDT" and command != "RDM" and command != "ATU" and command != "OUT" and command != "UPD"):
        print("> Error. Invalid command!")

    elif command == "MSG" or command == "DLT" or command == "EDT" or command == "RDM" or command == "ATU":
        clientSocket.send(userInput.encode('utf-8'))
        serverMessage = clientSocket.recv(1024)
        print(serverMessage.decode('utf-8'))
        
    elif command == "OUT":
        clientSocket.send(userInput.encode('utf-8'))
        serverMessage = clientSocket.recv(1024)
        print(serverMessage.decode('utf-8'))
        break

    elif command == "UPD":       
        audienceUser = userInput[1]
        filename = userInput[2]
        if audienceUser == username:
            print("> Can't send file to yourself!")
        
        else:
            sent = False
            for clientSocket in online_p2p_clients:
                if online_p2p_clients[clientSocket]['audience'] == audienceUser:
                    clientSocket.send(filename.encode('utf-8'))
                    sent = True
                    print(f'p2p message sent to {audienceUser}!')
                    break
            if not sent:
                # Create new socket and connect it to the audience user's IP and port number
                print(f'Attempting to connect {serverName} : {serverPort}')
                newSocket = socket(AF_INET, SOCK_STREAM)
                newSocket.connect((serverName, int(serverPort)))
                print(f'newSocket: {newSocket.getsockname()}')

                p2p_user = {}
                p2p_user['presenter'] = username
                p2p_user['audience'] = audienceUser

                online_p2p_clients[newSocket] = p2p_user
                newSocket.send(f"p2p connection established between {username} and {audienceUser}".encode('utf-8'))

                newSocket.send(f"{filename}".encode('utf-8'))
                print(f'p2p message sent to {audienceUser}')

clientSocket.close()

def handleUDPClient(conn, addr):
    print(f"NEW CONNECTION {addr} connected.")

    connected = True
    while connected:
        msg = conn.recv(1024)
    # receive data from other clients + sava data as local file
    

def startP2P():
    conn, addr = clientSocket.accept()
    UDPThread = threading.Thread(target=handleUDPClient, args=(conn, addr))
    UDPThread.start()
    print(f'Connection established, clientSocket: {clientSocket.getsockname()}, clientAddr: {addr}')
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


