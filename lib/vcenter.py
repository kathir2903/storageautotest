
import json
import sys
import os
import re
import time
import shutil
from contextlib import contextmanager
from time import sleep, strftime, daylight
from datetime import datetime, timedelta
from ns.src.lib.common.utils import *
from psphere import client
from psphere import managedobjects
from psphere import errors
import traceback
import pdb


class Wrapper(object):
    """wrapper around Task objects"""

    def __init__(self, taskcls, *args, **kwargs):
        self.taskcls = taskcls
        self.args = args
        self.kwargs = kwargs
        self.task = None

    def createtask(self):
        """create a psphere task object"""
        self.task = self.taskcls(*self.args, **self.kwargs)
        return self.task

    def gettask(self):
        """ return task object """
        if self.task is None:
            self.task = self.createtask()
        return self.task


def connect(server, user, pwd, timeout=600):
    """ open vcenter connection  """
    def _connect():
        return client.Client(server, user, pwd, timeout=timeout)
    return onerrorretry(_connect, limit=10, interval=5)


def vsconnect(server, user, pwd, timeout=600):
    return connect(server, user, pwd, timeout=timeout)


@contextmanager
def vspherehandle(server, user, pwd, timeout=600):
    """ vsphere connect context """
    try:
        vshandle = vsconnect(server, user, pwd, timeout=timeout)
        yield vshandle
    except Exception as exc:
        print '\n********\n%s\n*********\n' % traceback.format_exc()
        raise exc
    finally:
        if vshandle:
            vshandle.logout()
            cache = vshandle.options.cache
            if hasattr(cache, 'location') and cache.location is not None:
                shutil.rmtree(cache.location, True)


def success(task):
    """returns True if a task is complete successfully, else False"""
    return task.info.state == 'success'


def failure(task):
    """returns True if a task failed, else False"""
    return task.info.state == 'error'


def elapsedtime(task):
    """
    returns the time elapsed in
    seconds between start and complete time
    """
    dst = -1 if daylight else 0
    completeTime = datetime.now() + timedelta(hours=dst)
    tt = completeTime - task.info.startTime.replace(tzinfo=None)
    val = (tt.microseconds + (tt.seconds + tt.days * 24 * 3600) * 10**6) / 10**6
    return val


def raisefailure(task):
    """ raise error when failed """
    raise Exception(task.info)


def gettask(taskobj):
    """ get, return task object if wrapped """
    if isinstance(taskobj, Wrapper):
        return taskobj.gettask()
    return taskobj


def waiter(taskobj, _cnt=None, log=stdoutwrite):
    """ initiate the task and wait to complete """
    try:
        return _helper(taskobj, _cnt=_cnt, log=stdoutwrite)
    except Exception as exc:
        raise exc


def _helper(taskobj, _cnt=None, log=stdoutwrite):
    """ helper method for task runner """
    progress = None
    if _cnt is None:
        _cnt = 5
    iswrapper = isinstance(taskobj, Wrapper)
    task = gettask(taskobj)
    while True:
        task.update_view_data(properties=['info'])
        if success(task):
            log('100%% at %s\n' % strftime('%Y-%m-%d %H:%M:%S'))
            return elapsedtime(task)
        elif failure(task):
            log('Error reported: %s\n' % str(task.info.error.localizedMessage))
            if iswrapper:
                log('Retrying...\n')
                task = taskobj.createtask()
            else:
                failure(task)
        elif hasattr(task.info, 'progress'):
            if task.info.progress != progress:
                log(str(task.info.progress) + '%')
                progress = task.info.progress
        log('.')
        stdoutflush()
        if _cnt == 0:
            break
        sleep(2)
        _cnt -= 1
    return None


def get_host_nw(host, nwname):
    #_ = [net for net in host.network if hasattr(net, 'name') and net.name==nwname]
    for net in host.network:
        if hasattr(net, 'name') and net.name == nwname:
            return net
    return None
    """
    for net in host.network:
        if hasattr(net, 'name'):
            print net.name
    """


def _rm_nic_devchange(vsclient, nics):
    changes = []
    for dev in nics:
        nic = vsclient.create('VirtualEthernetCard')
        nic.key = dev.key
        spec = vsclient.create('VirtualDeviceConfigSpec')
        spec.operation = 'remove'
        spec.fileOperation = None
        spec.device = nic
        changes.append(spec)
    return changes


