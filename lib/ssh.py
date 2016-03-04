
import os
import sys
import paramiko
import re
import traceback
import time
import json
import pdb
from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint

class RemoteConnect(object):
    """
    connect to remove server that has
    ssh server running on it
    """
    def __init__(self, **cred):
        self.sess, self.sftp_sess = init_sess(**cred)

    def __del__(self):
        try:
            self.sess.close()
            self.sftp_sess.close()
        except Exception as exc:
            raise    

    def sendcmd(self,
                cmd,
                nsshell=True,
                configmode=True,
                timeout=5):
        """ send command to nsshell or to ubuntu shell """
        if not nsshell:
            stdin, stdout, stderr = self.sess.exec_command(cmd)
            if stdout.channel.recv_exit_status() !=0:
                print 'Command returns error code: %s' \
                        % stdout.channel.recv_exit_status()
                raise ValueError, "Command failed with Error code %s" \
                                    %(str(stoud.channel.recv_exit_status()))
            #print stdout.readlines()
            return stdout.readlines()
        else:
            nsshell = self.sess.invoke_shell()
            nsshell.send('nsshell'+"\n")
            _ = nsshell.recv(65535)
            time.sleep(1)
            if configmode:
                nsshell.send('configure'+"\n")
                out = nsshell.recv(65535)
                time.sleep(1)
            nsshell.send(cmd+"\n")
            #time.sleep(timeout)
            time.sleep(5) #give it 5 seconds delay always
            res = nsshell.recv(65535)
            if not configmode:
                res = res.split('nsshell\r\n')[2]
            print "^^^^^^^^^^^^^^^^^^^^"
            print res
            print "^^^^^^^^^^^^^^^^^^^^"
            obj = re.match(r'(.*)\r\n((.|\n)*)', res)
            if obj.group(2):
                recv_stat = True
            else:
                recv_stat = nsshell.recv_ready()
                start = time.time()
                end = time.time()
                while not recv_stat and (end-start)<=timeout:
                    print "Inside while loop"
                    time.sleep(30)
                    end = time.time()
                    recv_stat = nsshell.recv_ready()
                if recv_stat:
                    print "Yes, recv_status is True"
                    res = nsshell.recv(65535)
                else:
                    raise Exception, "No response data in PIPE"
            trim = [res.split(cmd)[0].split('\r\n')[-1].strip()] # trim='nsappliance>'
            try:
                out = json.loads([res.split(cmd)[1].split(trim[0])[0].strip()][0])
            except (ValueError, IndexError):
                if res.__contains__(cmd):
                    out = [res.split(cmd)[1].split(trim[0])[0].strip()][0]
                else:
                    try:
                        out = [res.split(trim[0])[0].strip()][0]
                    except (ValueError, IndexError):
                        return out
            return out
            
    def chk_process(self,cmd):
        """ check the process running state and return True if running """
        cmd = 'ps -aef | grep \"' + cmd +'\" | grep -v \"grep\" | wc -l'
        val = []
        stdout = self.sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0])>0 else False 
        return status

    def bg_sendcmd(self,cmd):
        """ run command in backgroud """
        stdin, stdout, stderr = self.sess.exec_command(cmd + ' &')
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            raise ValueError, "Command failed with Error code %s" \
                                %(str(stoud.channel.recv_exit_status()))
        return self.chk_process(cmd)

    def sftp_put(self, src, dest):
        """
        src-full path of source file from the scp originated server
        to destination server
        Ex: /home/user/sample.py to /tmp/sample.py
        """
        self.sftp_sess.put(src, dest)
        cmd = "ls -l " + dest + " | wc -l" 
        val = []
        stdout = self.sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0]) == 1 else False
        return status

    def sftp_get(self, src, dest):
        """ sftp get from remote server to local """
        self.sftp_sess.get(src, dest)
        cmd = "ls -l " + dest + " | wc -l" 
        out = os.popen(cmd)
        val = out.readline().strip()
        status=True if int(val) == 1 else False
        return status
    
    
def get_ssh(ip, user, pwd, port=22):
    """ return ssh connection handle """
    try:
        conn = paramiko.SSHClient()
        conn.load_system_host_keys()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _conn = conn.connect(ip, port, user, pwd)
    except Exception, e:
        print 'Caught exception: %s: %s' %(e.__class__, e)
        conn.close()
        sys.exit()
    return conn 

def get_sftp(ip, user, pwd=None, prvkeyfile=None, port=22):
    """ get sftp connection handle """
    try:
        conn = paramiko.SFTPClient
        trans = paramiko.Transport((ip, port))
        #trans.connect(username=user, password=pwd)
        if pwd:
            trans.connect(username=user, password=pwd)
            _conn = conn.from_transport(trans)
        elif prvkeyfile:
            if os.path.exists(os.path.expanduser(prvkeyfile)):
                rsa = paramiko.RSAKey.from_private_key_file(prvkeyfile)
                trans.connect(username=user, pkey=rsa)
                _conn = conn.from_transport(trans)
            else:
                raise Exception,  "Private Key missing"
    except Exception, e:
        print 'Caught exception: %s: %s' %(e.__class__, e)
        sys.exit()
    return _conn 

def get_telnet(dev):
    return NotImplemented

def init_sess(**cred):
    """ return sftp and ssh sessions """
    print cred
    dev, ip = cred['device'].split(':')
    if dev == "ssh":
        _sess = get_ssh(ip, user=cred['user'], pwd=cred['pwd'])
        _sftp_sess = get_sftp(ip, user=cred['user'], pwd=cred['pwd'])
    elif dev == "telnet":
        raise NotImplementedError("Telnet is not implemented yet")
    else:
        raise ValueError, "IP or connection configuration is not correct"

    return _sess, _sftp_sess

if __name__ == "__main__":
    inst = RemoteConnect(device="ssh:192.168.64.71", user="nsadmin", pwd="nsappliance")
    #inst.sendcmd('ls', nsshell=False)
    #out = inst.sendcmd('traceroute host 172.16.181.1', configmode=False, timeout=30)
    #print out
    out = inst.sendcmd('change-password nsadmin', configmode=False, timeout=30)
    #inst.sendcmd('show', configmode=True)
