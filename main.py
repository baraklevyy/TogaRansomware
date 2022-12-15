import sys
import os
import py7zr
import rarfile
import mobi
from PIL import Image, UnidentifiedImageError
from PyPDF2 import PdfFileReader

from traverser import FileValidator, Volume

#
# sf: class SnapFile(object)
#   .name               name of file
#   .snap_paths         List of 10 (num of snapshots) with None or FileEntry for each
#   .validators_results   dict{"ValidatorName": result}, while result is None (if validator doesn't match) or earliest snapshot index
#
# FileEntry:
#   __str__, .path      file path
#   .entropy            entropy of file
#

class EntropyValidator(FileValidator):
    def __init__(self, entropy_threshold, max_diff_entropy):
        self._entropy_threshold = entropy_threshold
        self._max_diff_entropy = max_diff_entropy

    @property
    def name(self):
        return 'EntropyValidator(threshold %s, diff %s)' % (self._entropy_threshold, self._max_diff_entropy, )

    def validate(self, sf):
        entropies = [None if fe is None else fe.entropy
                     for fe in sf.snap_paths]
        for i in range(1, len(entropies)):
            if entropies[i] is None:
                continue

            is_large_and_shouldnt = entropies[i] > self._entropy_threshold and (not sf.is_high_entropy_extension())
            if is_large_and_shouldnt:
                return i
            if entropies[i - 1] is not None:
                diff = entropies[i] - entropies[i - 1]
                is_big_diff = diff > self._max_diff_entropy
                if is_big_diff:
                    return i

        return None

class SevenzipValidator(FileValidator):
    @property
    def name(self):
        return 'SevenzipValidator'

    def validate(self, sf):
        for i in range(len(sf.snap_paths)):
            sp = sf.snap_paths[i]
            if sp is None:
                continue
            try:
                py7zr.SevenZipFile(sp.path)
            except py7zr.Bad7zFile:
                return i
            except Exception:
                return i
        return None

class RarValidator(FileValidator):
    @property
    def name(self):
        return 'RarValidator'

    def validate(self, sf):
        for i in range(len(sf.snap_paths)):
            sp = sf.snap_paths[i]
            if sp is None:
                continue
            try:
                rarfile.RarFile(sp.path)
            except rarfile.NotRarFile:
                return i
            except Exception:
                return i
        return None

class ImageValidator(FileValidator):
    @property
    def name(self):
        return 'ImageValidator'

    def validate(self, sf):
        for i in range(len(sf.snap_paths)):
            sp = sf.snap_paths[i]
            if sp is None:
                continue
            try:
                Image.open(sp.path)
            except UnidentifiedImageError:
                return i
            except Exception:
                return i
        return None

class PdfValidator(FileValidator):
    @property
    def name(self):
        return 'PdfValidator'

    def validate(self, sf):
        for i in range(len(sf.snap_paths)):
            sp = sf.snap_paths[i]
            if sp is None:
                continue
            try:
                PdfFileReader(sp.path)
            except Exception:
                return i
        return None

class MobiValidator(FileValidator):
    def __init__(self, first_bytes_amount=0x10):
        self._first_bytes_amount = first_bytes_amount

    @property
    def name(self):
        return 'MobiValidator'

    def validate(self, sf):
        prefixes = [
            sp.get_first_bytes(self._first_bytes_amount) if sp is not None else None
            for sp in sf.snap_paths
        ]

        for i in range(1, len(prefixes)):
            if prefixes[i] is not None and prefixes[i - 1] is not None and\
                    prefixes[i] != prefixes[i - 1]:
                        return i
        return None

class RansomwareNoteValidator(FileValidator):
    @property
    def name(self):
        return 'RansomwareNoteValidator'

    def validate(self, sf):
        for i in range(len(sf.snap_paths)):
            sp = sf.snap_paths[i]
            if sp is None:
                continue
            content = sp.get_first_bytes(-1).lower()
            dangerous_words = [b'bitcoin', b'encrypt']
            dangerous_words_found = [w in content for w in dangerous_words]
            if all(dangerous_words_found):
                return i

        return None

EXTENSIONS_TO_VALIDATORS = {
    '7z': [SevenzipValidator()],
    'rar': [RarValidator()],
    'jpg': [ImageValidator()],
    'png': [ImageValidator()],
    'pdf': [PdfValidator()],
    'mobi': [MobiValidator(0x10)],
    'txt': [EntropyValidator(7.5, 3), RansomwareNoteValidator()],
    'html': [EntropyValidator(7.5, 3), RansomwareNoteValidator()],
}
DEFAULT_VALIDATORS = [EntropyValidator(7.5, 3)]


def main():
    if len(sys.argv) < 2:
        print('Usage: %s VOLUMES_DIR' % (sys.argv[0], ))
        return 1

    vol_dir = sys.argv[1]

    for vol_name in ('vol_1', 'vol_2', 'vol_3'):
        vol_path = os.path.join(vol_dir, vol_name)
        vol = Volume(vol_path)
        vol.set_validators(EXTENSIONS_TO_VALIDATORS, DEFAULT_VALIDATORS)
        vol.run_validators()
        with open(f'results_{vol_name}.txt', 'w') as f:
            vol.write_attacked_files(f)


if __name__ == '__main__':
    exit(main())

