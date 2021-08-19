import sys
import time
import datetime

# global variable for storing active sequence number in userlog.txt
activeSeqNum = 1

# check if client username and password is correct
def authenticate(credential):
    if len(credential) != 2:
        return 'Credentials needs to contain 2 strings!'
    credentials = 'credentials.txt'
    with open(credentials, 'r') as reader:
        line = reader.readline()
        while line != '': 
            check = line.split()
            if credential == check:
                return 'Login Successful'
            if credential[0] == check[0] and credential[1] != check[0]:
                return 'Invalid Password. Please try again!'
            line = reader.readline()
        return 'Invalid Username. Please try again!'

# check blocked users
def checkBlocked(blockedList, username, clientSocket):
    for blocked in blockedList:
        # if the client is found in the blocked list, check their blocked duration
        if username == blocked['username']:
            user = blocked['username']
            blockedStartTime = blocked['blockedStartTime']
            currentTime = datetime.datetime.now()
            # if blocked duration is over, remove from blocked list
            if blockedStartTime < currentTime - datetime.timedelta(seconds = 10):
                if user == username:
                    clientSocket.send("> Your account has been unblocked.".encode('utf-8'))
                    blockedList.remove(blocked)
                    return False
            # else blocked duration isn't over yet
            else:
                if user == username:
                    clientSocket.send("> Your account is blocked due to multiple login failures. Please try again later".encode('utf-8'))
                    return True

# Displays a welcome message to the client and adds the client's details to the userlog.txt file
def logIn(clientSocket, username, clientAddr, clientPortNum):

    global activeSeqNum
    clientSocket.send(f"> Welcome to TOOM!".encode('utf-8'))

    f = open("cse_userlog.txt", "a")
    f.write(f"{activeSeqNum}; {datetime.datetime.now().strftime('%d %b %Y %X')}; {username}; {clientAddr}; {clientPortNum}\n")
    f.close()

    activeSeqNum += 1

# helper function to convert a list of strings into a single string
def listToString(oldList):
    newString = " "
    for a in oldList:
        newString = newString + ' ' + a
        newString = newString.strip()
    return newString

# adds a new message to messagelog.txt
def writeToMsgLog(messageNum, username, message):
    f = open("messagelog.txt", "a")
    f.write(f"{messageNum}; {datetime.datetime.now().strftime('%d %b %Y %X')}; {username}; {message}; no\n")
    f.close()

# Usage examples:
# DLT 1 19 Feb 2021 21:39:04
# DLT 2 19 Feb 2021 21:42:04
# DLT 3 19 Feb 2021 21:40:14
def deleteMessage(messageNum, timeStamp, username, clientSocket):

    lineToDelete = ""
    found = False
    deleted = False
    currentTime = datetime.datetime.now().strftime('%d %b %Y %X')

    f = open("messagelog.txt", "r")
    for line in f: 
        time = listToString(line.split()[1:5]).replace(';', '')
        user = listToString(line.split()[5:6]).replace(';', '')
        message = listToString(line.split()[6:-1]).replace(';', '')
        # check if the message number is valid
        if messageNum == line[0]:
            # check if the timestamp is valid
            if (timeStamp == time):
                # check if it is the user's own message
                if (username == user):
                    found = True
                    lineToDelete = line.strip("\n")
                    break
    f.close()

    # if the line to be deleted has been found and is valid, store all the contents of txt file in lines
    if found == True:
        f = open("messagelog.txt", "r")
        lines = f.readlines()
        f.close()

        f = open("messagelog.txt", "w")
        for line in lines:
            # keep writing lines to the new file except for the line to be deleted 
            if line.strip("\n") != lineToDelete:
                # if the line to be deleted has already been deleted
                # write the rest of the lines with updated message numbers
                if deleted == True:
                    updatedMsgNum = str(int(line[0]) - 1)
                    updatedLine = updatedMsgNum + line[1:]
                    f.write(updatedLine)
                else:
                    f.write(line)
            else:
                deleted = True
        f.close()

        print(f"> {username} deleted MSG #{messageNum} '{message}' at {currentTime}.")
        clientSocket.send(f"> Message #{messageNum} deleted at {currentTime}".encode('utf-8'))
    else:
        print(f"> {username} attempts to delete MSG #{messageNum} at {currentTime}. Authorisation fails.")
        clientSocket.send(f"> Unauthorised to delete Message #{messageNum}".encode('utf-8'))

