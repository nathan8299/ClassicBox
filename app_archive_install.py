#!/usr/bin/env python

"""
Automatically installs an app from an archive file.

Syntax:
    app_archive_install.py <box directory> <archive file>
"""

from classicbox.disk import is_disk_image
from collections import namedtuple
import os
import os.path
import re
import subprocess
import shutil
import sys
import tempfile


RECOGNIZED_INSTALLER_APP_CREATORS = [
    'STi0',         # Stuffit InstallerMaker
    # TODO: What about InstallerVISE?
]

DEVNULL = open(os.devnull, 'wb')


def main(args):
    # Parse arguments
    (box_dirpath, archive_filepath) = args
    
    # Extract the archive
    contents_dirpath = extract_archive_to_temporary_directory(archive_filepath)
    try:
        # TODO: Probably will need to be smarter here for archives
        #       that expand with a single directory at the root
        
        # Locate disk images in archive, if any
        disk_image_filepaths = []
        for filename in os.listdir(contents_dirpath):
            if is_disk_image(filename):
                disk_image_filepaths.append(os.path.join(contents_dirpath, filename))
        
        # Identify the primary disk image
        if len(disk_image_filepaths) == 0:
            # TODO: ...
            raise NotImplementedError('Did not find any disk images in archive. Not sure what to do.')
            
        elif len(disk_image_filepaths) == 1:
            primary_disk_image_filepath = disk_image_filepaths[0]
            
        elif len(disk_image_filepaths) >= 2:
            # TODO: Probably want to ask the user to select one of the disk
            #       images as the primary disk image.
            raise NotImplementedError('Found multiple disk images in archive. Not sure what to do.')
        
        # Open the primary disk image
        subprocess.check_call(
            ['hmount', primary_disk_image_filepath],
            stdout=DEVNULL, stderr=DEVNULL)
        
        # List the root items
        hdir_lines = subprocess.check_output(['hdir']).split('\n')[:-1]
        root_items = [parse_hdir_line(line) for line in hdir_lines]
        
        # Look for installer apps
        installer_app_items = []
        for item in root_items:
            if item.type == 'APPL' and item.creator in RECOGNIZED_INSTALLER_APP_CREATORS:
                installer_app_items.append(item)
        
        # Identify the primary installer app
        if len(installer_app_items) == 0:
            # TODO: Continue looking for the designated app...
            raise NotImplementedError('Did not find any installer applications. Not sure what to do.')
            
        elif len(installer_app_items) == 1:
            primary_installer_app_item = installer_app_items[0]
            
        elif len(installer_app_items) >= 2:
            # TODO: Extract to method
            print 'Found multiple installer applications.'
            while True:
                print
                print 'Please choose the primary installer for this program:'
                i = 1
                for item in installer_app_items:
                    print '    %d: %s' % (i, item.name); i += 1
                print '    %d: <Cancel>' % i; i += 1
                try:
                    choice = int(raw_input('Choice? '))
                    if choice >= i:
                        raise ValueError
                    if choice == (i - 1):
                        # Cancel
                        return
                    else:
                        primary_installer_app_item = installer_app_items[choice - 1]
                        break
                except ValueError:
                    print 'Not a valid choice.'
                    continue
            
        
        # Temporarily mount the disk images inside the VM
        with mount_disk_images_temporarily(box_dirpath, disk_image_filepaths):
            
            # Set the installer app as the boot app
            set_boot_app_of_box(box_dirpath, primary_disk_image_filepath, [primary_installer_app_item.name])
            
            # Boot the box and wait for the user to install the app
            run_box(box_dirpath)
            
            # FIXME: ...
            # Look for the installed app and set it as the boot app
            raise NotImplementedError
        
    finally:
        shutil.rmtree(contents_dirpath)
    
    pass


# TODO: Merge this code with that in box_bootstrap.py
def extract_archive_to_temporary_directory(archive_filepath):
    extraction_dirpath = tempfile.mkdtemp()
    try:
        subprocess.check_call([
            'unar',
            # recursively extract inner archives by default
            '-forks', 'fork',   # save resource forks natively (OS X only)
            '-no-quarantine',   # don't display warnings upon launch of extracted apps
            '-no-directory',    # don't create an extra enclosing directory
            '-output-directory', extraction_dirpath,
            archive_filepath
        ], stdout=DEVNULL, stderr=DEVNULL)
        
        return extraction_dirpath
    except:
        shutil.rmtree(extraction_dirpath)
        raise


def is_disk_image(filename):
    for ext in DISK_IMAGE_EXTENSIONS:
        if filename.endswith(ext):
            return True
    return False


HFSItem = namedtuple('HFSItem', 'name, is_file, type, creator, data_size, rsrc_size, date_modified')

FILE_LINE_RE = re.compile(r'f  (....)/(....) +([0-9]+) +([0-9]+) ([^ ]...........) (.+)')
DIR_LINE_RE = re.compile(r'd +([0-9]+) items? +([^ ]...........) (.+)')

# TODO: Merge with original copy in catalog_create.py
def parse_hdir_line(line):
    """
    Arguments:
    * line -- A line from the `hdir` command.
    
    Returns:
    * an HFSItem
    """
    file_matcher = FILE_LINE_RE.match(line)
    if file_matcher is not None:
        (type, creator, data_size, rsrc_size, date_modified, name) = file_matcher.groups()
        return HFSItem(name, True, type, creator, data_size, rsrc_size, date_modified)
    
    dir_matcher = DIR_LINE_RE.match(line)
    if dir_matcher is not None:
        (num_children, date_modified, name) = dir_matcher.groups()
        return HFSItem(name, False, '    ', '    ', 0, 0, date_modified)
    
    raise ValueError('Unable to parse hdir output line: %s' % line)


def mount_disk_images_temporarily(box_dirpath, disk_image_filepaths):
    raise NotImplementedError


def set_boot_app_of_box(box_dirpath, disk_image_filepath, app_filepath_components):
    install_autoquit_in_box(box_dirpath)
    set_autoquit_app(box_dirpath, disk_image_filepath, app_filepath_components)


def install_autoquit_in_box(box_dirpath):
    raise NotImplementedError


def set_autoquit_app(box_dirpath, disk_image_filepath, app_filepath_components):
    (boot_disk_image_filepath, autoquit_filepath_components) = locate_autoquit_in_box(box_dirpath)
    
    create_alias(
        boot_disk_image_filepath, autoquit_filepath_components + ['app'],
        disk_image_filepath, app_filepath_components)


def locate_autoquit_in_box(box_dirpath):
    raise NotImplementedError


def create_alias(
        source_disk_image, source_filepath_components,
        target_disk_image, target_filepath_components):
    # FIXME: How do I create an alias? What is the format?
    raise NotImplementedError


def run_box(box_dirpath):
    raise NotImplementedError


if __name__ == '__main__':
    main(sys.argv[1:])