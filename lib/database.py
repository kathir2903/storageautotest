
import sys
import os
import datetime
import sqlite3
import MySQLdb
from sqlobject import *
import pprint
import pdb

# dbpath will be the location where db file is saved in
# jenkins server, review again
dbmod = sys.modules[__name__]

__all__ = ['dbconnect', 'dbdisconnect', 'gettables']
class SQLError(dberrors.Error):
    pass

def dbconnect(uri):
    global sqlhub
    if not hasattr(sqlhub, "processConnection"):
        conn = connectionForURI(uri)
        sqlhub.processConnection = conn
    return sqlhub.processConnection

def dbdisconnect():
    global sqlhub
    if hasattr(sqlhub, "processConnection"):
        conn = sqlhub.processConnection
        del sqlhub.processConnection

def _initialize(argv):
    global sqlhub
    return dbconnect()

def gettables():
    #mod = sys.modules[__name__]
    tables = []
    exclude = ["sqlmeta", "SQLObject", "OneToMany", "ManyToMany"]
    for name in dir(dbmod):
        obj = getattr(dbmod, name)
        #print "Type of Obj", type(obj)
        if type(obj) is declarative.DeclarativeMeta:
            if name not in exclude: yield name

def createtables(dbURI):
    dbconnect(dbURI)
    #dbmod = sys.modules[__name__]
    for table in gettables():
        tbl = getattr(dbmod, table)
        try:
            #if tbl==TestSuite: tbl.createTable()
            tbl.createTable()
        except dberrors.OperationalError as e:
            print e

def droptable(tablename):
    tbl = getattr(dbmod, tablename)
    return tbl.dropTable()

def issqlite(filename='test.db'):
    with open(filename, 'rb') as fd:
        header = fd.read(100)
    return header[:].__contains__('SQLite format') 
    
class TenantInfo(SQLObject):
    tenantname = StringCol()
    tenantid = StringCol()
    env = StringCol()
    token = StringCol()
    user = StringCol()
    pwd = StringCol()
    sftpuser = StringCol()
    uploadname = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class NsService(SQLObject):
    tenantinfo = ForeignKey('TenantInfo')
    servicename = StringCol()
    hostname = StringCol()
    port = IntCol()
    datetime = DateTimeCol(default=DateTimeCol.now)
    
class Infra(SQLObject):
    name = StringCol(length=255, unique=True)
    hostname = StringCol(length=255, unique=True)
    ip = StringCol(length=255, unique=True)
    user = StringCol()
    pwd = StringCol()
    accesstoken = StringCol()
    refreshtoken = StringCol()
    apikey = StringCol()
    clientid = StringCol()
    clientsecret = StringCol()
    port = StringCol()
    namespace = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

# TestSuite can have more 
# columns later
class TestSuite(SQLObject):
    suitename = StringCol(length=255, unique=True)
    datetime = DateTimeCol(default=DateTimeCol.now)
    path = StringCol()
    
# TestConfig can have more 
# coloums later
class TestConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = BLOBCol()
    active = IntCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class QueryServiceParams(SQLObject):
    testsuite = ForeignKey('TestConfig')
    firtseendate = DateTimeCol(default=DateTimeCol.now)
    deletiondate = DateTimeCol(default=DateTimeCol.now)
    active = IntCol() 

class ApplianceConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class QueryserviceConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class AnomaliesConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class ApiconnectorConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class DataplaneConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class NsclientConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class PasswordbreachConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class ProvisionerConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class WebuiConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class EventserviceConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class ReportjobstringConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

class ReportjobsConfig(SQLObject):
    testsuite = ForeignKey('TestSuite')
    confgroup = StringCol()
    value = StringCol()
    bunchrecords = StringCol()
    datetime = DateTimeCol(default=DateTimeCol.now)

def addcolumn():
    #TestConfig.sqlmeta.addColumn(IntCol('active'), changeSchema=True)
    #Infra.sqlmeta.addColumn(DateTimeCol('datetime'), changeSchema=True)
    #TestSuite.sqlmeta.addColumn(StringCol('suitename', unique=True), changeSchema=True)
    #TestSuite.sqlmeta.addColumn(DateTimeCol('datetime'), changeSchema=True)
    pass

