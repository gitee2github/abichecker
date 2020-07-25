import os
import shutil
import traceback
import re
import sys
from disutils.version import LooseVersion

def move_file(src_path, dst_path, file):
    f_src = os.path.join(src_path, file)
    if not os.path.exists(dst_path):
        os.mkdir(dst_path)
    f_dst = os.path.join(dst_path, file)
    shutil.move(f_src, f_dst)


class Package:
    def __init__(self, file_name):
        package_arch = file_name.split('.')[-2]
        package_name_version = re.sub(package_arch + '.rpm', '', file_name)
        package_version = re.findall('-\d+.*$', package_name_version)[0]
        package_name = re.sub(package_verison, '', package_name_version)
        package_version = re.sub('^-', '', package_version)
        package_version = re.sub('\.+$', '', package_version)
        self.file_name = file_name
        self.name = package_name
        self.version = package_version
        self.arch = package_arch
        if self.name.endswith('libs'):
            self.type = 'libs'
        elif self.name.endswith('devel'):
            self.type = 'devel'
        elif self.name.endswith('debuginfo'):
            self.type='debuginfo'
        else:
            self.type='main'

    def __str__(self):
        return 'Name: ' + self.name + ', Version: ' + self.version +\
               ', Arch: ' + self.arch


def get_version_num(packages):
    version_num = []
    for package in packages:
        if package.version not in version_num:
            version_num.append(package.version)
    return version_num


def get_sofile_name(sofilename):
    return  re.findall('.*.so', sofilename)[0]


def get_rpms(pkg, filepath):
    files = os.listdir(filepath)
    rpms = []
    for file in files:
        if file.endswith('.rpm') and file.startswith(pkg):
            rpms.append(file)
    return rpms


def check_valid_rpmnum(packages):
    type_num = {}
    for package in packages:
        if package.type in type_num.keys():
            type_num[package.type] += 1
        else:
            type_num[package.type] = 1
    if type_num['main'] == 2 or 'libs' in type_num.keys() and type_num['libs'] == 2:
        return True
    else:
        print('The valid number of main rpmfiles and lib rpmfiles should be 2+2 or 0+2 or 2+0')
        return False



def check_valid_version(packages):
    version_num = get_version_num(packages)
    if len(version_num) != 2:
        print('The version to be checked is not 2.')
        return False
    else:
        return True


def rpm_uncompress(packages, common_dir):
    version_num = get_version_num(packages)
    if LooseVersion(version_num[0]) > LooseVersion(version_num[1]):
        version_num[0], version_num[1] = version_num[1],version_num[0]
    os.chdir(common_dir)
    for version in version_num:
        if not os.path.exists(version):
            os.mkdir(version)
    for package in packages:
        os.chdir(common_dir)
        move_file(common_dir, common_dir + '/' + package.version, package.file_name)
        os.chdir(package.version)
        os.system('rpm2cpio ' + package.file_name + ' | cpio -div')


def dumper_by_debuginfo(verdir):
    os.chdir(verdir)
    sofiles = []
    for root, dirs, files in os.walk(verdir):
        for file in files:
            full_file = os.path.join(root, file)
            if re.match('.*\.so.*', full_file) and not os.path.islink(full_file):
                sofiles.append(full_file)
    res = []
    if len(sofiles) > 0:
        for sofile in sofiles:
            (sofile_path, sofile_name) = os.path.split(sofile)
            sofile_name = get_sofile_name(sofile_name)
            if os.system('abi-dumper ' + sofile + ' --search-debuginfo='
                         + verdir + '/usr/lib/debug/'
                         + ' -o ' + 'ABI-' + sofile_name + '.dump') == 0:
                res.append(sofile_name)
    return res
def do_abi_compliance_check(common_dir, old_dumpi, new_dumpi, old_version, new_version):
    os.system('abi-compliance-checker -l ' + old_dumpi +
              ' -old ' + common_dir + '/' + old_version + '/' + 'ABI-' + old_dumpi + '.dump'
              ' -new ' + common_dir + '/' + new_version + '/' + 'ABI-' + new_dumpi + '.dump')


def abi_compliance_check(common_dir, dumps, verdirs):
    old_dump = dumps[0]
    new_dump = dumps[1]
    if len(old_dump) == 0:
        print('Error: Did not find .so file in old_version')
        return
    if len(new_dump)==0:
        print('Error: Did not find .so file in new_version')
        return
    os.chdir(common_dir)
    if len(old_dump) == len(new_dump):
        for i in range(len(old_dump)):
            do_abi_compliance_check(common_dir, old_dump[i], new_dump[i], verdirs[0], verdirs[1])
    elif len(old_dump) < len(new_dump):
        print('Warning: old_version has less .so files, try checking these .so files.')
        for i in range(len(old_dump)):
            if old_dump[i] in new_dump:
                do_abi_compliance_check(common_dir, old_dump[i], old_dump[i], verdirs[0], verdirs[1])
    else:
        print('Warning: new_version has less .so files, try checking these .so files.')
        for i in range(len(new_dump)):
            if new_dump[i] in new_dump:
                do_abi_compliance_check(common_dir, new_dump[i], new_dump[i], verdirs[0], verdirs[1])


if __name__ == 'main':
    pkg = sys.argv[1]
    analyze_type = 'debuginfo'
    common_dir = '/root/checkdir/' + pkg
    rpms = get_rpms(pkg, common_dir)
    packages = []
    for rpm in rpms:
        packages.append(Package(rpm))
    if check_valid_rpmnum(packages) and check_valid_version(packages):
        rpm_uncompress(packages, common_dir)
        dumps = []
        verdirs = get_version_num(packages)
        for verdir in verdirs:
            dumps.append(dumper_by_debuginfo(common_dir + '/' + verdir))
        abi_compliance_check(common_dir, dumps, verdirs)