def _cr_nic_devchange(vclient, vm, net=['qaNet03'], nicintf='VirtualVmxnet3'):
    host = vm.runtime.host
    changes = []
    for nw in net:
        # pdb.set_trace()

        nw_inhost = get_host_nw(host, nw)
        backing = vclient.create('VirtualEthernetCardNetworkBackingInfo')
        backing.network = nw_inhost
        backing.deviceName = nw
        conninfo = vclient.create('VirtualDeviceConnectInfo')
        conninfo.allowGuestControl = False
        conninfo.startConnected = True
        conninfo.connected = True
        nic = vclient.create(nicintf)
        nic.key = 0
        nic.connectable = conninfo
        nic.backing = backing
        spec = vclient.create('VirtualDeviceConfigSpec')
        spec.operation = 'add'
        spec.fileOperation = None
        spec.device = nic
        changes.append(spec)
    return changes
    # print host


def get(moclass, vclient, name):
    """ wrap for managedobjects get method """
    try:
        return moclass.get(vclient, name=name)
    except errors.ObjectNotFoundError as exc:
        raise errors.ObjectNotFoundError(exc, moclass.__name__, exc.message)


def all(moclass, vclient, names=None, properties=[]):
    """ get all vm properties """
    if names is not None and not names:
        return []
    properties = list(properties)
    if 'name' not in properties:
        properties.append('name')
    property_spec = vclient.create('PropertySpec')
    property_spec.type = moclass.__name__
    property_spec.all = False
    property_spec.pathSet = ['name']

    pfs = vclient.get_search_filter_spec(
        vclient.sc.rootFolder._mo_ref, property_spec)
    objs = vclient.sc.propertyCollector.RetrieveProperties(specSet=pfs)
    vms = []
    for obj in objs:
        for prop in obj.propSet or []:
            if prop.name == 'name' and \
               names is None or prop.val in names:
                vms.append(obj.obj)
    return vms


def create_vmrelocspec(vsclient, host, dsname):
    """ make vm reloc spec """
    datastore = find_datastore(host, dsname)
    if datastore is None:
        raise Exception(
            'Could not find datastore [%s] on host [%s]' %
            (dsname, host.name))
    spec = vsclient.create('VirtualMachineRelocateSpec')
    spec.datastore = datastore
    spec.host = host
    spec.pool = host.parent.resourcePool
    spec.diskMoveType = 'moveAllDiskBackingsAndDisallowSharing'
    spec.transform = None
    return spec


def find_datastore(host, dsname, require_access=True):
    """ return datastore details """
    for ds in host.datastore:
        if ds.summary.name == dsname:
            if require_access and not ds.summary.accessible:
                raise ValueError(
                    'Datastore [%s] is not accessible from host [%s]' %
                    (dsname, host.name))
            return ds
    return None


def create_relocspec_disklocator(vsclient, ds, disk, vmdktype):
    """ make disklocator structure for relocspec """
    _, filepath = parse_vmdk_path(disk['vmdkpath'])
    vmdkpath = '[%s] %s' % (ds.name, filepath)
    locator = vsclient.create('VirtualMachineRelocateSpecDiskLocator')
    locator.datastore = ds
    locator.diskId = disk['key']

    def _diskbackinginfo(vsclient, vmdkpath, vmdktype):
        backing = vsclient.create('VirtualDiskFlatVer2BackingInfo')
        backing.diskMode = 'presistent'
        backing.fileName = vmdkpath
        if vmdktype is not None:
            backing.thinProvisioned = vmdktype == disktype.thin
            if vmdktype in [disktype.thickeagerzero, disktype.thicklazyzero]:
                backing.eagerlyScrub = vmdktype == disktype.thickeagerzero
        return backing
    locator.diskBackingInfo = _diskbackinginfo(vsclient, vmdkpath, vmdktype)
    return locator


def find_scsi_controller(vm, scsibusnum):
    """ return scsi controller info """
    for dev in vm.config.hardware.device:
        if dev.deviceInfo.label == 'SCSI controller %d' % scsibusnum:
            return dev
    return None


