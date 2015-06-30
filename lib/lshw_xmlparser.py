#!/usr/bin/python

#Editor vim: ts=4:sw=4

#title      : lshw_xmlparser.py
#description: Parses the lshw XML output 
#             save records the database.
#author     : "kathir.gitit@gmail.com"
#usage      : python lshw_xmlparser.py
#notes      : Can be used as module by calling from another program
#py version : 2.7

"""
XML parser to parse lshw output of any commoditiy hardware like supermicro.
XML is converted to <key, value> dict type output, similar to json
Examples:

    1)  System infromation :-
        {'system_info':[{'description': 'Computer', 'serial' : 'SN#' and more key value pairs},
                        {cofiguration key, value pairs},
                        {capabilities key, value pairs},
                        {resources key, value pairs}]}
           --> Data from above dict of list of dict can be retrieved like this, x['system_info'][0]['serial']
    2) CPU information:
        { 'cpu:0': { '_info': [{description, bus_info etc..},
                               {configuration},{capabilities},{resources}],
                    'cache:0':[{description, bus_info etc..},
                               {configuration},{capabilities},{resources}],
                    'cache:1':[{description, bus_info etc..},
                               {configuration},{capabilities},{resources}],
                    'cache:3':[{description, bus_info etc..},
                               {configuration},{capabilities},{resources}]},
         'cpu:1': { '_info': [{description, bus_info etc..},
                               {configuration},{capabilities},{resources}],
                    'cache:0':[{description, bus_info etc..},
                               {configuration},{capabilities},{resources}],
                    'cache:1':[{description, bus_info etc..},
                               {configuration},{capabilities},{resources}],
                    'cache:3':[{description, bus_info etc..},
                               {configuration},{capabilities},{resources}]}}
           --> Data can be accessed like this, x['cpu:1']['_info'][0]['serial'], x['cpu:0']['cache:0'][1][configuration attribute']

-------------These few lines here are the basic logic-------------
file = open("lshw.log" , 'r')

data = file.read()
i = 0
datastruct = {}
doc = parseString(data)
for t in doc.getElementsByTagName('node'):
  #out = t.getAttribute('id') 
  print "============================="
  out = t.toxml()
  print out
  i +=1
--------------------------------------------------------------------
"""
__all__ = ['LshwInfo', 'System', 'Devices']

import pdb
import xml.dom.minidom
from xml.dom.minidom import *
#pdb.set_trace()
from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint


class LshwInfo(object):
  def __init__(self, file):
    self.file = open(file, 'r')
    self.data = self.file.read()
    self.doc = parseString(self.data)
    self._system = {}


