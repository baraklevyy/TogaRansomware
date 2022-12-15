import sys
from traverser import FilesScanner, Volume

#
# sf: class SnapFile(object)
#   .name               name of file
#   .snap_paths         List of 10 (num of snapshots) with None or FileEntry for each
#   .scanners_results   dict{"ScannerName": result}, while result is None (if scanner doesn't match) or earliest snapshot index
#
# FileEntry:
#   __str__, .path      file path
#   .entropy            entropy of file
#

class DisappearedScanner(FilesScanner):
    @property
    def name(self):
        return 'DisappearedScanner'

    def scan(self, sf):
        if None in sf.snap_paths:
            last_index = sf.snap_paths.index(None)
            return last_index

        return None

class EntropyScanner(FilesScanner):
    @property
    def name(self):
        return 'EntropyScanner'

    def scan(self, sf):
        entropies_thresholds = {
            'jpg': 10,
        }
        #  if None in sf.snap_paths:
        #      last_index = sf.snap_paths.index(None)
        #      return last_index

        return None

def main():
    if len(sys.argv) < 2:
        print('Usage: %s VOLUME_PATH' % (sys.argv[0], ))
        return 1

    volume_path = sys.argv[1]
    vol = Volume(volume_path)
    vol.add_scanners([DisappearedScanner()])

    vol.run_scanners()
    vol.print_attacked_files()


if __name__ == '__main__':
    exit(main())