def find_target(vm, scsibusnum, scsiunitnum):
    """ return target scsi details """
    controller = find_scsi_controller(vm, scsibusnum)
    for dev in vm.config.hardware.device:
        if getattr(dev, 'controllerKey', None) and \
                dev.controllerKey == controller.key and \
                dev.unitNumber == scsiunitnum:
            return dev
    return None


def get_scsi_controllers(vm):
    """ get available scsi controllers """
    controllernos = [0, 1, 2, 3]
    controllers = [find_scsi_controller(vm, x) for x in controllernos]
    return dict([(x.key, x) for x in controllers if x is not None])


def get_vm_disk_control(vm):
    disks = []
    controllers = get_scsi_controllers(vm)
    for dev in vm.config.hardware.device:
        if hasattr(dev, 'controllerKey') and dev.controllerKey in controllers:
            controller = controllers[dev.controllerKey]
            disks.append((controller, dev))
    return disks


def get_vm_disks(vm):
    """ return all vm disk details """
    diskinfo = []
    for controller, disk in get_vm_disk_control(vm):
        diskinfo.append({'label': str(disk.deviceInfo.label),
                         'vmdkpath': str(disk.backing.fileName),
                         'targetid': '%d:%d' % (controller.busNumber,
                                                disk.unitNumber),
                         'key': str(disk.key)})
    return diskinfo


def parse_vmdk_path(path):
    m = re.match(r'(\[[^\]]+\]) ([\S]+)', path)
    if not m:
        raise ValueError('%s is not a valid VMDK path' % str(path))
        ds = m.group(1)
        datastore = ds[1:-1]
    return datastore, m.group(2)


def create_snapshot(vsclient, host, vmname):
    """ create snapshot of a given vm """
    from datetime import datetime
    snapname = vmname + datetime.now().strftime('-%Y%m%d %H:%M:%S-snapshot')
    vm = get(managedobjects.VirtualMachine, vsclient, name=vmname)
    taskobj = Wrapper(
        vm.CreateSnapshot_Task,
        name=snapname,
        memory=False,
        quiesce=True)
    return waiter(taskobj)


def fullclone_task(vsclient,
                   esxserver,
                   datastore,
                   srcvmname,
                   newvmname,
                   vmdktype=None,
                   memory=None,
                   numcpus=None,
                   log=None):
    """ task to run run full clone of given vm """
    vm = get(managedobjects.VirtualMachine, vsclient, name=srcvmname)
    clonespec = vsclient.create('VirtualMachineCloneSpec')
    configspec = vsclient.create('VirtualMachineConfigSpec')
    host = get(managedobjects.HostSystem, vsclient, name=esxserver)
    relocspec = create_vmrelocspec(vsclient, host, datastore)
    if vmdktype is not None:
        relocspec.disk = [
            create_relocspec_disklocator(
                vsclient,
                relocspec.datastore,
                disk,
                vmdktype) for disk in get_vm_disks(vm)]
    configspec.name = newvmname
    configspec.guestId = vm.config.guestId
    configspec.memoryMB = None
    configspec.numCPUs = None
    clonespec.powerOn = True
    clonespec.template = False
    clonespec.location = relocspec
    clonespec.config = configspec
    clonespec.customization = None
    clonespec.snapshot = None
    taskobj = Wrapper(vm.CloneVM_Task,
                      name=newvmname,
                      folder=vm.parent,
                      spec=clonespec)
    return taskobj


def linkedclone_task(vsclient, esxserver, datastore, srcvmname, newvmname):
    """ task to run run linked clone of given vm """
    vm = get(managedobjects.VirtualMachine, vsclient, name=srcvmname)
    create_snapshot(vsclient, esxserver, vm.name)
    host = get(managedobjects.HostSystem, vsclient, name=esxserver)
    relocspec = create_vmrelocspec(vsclient, host, datastore)
    clonespec = vsclient.create('VirtualMachineCloneSpec')
    relocspec.diskMoveType = 'createNewChildDiskBacking'
    clonespec.powerOn = False
    clonespec.template = False
    clonespec.location = relocspec
    clonespec.customization = None
    clonespec.snapshot = vm.snapshot.currentSnapshot
    taskobj = Wrapper(vm.CloneVM_Task,
                      name=newvmname,
                      folder=vm.parent,
                      spec=clonespec)
    return taskobj


