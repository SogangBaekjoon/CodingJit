#-*- coding: utf8 -*-
import sys
import socket
import json
import tempfile
import shutil
import time
import os
import logging
import datetime

def sendResponse(conn, state, stdout, stderr, logger):
    res = json.dumps({ 'state': state, 'stdout': stdout, 'stderr': stderr })
    try:
        conn.sendall(res)
    except Exception as e:
        logger.error('Failed to send the response. ' + str(e))
    finally:
        logger.debug(res)

def getFromDict(key, D, default='', errorMessage=None, logger=None):
    if key not in D:
        if errorMessage is not None:
            if logger is None:
                print errorMessage
            else:
                logger.error(errorMessage)
            sendResponse(conn, state='error', stdout='', stderr=errorMessage, logger=logger)
            return None
        return default
    return D[key]

HOST = ''
PORT = 3000

#IP blocking activation
ipBlock = True

if len(sys.argv) >= 2:
    PORT = int(sys.argv[1])
if len(sys.argv) >= 3:
    ipBlock = bool(int(sys.argv[2]))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))

#configure compile/run fuctions and arguments
from languageConfigure import *


#Configure logger
logger = logging.getLogger('sever')
logger.setLevel(logging.DEBUG)

#make logfile directory
if not os.path.exists('log'):
    os.makedirs('log')
fileHandler = logging.FileHandler('log/server_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.log')
fileHandler.setLevel(logging.WARNING)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
consoleHandler.setFormatter(formatter)

logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)

conn = None