# Usage examples:
# EDT 1 19 Feb 2021 21:39:04 do or do not
# EDT 2 19 Feb 2021 21:42:04 pog
def editMessage(messageNum, timeStamp, username, newMessage, clientSocket):

    found = False

    f = open("messagelog.txt", "r")
    for line in f: 
        time = listToString(line.split()[1:5]).replace(';', '')
        user = listToString(line.split()[5:6]).replace(';', '')
        message = listToString(line.split()[6:-1]).replace(';', '')
        # check if the message to be edited is valid (similar to checking DLT process)
        if messageNum == line[0]:
            if (timeStamp == time):
                if (username == user):
                    found = True
                    lineToEdit = line.strip("\n")
                    break
    f.close()

    # if the line to be edited has been found and is valid, store all the contents of txt file in lines
    if found == True:
        f = open("messagelog.txt", "r")
        lines = f.readlines()
        f.close()

        f = open("messagelog.txt", "w")
        # keep writing lines to the new file except for the line to be edited 
        for line in lines:
            if line.strip("\n") != lineToEdit:
                f.write(line)
            else:
                f.write(lineToEdit[:31])
                f.write(newMessage)
                f.write("; yes\n")
        f.close()

        currentTime = datetime.datetime.now().strftime('%d %b %Y %X')
        print(f"> {username} edited MSG #{messageNum} '{message}' at {currentTime}.")
        clientSocket.send(f"> Message #{messageNum} edited at {currentTime}".encode('utf-8'))
    else:
        print(f"> {username} attempts to edit MSG #{messasgeNum} at {currentTime}. Authorisation fails.")
        clientSocket.send(f"> Unauthorised to edit Message #{messageNum}".encode('utf-8'))

# Usage examples: 
# RDM 19 Feb 2021 21:42:04
# RDM 20 Feb 2021 21:50:08
# RDM 19 Feb 2021 21:50:08
def readMessages(timeStamp, username, clientSocket):

    userDate = datetime.datetime.strptime(timeStamp, "%d %b %Y %X")
    newMessages = ""
        
    f = open("messagelog.txt", "r")
    for line in f: 
        messageNum = listToString(line.split()[0]).replace(';', '').strip()
        user = listToString(line.split()[5:6]).replace(';', '').strip()
        message = listToString(line.split()[6:-1]).replace(';', '').strip()
        time = listToString(line.split()[1:5]).replace(';', '').strip()
        date = datetime.datetime.strptime(time, "%d %b %Y %X")
        edited = listToString(line.split()[-1:]).replace(';', '').strip()
        
        if userDate < date:
            if edited == "yes":
                tempLine = f"#{messageNum} {user}, {message}, edited at {time}.\n"
            else:
                tempLine = f"#{messageNum} {user}, {message}, posted at {time}.\n"
            newMessages = newMessages + tempLine

    print(f"> {username} issued RDM command")

    if newMessages == "":
        clientSocket.send("> No new messages".encode('utf-8'))
    else:
        print(f"> Return messages:")
        print(f"{newMessages}")
        clientSocket.send(f"> {newMessages}".encode('utf-8'))

    f.close()

# send the usernames, timestamp since the users are active and their IP addresses and Port Numbers
# exclude the information of client requesting the ATU
def getActiveUsers(onlineList, clientUser, clientAddr, clientPortNum, clientSocket):

    print(f"> {clientUser} issued ATU command ATU.")
    if len(onlineList) == 1:
        print("> no other active user")
        clientSocket.send(f"> no other active user".encode('utf-8'))
    else:
        clientMsg = ""
        print("> Return active user list: ")
        for online in onlineList:
            username = online['username']
            lastActive = online['last-active'].strftime('%d %b %Y %X')
            if clientUser == username:
                continue
            message = f"{username}; {clientAddr}, {clientPortNum}; active since {lastActive}"
            print(message) 
            clientMsg = clientMsg + message
        clientSocket.send(clientMsg.encode('utf-8'))

# close the TCP connection (UDP client server)
# update its state information about currently logged on users and the active user log file
def logOut(username, clientSocket):

    print(f"> {username} logout")    
    clientSocket.send(f"> Bye, {username}!".encode('utf-8'))
    
    f = open("cse_userlog.txt", "r")
    for line in f: 
        user = listToString(line.split()[5:6]).replace(';', '')
        if (username == user):
            lineToDelete = line.strip("\n")
            break
    f.close()
   
    f = open("cse_userlog.txt", "r")
    lines = f.readlines()
    f.close()

    deleted = False

    f = open("cse_userlog.txt", "w")
    for line in lines:
        if line.strip("\n") != lineToDelete:
            if deleted == True:
                updatedMsgNum = str(int(line[0]) - 1)
                updatedLine = updatedMsgNum + line[1:]
                f.write(updatedLine)
            else:
                f.write(line)
        else:
            deleted = True
    f.close()

def checkOnlineClients(username, onlineList):
    for online in onlineList:
        if username == online['username']:
            return True 
    return False

def isInteger(num):
    try:
        num = int(num)
        return True
    except Exception:
        return False