class vcenter(object):

    def __init__(self,
                 vcserver='172.18.39.200',
                 esx='vm09.mgmt.netskope.com',
                 datastore='qa.local',
                 vcuser='netskope\\jenkins',
                 vcpwd='Test1234'):
        self.vcserver = vcserver
        self.esx = esx
        self.datastore = datastore
        self.vcuser = vcuser
        self.vcpwd = vcpwd
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context

    def find_hosts(self):
        hslist = managedobjects.HostSystem.all(self.vsclient)
        for hs in hslist:
            print hs.name
        return hslist

    def getallhosts(self):
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            hslist = managedobjects.HostSystem.all(vsclient)
            hsnames = []
            for hs in hslist:
                hsnames.append(hs.name)
            return hsnames

    def fullclone(self, sourcevm, newvm):
        """ create full clone of a vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            #task = fullclone_task(vsclient, self.esx, self.datastore, 'Appliance-36.6.0-Template', 'kathir-tester')
            task = fullclone_task(
                vsclient,
                self.esx,
                self.datastore,
                sourcevm,
                newvm)
            return waiter(task, _cnt=None)

    def create_fullclone(self, srcvmname, newvmname, vmdktype=None):
        """ create full clone of a vm: deprecated """
        vm = managedobjects.VirtualMachine.get(self.vsclient, name=srcvmname)
        relocspec = create_vmrelocspec(
            self.vsclient, self.host, self.datastore)
        if vmdktype is not None:
            relocspec.disk = [
                create_relocspec_disklocator(
                    self.vsclient,
                    relocspec.datastore,
                    disk,
                    vmdktype) for disk in get_vm_disks(vm)]
        self.configspec.name = newvmname
        self.configspec.guestId = vm.config.guestId
        self.configspec.memoryMB = None
        self.configspec.numCPUs = None
        self.clonespec.powerOn = False
        self.clonespec.template = False
        self.clonespec.location = relocspec
        self.clonespec.config = self.configspec
        self.clonespec.customization = None
        self.clonespec.snapshot = None
        vm.CloneVM_Task(name=newvmname, folder=vm.parent, spec=clonespec)

    def linkedclone(self):
        """ create linked clone of a vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            task = linkedclone_task(
                vsclient,
                self.esx,
                self.datastore,
                'kathir-tester',
                'linkedclone-kathir-test')
            return waiter(task)

    def create_linkedclone(self, srcvmname, newvmname):
        """ create linked clone of a vm:deprecated """
        vm = managedobjects.VirtualMachine.get(self.vsclient, name=srcvmname)
        create_snapshot(self.vsclient, self.host, vm.name)
        relocspec = create_vmrelocspec(
            self.vsclient, self.host, self.datastore)
        relocspec.diskMoveType = 'createNewChildDiskBacking'
        self.clonespec.powerOn = False
        self.clonespec.template = False
        self.clonespec.location = relocspec
        self.clonespec.customization = None
        self.clonespec.snapshot = vm.snapshot.currentSnapshot
        vm.CloneVM_Task(name=newvmname, folder=vm.parent, spec=self.clonespec)

    def delete_vm(self, vmname):
        """ delete a given vm """
        #vm = managedobjects.VirtualMachine.get(self.vsclient, name=vmname)
        # return vm.Destroy_Task()
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            task = vmt.Destroy_Task()
            return waiter(task, _cnt=5)

    def getallvms(self):
        """ get all vms in a given esx server """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            if self.esx:
                hs = get(managedobjects.HostSystem, vsclient, name=self.esx)
                hs.preload('vm', properties=['name'])
                out = hs.vm
            else:
                out = managedobjects.VirtualMachine.all(vsclient)
            return [x.name for x in out]

    def migrate_vm(self, dstesx, vmname, priority='default'):
        """ vmotion vm to given esxserver """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vm = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            dsthost = get(managedobjects.HostSystem, vsclient, name=dstesx)
            dstpool = dsthost.parent.resourcePool
            mvpri = vsclient.create('VirtualMachineMovePriority')
            task = vm.MigrateVM_Task(
                pool=dstpool,
                host=dsthost,
                priority=mvpri.defaultPriority)
            return waiter(task)

    def poweron_vm(self, vmname):
        """ power-on a given vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            task = vmt.PowerOnVM_Task()
            return waiter(task)

    def poweroff_vm(self, vmname):
        """ power-off a given vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            task = vmt.PowerOffVM_Task()
            return waiter(task)

    def shutdown_vm(self, vmname):
        """ power-off a given vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            task = Wrapper(vmt.ShutdownGuest)
            return waiter(task)

    def unregister_vm(self, vmname):
        """ unregister a given vm from vcenter """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            task = vmt.UnregisterVM()
            return waiter(task)

    def rename_vm(self, oldname, newname):
        """ rename a given vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=oldname)
            task = Wrapper(vmt.Rename_Task, newName=newname)
            return waiter(task)

    def deletevmsnaps(self, vmname):
        """ remove all snapshots of given vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            task = Wrapper(vmt.RemoveAllSnapshots_Task)
            return waiter(task)

    def reboot(self, vmname):
        """ reboot vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            task = Wrapper(vmt.RebootGuest)
            return waiter(task)

    def reset(self, vmname):
        """ hard reset vm """
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vmt = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            task = Wrapper(vmt.ResetVM_Task)
            return waiter(task)

    def getnicdevices(self, vmname, nic=20):
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vm = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            vmhwdev = vm.config.hardware.device
        labels = ["Network adapter %d" % int(i) for i in range(nic)]
        # print labels
        nics = [device for device in vmhwdev if device.deviceInfo.label in labels]
        return nics

    def createnics(self, vmname):
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vm = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            devchanges = _cr_nic_devchange(vsclient, vm, ['qaNet03'])
            spec = vsclient.create('VirtualMachineConfigSpec')
            spec.deviceChange.extend(devchanges)
            task = vm.ReconfigVM_Task(spec=spec)
            return waiter(task)

    def getvmstate(self, vmname):
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vm = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            return vm.runtime.powerState

    def modifynics(self, vmname):
        with vspherehandle(self.vcserver, self.vcuser, self.vcpwd) as vsclient:
            vm = get(managedobjects.VirtualMachine, vsclient, name=vmname)
            nics = self.getnicdevices(vmname)
            nets = [dev.backing.deviceName for dev in nics]
            changes = _rm_nic_devchange(vsclient, nics)
            changes.extend(_cr_nic_devchange(vsclient, vm, nets))
            spec = vsclient.create('VirtualMachineConfigSpec')
            spec.deviceChange.extend(changes)
            # pdb.set_trace()
            task = vm.ReconfigVM_Task(spec=spec)
            return waiter(task), vm.runtime.powerState