def get_tenantinfo(tenantname):
    tb = TenantInfo
    tnt = list(tb.select(tb.q.tenantname==tenantname))[0]
    tnt_id = tnt.id
    tnt_name = tnt.tenantname
    tenantinfo = {'tid': tnt.tenantid,
                'token': tnt.token,
                'user': tnt.user,
                'pwd': tnt.pwd,
                'sftpuser': tnt.sftpuser,
                'uploadname':tnt.uploadname,
                'resource': 'https://%s.%s' %(tnt.tenantname, tnt.env)}
    nstb = NsService
    res = list(nstb.select(nstb.q.tenantinfo==tnt_id))
    for row in res:
        tenantinfo[row.servicename] = {}
        tenantinfo[row.servicename]['hostname'] = row.hostname
        tenantinfo[row.servicename]['port'] = row.port
        tenantinfo[row.servicename]['resource'] = 'https://%s.%s:%s' % (row.hostname, tnt.env, row.port)
    return tenantinfo

def get_infra():
    res = Infra.select()
    infra = {}
    for row in res:
        infra[row.name] = {}
        infra[row.name]['hostname'] = row.hostname.strip() if row.hostname else row.hostname
        infra[row.name]['ip'] = row.ip.strip() if row.ip else row.ip
        infra[row.name]['user'] = row.user.strip() if row.user else row.user
        infra[row.name]['pwd'] = row.pwd.strip() if row.pwd else row.pwd
        infra[row.name]['accesstoken'] = row.accesstoken.strip() if row.accesstoken else row.accesstoken
        infra[row.name]['refreshtoken'] = row.refreshtoken.strip() if row.refreshtoken else row.refreshtoken
        infra[row.name]['apikey'] = row.apikey.strip() if row.apikey else row.apikey
        infra[row.name]['clientid'] = row.clientid.strip() if row.clientid else row.clientid
        infra[row.name]['clientsecret'] = row.clientsecret.strip() if row.clientsecret else row.clientsecret
        infra[row.name]['port'] = row.port.strip() if row.port else row.port
        infra[row.name]['namespace'] = row.namespace.strip() if row.namespace else row.namespace
    return infra 

def get_alltestsuites():
    res = TestSuite.select()
    return [ i.suitename for i in res ] 

def get_testsuiteid(suitename):
    data =list(TestSuite.select(TestSuite.q.suitename == suitename.lower()))
    return data[0].id

def get_suiteconfig(suitename):
    tbl = getattr(dbmod, '%sConfig' % suitename.title())
    tsid = get_testsuiteid(suitename)
    res = list(tbl.select(tbl.q.testsuite==tsid))
    suitecfg = {}
    for row in res:
        if row.value:
            suitecfg[row.confgroup] = row.value.strip()
        else:
            _tmp = row.bunchrecords.split(',')
            suitecfg[row.confgroup] = [i.strip() for i in _tmp]
    return suitecfg
    
def createdb(dbtype='sqlite'):
    dbdisconnect()
    CREATE = """CREATE DATABASE IF NOT EXISTS test
        DEFAULT CHARACTER SET 'utf8' DEFAULT COLLATE 'utf8_general_ci';"""

    GRANT = """GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP ON sandbox.* 
        TO 'username:passwordusername'@'%' IDENTIFIED BY 'password'"""
    if dbtype == 'sqlite':
        dbpath = os.environ['PYTHONPATH'] + '/ns/src/lib/common/test.db'
        dbURI = 'sqlite://%s' % dbpath
        conn = sqlite3.connect(dbpath)
    else:
        conn = MySQLdb.connect(host="172.18.39.72", user="user", passwd="pwd", db="mysql", use_unicode=True)
        inst = conn.cursor()
        inst.execute(CREATE)
        inst.execute(GRANT)
        conn.commit()
        inst.close()
        dbURI = 'mysql://username:password@172.18.39.72/test'
    """
    if issqlite():
        conn = sqlite3.connect(dbpath)
    else:
        raise SQLError, "Database file is missing, please check if it is checkedout from Git"
    """
    return dbURI

#save records to the tables
def updaterecords(tablename, *args, **kw):
    tbl = getattr(dbmod, tablename)
    data =list(tbl.select(AND(tbl.q.id == args[0], tbl.q.tenantname == args[1])))
    print data
    if data:
        data[0].set(**kw) 
        result =list(tbl.select(AND(tbl.q.id == args[0], tbl.q.tenantname == args[1])))
        return result
    else:
        return False

def setrecords(record):
    for rec in record:
        sampler(**record)
        pass

if __name__ == "__main__":
    dbURI = createdb(dbtype="mysql")
    createtables(dbURI)
    #get_infra()
    print get_alltestsuites()
    #print get_testsuite()
    #addcolumn()
    #setrecords(record)
    #droptable('')
    #droptable('')
    #record['tenantname'] = 'kathir'
    #record['env'] = 'qa.local'
    #updaterecords('TenantInfo', 1, 'umbrella', tenantname='umbrella', env='stg.local')
    #pprint.pprint(get_suiteconfig('appliance'))