while True:
    s.listen(5) #maximum number of queued connections

    conn, addr = s.accept()

    logger.info('Connected by ' + str(addr))

    #Block ip except for our web server
    if ipBlock == True and addr[0] != 'your_webserver_ip':
        logger.warning('Unauthorized connection by ' + str(addr))

        sendResponse(conn, state='error', stdout='', stderr='Connection refused', logger=logger)
        conn.close()
        continue

    data = conn.recv(8192)
    if not data:
        continue
    logger.debug(str(data))

    #JSON string to python dictionary
    try:
        D = json.loads(data)
    except Exception as e:
        #JSON load failed
        logger.error('Cannot load the received data as json. ', str(e))
        sendResponse(conn, state='error', stdout='', stderr='Not an appropriate data.', logger=logger)
        conn.close()
        continue

    try:
        #Get file name
        fileName = getFromDict(key='filename', D=D, default='a.cpp')

        #Get source code
        sourceCode = getFromDict(key='source', D=D, errorMessage='No source code', logger=logger)
        if sourceCode is None:
            conn.close()
            continue

        #Get stdin string
        stdin = getFromDict(key='stdin', D=D, default='')

        #Get running time limit
        try:
            runningTimeLimit = int(getFromDict(key='time_limit', D=D, default=5))
        except ValueError as verr:
            logger.error('running time limit value error. ' + str(e))
            sendResponse(conn, state='error', stdout='', stderr='Running time limit value is not an acceptable form. It should be only a integer.', logger=logger)
        except Exception as e:
            logger.critical(str(e))
            sendResponse(conn, state='error', stdout='', stderr='Server error.', logger=logger)

        #Get memory limit
        try:
            memoryLimit = int(getFromDict(key='memory_limit', D=D, default=128))
        except ValueError as verr:
            logger.error('memory limit value error. ' + str(e))
            sendResponse(conn, state='error', stdout='', stderr='Memory limit value is not an acceptable form.', logger=logger)
        except Exception as e:
            logger.critical(str(e))
            sendResponse(conn, state='error', stdout='', stderr='Server error.', logger=logger)

        #Get if memory_strict option is on
        try:
            isStrict = bool(getFromDict(key='memory_limit_strict', D=D, default=False))
        except ValueError as verr:
            logger.error('memory limit value error. ' + str(e))
            sendResponse(conn, state='error', stdout='', stderr='Memory_limit_strict is not an acceptable form.', logger=logger)
        except Exception as e:
            logger.critical(str(e))
            sendResponse(conn, state='error', stdout='', stderr='Server error.', logger=logger)

        #Set memory limit and memory swap limit
        memorySwapLimit = memoryLimit * 2
        if isStrict:
            memoryLimitStrict = memoryLimit

        #Get mime (file type)
        filetype = getFromDict(key='mime', D=D, errorMessage='The language should be specified.', logger=logger)
        if filetype is None:
            conn.close()
            continue

        #See if the type is supported
        if filetype not in supportType:
            logger.warning('Bad request: ' + str(D['mime']) + ' not supported.')
            sendResponse(conn, state='error', stdout='', stderr=D['mime'] + ' is currently not supported.', logger=logger)
            conn.close()
            continue

        #Get which stage should be done
        stage = getFromDict(key='stage', D=D, errorMessage='Specify \'stage\'', logger=logger)
        if stage is None:
            conn.close()
            continue

        #See if the stage is invalid
        if stage != 'compile' and stage != 'run':
            logger.warning('Bad request: invalid stage')
            sendResponse(conn, state='error', stdout='', stderr='Invalid value in \'stage\'', logger=logger)
            conn.close()
            continue

        #make temp directory
        try:
            dirpath = tempfile.mkdtemp()
        except Exception as e:
            logger.critical('Cannot write source code. ' + str(e))
            sendResponse(conn, state='error', stdout='', stderr='Server error.', logger=logger)
            conn.close()
            continue

        try:
            with open(dirpath + '/' + fileName, 'w') as fp:
                fp.write(sourceCode.encode('utf8'))
            #make the file to be redirected as stdin
            with open(dirpath + '/stdin.txt', 'w') as fp:
                fp.write(stdin.encode('utf8'))
        except Exception as e:
            logger.critical('Cannot write source code or stdin file. ' + str(e))
            sendResponse(conn, state='error', stdout='', stderr='Server error.', logger=logger)
            conn.close()
            continue

        #compile
        if filetype not in noCompileType:
            result = compileCallingFunction[filetype](
                    sourceFile=[fileName], volumn = dirpath+':/data',
                    logger=logger,
                    **compileKwargs[filetype])

            if result['state'] != 'success':
                sendResponse(conn, state=result['state'], stdout=result['stdout'], stderr=result['stderr'], logger=logger)
                conn.close()
                continue

            if stage == 'compile':
                try:
                    shutil.rmtree(dirpath)
                except Exception as e:
                    logger.error('Cannot remove dir. (' + dirpath + ') ' + str(e))
                    logger.info('Compile success')
                    sendResponse(conn, state='success', stdout=result['stdout'], stderr=result['stderr'], logger=logger)
                    conn.close()
                    continue
                sendResponse(conn, state='success', stdout=result['stdout'], stderr=result['stderr'], logger = logger)
                conn.close()
                continue

            binaryName = getFromDict(D=compileKwargs[filetype], key='binaryName', default=None)
            if binaryName is None:
                binaryName = fileName[:fileName.rfind('.')] + '.class'
            print ' >', binaryName

            #Block until file writing done
            if not isFileWritingDone(dirpath+'/'+binaryName,
                    checkXMode=ifTheBinaryFileNeedsXMode[filetype],
                    blockTimeLimit=2):
                logger.critical('Cannot write binary file.')
                sendResponse(conn, state='error', stdout='', stderr='Server error.', logger=logger)
                conn.close()
                continue

        #run
        runName = 'a.out'
        if filetype == 'text/x-python':
            runName = '/data/'+fileName
        elif filetype == 'text/x-java':
            runName = fileName[:fileName.rfind('.')]
        result = runCallingFunction[filetype](
                runName = runName,
                stdinName = 'stdin.txt',
                volumn=dirpath+':/data', memoryLimit=memoryLimit, memorySwapLimit=memorySwapLimit,
                timeLimit = runningTimeLimit, logger = logger,
                **runKwargs[filetype])

        if result['state'] != 'success':
            logger.info('Run failed: ' + result['stderr'])
            sendResponse(conn, state=result['state'], stdout=result['stdout'], stderr=result['stderr'], logger=logger)
            conn.close()
            continue

        logger.info('Run success')
        sendResponse(conn, state='success', stdout=result['stdout'], stderr=result['stderr'], logger=logger)
        conn.close()

    except Exception as e:
        logger.critical('Unknown exception.s ' + str(e))
        if conn:
            sendResponse(conn, state='error', stdout='', stderr='Server error.', logger=logger)
    try:
        shutil.rmtree(dirpath)
    except Exception as e:
        logger.error('Cannot remove dir. (' + dirpath + ') ' + str(e))
        if conn:
            sendResponse(conn, state='success', stdout=result['stdout'], stderr=result['stderr'], logger=logger)
            conn.close()