if __name__ == "__main__":
    """
    self test program,
    below commented lines are the way
    this module can be used
    """
    #import ssl
    #ssl._create_default_https_context = ssl._create_unverified_context
    VirtualVmxnet3 = 'VirtualVmxnet3'
    vcenter_ip = '172.18.39.200'
    esx_ip = 'vm09.mgmt.netskope.com'
    datastore = 'qa.local'
    #vcenter_user = 'netskope\\kathir'
    #vcenter_pwd = 'Palani123$'
    vcenter_user = 'netskope\\jenkins'
    vcenter_pwd = 'Test1234'
    inst = vcenter(vcserver=vcenter_ip,
                   esx=esx_ip,
                   datastore=datastore,
                   vcuser=vcenter_user,
                   vcpwd=vcenter_pwd)
    print inst.getallvms()
    # inst.deletevmsnaps('renamed-kathir-test')
    # inst.fullclone()
    #inst.rename_vm('kathir-tester', 'renamed-kathir-test')
    # inst.poweroff_vm('renamed-kathir-test')
    # inst.poweron_vm('renamed-kathir-test')
    #inst.migrate_vm('vm09.mgmt.netskope.com', 'kathir-tester')
    # inst.linkedclone()
    # inst.reboot('renamed-kathir-test')
    # inst.delete_vm('renamed-kathir-test') # if a vm is powered-on delete_vm will fail
    #out = inst.getnicdevices('kathir-tester')
    #out = inst.getnicdevices('lxr')
    #out = inst.getnicdevices('qaautomation01')
    # inst.createnics('kathir-tester')
    # inst.modifynics('kathir-tester')

    def nw_stg():
        import pprint
        vcenter_ip = '172.18.39.200'
        esx = 'vm07.mgmt.netskope.com'
        datastore = 'qa.local'
        vcenter_user = 'netskope\\kathir'
        vcenter_pwd = 'Palani123$'
        vm07 = vcenter(vcserver=vcenter_ip,
                       esx=esx,
                       datastore=datastore,
                       vcuser=vcenter_user,
                       vcpwd=vcenter_pwd)
        """
        res = {}
        totalvms = 0
        for host in vm07.getallhosts():
            res[host] = []
            linst = vcenter(vcserver=vcenter_ip,
                    esx=host,
                    datastore=datastore,
                    vcuser=vcenter_user,
                    vcpwd=vcenter_pwd)
            allvms = linst.getallvms()
            totalvms += len(allvms)
            res[host].extend(allvms)
            #print host + ": "  + str(allvms)
            print host
            print "-----"
            for vm in allvms:
                print vm
            print "WAITING**********"
            time.sleep(10)
            res['total_vms'] = totalvms
            del linst
        pprint.pprint(res)

        """
        """
        for host in vm07.getallhosts():
            print "Working on Host %s" % host
            linst = vcenter(vcserver=vcenter_ip,
                    esx=host,
                    datastore=datastore,
                    vcuser=vcenter_user,
                    vcpwd=vcenter_pwd)
            allvms = linst.getallvms()
            for vmname in allvms:
                print "FOUND %s" % vmname
                status, powerstate = linst.modifynics(vmname)
                if powerstate== 'poweredOn':
                    vm07.reset(vmname)
            del linst
        """
        for host in vm07.getallhosts():
            print "Working on Host (%s)" % host
            linst = vcenter(vcserver=vcenter_ip,
                            esx=host,
                            datastore=datastore,
                            vcuser=vcenter_user,
                            vcpwd=vcenter_pwd)
            #allvms = vm07.getallvms()
            allvms = linst.getallvms()
            print "All vms (%s) found  on Host (%s)" % (str(allvms), host)
            completedvms = []
            for vmname in allvms:
                try:
                    # if vmname == 'blox01':
                    # print "FOUND %s" % vmname
                    out = linst.getnicdevices(vmname)
                    print "Nic Type on vm (%s) is (%s)" % (vmname, out[0].__class__.__name__)
                    print "total vms already completed nic modification (%s)" % str(completedvms)
                    if out[0].__class__.__name__ == 'VirtualE1000':
                        print "Working on vm (%s) served by host (%s)" % (vmname, host)
                        # if vm07.getvmstate(vmname) == 'poweredOn':
                        if linst.getvmstate(vmname) == 'poweredOn':
                            print "vm (%s) is on powered-on mode, so powering off now" % (vmname)
                            # vm07.poweroff_vm(vmname)
                            linst.poweroff_vm(vmname)
                            print "Modifying the VMNIC to 10G on vm (%s)" % (vmname)
                            #status, powerstate = vm07.modifynics(vmname)
                            status, powerstate = linst.modifynics(vmname)
                            completedvms.append(vmname)  # move out
                            if powerstate == 'poweredOn':
                                print "Resetting vm (%s)" % (vmname)
                                # vm07.reset(vmname)
                                linst.reset(vmname)
                            else:
                                print "Powering ON vm (%s) after changing the network adapter to 10G" % (vmname)
                                # vm07.poweron_vm(vmname)
                                linst.poweron_vm(vmname)
                        else:
                            print "vm (%s) is NOT on powered-on mode, so just modify VMNIC" % (vmname)
                            print "Modifying the VMNIC to 10G on vm (%s)" % (vmname)
                            #status, powerstate = vm07.modifynics(vmname)
                            status, powerstate = linst.modifynics(vmname)
                            completedvms.append(vmname)  # move out or delete
                    else:
                        print "Not modifying nic on vm (%s), nic is (%s)" % (vmname, out[0].__class__.__name__)
                        completedvms.append(vmname)
                except Exception as exc:
                    continue
            del linst
    # nw_stg()
