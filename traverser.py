#!/usr/bin/env python3

import os
import sys
import re
import math

def get_entropy(filename):
    """ Code from internet """
    with open(filename, "rb") as file:
        counters = {byte: 0 for byte in range(2 ** 8)}  # start all counters with zeros
        for byte in file.read():  # read in chunks for large files
            counters[byte] += 1  # increase counter for specified byte
        filesize = file.tell()  # we can get file size by reading current position
        probabilities = [counter / filesize for counter in counters.values()]  # calculate probabilities for each byte
        entropy = -sum(probability * math.log2(probability) for probability in probabilities if probability > 0)  # final sum
        return entropy


class FileEntry(object):
    """
    Meta data on actual file
    """

    def __init__(self, path, snap_index):
        self._path = path
        self._snap_index = snap_index
        self._entropy = None

    @property
    def snap_index(self):
        return self._snap_index

    @property
    def path(self):
        return self._path

    def __str__(self):
        return self.path

    def __repr_(self):
        return self.path

    @property
    def entropy(self):
        if self._entropy is None:
            self._entropy = get_entropy(self._path)
        return self._entropy

    def get_first_bytes(self, amount):
        with open(self.path, 'rb') as f:
            if -1 == amount:
                return f.read()
            else:
                return f.read(amount)

HIGH_ENTROPY_EXTENSIONS = ['7z', 'rar', 'jpg', 'png', 'pdf', 'mobi']

class SnapFile(object):
    '''
    Contains filename, and list of paths in all snapshots
    Contains dict of validator names, mapped to their results
    '''
    def __init__(self, name, snap_count=10):
        self._name = name
        self._snap_paths = [None for i in range(snap_count)]
        self._validators_results = dict()

    @property
    def name(self):
        return self._name

    @property
    def snap_paths(self):
        return self._snap_paths

    @property
    def validators_results(self):
        return self._validators_results

    @property
    def file_extension(self):
        return self.name.split('.')[-1]

    def is_high_entropy_extension(self):
        return self.file_extension in HIGH_ENTROPY_EXTENSIONS

    def __str__(self):
        slen = len([p for p in self._snap_paths if p])
        basic_info = 'Name: %s, found in %d snapshot(s) (%s)' % (self.name, slen, self._snap_paths, )
        run_results = ['%s: %s' % f for f in self._validators_results.items()]
        result = '____________________\n%s\n-- start of run results --\n%s\n-- end of run results --\n___________________\n' % (basic_info, '\n'.join(run_results), )
        return result

    def was_attacked(self):
        return bool(self.validators_results.items())

class Volume(object):
    '''
    Organizes a dict of files, each contains a list of the file path within all snapshots
    '''
    def __init__(self, volume_path):
        self._volume_path = volume_path
        # An array of length snapshots
        self.files = dict()
        self._process()
        self._validators = dict()
        self._default_validators = list()

    def _process(self):
        snapshot_exp = re.compile('^snapshot_([0-9]*)$')
        current_snapshot = 0

        self._number_of_snaps = len([f for f in os.listdir(self._volume_path) if snapshot_exp.match(f)])

        for snapshot in os.listdir(self._volume_path):
            match = snapshot_exp.match(snapshot)
            if not match:
                continue
            index = int(match.groups()[0]) - 1
            snapshot_full_path = os.path.join(self._volume_path, snapshot)
            self._process_files(snapshot_full_path, index)

    def _process_files(self, snapshot_dir, index):
        for root, dirs, files in os.walk(snapshot_dir):
            for f in files:
                full_path = os.path.join(root, f)
                snapfile = self.files.setdefault(f, SnapFile(f, self._number_of_snaps))
                snapfile.snap_paths[index] = FileEntry(full_path, index)

    def __iter__(self):
        return self.files.__iter__()

    def __getitem__(self, *args, **kwargs):
        return self.files.__getitem__(*args, **kwargs)

    def set_validators(self, validators, default_validators):
        self._validators = validators
        self._default_validators = default_validators

    def run_validators(self):
        for snapfile in self.files.values():
            e = snapfile.file_extension
            validators = self._validators.get(e, self._default_validators)
            for v in validators:
                validator_result = v.validate(snapfile)
                # Convert snapshot index to number
                if validator_result is not None:
                    validator_result += 1
                snapfile.validators_results[v.name] = validator_result

    def get_attacked_list(self):
        attacked_list = dict()
        for snapfile in self.files.values():
            attacked_indexes = [i for i in snapfile.validators_results.values() if i is not None]
            if not attacked_indexes:
                continue

            min_attacked_index = min(attacked_indexes)
            attacked_list.setdefault(min_attacked_index, list()).append(snapfile)
        return attacked_list

    def write_attacked_files(self, f):
        print('===Volume %s start===' % (self._volume_path, ))
        attacked_list = self.get_attacked_list()
        for snap_index in sorted(attacked_list.keys()):
            for snapfile in attacked_list[snap_index]:
                message = '%s\tsnapshot_%d' % (snapfile.name, snap_index, )
                print(message)
                f.write('%s\n' % (message, ))

        print('===Volume %s end===' % (self._volume_path, ))

class FileValidator(object):
    @property
    def name(self):
        return 'FileValidator'

    def __init__(self):
        super(FileValidator, self).__init__()

    def __str__(self):
        return self.name

    def validate(self, snapfile):
        raise NotImplementedError()