class System(LshwInfo):

  def system_info(self):
    nodes = self.doc.getElementsByTagName('node')
    self._system = {}
    _sys ={}
    _capab = {}
    _config = {}
    _tmp = []
    
    for node in nodes:
      if node.attributes['class'].value == 'system':
        _sys = self.mfg_data(node)
        subnodes = self.doc.getElementsByTagName('width')
        for n in subnodes:
            try:
                unit =  str(n.attributes['units'].value)
                val = n.firstChild.nodeValue.__str__()
                _sys['width'] = val + " " + unit
            except:
                #print "Some attributes missing"
                pass
        tag = node.getElementsByTagName('configuration')
        for n in tag:
            n1 = n.getElementsByTagName('setting')
            for l in n1:
                _config[str(l.attributes['id'].value)] = l.attributes['value'].value.__str__()
            break
        tag = node.getElementsByTagName('capabilities')
        for n in tag:
            n1 = n.getElementsByTagName('capability')
            _capab = self.config_capab_res(n1)
            break
        _tmp.append(_sys)
        _tmp.append(_config)
        _tmp.append(_capab)
    self._system['system_info'] = _tmp
    return self._system

  def core(self):
    _core_info ={}
    _core = {}
    _tmp = []
    for e in self.doc.getElementsByTagName('node'):
        for e1 in e.getElementsByTagName('node'):
            if e.getAttribute('id').startswith('core') and e.getAttribute('class')=='bus':
                _core_info = self.mfg_data(e)
                _core_info['physid'] = str(e.getElementsByTagName('physid')[0].firstChild.nodeValue)
                _core_info['slot'] = str(e.getElementsByTagName('physid')[0].firstChild.nodeValue)
                _tmp.append(_core_info)
                _core['core_info'] = _tmp
                break
    return _core
    
  def mfg_data(self,node):
    """
    description, product name, vendor, version, serial are generic
    information container for all devices/components
    """
    self._mfg_data = {}
    val = node.getElementsByTagName('description')
    for v in val:
        self._mfg_data['description'] = v.firstChild.nodeValue.__str__()
        break
    val = node.getElementsByTagName('product')
    for v in val:
        self._mfg_data['product'] = v.firstChild.nodeValue.__str__()
        break
    val = node.getElementsByTagName('version')
    for v in val:
        self._mfg_data['version'] = v.firstChild.nodeValue.__str__()
        break
    val = node.getElementsByTagName('vendor')
    for v in val:
        self._mfg_data['vendor'] = v.firstChild.nodeValue.__str__()
        break
    val = node.getElementsByTagName('serial')
    for v in val:
        self._mfg_data['serial'] = v.firstChild.nodeValue.__str__()
        break
    return self._mfg_data
    
  def extended_mfg_data(self,node):
    pass
    
  def config_capab_res(self, node, attr1='id',attr2=None):
    self._res = {}
    for n in range(len(node)):
        try:
            self._res[str(node[n].getAttribute(attr1))] = node[n].firstChild.data.__str__()
        except:
            if attr2 !=None:
                self._res[str(node[n].getAttribute(attr1))] = str(node[n].getAttribute(attr2))
            else:
                self._res[str(node[n].getAttribute(attr1))] = None
    return self._res
        
    
