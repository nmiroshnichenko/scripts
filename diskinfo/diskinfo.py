_PARTITIONS_FILE_NAME = '/proc/partitions'


class DiskInfo:


    def get_disk_info(self):
        f = open(_PARTITIONS_FILE_NAME)
        return f.read()

if __name__ == '__main__':
    print DiskInfo().get_disk_info()
