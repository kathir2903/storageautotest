#!/usr/bin/python

#Editor vim: ts=4:sw=4

#title      : dbconnect.py
#description: This is the database interface to create, retrieve,
#             save records the database.
#author     : "kathir.gitit@gmail.com"
#usage      : python dbconnect.py
#py version : 2.7
"""
Database Interface to access db schema 
    * Create database chema
    * Add new tables to the database schema
    * Use the Table Classes to do CRUD operations 
    * Database is built-in for handling commodity
        storage server that has standard chassis
        with one or more nodes in it.
"""

import MySQLdb
from sqlobject import *
import sys
import datetime
import os
dbURI = 'mysql://root:midas@localhost/sandbox1?debug=1'
dbURI_inv = 'mysql://root:midas@localhost/Inventory'


def dbconn(uri=dbURI):
    global sqlhub
    if not hasattr(sqlhub, "processConnection"):
        conn = connectionForURI(uri)
        sqlhub.processConnection = conn
    return sqlhub.processConnection

def dbdisconn():
    global sqlhub
    if hasattr(sqlhub, "processConnection"):
        conn = sqlhub.processConnection
        del sqlhub.processConnection

class UChassis(SQLObject):
    sn = StringCol(length=255, alternateID=True, unique=True)
    pn = StringCol(length=255)
    vendorSn = StringCol(length=255, unique=True)
    vendorPn = StringCol(length=255)
    vendorName = StringCol(length=255)
    mfgDate = DateTimeCol() 
    version = StringCol()
    description = StringCol()
    rev = StringCol()
    user = StringCol()

class UNode(SQLObject):
    uchassis = ForeignKey("UChassis")
    sn = StringCol(length=255, alternateID=True, unique=True)
    pn = StringCol(length=255)
    vendorSn = StringCol(length=255, unique=True)
    vendorPn = StringCol(length=255)
    vendorName = StringCol(length=255)
    mfgDate = DateTimeCol()
    version = StringCol()
    description = StringCol()
    rev = StringCol()
    user = StringCol()

class UDeviceName(SQLObject):
    devName = StringCol()
    udevBom = ForeignKey("UDevBom")

class UDevBom(SQLObject):
    devName = StringCol()

class UNodeDev(SQLObject):
    unode = ForeignKey("UNode")
    udeviceName = ForeignKey("UDeviceName")
    sn = StringCol(length=255, unique=True)
    pn = StringCol(length=255)
    vendorSn = StringCol(length=255)
    vendorPn = StringCol(length=255)
    vendorName = StringCol(length=255)
    version = StringCol()
    capacity = StringCol()

class UNodeDevTest(SQLObject):
    udevBom = ForeignKey("UDevBom")
    testName = StringCol()

class UTestRecords(SQLObject):
    unodeDevTest = ForeignKey("UNodeDevTest")
    unode = ForeignKey("UNode")
    uchassis = ForeignKey("UChassis")
    startTime = DateTimeCol()
    endTime = DateTimeCol()
    passFail = EnumCol(enumValues=["P","F","I"])
    logFile = StringCol(length=255)
    errorCode = StringCol()
    user = StringCol()
    comments = StringCol()

class UDevTestSpec(SQLObject):
    #This table must be filled by Engineer per product
    unodeDevTest = ForeignKey("UNodeDevTest")
    specName = StringCol(length=255)
    minLimit = StringCol() #must be floatcol in future
    maxLimit = StringCol() #must be floatcol in future


class UPowercycleTest(SQLObject):
    utestRecords= ForeignKey("UTestRecords")
    iteration = IntCol()
    measName = StringCol(length=255)
    measValue = StringCol(length=255)
    lowSpec = StringCol()
    highSpec = StringCol()

class UHddTest(SQLObject):
    utestRecords= ForeignKey("UTestRecords")
    measName = StringCol(length=255)
    measValue = StringCol(length=255)
    lowSpec = StringCol()
    highSpec = StringCol()

class UChecksensorsTest(SQLObject):
    utestRecords= ForeignKey("UTestRecords")
    measName = StringCol(length=255)
    measValue = StringCol(length=255)
    lowSpec = StringCol()
    highSpec = StringCol()

#This table is in Inventory db
class UMacPool(SQLObject):
    usedMac = StringCol(length=255)

