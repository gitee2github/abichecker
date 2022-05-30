#!/usr/bin/python3
"""
# **********************************************************************************
# Copyright (c) [Year] [name of copyright holder]
# [Software Name] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# Author:
# Create: 2020-08-03
# Description: abichecker tool
# **********************************************************************************
"""
import os
import shutil
import re
import sys
import distutils.version

def move_file(src_path, dst_path, infile):
    """
    move infile from src_path to dst_path
    """
    f_src = os.path.join(src_path, infile)
    if not os.path.exists(dst_path):
        os.mkdir(dst_path)
    f_dst = os.path.join(dst_path, infile)
    shutil.move(f_src, f_dst)


class Package(object):
    """
    rpm package
    """
    def __init__(self, file_name):
        """
        init function
        """
        package_arch = file_name.split('.')[-2]
        package_name_version = re.sub(package_arch + '.rpm', '', file_name)
        package_version = re.findall(r'-\d+.*$', package_name_version)[0]
        package_name = re.sub(package_version, '', package_name_version)
        package_version = re.sub(r'^-', '', package_version)
        package_version = re.sub(r'\.+$', '', package_version)
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
        """
        string of Package
        """
        return 'Name: ' + self.name + ', Version: ' + self.version +\
               ', Arch: ' + self.arch


def get_version_num(packages):
    """
    get the version of given packages
    """
    version_num = []
    for package in packages:
        if package.version not in version_num:
            version_num.append(package.version)
    return version_num


def get_sofile_name(sofilename):
    """
    get the .so file name
    ie: foo.so.0.0 -> foo.so
    """
    return  re.findall(r'.*.so', sofilename)[0]


def get_rpms(pkg, filepath):
    """
    get .rpm files starts with pkg in the given filepath
    """
    files = os.listdir(filepath)
    rpms = []
    for eachfile in files:
        if eachfile.endswith('.rpm') and eachfile.startswith(pkg):
            rpms.append(eachfile)
    return rpms


def check_valid_rpmnum(packages):
    """
    check if the number of .rpm files is valid
    """
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
    """
    check if the package version is valid
    """
    version_num = get_version_num(packages)
    if len(version_num) != 2:
        print('The version to be checked is not 2.')
        return False
    else:
        return True


def rpm_uncompress(packages, common_dir):
    """
    uncompress the rpm packages in common_dir
    """
    version_num = get_version_num(packages)
    if distutils.version.LooseVersion(version_num[0]) > distutils.version.LooseVersion(version_num[1]):
        version_num[0], version_num[1] = version_num[1], version_num[0]
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
    """
    generate .dump file by debuginfo .rpm file
    """
    os.chdir(verdir)
    sofiles = []
    for root, dirs, files in os.walk(verdir):
        for eachfile in files:
            full_file = os.path.join(root, eachfile)
            if re.match(r'.*\.so.*', full_file) and not os.path.islink(full_file):
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
    """
    abi compliance check
    """
    os.system('abi-compliance-checker -l ' + old_dumpi +
              ' -old ' + common_dir + '/' + old_version + '/' + 'ABI-' + old_dumpi + '.dump'
              ' -new ' + common_dir + '/' + new_version + '/' + 'ABI-' + new_dumpi + '.dump')


def abi_compliance_check(common_dir, dumps, verdirs):
    """
    check the compatibility by given .dump files in common_dir + verdirs
    """
    old_dump = dumps[0]
    new_dump = dumps[1]
    if len(old_dump) == 0:
        print('Error: Did not find .so file in old_version')
        return
    if len(new_dump) == 0:
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


def main_function(pkg, common_dir):
    """
    main_function
    """
    analyze_type = 'debuginfo'
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


if __name__ == '__main__':
    """
    main
    1. create a directory named sys.argv[1] (libfoo) in sys.argv[2] (/root/checkdir/);
    2. put the rpm files and debuginfo files of 2 versions in libfoo;
    3. run 'python abichecker.py 'libfoo' '/root/checkdir/'
    4. the results are saved in /root/checkdir/libfoo/compat_reports
    """
    main_function(sys.argv[1], sys.argv[2] + sys.argv[1])
