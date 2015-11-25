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
import gitControl
import subprocess
import tempfile
from github import Github

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

def sendError(conn, err='Unknown error'):
    conn.sendall(json.dumps({'error': err}))
    logger.error(err)
    conn.close()

HOST = ''
PORT = 4592

#IP blocking activation
ipBlock = False

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))

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

logger.debug('start')
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
        cmd = D['cmd']
    except:
        logger.debug('Maybe no cmd')
        continue

    if cmd == 'auth':
        g = gitControl.getGithubInstance(D['username'], D['password'])
        gitUser = g.get_user()
        try:
            a = gitUser.login
            res = json.dumps({'auth': True})
        except:
            res = json.dumps({'auth': False})


    elif cmd == 'getRepoList':
        try:
            g = gitControl.getGithubInstance(D['username'], D['password'])
            gitUser = g.get_user()

            repoList = []
            for repo in gitUser.get_repos():
                if not repo.private:
                    repoList.append({'name':repo.name, 'url': repo.git_url})

            res = json.dumps(repoList)
        except Exception as e:
            logger.error(str(e))
            res = {'error': str(e)}
            continue

    elif cmd == 'getRepo':
        try:
            dirpath = tempfile.mkdtemp()
            command = 'git clone %s %s' % (D['url'], dirpath)
            kwargs = { 
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "shell": True
            }
            logger.debug( 'start cloning at %s' % dirpath)
            popen = subprocess.Popen(command, **kwargs)
            start = time.time()
            timeLimit = 3
            while time.time() < start + timeLimit and popen.poll() is None:
                time.sleep(0.1)
            wait = popen.poll()
            if wait is None:
                popen.kill()
                sendError(conn, 'cannot connect to github')
                continue
            logger.debug( 'done?')

            F = [f for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f))]
            logger.debug(str(F))
        except Exception as e:
            logger.error(str(e))
            sendError(conn, 'cannot write file')
            continue

        res = json.dumps({'path': dirpath, 'files': F})

    elif cmd == 'getFile':
        try:
            path = D['path']
            filename = D['filename']
            with open(path + '/' + filename, 'r') as fp:
                content = fp.read()
            res = json.dumps({'content': content})
        except Exception as e:
            sendError(conn, str(e))
            continue

    elif cmd == 'commit':
        try:
            path = D['path']
            filename = D['filename']
            content = D['content']
            url = D['url'].replace('git://', '')
            username = D['username']
            password = D['password']
            commitMsg = D['commitMsg']
            gitUrl = 'https://%s:%s@%s' % (username, password, url)

            with open(path + '/' + filename, 'w') as fp:
                fp.write(content)

            command = 'git add %s && git commit -m "%s" && git remote set-url origin %s && git push -u origin master' \
                % (filename, commitMsg, gitUrl)
            kwargs = { 
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "cwd": path,
                "shell": True
            }
            logger.debug( 'start commiting')
            popen = subprocess.Popen(command, **kwargs)
            start = time.time()
            timeLimit = 5
            while time.time() < start + timeLimit and popen.poll() is None:
                time.sleep(0.1)
            wait = popen.poll()
            if wait is None:
                popen.kill()
                sendError(conn, 'cannot commit to github')
                continue
            logger.debug( 'done?')
            returncode = popen.returncode
            stdout = str(popen.stdout.read().strip())
            logger.debug('EXITCODE: %d, stdout: %s' % (int(returncode), stdout))

            res = json.dumps({
                    'returncode': returncode,
                    'stdout': stdout
            })

        except Exception as e:
            sendError(conn, str(e))
            continue

    elif cmd == 'newRepo':
        try:
            repoName = D['repoName']
            repoDesc = D['repoDesc']
            g = gitControl.getGithubInstance(D['username'], D['password'])
            gitUser = g.get_user()

            if repoDesc == '':
                newRepo = gitUser.create_repo(repoName, auto_init=True)
            else:
                newRepo = gitUser.create_repo(repoName, description=repoDesc, auto_init=True)

            res = json.dumps({})

            dirpath = tempfile.mkdtemp()
            command = 'git clone %s %s' % (newRepo.git_url, dirpath)
            kwargs = { 
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "shell": True
            }
            logger.debug( 'start cloning at %s' % dirpath)
            popen = subprocess.Popen(command, **kwargs)
            start = time.time()
            timeLimit = 3
            while time.time() < start + timeLimit and popen.poll() is None:
                time.sleep(0.1)
            wait = popen.poll()
            if wait is None:
                popen.kill()
                sendError(conn, 'cannot connect to github')
                continue
            logger.debug( 'done?')

            res = json.dumps({'path': dirpath, 'url': newRepo.git_url})
        except Exception as e:
            sendError(conn, str(e))
            continue

    logger.debug( 'SEND: %s' % res)
    conn.sendall(res)
    conn.close()