class Devices(System):
  def firmware(self):
    self._fw_data =[]
    self._fw_mfg = {}
    self._firmware = {}
    nodes = self.doc.getElementsByTagName('node')[0].getElementsByTagName('node')[0].getElementsByTagName('node')
    for node in nodes:
        self._fw_mfg = self.mfg_data(node)
        self._fw_mfg['physid'] = str(node.getElementsByTagName('physid')[0].firstChild.nodeValue)
        self._fw_mfg['date'] = str(node.getElementsByTagName('date')[0].firstChild.nodeValue)
        subnodes = self.doc.getElementsByTagName('size')
        for node in subnodes:
            unit =  str(node.attributes['units'].value)
            val = node.firstChild.nodeValue.__str__()
            self._fw_mfg['size'] = val+ " " + unit
            break
        subnodes = self.doc.getElementsByTagName('capacity')
        for node in subnodes:
            #print node.toxml()
            unit =  str(node.attributes['units'].value)
            val = node.firstChild.nodeValue.__str__()
            self._fw_mfg['capacity'] = val + " " + unit
            break
        subnodes = nodes[0].getElementsByTagName('capabilities')
        for node in subnodes:
            inode = node.getElementsByTagName('capability')
            self._capabilities = self.config_capab_res(inode)
        break
    self._fw_data.append(self._fw_mfg)
    self._fw_data.append(self._capabilities)
    self._firmware['firmware_info'] = self._fw_data
    return self._firmware
    
  def cpu(self, xml_chunk):
    self._cpudata ={}
    self._cpuinterim =[]
    self._cpu = {}
    self._capab = {}
    self._config = {}
    dev_type = xml_chunk.attributes['class'].value
    dev_id = xml_chunk.attributes['id'].value
    try:
        self._cpu = self.mfg_data(xml_chunk)
        self._cpu['physid'] = str(xml_chunk.getElementsByTagName('physid')[0].firstChild.nodeValue)
        self._cpu['businfo'] = str(xml_chunk.getElementsByTagName('businfo')[0].firstChild.nodeValue)
        self._cpu['slot'] = str(xml_chunk.getElementsByTagName('slot')[0].firstChild.nodeValue)
        subnode = xml_chunk.getElementsByTagName('size')
        unit =  str(subnode[0].attributes['units'].value)
        val = subnode[0].firstChild.nodeValue.__str__()
        self._cpu['size'] = val+ " " + unit
        subnode = xml_chunk.getElementsByTagName('capacity')
        unit =  str(subnode[0].attributes['units'].value)
        val = subnode[0].firstChild.nodeValue.__str__()
        self._cpu['capacity'] = val+ " " + unit
        subnode = xml_chunk.getElementsByTagName('width')
        unit =  str(subnode[0].attributes['units'].value)
        val = subnode[0].firstChild.nodeValue.__str__()
        self._cpu['width'] = val+ " " + unit
        subnode = xml_chunk.getElementsByTagName('clock')
        unit =  str(subnode[0].attributes['units'].value)
        val = subnode[0].firstChild.nodeValue.__str__()
        self._cpu['clock'] = val+ " " + unit
        subnodes = xml_chunk.getElementsByTagName('capabilities')
        node = subnodes[0]
        inode = node.getElementsByTagName('capability')
        self._capab = self.config_capab_res(inode)
        subnodes = xml_chunk.getElementsByTagName('configuration')
        node = subnodes[0]
        inode = node.getElementsByTagName('setting')
        self._config = self.config_capab_res(inode,'id','value')
        self._cpuinterim.append(self._cpu)
        self._cpuinterim.append(self._config)
        self._cpuinterim.append(self._capab)
        self._cpudata['_info'] = self._cpuinterim
    except:
        #print "Some attributes are missing"
        pass
    for e in xml_chunk.getElementsByTagName('node'):
        self._memcache_data = []
        self._memcache = {}
        self._memcachemfg = {}
        self._memcachecapab = {}
        if e.getAttribute('id').startswith('cache'):
            try:
                self._memcachemfg = self.mfg_data(e)
                self._memcachemfg['physid'] = str(e.getElementsByTagName('physid')[0].firstChild.nodeValue)
                self._memcachemfg['slot'] = str(e.getElementsByTagName('slot')[0].firstChild.nodeValue)
                subnode = e.getElementsByTagName('size')
                unit =  str(subnode[0].attributes['units'].value)
                val = subnode[0].firstChild.nodeValue.__str__()
                self._memcachemfg['size'] = val+ " " + unit
                subnode = e.getElementsByTagName('capacity')
                unit =  str(subnode[0].attributes['units'].value)
                val = subnode[0].firstChild.nodeValue.__str__()
                self._memcachemfg['capacity'] = val+ " " + unit
                node=e.getElementsByTagName('capabilities')
                inode = node[0].getElementsByTagName('capability')
                self._memcachecapab = self.config_capab_res(inode)
            except:
                #print "Some attributes are missing"S
                pass
            self._memcache_data.append(self._memcachemfg)
            self._memcache_data.append(self._memcachecapab)
            self._memcache[str(e.getAttribute('id'))] = self._memcache_data
        self._cpudata.update(self._memcache)
    return self._cpudata

  def memory(self, xml_chunk):
    self._memdata ={}
    self._meminterim =[]
    self._mem = {}
    dev_type = xml_chunk.attributes['class'].value
    dev_id = xml_chunk.attributes['id'].value
    try:
        self._mem = self.mfg_data(xml_chunk)
        self._mem['physid'] = str(xml_chunk.getElementsByTagName('physid')[0].firstChild.nodeValue)
        self._mem['slot'] = str(xml_chunk.getElementsByTagName('slot')[0].firstChild.nodeValue)
        self._meminterim.append(self._mem)
        self._memdata['_info'] = self._meminterim
    except:
        #print "Some attributes are missing"
        pass
    subnodes = xml_chunk
    for e in xml_chunk.getElementsByTagName('node'):
        self._bank_data = []
        self._bank = {}
        self._bankmfg = {}
        if e.getAttribute('id').startswith('bank'):
            dev_type = xml_chunk.attributes['class'].value
            dev_id = subnodes.attributes['id'].value
            try:
                self._bankmfg = self.mfg_data(e)
                self._bankmfg['physid'] = str(e.getElementsByTagName('physid')[0].firstChild.nodeValue)
                self._bankmfg['slot'] = str(e.getElementsByTagName('slot')[0].firstChild.nodeValue)
                subnode = e.getElementsByTagName('size')
                unit =  str(subnode[0].attributes['units'].value)
                val = subnode[0].firstChild.nodeValue.__str__()
                self._bankmfg['size'] = val+ " " + unit
                subnode = e.getElementsByTagName('width')
                unit =  str(subnode[0].attributes['units'].value)
                val = subnode[0].firstChild.nodeValue.__str__()
                self._bankmfg['width'] = val+ " " + unit
                subnode = e.getElementsByTagName('clock')
                unit =  str(subnode[0].attributes['units'].value)
                val = subnode[0].firstChild.nodeValue.__str__()
                self._bankmfg['clock'] = val+ " " + unit
                self._bank_data.append(self._bankmfg)
                #here add capabilities, config & resources to the list _bank_data
                self._bank[str(e.getAttribute('id'))] = self._bank_data
            except:
                #print "Some tags or attributes are missing..."
                pass
        self._memdata.update(self._bank)
    return self._memdata

  def network(self, xml_chunk):
    self._networkdata =[]
    self._network = {}
    _capab = {}
    _resource = {}
    _config = {}
    dev_type = xml_chunk.attributes['class'].value
    dev_id = xml_chunk.attributes['id'].value

    self._network = self.mfg_data(xml_chunk)
    self._network['physid'] = str(xml_chunk.getElementsByTagName('physid')[0].firstChild.nodeValue)
    self._network['businfo'] = str(xml_chunk.getElementsByTagName('businfo')[0].firstChild.nodeValue)
    self._network['logicalname'] = str(xml_chunk.getElementsByTagName('logicalname')[0].firstChild.nodeValue)
    self._network['serial'] = str(xml_chunk.getElementsByTagName('serial')[0].firstChild.nodeValue)
    try:
        subnode = xml_chunk.getElementsByTagName('size')
        unit =  str(subnode[0].attributes['units'].value)
        val = subnode[0].firstChild.nodeValue.__str__()
        self._network['size'] = val+ " " + unit
    except:
        self._network['size'] = None
    self._network['capacity'] = str(xml_chunk.getElementsByTagName('capacity')[0].firstChild.nodeValue)
    subnode = xml_chunk.getElementsByTagName('width')
    unit =  str(subnode[0].attributes['units'].value)
    val = subnode[0].firstChild.nodeValue.__str__()
    self._network['width'] = val+ " " + unit
    subnode = xml_chunk.getElementsByTagName('clock')
    unit =  str(subnode[0].attributes['units'].value)
    val = subnode[0].firstChild.nodeValue.__str__()
    self._network['clock'] = val+ " " + unit
    subnodes = xml_chunk.getElementsByTagName('configuration')
    node = subnodes[0]
    inode = node.getElementsByTagName('setting')
    _config = self.config_capab_res(inode,'id','value')
    subnodes = xml_chunk.getElementsByTagName('capabilities')
    node = subnodes[0]
    inode = node.getElementsByTagName('capability')
    _capab = self.config_capab_res(inode)
    subnodes = xml_chunk.getElementsByTagName('resources')
    node = subnodes[0]
    inode = node.getElementsByTagName('resource')
    _resource = self.config_capab_res(inode,'type','value')
    self._networkdata.append(self._network)
    self._networkdata.append(_capab)
    self._networkdata.append(_config)
    self._networkdata.append(_resource)
    return self._networkdata

  def sas_storage(self, xml_chunk):
    self._sas_storageall ={}
    self._sas_storagedata =[]
    self._sas_storage = {}
    _capab = {}
    _resource = {}
    _config = {}
    self._volinfo={}
    dev_type = xml_chunk.attributes['class'].value
    dev_id = xml_chunk.attributes['id'].value
    try:        
        self._sas_storage = self.mfg_data(xml_chunk)
        self._sas_storage['physid'] = str(xml_chunk.getElementsByTagName('physid')[0].firstChild.nodeValue)
        self._sas_storage['businfo'] = str(xml_chunk.getElementsByTagName('businfo')[0].firstChild.nodeValue)
        self._sas_storage['logicalname'] = str(xml_chunk.getElementsByTagName('logicalname')[0].firstChild.nodeValue)
        subnode = xml_chunk.getElementsByTagName('width')
        unit =  str(subnode[0].attributes['units'].value)
        val = subnode[0].firstChild.nodeValue.__str__()
        self._sas_storage['width'] = val+ " " + unit
        subnode = xml_chunk.getElementsByTagName('clock')
        unit =  str(subnode[0].attributes['units'].value)
        val = subnode[0].firstChild.nodeValue.__str__()
        self._sas_storage['clock'] = val+ " " + unit
        subnodes = xml_chunk.getElementsByTagName('configuration')
        node = subnodes[0]
        inode = node.getElementsByTagName('setting')
        _config = self.config_capab_res(inode,'id','value')
        subnodes = xml_chunk.getElementsByTagName('capabilities')
        node = subnodes[0]
        inode = node.getElementsByTagName('capability')
        _capab = self.config_capab_res(inode)
        subnodes = xml_chunk.getElementsByTagName('resources')
        node = subnodes[0]
        inode = node.getElementsByTagName('resource')
        _resource = self.config_capab_res(inode,'value', 'type')
    except:
        #print "Some attribute missing in the tag"
        pass
    self._sas_storagedata.append(self._sas_storage)
    self._sas_storagedata.append(_capab)
    self._sas_storagedata.append(_config)
    self._sas_storagedata.append(_resource)
    self._sas_storageall['_info']=self._sas_storagedata
    for e in xml_chunk.getElementsByTagName('node'):
        if e.getAttribute('id').startswith('disk'):
            self._diskinfo = []
            _diskmfg = {}
            _config = {}
            _capab = {}
            subnodes = e
            dev_type = subnodes.attributes['class'].value
            dev_id = subnodes.attributes['id'].value
            _diskmfg = self.mfg_data(subnodes)
            _diskmfg['physid'] = str(subnodes.getElementsByTagName('physid')[0].firstChild.nodeValue)
            _diskmfg['businfo'] = str(subnodes.getElementsByTagName('businfo')[0].firstChild.nodeValue)
            _diskmfg['logicalname'] = str(subnodes.getElementsByTagName('logicalname')[0].firstChild.nodeValue)
            _diskmfg['dev'] = str(subnodes.getElementsByTagName('dev')[0].firstChild.nodeValue)
            subnode = subnodes.getElementsByTagName('size')
            unit =  str(subnode[0].attributes['units'].value)
            val = subnode[0].firstChild.nodeValue.__str__()
            _diskmfg['size'] = val+ " " + unit
            try:
                node=subnodes.getElementsByTagName('configuration')
                inode = node[0].getElementsByTagName('setting')
                _config = self.config_capab_res(inode,'id','value')
                node =subnodes.getElementsByTagName('capabilities')
                inode = node[0].getElementsByTagName('capability')
                _capab = self.config_capab_res(inode)
            except:
                pass
            self._diskinfo.append(_diskmfg)
            self._diskinfo.append(_config)
            self._diskinfo.append(_capab)
            _vol = []
            _vol.append(self._diskinfo)
            for tag1 in subnodes.getElementsByTagName('node'):
                tmp = []
                _vol_mfg = {}
                _vol_capab = {}
                tmp_dict = {}
                if tag1.getAttribute('id').startswith('volume'):
                    try:
                        _vol_mfg = self.mfg_data(tag1)
                        _vol_mfg['physid'] = str(tag1.getElementsByTagName('physid')[0].firstChild.nodeValue)
                        _vol_mfg['businfo'] = str(tag1.getElementsByTagName('businfo')[0].firstChild.nodeValue)
                        _vol_mfg['logicalname'] = str(tag1.getElementsByTagName('logicalname')[0].firstChild.nodeValue)
                        _vol_mfg['capacity'] = str(tag1.getElementsByTagName('capacity')[0].firstChild.nodeValue)
                        sub = tag1.getElementsByTagName('capabilities')
                        node = sub[0]
                        inode = node.getElementsByTagName('capability')
                        _vol_capab = self.config_capab_res(inode)
                    except:
                        #print "Some tags are missing"
                        pass
                    tmp.append(_vol_mfg)
                    tmp.append(_vol_capab)
                    tmp_dict[str(tag1.getAttribute('id'))] = tmp
                    _vol.append(tmp_dict)
            self._volinfo[str(subnodes.getAttribute('id'))] = _vol
        self._sas_storageall.update(self._volinfo)
    return self._sas_storageall
        
  def get_cpu(self):
    self._cpuinfo ={}
    for e in self.doc.getElementsByTagName('node'):
        if e.getAttribute('id').startswith('cpu'):
            self._cpuinfo[str(e.getAttribute('id'))] = self.cpu(e)
    return self._cpuinfo
  def get_memory(self):
    self._meminfo ={}
    for e in self.doc.getElementsByTagName('node'):
        if e.getAttribute('id').startswith('memory'):
            self._meminfo[str(e.getAttribute('id'))] = self.memory(e)
    return self._meminfo

  def get_network(self):
    self._nicinfo ={}
    for e in self.doc.getElementsByTagName('node'):
        if e.getAttribute('id').startswith('pci'):
            for tag in e.getElementsByTagName('node'):
                if tag.getAttribute('id').startswith('pci'):
                    self._nicinfo[str(tag.getAttribute('id'))] = {}
                    for tag1 in tag.getElementsByTagName('node'):
                        if tag1.getAttribute('id').startswith('network'):
                            #print tag.getAttribute('id')
                            #print tag1.getAttribute('id')
                            self._nicinfo[str(tag.getAttribute('id'))][str(tag1.getAttribute('id'))] = self.network(tag1)
    return self._nicinfo
  
  def get_sas_storage(self):
    self._sas_storage_info ={}
    for e in self.doc.getElementsByTagName('node'):
        if e.getAttribute('id').startswith('pci'):
            for tag in e.getElementsByTagName('node'):
                if tag.getAttribute('id').startswith('pci'):
                    self._sas_storage_info[str(tag.getAttribute('id'))] = {}
                    for tag1 in tag.getElementsByTagName('node'):
                        if tag1.getAttribute('id').startswith('storage'):
                            self._sas_storage_info[str(tag.getAttribute('id'))][str(tag1.getAttribute('id'))] = self.sas_storage(tag1)
    return self._sas_storage_info
  def get_sata_storage(self):
    self._sas_storage_info ={}
    for e in self.doc.getElementsByTagName('node'):
        if e.getAttribute('id').startswith('scsi') and e.getAttribute('class')=='storage':
            self._sas_storage_info[str(e.getAttribute('id'))] = {}
            self._sas_storage_info[str(e.getAttribute('id'))] = self.sas_storage(e)
    return self._sas_storage_info

  def get_power(self):
    self._power = {}
    self._power_info={}
    for e in self.doc.getElementsByTagName('node'):
        if e.getAttribute('id').startswith('power') and e.getAttribute('class')=='power':
            self._power_info[str(e.getAttribute('id'))] = {}

            try:
                self._power = self.mfg_data(e)
                self._power['physid'] = str(e.getElementsByTagName('physid')[0].firstChild.nodeValue)
                self._power['serial'] = str(e.getElementsByTagName('serial')[0].firstChild.nodeValue)
                subnode = e.getElementsByTagName('capacity')
                unit =  str(subnode[0].attributes['units'].value)
                val = subnode[0].firstChild.nodeValue.__str__()
                self._power['capacity'] = val+ " " + unit
            except:
                #print "Hmm, some attributes are missing...."
                pass
            self._power_info[str(e.getAttribute('id'))] = self._power 
    return self._power_info
if __name__=='__main__':
  #Below line are not needed while using this a module.
  x = Devices("lshw.log")
  print "-------- SYSTEM --------"
  pprint(x.system_info())
  print "-------- CORE --------"
  pprint(x.core())
  print "-------- FIRMWARE --------"
  pprint(x.firmware())
  print "-------- CPU --------"
  pprint(x.get_cpu())
  print "-------- MEMORY --------"
  pprint(x.get_memory())
  print "-------- NETWORK --------"
  pprint(x.get_network())
  print "-------- SAS STORAGE --------"
  pprint(x.get_sas_storage())
  print "-------- SATA STORAGE --------"
  pprint(x.get_sata_storage())
  print "-------- POWER --------"
  pprint(x.get_power())