def get_tables():
    mod = sys.modules[__name__]
    l = []
    for name in dir(mod):
        obj = getattr(mod, name)
        #print "Type of Obj", type(obj)
        if type(obj) is declarative.DeclarativeMeta:
            #print name
            l.append(name)
    l.remove("sqlmeta")
    l.remove("SQLObject")
    l.remove("OneToMany")
    l.remove("ManyToMany")
    #l = ['UDevTestSpec'] # Create only one table
    #l = ['UHddTest'] # Create only one table
    return l

def get_specs(tname_id, name):
    #print "-----TestName id %s" %tname_id
    #print "-----SpecName id %s" %name
    tbl = UDevTestSpec
    res = list(tbl.select(AND(tbl.q.unodeDevTestID==tname_id, tbl.q.specName==name)))[0]
    return (res.minLimit, res.maxLimit)

def update_node(node_id, *args):
    res = list(UNode.select(UNode.q.id == node_id))
    res[0].set(sn=args[1])
    return None

def get_specnames(tname_id):
    tmp = list(UDevTestSpec.select(UDevTestSpec.q.unodeDevTestID == tname_id))
    return [out.specName for out in tmp]


def update_node_dev(node_id, *args):
    data = list(UNodeDev.select(AND(UNodeDev.q.vendorSn == args[0], UNodeDev.q.unode == node_id)))
    print data
    data[0].set(sn=args[1])
    return None

def get_inventory(dev_id,pn_id): # Method not used
    tbl = UDevBomInv
    pn_l = []
    ver_l = []
    res = list(tbl.select(AND(tbl.q.udevBomID==dev_id, tbl.q.upnID==pn_id)))
    for each in res:
        pn_l.append(each.pn)
        ver_l.append(each.version)
        mfg = each.mfg
        cap = each.capacity
    return pn_l, ver_l, mfg, cap

def get_chassis(node_sn):
    tbl = UNode
    res = list(tbl.select(tbl.q.sn==node_sn))[0]
    tbl = UChassis
    res = list(tbl.select(tbl.q.id ==res.uchassisID))[0]
    return res.sn
#---------------
#Inventory
#---------------
def get_usedmac(mac):
    dbdisconn()
    dbconn(dbURI_inv)
    tbl = UMacPool
    res = list(tbl.select(tbl.q.usedMac == mac))
    status = False if len(res)>=1 else True
    dbdisconn()
    dbconn(dbURI)
    return status

def set_usedmac(mac):
    dbdisconn()
    dbconn(dbURI_inv)
    mac_id = UMacPool(usedMac = mac)
    dbdisconn()
    dbconn(dbURI)
    return mac_id


CREATE = """CREATE DATABASE IF NOT EXISTS sandbox1
        DEFAULT CHARACTER SET 'utf8' DEFAULT COLLATE 'utf8_general_ci';"""


GRANT = """GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP ON DS1000.* 
        TO 'user'@'localhost' IDENTIFIED BY 'mypwdrocks'"""


def create_db():
    dbdisconn() #Tear down the database connection, if it is open
    conn = MySQLdb.connect(host="localhost", user="root", passwd="midas", db="mysql", use_unicode=True)
    inst = conn.cursor()
    inst.execute(CREATE)
    inst.execute(GRANT)
    conn.commit()
    inst.close()

def create_tables(uri=dbURI):
    """
    List order is different from mysql schema
    link structure, so tbllist is assigned 
    with a list of tables(class names) in oder to 
    handle the database schema structure
    """

    dbmod = sys.modules[__name__]
    dbconn(uri)
    tbllist = get_tables()
    print tbllist
    tbllist = ['UChassis', 
            'UNode', 
            'UDevBom', 
            'UNodeDevTest', 
            'UTestRecords',
            'UChecksensorsTest', 
            'UDevTestSpec', 
            'UDeviceName', 
            'UHddTest', 
            'UMacPool', 
            'UNodeDev', 
            'UPowercycleTest']
    for tblname in tbllist:
        tbl = getattr(dbmod, tblname)
        tbl.createTable()

def _initialize(argv):
    global sqlhub
    print "Database URI: %s" %dbURI
    dbconn(dbURI)

if __name__== "__main__":
    """
    To create database schema and tables
    just uncomment below lines(create_db()
    and create_tables() and run as ./dbconnect.py
    This will create a database with name a name
    given in varible dbURI as below, 'sandbox1' is
    db name.
    (dbURI = 'mysql://root:midas@localhost/sandbox1?debug=1')
    """
    #_initialize(sys.argv)
    create_db()
    create_tables()
    pass
