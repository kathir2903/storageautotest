#!/usr/bin/python


#Editor vim: ts=4:sw=4

#title      : remoteconnect.py
#description: Connection to Servers(SSH connection)
#author     : "kathir.gitit@gmail.com"
#usage      : python remoteconnect.py
#notes      : Can be used as module by calling from another program
#py version : 2.7


import os
import sys
import paramiko
import re
import traceback
import time
import json
from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint

class RemoteConnect(object):
    def __init__(self, uut):
        self.sess, self.sftp_sess = init_sess(uut)
    def __del__(self):
        try:
            self.sess, self.sftp_sess
        except:
            pass

class BuildReport(object):

    def sensor_rep(self, rec):
        """
        Output format will be in a dictionary like this,
        output_dict = { 'SENSOR': [value, units, status, 
                        low_norecovery, low_critical, low_nocritical,
                        up_norecovery, up_critical, up_nocritical]}
        """
        res = {}
        for l in rec:
            res[[str(v.strip()) for v in l.split("|")][0]] = \
                    [str(v.strip()) for v in l.split("|")][1:]
        return res

    def fru_rep(self, rec):
        """
        Output format will be in a dictionary like this,
        output_dict = { 'SENSOR': [value, units, status, 
                        low_norecovery, low_critical, low_nocritical,
                        up_norecovery, up_critical, up_nocritical]}
        """
        res = {}
        for l in rec:
            res[str(l.split(':')[0].strip())] = \
                    str(l.split(':')[1].strip()) if ":" in l else 0
        return res

    def ethtest_rep(self, rec):
        """ Report eth test output """
        res = {}
        for l in rec:
            res[str(l.split(':')[0].strip())] = \
                    str(l.split(':')[1].strip()) if ":" in l else 0
        return res 

    def storage_rep(self, rec, inventory):
        """
        Output format here,
        output_dict = { 'device_id': [name, maj:min, rm, 
                                    size, ro, type,mount_point]}
        
        """
        drive_pres = []
        res = {}
        for l in rec:
            if (l.startswith('s') or l.startswith('rs') or l.startswith('nvm')):
                res[[str(v.strip()) for v in l.split()][0]] = \
                        [str(v.strip()) for v in l.split()][1:]
        [drive_pres.append(key) for key in res.keys()]
        missing_drive = list(set(inventory).difference(set(drive_pres)))  
        status = False if len(missing_drive) == 0 else True
        return res, missing_drive, status
    
    def per_dev_rep(self, dest, drive_pres):
        dev_records = {}
        strings = ("Raw_Read_Error_Rate", "Throughput", "Spin_", "_Count", \
                "Reallocated", "Seek_Error", "Seek_Time", "Power_On", \
                "Temperature_Celsius", "Current_Pending", \
                "Offline_Uncorrectable")
        for drv in drive_pres:
            stdin, stdout, stderr = self.sess.exec_command('smartctl -a /dev/'+drv)
            if stdout.channel.recv_exit_status() != 0:
                print 'Command returns error code: %s' % \
                        stdout.channel.recv_exit_status()
                sys.exit()

            record = {}
            for line in stdout.readlines():
                if not line.startswith('Copyright') and line.count(':') == 1:
                    record[str(line.split(':')[0].strip())] =\
                            str(line.split(':')[1].strip())
                if any(st in line for st in strings):
                    record[str(line.split()[1].strip())] =\
                            [str(v.strip()) for v in line.split()][2:]

            cmd = 'smartctl -a /dev/'+drv + ' >/tmp/'+ drv + '.log'
            stdin, stdout, stderr = self.sess.exec_command(cmd)
            if stdout.channel.recv_exit_status() != 0:
                print 'Command returns error code: %s' \
                        % stdout.channel.recv_exit_status()
                sys.exit()
            self.sftp_sess.get('/tmp/'+drv+'.log', dest+"/"+drv+".log")
            dev_records.update({drv:record})
        return dev_records

    def per_dev_rep_nvme(self, dest, drive_pres):
        dev_records = {}
        for drv in drive_pres:
            drvid = re.match(r'nvme(\d+)\w+',drv).group(1)
            cmd = 'isdct show -a -o json -intelssd ' + str(drvid)
            stdin, stdout, stderr = self.sess.exec_command(cmd)
            if stdout.channel.recv_exit_status() != 0:
                print 'Command returns error code: %s' % \
                        stdout.channel.recv_exit_status()
                sys.exit()
            #print stdout.read()
            res = json.loads(stdout.read())
            res = res['IntelSSD Index ' + str(drvid)]
            cmd = ('isdct show -a -o json -intelssd '
                    + str(drvid) + ' >/tmp/'+ drv + '.log')
            stdin, stdout, stderr = self.sess.exec_command(cmd)
            if stdout.channel.recv_exit_status() != 0:
                print 'Command returns error code: %s' \
                        % stdout.channel.recv_exit_status()
                sys.exit()
            self.sftp_sess.get('/tmp/'+drv+'.log', dest+"/"+drv+".log")
            dev_records.update({drv:res})
        return dev_records


    def per_dev_rep_vendor(self, dest, drive_pres, vendor): 
        dev_records = {}
        drive_pres.sort()
        for drv in drive_pres:
            stdin, stdout, stderr = self.sess.exec_command('rssdm -L -n '+ str(drive_pres.index(drv)))
            if stdout.channel.recv_exit_status() !=0:
                print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
                if stdout.channel.recv_exit_status() == 8:
                    time.sleep(3)
                    stdin, stdout, stderr = self.sess.exec_command(cmd)
                else:
                    sys.exit()
            record = {}
            for line in stdout.readlines():
                if not line.startswith('Copyright') and line.count(':') == 1:
                    record[str(line.split(':')[0].strip())] =\
                            str(line.split(':')[1].strip())
            """
            cmd ='rssdm -L -n '+ str(drive_pres.index(drv)) + ' >/tmp/'+ drv + '.log'
            stdin, stdout, stderr = self.sess.exec_command(cmd)
            if stdout.channel.recv_exit_status() !=0:
                print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
                sys.exit()
            self.sftp_sess.get('/tmp/'+drv+'.log', dest+"/"+drv+".log")
            """
            pprint(record)
            time.sleep(10)
            dev_records.update({drv:record})
        return dev_records


    def isdct_rep(self, drive, logid, dest='/tmp'): 
        dev_records = {}
        strings = ("Raw_Read_Error_Rate", "Throughput", "Spin_", "_Count", \
                "Reallocated", "Seek_Error", "Seek_Time", "Power_On", \
                "Temperature_Celsius", "Current_Pending", \
                "Offline_Uncorrectable")
        (dev, drv) = drive.split('-')[1], drive.split('-')[3]
        cmd = '/root/isdct -device ' + dev + ' -drive ' + drv + ' -log ' + str(logid)
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        return stdout.readlines()
    
    def p3600_isdct_rep(self, drive, dest='/tmp'):
        dev_records = {}
        drvid = re.match(r'nvme(\d+)\w+',drive).group(1)
        showcmd = 'isdct show -a -o json -intelssd ' + drvid
        dumpcmd = 'isdct dump -o json -intelssd ' \
                + drvid + ' DataType=nvmelog LogID=2'
        cmdlist = [showcmd, dumpcmd]
        for cmd in cmdlist:
            stdin, stdout, stderr = self.sess.exec_command(cmd)
            if stdout.channel.recv_exit_status() !=0:
                print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
                sys.exit()
            res = json.loads(stdout.read())
            try:
                res = res['IntelSSD Index ' + drvid]
            except:
                res = res["SMART / Health Information (Log ID = 2)"]
                for k, v in res.iteritems():
                    if str(v).startswith('0x'): res[k] = int(v, 16)
            dev_records.update(res)
        return dev_records


    def rssdm_rep(self, drive,dest='/tmp'): 
        dev_records = {}
        strings = ('Power On Hours Count', 'Power Cycle Count',\
                'New Failing Block Count', 'Program Fail Count',\
                'Erase Fail Count', 'Unexpected Power Loss Count',\
                'Reported Uncorrectable Errors', 'Command Timeouts',\
                'Enclosure Temperature', 'Percentage Lifetime Used',\
                'Available Reserved Space', 'Power On Minutes',\
                'Write Protect Progress')
        cmd = 'rssdm -S -n '+ drive 
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() != 0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            if stdout.channel.recv_exit_status() == 8:
                time.sleep(3)
                stdin, stdout, stderr = self.sess.exec_command(cmd)
            else:
                sys.exit()
        buf = stdout.readlines()
        pat = re.compile(r'(\d+)')
        for line in buf:
            if any(st in line for st in strings):
                dev_records[pat.split(str(line))[2].strip()] = pat.split(str(line))[3]
        return dev_records       

    def fio_test_rep(self, rec, *args):
        fio_rec = {}
        for line in rec:
            if line.startswith(str(args[0])+"-"+ str(args[1][0] + ": (groupid")):
                try:
                    #print "First if %s" %args[1][0]
                    fio_rec[args[1][0]] = int(re.findall("err=(\s+\d+)", \
                            line)[0].strip())
                except IndexError:
                    print " No MD devices found, FIO test failed"
            if line.startswith(str(args[0])+"-"+ str(args[1][1] + \
                    ": (groupid")):
                try:
                    #print "Second if %s" %args[1][1]
                    fio_rec[str(args[1][1])] = int(re.findall("err=(\s+\d+)", \
                            line)[0].strip())
                except IndexError:
                    print " No MD devices found, FIO test failed"
        pprint(fio_rec)  
        return fio_rec
         
    def ipmi_frutable_rep(self, rec):
        """
        Output format,
        output_dict = { 'name': 'value'} 
        """
        res = {}
        for l in rec:
            res[str(re.split('[()=]',l)[1].strip())] = \
                    str(l.split('=')[1].strip()) if ":" in l else 0
        return res
    

