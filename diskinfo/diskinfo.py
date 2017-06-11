#!/usr/bin/env python

import sys

_LINUX_PARTITIONS_FILE_NAME = '/proc/partitions'
_LINUX_PARTITION_SIZE_MULTIPLIER = 1024
_LINUX_DISK_TYPE_NUMBERS = (3, 8)


class DiskInfo(object):
    def get_disk_full_list(self):
        raise NotImplementedError("Should be called in subclasses")


class DiskInfoLinux(DiskInfo):
    def get_disk_full_list(self):
        return self._get_linux_disk_list()

    @staticmethod
    def _get_linux_disk_list():
        disk_list = []
        with open(_LINUX_PARTITIONS_FILE_NAME) as file:
            # omit header and empty line
            lines_total = file.readlines()[2:]
            hard_disk_number = 0
            partition_number = 0
            current_hard_disk = None
            for line in lines_total:
                # fields: major minor  #blocks  name
                fields = line.split()
                major = int(fields[0])
                if major not in _LINUX_DISK_TYPE_NUMBERS:
                    continue
                size = int(fields[2]) * _LINUX_PARTITION_SIZE_MULTIPLIER
                is_partition = fields[3][-1].isdigit()
                if is_partition:
                    partition_number += 1
                    disk = Disk(partition_number, size, current_hard_disk)
                else:
                    partition_number = 0
                    hard_disk_number += 1
                    disk = Disk(hard_disk_number, size, None)
                    current_hard_disk = disk
                disk_list.append(disk)
        return disk_list


class DiskInfoWindows(DiskInfo):
    def get_disk_full_list(self):
        return self._get_windows_disk_list()

    @staticmethod
    def _get_windows_disk_list():
        disk_list = []
        try:
            import win32com.client
        except ImportError:
            print 'ERROR: you should install lib: pip install pypiwin32'
            sys.exit(66)

        strComputer = '.'
        objWMIService = win32com.client.Dispatch('WbemScripting.SWbemLocator')
        objSWbemServices = objWMIService.ConnectServer(strComputer,'root\cimv2')
        colItems = objSWbemServices.ExecQuery('Select * from Win32_DiskDrive')
        hd_list = []
        for objItem in colItems:
            hd_list.append((objItem.DeviceID, objItem.Size))
        hd_list.sort()

        hard_disk_number = 0
        current_hard_disk = None
        for hd in hd_list:
            partition_number = 0
            hard_disk_number += 1
            disk = Disk(hard_disk_number, hd[1], None)
            current_hard_disk = disk
            disk_list.append(disk)
            colItems = objSWbemServices.ExecQuery(
                'Select * from Win32_DiskPartition where DiskIndex={}'.format(hard_disk_number - 1))
            for objItem in colItems:
                partition_number += 1
                disk = Disk(partition_number, objItem.Size, current_hard_disk)
                disk_list.append(disk)
        return disk_list


class Disk(object):
    def __init__(self, number, size, parent=None):
        self.number = int(number)

        self.size = int(size)
        '''size in bytes'''

        self.parent = parent
        '''None for hard disk or parent hard disk for partition'''

    def __repr__(self):
        return {self.number: self.size}.__str__()


def get_disk_full_list():
    platform = sys.platform
    if platform.lower().startswith('linux'):
        return DiskInfoLinux().get_disk_full_list()
    elif platform.lower().startswith('win'):
        return DiskInfoWindows().get_disk_full_list()
    else:
        print 'ERROR: unsupported platform: {}'.format(platform)
        sys.exit(65)


def print_disk_list(disk_list):
    print '\n'.join([str(e) for e in disk_list])


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Print disk info')
    parser.add_argument('hard_disk_number', type=int, nargs='?', help='hard disk number')

    args = parser.parse_args()
    hd_number = args.hard_disk_number
    if hd_number is not None and hd_number < 1:
        parser.error('invalid disk number: {}'.format(hd_number))

    disk_full_list = get_disk_full_list()
    hard_disk_list = [e for e in disk_full_list if e.parent is None]
    result_list = []
    if args.hard_disk_number is None:
        result_list.extend(hard_disk_list)
    else:
        if hd_number not in [e.number for e in hard_disk_list]:
            parser.error('no such disk: {}'.format(hd_number))
        result_list.extend(
            [e for e in disk_full_list if e.parent is not None and e.parent.number == hd_number])
    print_disk_list(result_list)


if __name__ == '__main__':
    main()
