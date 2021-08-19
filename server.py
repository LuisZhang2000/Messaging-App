# Usage: python3 server.py 12000 3
#coding: utf-8
from socket import *
from helper import *
from select import *
import time
import datetime
import sys
import threading

if len(sys.argv) != 3:
    print(f"Wrong number of arguments. Usage: python3 server.py (port number) (maxLoginAttempts)")
    sys.exit(1)

if isInteger(sys.argv[2]) == False:
    print(f"Invalid number of allowed failed consecutive attempts: {sys.argv[2]}. The valid value of argument number is an integer between 1 and 5")
    sys.exit(1)

serverPort = int(sys.argv[1]) 
maxLoginAttempts = int(sys.argv[2])

if maxLoginAttempts < 1 or maxLoginAttempts > 5:
    print(f"Invalid number of allowed failed consecutive attempts: {maxLoginAttempts}. The valid value of argument number is an integer between 1 and 5")
    sys.exit(1)

# Define server socket
# AF_INET -> IPv4, SOCK_STREAM -> TCP (whereas SOCK_DGRAM -> UDP)
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Assign serverPort to server's socket
serverSocket.bind(('localhost', serverPort))

# Listen for client connection requests
serverSocket.listen(1)

# list of sockets, initially only containing serverSocket
socketList = [serverSocket]

# List for storing clients blocked for too many failled login attempts
blockedClients = []

#List of clients that have successfully logged in
onlineClients = []

# Global variable for storing message number in messagelog.txt
messageNum = 1

print("The server is ready to receive")

def handleClient(connectionSocket, clientAddress):

    global messageNum
    loginAttempts = 0

    while (1):
        user = connectionSocket.recv(1024).decode('utf-8')

        # If False, client disconnected before sending credentials
        if user is False:
            break

        credentials = user.split()
        clients = {}

        # Check if the client has been blocked
        if checkBlocked(blockedClients, credentials[0], connectionSocket) == True:
            continue

        result = authenticate(credentials) 

        # if client enters correct login info, log client in 
        if 'Login Successful' in result:
            logIn(connectionSocket, credentials[0], addr[0], serverPort)
            clients['username'] = credentials[0]
            clients['last-active'] = datetime.datetime.now()
            onlineClients.append(clients)
            break

        # if client enters incorrect password
        elif 'Invalid Password' in result:
            loginAttempts += 1
            # if client uses all login attempts unsuccessfully, add to blocked list 
            if (loginAttempts >= maxLoginAttempts):
                connectionSocket.send("> Invalid Password. Your account has been blocked. Please try again later".encode('utf-8'))
                clients['username'] = credentials[0]
                clients['blockedStartTime'] = datetime.datetime.now()
                blockedClients.append(clients)
            else:
                connectionSocket.send(f"> Invalid Password. Please try again".encode('utf-8'))

        # if client enters a username which doesn't exist
        elif 'Invalid Username' in result:
            connectionSocket.send("> Invalid Username. Please try again.".encode('utf-8'))

        else:
            connectionSocket.send("Username and password should each be only one word!".encode('utf-8'))

    # infinite loop for client to enter commands
    while 1:
        message = connectionSocket.recv(1024).decode('utf-8')
        userInput = message.split()
        command = userInput[0]

        # Message operation
        if (command == "MSG"):
            msgWithoutCommand = listToString(userInput[1:])
            print(f"> {credentials[0]} posted MSG #{messageNum} '{msgWithoutCommand}' at {datetime.datetime.now().strftime('%d %b %Y %X')}")
            currentTime = datetime.datetime.now().strftime('%d %b %Y %X')
            connectionSocket.send(f"> Message #{messageNum} posted at {currentTime}".encode('utf-8'))
            writeToMsgLog(messageNum, credentials[0], msgWithoutCommand)
            messageNum = messageNum + 1

        # Delete operation
        elif (command == "DLT"):
            userMsgNum = userInput[1]
            userTimeStamp = listToString(userInput[2:6]).replace(';', '')
            if len(userInput) != 6:
                connectionSocket.send("> Usage: DLT messagenumber timestamp\n  e.g. DLT 1 19 Feb 2021 21:39:04".encode('utf-8'))
            elif isInteger(userMsgNum) == False:
                connectionSocket.send("> Message number must be an integer!".encode('utf-8'))
            else:
                deleteMessage(userMsgNum, userTimeStamp, credentials[0], connectionSocket)
                messageNum = messageNum - 1

        # Edit operation
        elif (command == "EDT"):
            userMsgNum = userInput[1]
            userTimeStamp = listToString(userInput[2:6]).replace(';', '')
            editedMsg = listToString(userInput[6:])
            if len(userInput) < 6:
                connectionSocket.send("> Usage: EDT messagenumber timestamp message\n  e.g. EDT 1 19 Feb 2021 21:39:04 do or do not".encode('utf-8'))
            elif isInteger(userMsgNum) == False:
                connectionSocket.send("> Message number must be an integer!".encode('utf-8'))
            else:
                editMessage(userMsgNum, userTimeStamp, credentials[0], editedMsg, connectionSocket)

        # Read new messasges operation
        elif (command == "RDM"):
            userTimeStamp = listToString(userInput[1:6]).replace(';', '')
            if len(userInput) != 5:
                connectionSocket.send("> Usage: RDM timestamp\n  e.g. RDM 19 Feb 2021 21:42:04".encode('utf-8'))
            else:
                readMessages(userTimeStamp, credentials[0], connectionSocket)

        # Show active users operation
        elif (command == "ATU"):
            if len(userInput) != 1:
                connectionSocket.send("> There should be no arguments for ATU!".encode('utf-8'))
            else:
                getActiveUsers(onlineClients, credentials[0], addr[0], addr[1], connectionSocket)

        # Log out operation
        elif (command == "OUT"):
            if len(userInput) != 1:
                connectionSocket.send("> There should be no arguments for OUT!".encode('utf-8'))
            else:
                logOut(credentials[0], connectionSocket)
                connectionSocket.close()
                break

if __name__ == '__main__':
    while 1:
        # read_sockets are sockets we received some data on
        readSockets, _, _ = select(socketList, [], [], 1)

        # If notified socket is a server socket - new connection, accept it
        for notifiedSocket in readSockets:
            if notifiedSocket == serverSocket:
                connectionSocket, addr = serverSocket.accept()
                clientThread = threading.Thread(target=handleClient, args=(connectionSocket, addr))
                clientThread.start()
                print(f'Connection established, clientSocket: {connectionSocket.getsockname()}, clientAddr: {addr}')
                print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

            






       