class UbuntuCmd(RemoteConnect,BuildReport):

    def _sendcmd(self,cmd):
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        #print stdout.readlines()
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' \
                    % stdout.channel.recv_exit_status()
            sys.exit()
        return stdout.readlines()

    def ipmi_sensor(self):
        self.modprobe_ipmi()
        stdout = self._sendcmd('ipmitool sensor')
        return self.sensor_rep(stdout)

    def ipmi_fru(self):
        self.modprobe_ipmi()
        stdout = self._sendcmd('ipmitool fru')
        return self.fru_rep(stdout)

    def smart(self,dev):
        stdout = self._sendcmd('python smart /dev/'+ dev)
        return stdout

    def modprobe_ipmi(self):
        stdout = self._sendcmd('modprobe ipmi_msghandler')
        stdout = self._sendcmd('modprobe ipmi_devintf')
        stdout = self._sendcmd('modprobe ipmi_si')
        return True

    def lshw_xml(self,dest="/tmp"):
        stdout = self._sendcmd('lshw -xml > /tmp/lshw.xml')
        return self.sftp_sess.get('/tmp/lshw.xml', dest+"/lshw.xml")

    def cp_file(self, filename, dest="/tmp"):
        res =  self.sftp_get(filename, dest+"/"+filename.split("/tmp/")[1])
        if res:
            #stdin, stdout, stderr = self.sess.exec_command('rm '+ filename)
            stdout = self._sendcmd('rm '+ filename)
        else:
            print 'Copy file failed'
            sys.exit()
        return None

    def memtest(self,size,loop, dest="/tmp"):
        print "Starting Memory Tests..."
        cmd = 'memtester ' + size + ' ' + loop + ' > /tmp/memtester.out &'
        print cmd
        stdout = self._sendcmd(cmd)
        return None

    def mt_progress(self):
        cmd = 'ps -aef | grep \"memtester\" | grep -v \"grep\" | wc -l'
        val = []
        """
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        """
        stdout = self._sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0])>0 else False 
        return status

    def chk_process(self,cmd):
        cmd = 'ps -aef | grep \"' + cmd +'\" | grep -v \"grep\" | wc -l'
        val = []
        stdout = self._sendcmd(cmd)
        """
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        """
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0])>0 else False 
        return status

    def ethtest(self, *params):
        cmd = 'ethtool -s ' + params[0] + " speed " + params[1] + " duplex " + params[2] 
        stdout = self._sendcmd(cmd)
        time.sleep(60)
        cmd = "ethtool " + params[0]
        stdout = self._sendcmd(cmd)
        return self.ethtest_rep(stdout) 

    def sendcmd(self,cmd):
        stdin, stdout, stderr = self.sess.exec_command(cmd + ' &')
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        return self.chk_process(cmd)
        
    def eth_up(self,intf):
        cmd = "ifconfig " + intf + " up"
        stdout = self._sendcmd(cmd)
        return True 
        
    def get_intfname(self,ethid=[4,5]):
        regex = re.compile(r'\d\:\s(.+)\:')
        stdout = self._sendcmd('ip link')
        ethname = []
        for line in stdout:
            for eid in ethid:
                if line.startswith(str(eid)):
                    ethname.append(regex.match(line).group(1))
        return ethname
     
    def bb_progress(self, drv):
        cmd = 'ps -aef | grep \"badblocks /dev/sd['+drv+']\"| grep -v \"grep\" | wc -l'
        val = []
        stdout = self._sendcmd(cmd)
        
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0]) > 0 else False 
        return status
    
    def bb_start(self, dev, write=False):
        print "Starting badblocks test..."
        #cmd = 'badblocks -o > /tmp/' + dev.strip("\dev\\")+ ".out" + " " + dev + " &"
        print dev
        if not write:
            cmd = 'badblocks ' + dev + " -o /tmp/" + dev.split("/dev/")[1]+ ".out &"
        else:
            cmd = 'badblocks -w -t 0x55 ' + dev + " -o /tmp/" + dev.split("/dev/")[1]+ ".out &"
        print cmd
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        return None
   
    def bb_progress_rssd(self, drv):
        cmd = 'ps -aef | grep \"badblocks /dev/rssd['+drv+']\"| grep -v \"grep\" | wc -l'
        val = []
        stdout = self._sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0]) > 0 else False
        return status

    def bb_progress_nvme(self, drv, write=False):
        if not write:
            cmd = 'ps -aef | grep \"badblocks /dev/nvme['+drv+']\"| grep -v \"grep\" | wc -l'
        else:
            cmd = 'ps -aef | grep \"badblocks -w -t 0x55 /dev/nvme['+drv+']\"| grep -v \"grep\" | wc -l'
        val = []
        stdout = self._sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0]) > 0 else False
        return status

    def list_storage(self, drv_list):
        stdout = self._sendcmd("lsblk -d")
        return self.storage_rep(stdout, drv_list)

    def rec_per_dev(self, drv_list, dest="/tmp"):
        drive_pres = []
        (res, miss_drv, status) = self.list_storage(drv_list)
        [drive_pres.append(key) for key in res.keys()]
        drive_pres.sort(reverse=True)
        if len(drive_pres) == 8: 
            return self.per_dev_rep(dest, drive_pres[:6])
        else: 
            return self.per_dev_rep(dest, drive_pres)

    def rec_per_dev_pcie(self, drv_list, dest="/tmp"):
        drive_pres = []
        (res, miss_drv, status) = self.list_storage(drv_list)
        [drive_pres.append(key) for key in res.keys()]
        drive_pres.sort(reverse=True)
        nvme = [i for i in drive_pres if i.startswith('nvm')]
        if len(drive_pres) == 8:
           #print "Inside nvme"
            return self.per_dev_rep_nvme(dest, nvme)
        else:
           #print "NVME drives not present"
            return self.per_dev_rep(dest, drive_pres)

    def rec_per_dev_vendor(self, drv_list, dest="/tmp", vendor=None):
        drive_pres = []
        (res, miss_drv, status) = self.list_storage(drv_list)
        [drive_pres.append(key) for key in res.keys()]
        drive_pres.sort(reverse=True)
        if vendor == 'micron':
            return self.per_dev_rep_vendor(dest, drive_pres[6:], vendor)
        else:
            return self.per_dev_rep_vendor(dest, drive_pres[6:])

    def rec_isdct(self,drv_list,logid,dest="/tmp"):
        drive_pres = []
        (res, miss_drv, status) = self.list_storage(drv_list)
        [drive_pres.append(key) for key in res.keys()]
        drive_pres.sort()
        drive_pres = drive_pres[6:]
        for elem in drive_pres:
            if drive_pres.index(elem) <= 3:
                drive_pres[drive_pres.index(elem)] = \
                        "dev-0-drv-"+str(drive_pres.index(elem))
            else:
                drive_pres[drive_pres.index(elem)] = \
                        "dev-1-drv-"+str(drive_pres.index(elem)-4)
        print drive_pres
        return self.isdct_rep(drive_pres, logid, dest)

    def dpkg_present(self,pkgname):
        cmd = "dpkg --get-selections | grep " + pkgname + " | wc -l" 
        val = []
        stdout = self._sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0]) == 1 else False 
        return status
        
    def file_present(self,filename):
        """ file name must me with path """
        cmd = "ls -l " + filename + " | wc -l" 
        val = []
        stdout = self._sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0]) == 1 else False 
        return status

    def file_size(self,filename):
        """ file name must me with path """
        cmd = "du -s " + filename
        val = []
        stdout = self._sendcmd(cmd)
        [str(val.append(v.split("\t")[0].strip())) for v in stdout]
        status=True if int(val[0]) == 0 else False
        return status

    def echo_cmd(self):
        cmd = "echo $?" 
        val = []
        stdout = self._sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0]) == 0 else False 
        return status
        
    def update_fru(self, name, info):
        fru_map = {"CT":"Chassis Type", "CS":"Chassis Serial", \
                "BMD":"Board Mfg Date", "BM": "Board Mfg", \
                "BP":"Board Product","BS":"Board Serial", \
                "PM":"Product Manufacturer","PN":"Product Name", \
                "PS":"Product Serial"}
        cmd = "/root/driver/ipmi_cfg/ipmicfg-linux.x86_64 -fru " + name + ' "' + info + '"'
        stdout = self._sendcmd(cmd)
        time.sleep(5)
        res = self.ipmi_fru()
        try:
            if res[fru_map[name]] == info:
                return True
            else:
                return False
        except Exception, e:
            print 'Caught exception: %s: %s' %(e.__class__, e)
            return False


    def update_10g_mac(self, mac, port):
        mac = ''.join((j)for j in mac.split(':'))
        cmd = "/root/driver/OEM_Mfg/eeupdate64e \"/MAC=" + mac +"\" " + "\"/NIC="+ str(port) +"\""
        stdout = self._sendcmd(cmd)
        time.sleep(5)
        self.reset_10g_port(port)
        return self.read_10g_mac(port,mac)

    def reset_10g_port(self, port):
        cmd = "/root/driver/OEM_Mfg/eeupdate64e \"/ADAPTERRESET\" \"/NIC="+ str(port) +"\""
        print cmd
        stdout = self._sendcmd(cmd)
        time.sleep(5)
        return True

    def read_10g_mac(self, port, in_mac=None):
        cmd = "/root/driver/OEM_Mfg/eeupdate64e \"/MAC_DUMP\" \"/NIC="+ str(port) +"\""
        print cmd
        exp = re.compile('\s+(\d)\:(.*?)\s+([a-fA-F0-9]{12})')
        stdout = self._sendcmd(cmd)
        for line in stdout:
            if exp.match(line):
                if exp.match(line).group(1).strip()== port:
                    mac = (str(exp.match(line).group(3).strip())).lower()
                    #mac = ':'.join([mac[i:i+2] for i in range(0, len(mac)-1, 2)])
                    break
        in_mac.lower() if in_mac != None else in_mac
        return (True, mac) if mac == in_mac else (False,mac)

    def update_ipmi_mac(self, mac):
        cmd = "/root/driver/ipmi_cfg/ipmicfg-linux.x86_64 -a " + mac
        stdout = self._sendcmd(cmd)
        time.sleep(5)
        return self.read_ipmi_mac(mac)

    def read_ipmi_mac(self, mac='None'):
        cmd = "/root/driver/ipmi_cfg/ipmicfg-linux.x86_64 -m "
        stdout = self._sendcmd(cmd)
        res = {str(v.split("=")[0].strip()):str(v.split("=")[1].strip()) for v in stdout}
        return (True, res['MAC']) if res['MAC'].lower() == mac.lower() else (False,res['MAC'])

    def set_fan_mode(self, mode):
        cmd = "/root/driver/ipmi_cfg/ipmicfg-linux.x86_64 -fan " + mode
        stdout = self._sendcmd(cmd)
        time.sleep(5)
        return self.ipmi_sensor()

    def dpkg_install(self, pkgname):
        cmd = "dpkg -i "+ pkgname 
        stdout = self._sendcmd(cmd)
        stdout = self._sendcmd("apt-get install -f -y")
        return None

    def micron_install(self, pkg):
        stdin, stdout, stderr = self.sess.exec_command('rssdma -V')
        if stdout.channel.recv_exit_status() !=0:
            stdin, stdout, stderr = self.sess.exec_command(pkg)
            buf = stdout.channel.recv(1000)
            stdin.write('\n')
            buf = stdout.channel.recv(10000)
            stdin.write('Y\n')
            buf = stdout.channel.recv(10000)
            stdin.write('Y\n')
            buf = stdout.channel.recv(10000)
            stdin.write('Y\n')
            buf = stdout.channel.recv(10000)
            stdin.write('Y\n')
            buf = stdout.channel.recv(10000)
            stdin.write('n\n')
            buf = stdout.channel.recv(10000)
        return True

    def micron_fw_upgrade(self, fw_file, dev_id):
        cmd = 'rssdm -T ' + fw_file + ' -n ' + str(dev_id)
        stdin, stdout, stderr = self.sess.exec_command(cmd+'\n')
        stdin.write('Y\n')
        stdin.flush()
        buf = stdout.read()
        if "completed successfully" in buf:
            return True
        else:
            return False

    def apt_get(self,pkgname,stat="install"):
	if pkgname.strip() == 'mdadm':
            cmd = "DEBIAN_FRONTEND=noninteractive apt-get " + stat + " -y " + pkgname
	else:
            cmd = "apt-get " + stat + " -y " + pkgname
        print cmd
        stdout = self._sendcmd(cmd)
        status = self.dpkg_present(pkgname)
        if not status:
            print "Package %s installation FAILED.\nContact Engineer" %pkgname 
            sys.exit()
        else:
            pass
        return status

    def driver_install(self,pkgname):
        cmd = "tar -xmvf " + pkgname
        stdout = self._sendcmd(cmd)
        time.sleep(2)
        cmd = "chmod +x /root/driver/ipmi_cfg/ipmicfg-linux.x86_64"
        stdout = self._sendcmd(cmd)
        cmd = "chmod +x /root/driver/OEM_Mfg/install"
        stdout = self._sendcmd(cmd)
        cmd = "cd /root/driver/OEM_Mfg;/root/driver/OEM_Mfg/install"
        stdout = self._sendcmd(cmd)
        cmd = "chmod +x /root/driver/OEM_Mfg/eeupdate64e"
        stdout = self._sendcmd(cmd)
        return None 
    
    def chmod(self, filename):
        stdout = self._sendcmd("chmod +x " + filename)
        return None

    def fio_test(self,cfg,*dev):
        stdout = self._sendcmd('fio '+cfg+'.fio')
        return self.fio_test_rep(stdout, cfg, dev)

    def mdadm_stop(self,dev):
        """ Manage MD arrays """
        cmd = "mdadm --stop " + dev
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        return stdout.channel.recv_exit_status()

    def md0_create(self):
        """ Manage MD arrays """
        cmd = "mdadm -C -c 16 -l 0 -n 4 /dev/md0 /dev/sd[ghij] -R"
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        return stdout.channel.recv_exit_status()


    def dpkg_install(self,pkgname):
        cmd = "dpkg -i "+ pkgname 
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() !=0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        stdin, stdout, stderr = self.sess.exec_command("apt-get install -f -y")
        return None

    def md1_create(self):
        """ Manage MD arrays """
        cmd = "mdadm -C -c 16 -l 0 -n 4 /dev/md1 /dev/sd[klmn] -R"
        print cmd
        stdin, stdout, stderr = self.sess.exec_command(cmd)
        if stdout.channel.recv_exit_status() != 0:
            print 'Command returns error code: %s' % stdout.channel.recv_exit_status()
            sys.exit()
        return stdout.channel.recv_exit_status()

    def proc_mdstat(self):
        """ Check /proc/mdstat """
        cmd = "cat /proc/mdstat"
        print cmd
        stdout = self._sendcmd(cmd)
        return stdout 

    def sftp_put(self, src, dest):
        """
        src-full path of source file from the scp originated server
        to destination server
        Ex: /home/user/sample.py to /tmp/sample.py
        """
        self.sftp_sess.put(src, dest)
        cmd = "ls -l " + dest + " | wc -l" 
        val = []
        stdout = self._sendcmd(cmd)
        [str(val.append(v.strip())) for v in stdout]
        status=True if int(val[0]) == 1 else False
        return status

    def sftp_get(self, src, dest):
        self.sftp_sess.get(src, dest)
        cmd = "ls -l " + dest + " | wc -l" 
        out = os.popen(cmd)
        val = out.readline().strip()
        status=True if int(val) == 1 else False
        return status

