
"""
Interface that provide methods
to access cloud apps.
box, dropbox, salesforce,
google drive, onedrive, egnyte
"""
 
import rest
import pdb
import os
import abc
import sys
from ns.src.lib.common.utils import *

#Below url is used to get Authentication code (Not Authorization Code)
#https://app.box.com/api/oauth2/authorize?response_type=code&client_id=b5d8yhq6v8xd4va9shnd6w6kp82qbvpk&state=authenticated

def oauth_validator(func):
    def validator(*args, **kwargs):
        print dir(args[0])
        app = args[0]
        print kwargs
        try:
            #print app.reftok
            res = func(*args, **kwargs)
            return res
        except rest.HTTPException as exc:
            if exc[0] == 'Unauthorized':
                #pdb.set_trace()
                app.getnewtokens()
                res = func(*args, **kwargs)
                return res
            else:
                raise exc
    return validator

class ThirdPartyAPI(object):
    # Abstract class is not really needed here 
    # because it not required to mandate the
    # functions in the derived class.
    # Kathir to revisit
    class base(object):
        __metaclass__ = abc.ABCMeta
        def __init__(self, **cred):
            self.login = cred.get('login', None)
            self.cid = cred.get('cid', None)
            self.csec = cred.get('csec', None)
            self.acctok = cred.get('acctok', None)
            self.reftok = cred.get('reftok', None)
            self.tokurl = 'https://www.box.com'
            self.apiurl = "https://api.box.com/2.0"
            self.viewurl = "https://view-api.box.com"
            self.uploadurl = "https://upload.box.com/api/2.0"
            self.ins_tokurl = rest.createclient(server=self.tokurl)
            self.ins_apiurl = rest.createclient(server=self.apiurl)
            self.ins_viewurl = rest.createclient(server=self.viewurl)
            self.ins_uploadurl = rest.createclient(server=self.uploadurl)
            
            self.headers = [('Authorization', 'Bearer %s' %(self.acctok))]

        @abc.abstractmethod
        def getinfo(self):
            pass
        """ 
        @abc.abstractmethod
        def download(self):
            pass
        """
    class box(base):
        """
        def __init__(self, login='ravi+boxent@netskope.com',
                    cid='b5d8yhq6v8xd4va9shnd6w6kp82qbvpk',
                    csec='MJkfbFQZX9QOmY5XPGNoIqgqCixHjIJn',
                    acctok='ceCK8pSfSqQyqYubYHuL5q1jFaFmoCll',
                    reftok='h49LjnbxHBDNTPEw5LW2O4H1fOxmkOEVE2GMreYu9Yn8KnDzlwXEzfd5L4KmSAWv'):
            self.login = login
            self.cid = cid
            self.csec = csec
            self.acctok = acctok
            self.reftok = reftok
        """
        def __init__(self, **cred):
            # Kathir: not sure why super is not working
            # though the classes are new-style.
            ThirdPartyAPI().base.__init__(self, **cred)

        def getnewtokens(self):
            #app_url = "https://app.box.com"
            auth_ep = "/api/oauth2/token"
            headers = [('Content-type', 'application/x-www-form-urlencoded')]
            boxref = rest.createclient(server=self.tokurl)
            olddata = jfreader('box.json')
            key = 'ravi+boxent@netskope.com'
            data = {
                    'grant_type': 'refresh_token',
                    'client_id': olddata[key]['cid'],
                    'client_secret': olddata[key]['csec'],
                    'refresh_token': olddata[key]['reftok']
                    }
            res = boxref.post(path=auth_ep, data=data, headers=headers, encode=True)
            print res
            if res.has_key('access_token'):
                self.acctok = tostr(res['access_token'])
                self.reftok = tostr(res['refresh_token'])
                self.toktype = tostr(res['token_type'])
                self.headers = [('Authorization', 'Bearer %s' %(self.acctok))]
                olddata[key]['acctok'] = self.acctok
                olddata[key]['reftok'] = self.reftok
                with open('box.json', 'w') as handle:
                    json.dump(olddata, handle, indent=4)

        @oauth_validator
        def getinfo(self):
            ep = '/users/me'
            res = self.ins_apiurl.get(path=ep, headers=self.headers)
            print res
            return res

        def getdocuments(self):
            ep = '/1/documents'
            apikey = "7olhqklihzthcx56c9lv7j0xk9sa2qsg"
            auth_header = [('Authorization', 'Token %s' %(apikey))]
            res = self.ins_viewurl.get(path=ep, headers=auth_header)
            print res
            return res
        
        @oauth_validator
        def getfolderinfo(self, folderid=0, params=None):
            ep = '/folders/%s' %folderid
            res = self.ins_apiurl.get(path=ep, params=None, headers=self.headers)
            print res
            return res
        
        @oauth_validator
        def getfolderitems(self, folderid=0, params=None):
            ep = '/folders/%s/items' %folderid
            res = self.ins_apiurl.get(path=ep, params=None,  headers=self.headers)
            print res
            return res

        @oauth_validator
        def createfolder(self, name, parentname=None):
            ep = '/folders'
            data = {}
            data['name'] = name
            if parentname:
                out = self.getfolderitems()
                for d in out['entries']:
                    if d.get('name', None) == parentname:
                        parentid = d['id']
                        data['parent'] = {'id': parentid}           
                        break
            else: 
                data['parent'] = {'id': '0'}
            res = self.ins_apiurl.post(path=ep, data=json.dumps(data),  headers=self.headers)
            print res
        
        @oauth_validator
        def uploadfile(self, filepath, parentname=None):
            ep = '/files/content'
            fh = open(filepath)
            filename = os.path.basename(filepath)
            _file = {filename: fh}
            data = {filename: filename}
            #res = self.ins_uploadurl.upload(path=ep, file_path='/Users/kathir/src/ns/qa-auto/functional/NSTestFramework/ns/src/lib/restapi/box.json',headers=self.headers)
            #FIX ME: repeatable code:
            if parentname: 
                out = self.getfolderitems()
                for d in out['entries']:
                    if d.get('name', None) == parentname:
                        parentid = d['id']
                        data['folder_id'] = parentid         
                        break
            else: 
                data['folder_id'] = 0
            headers = dict(val for val in self.headers)
            res = self.ins_uploadurl.upload(url=self.uploadurl+ep, files=_file, headers=headers, data=data)
            print res
            return res

        @oauth_validator
        def downloadfile(self, localfile, fileid=None):
            if fileid:
                ep = '/files/%s/content' %str(fileid)
            else:
                #kathir: more login to be added
                sys.exit(1)
            res = self.ins_apiurl.get(path=ep, params=None, headers=self.headers, download=True)
            with open(localfile, "wb") as lf:
                lf.write(res.read())

    class dropbox(object):
        pass
    
    class egnyte(base):
        pass

    class salesforce(base):
        pass

if __name__ == '__main__':
    tp = 'Box'
    tp = tp.lower()
    target = getattr(ThirdPartyAPI, tp)
    old_data = jfreader('../restapi/box.json')
    key = 'ravi+boxent@netskope.com'
    inst = target(login=old_data[key]['login'],
                cid=old_data[key]['cid'],
                csec=old_data[key]['csec'],
                acctok=old_data[key]['acctok'],
                reftok=old_data[key]['reftok'])
        
    #inst.getnewtokens()
    inst.getinfo()
    """
    Kathir: Below implementation to get the authorization code is required going forward
    #https://app.box.com/api/oauth2/authorize?response_type=code&client_id=b5d8yhq6v8xd4va9shnd6w6kp82qbvpk&state=authenticated
    auth_url = 'https://app.box.com'
    api = '/api/oauth2/authorize'
    params = {'response_type': 'code', 'client_id': 'b5d8yhq6v8xd4va9shnd6w6kp82qbvpk', 'state': 'authenticated')
    boxref = rest.createclient(server=self.tokurl)
    """
    pass
