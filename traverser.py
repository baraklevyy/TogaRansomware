#!/usr/bin/env python3

import os
import sys
import re

def get_entropy(filename):
    """ Code from internet """
    with open(filename, "rb") as file:
        counters = {byte: 0 for byte in range(2 ** 8)}  # start all counters with zeros
        for byte in file.read():  # read in chunks for large files
            counters[byte] += 1  # increase counter for specified byte
        filesize = file.tell()  # we can get file size by reading current position
        probabilities = [counter / filesize for counter in counters.values()]  # calculate probabilities for each byte
        entropy = -sum(probability * math.log2(probability) for probability in probabilities if probability > 0)  # final sum
        print(entropy)


class FileEntry(object):
    """
    Meta data on actual file
    """

    def __init__(self, path):
        self._path = path
        self._entropy = None

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
            self._entropy = get_entroply(self._path)
        return self._entropy


class SnapFile(object):
    '''
    Contains filename, and list of paths in all snapshots
    Contains dict of scanner names, mapped to their results
    '''
    def __init__(self, name, snap_count=10):
        self._name = name
        self._snap_paths = [None for i in range(snap_count)]
        self._scanners_results = dict()

    @property
    def name(self):
        return self._name

    @property
    def snap_paths(self):
        return self._snap_paths

    @property
    def scanners_results(self):
        return self._scanners_results

    def __str__(self):
        slen = len([p for p in self._snap_paths if p])
        basic_info = 'Name: %s, found in %d snapshot(s) (%s)' % (self.name, slen, self._snap_paths, )
        run_results = ['%s: %s' % f for f in self._scanners_results.items()]
        result = '____________________\n%s\n-- start of run results --\n%s\n-- end of run results --\n___________________\n' % (basic_info, '\n'.join(run_results), )
        return result

    def was_attacked(self):
        return bool(self.scanners_results.items())

class Volume(object):
    '''
    Organizes a dict of files, each contains a list of the file path within all snapshots
    '''
    def __init__(self, volume_path):
        self._volume_path = volume_path
        # An array of length snapshots
        self.files = dict()
        self._process()
        self._scanners = list()

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

    def _process_files(self, snapshot, index):
        for root, dirs, files in os.walk(snapshot):
            for f in files:
                full_path = os.path.join(root, f)
                snapfile = self.files.setdefault(f, SnapFile(f, self._number_of_snaps))
                snapfile.snap_paths[index] = FileEntry(full_path)

    def __iter__(self):
        return self.files.__iter__()

    def __getitem__(self, *args, **kwargs):
        return self.files.__getitem__(*args, **kwargs)

    def add_scanners(self, scanners):
        for scanner in scanners:
            self.add_scanner(scanner)

    def add_scanner(self, scanner):
        self._scanners.append(scanner)

    def run_scanners(self):
        for snapfile in self.files.values():
            for s in self._scanners:
                scanner_result = s.scan(snapfile)
                snapfile.scanners_results[s.name] = scanner_result

    def print_attacked_files(self):
        for snapfile in self.files.values():
            attacked_indexes = [i for i in snapfile.scanners_results.values() if i is not None]
            if not attacked_indexes:
                continue

            min_attacked_index = min(attacked_indexes)
            print('%s\t%d' % (snapfile.name, min_attacked_index, ))

class FilesScanner(object):
    @property
    def name(self):
        return 'FilesScanner'

    def __init__(self):
        super(FilesScanner, self).__init__()

    def __str__(self):
        return self.name

    def scan(self, snapfile):
        raise NotImplementedError()