def get_ssh(ip):
    try:
        conn = paramiko.SSHClient()
        conn.load_system_host_keys()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _conn = conn.connect(ip, 22, 'root', 'myrootpwd')
    except Exception, e:
        print 'Caught exception: %s: %s' %(e.__class__, e)
        conn.close()
        sys.exit()
    return conn 

def get_sftp(ip):
    try:
        trans = paramiko.Transport((ip,22))
        trans.connect(username='root', password='myrootpwd')
        conn = paramiko.SFTPClient
        _conn = conn.from_transport(trans)
    except Exception, e:
        print 'Caught exception: %s: %s' %(e.__class__, e)
        sys.exit()
    return _conn 


def get_telnet(dev):
    return NotImplemented

def init_sess(dev):
    dev,ip = dev.split(':')
    if dev == "ssh":
        _sess = get_ssh(ip)
        _sftp_sess = get_sftp(ip)
    elif dev == "telnet":
        pass
    else:
        raise ValueError, "IP or connection configuration is not correct"

    return _sess, _sftp_sess

def init_sftp_sess(dev):
    dev,ip = dev.split(':')
    try:
        _sftp_sess = get_sftp(ip)
    except:
        raise ValueError, "IP or connection configuration is not correct"
    return _sftp_sess

if __name__ == "__main__":
    """ Self test the program """
    init = UbuntuCmd('ssh:192.168.32.105')
    init.ipmi_sensor() 
    init.ipmi_fru() 
    init.dpkg_present("libib")
    libs = ['libaio1', 'libibverbs1', 'librdmacm1', 'mdadm']
    for lib in libs:
        init.apt_get(lib)
    init.lshw_xml('/tmp')

