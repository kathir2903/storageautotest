"""
- Make dir my-mirror in a given path, if not one already.
- Get list of your repos from GitHub
    - if any repo not mirrored in the CI server, 
      then do clone --mirror
    - set remote url to 'localhost mirrored path'
- Make another directory 'mirrored' for push requests,
    - Get into the directory and create a direcotry as repo name
      and do git init with bare=true
- Go to my-mirror/<repo_name> and run 'git fetch -p'
  and git push --mirror

Update mirror changes:
- If directory present in my-mirror for repository
    - go into the directory and run git fetch -p 
      and git push mirror 
    
"""

import json
import os
import subprocess
import sys
import urllib2
import base64
import logging
import pwd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class restclient(object):
    """ rest client to connect to github """
    def __init__(self, server, header, user, pwd):
        self.server = server
        self.user = user
        self.pwd = pwd
        self.header = header
        if self.user == None or self.pwd == None:
            self.user = ''
            self.pwd = ''
        auth = ("Authorization", "Basic %s" % (base64.encodestring("%s:%s" % (self.user, self.pwd))[:-1]))
        self.header.append(auth)
        
    def get(self, endpoint, params=None):
        """ get request handle with params """
        if type(endpoint)   == unicode:
            endpoint = endpoint.encode('ascii')
        if params:
            endpoint = endpoint + "?" + urlencode(params)
        self.urlendpoint = self.server + endpoint
        request = urllib2.Request(self.urlendpoint)
        _ = [request.add_header(head[0], head[1]) for head in self.header]
        request.get_method = lambda:'GET'
        res = urllib2.urlopen(request, timeout=1200)
        return json.loads(res.read().strip())

def githttpclient(server='https://git.develop',
                    user=None,
                    pwd=None):
    """ interface for rest client """
    accept = [('Content-Type', 'application/json')]
    return restclient(server=server,
                        header=accept,
                        user=user,
                        pwd=pwd)

def makedir(path):
    """ create directory """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != os.errno.EEXIST:
            raise
def changedir(path):
    """ change directory """
    try:
        os.chdir(path)
    except OSError:
        raise

def localpath():
    """ local user """
    loginuser = pwd.getpwuid(os.getuid()).pw_name
    return loginuser + '@localhost'

def check_mirrored(path):
    """ check if already mirrored """
    return os.path.isdir(path)

def sync_mirror(gitpath, mirrpath, pmpath):
    """ run clone mirror, if not mirrored already """
    makedir(pmpath)
    changedir(pmpath)
    subprocess.check_call(['git','init'])
    subprocess.check_call(['git','config', '--bool', 'core.bare', 'true'])
    changedir(mirrpath)
    subprocess.check_call(['git', 'clone','--mirror', gitpath])
    changedir(mirrpath + '/' + os.path.basename(gitpath))
    pmpath = localpath() + ':' + pmpath
    subprocess.check_call(['git', 'remote', 'set-url', '--push', 'origin', pmpath])
    subprocess.check_call(['git','fetch', '-p'])
    subprocess.check_call(['git', 'push', '--mirror'])
    
    
def resync_mirrored(gitpath, mirrpath):
    """ do resync if already mirrored """
    changedir(mirrpath + '/' + os.path.basename(gitpath))
    subprocess.check_call(['git','fetch', '-p'])
    subprocess.check_call(['git', 'push', '--mirror'])
    
def runmirror(syspath, usr, pwd, orgname='myorg'):
    """ start mirroring all repositories of given org """
    for repo in getrepos(usr, pwd, orgname):
        gitpath = repo['ssh_url']
        logger.info('Working on remote repo (%s)', gitpath)
        chkpath = '{}/{}-mirror/{}'.format(syspath, orgname, os.path.basename(gitpath))
        pmpath = syspath + "/mirrored/" + os.path.basename(gitpath)
        path = '{}/{}-mirror'.format(syspath, orgname)
        exclude_repos = ['service.git', 'app-info.git']
        if not any(exrepo in gitpath for exrepo in exclude_repos):
            if not check_mirrored(chkpath):
                sync_mirror(gitpath, path, pmpath)
            else:
                resync_mirrored(gitpath, path)

def getrepos(user, pwd, orgname):
    giturl = 'https://api.github.com'
    client = githttpclient('https://api.github.com', user=user, pwd=pwd)
    api = '/orgs/%s/repos' %orgname
    out = client.get(api)
    for doc in out:
        required = {'git_url': doc['git_url'],
                    'clone_url': doc['clone_url'],
                    'ssh_url': doc['ssh_url'] }
        yield required

if __name__ == "__main__":
    """ 
    Input args: <local_mirror_path>,
    <git_orgs_name>, <git_user_name> <git_pwd>
    """
    if len(sys.argv) !=5:
        print "Usage: <local_mirror_path> <git orgs name> <git_user_name> ", "For example: python gitmirror.py /data <repository_name> <git_username> <pwd>"
        sys.exit(1)
    runmirror(sys.argv[1], sys.argv[3], sys.argv[4], sys.argv[2])
