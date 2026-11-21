import os
import re
import hashlib
import shutil as sh
from functools import lru_cache
from ..ext.scanner import Walker, Path
from ..ext.user_settings import ChangeTraceback, HOME_USER, BUILTIN_SETTINGS, RulesFields, RULES_PATH


ALLOWED_PARENT_FOLDERS_FOR_SCANNING = (
                                        HOME_USER / 'Pictures',
                                        HOME_USER / 'Videos',
                                        HOME_USER / 'Music',
                                        HOME_USER / 'Downloads',
                                        HOME_USER / 'Documents',
                                        HOME_USER / 'Desktop'
)


DESTINE_FOLDERNAME_FOR_SORTING = "sorted-by-sortex"
DESTINE_FOLDERNAME_FOR_IGNORED_FILES = "ignored-files"
DEFAULT_NAME_FOR_TEMP_SETTING_FILE = "sortex-rules"
DEFAULT_FILENAME_FOR_TEMP_SETTING_FILE = DEFAULT_NAME_FOR_TEMP_SETTING_FILE + ".json"
FOLDERNAME_FOR_UNKNOWN_EXTENSIONS = "unknown-extensions"


@lru_cache()
def get_pattern(reg) -> re.Pattern[str]:
    return re.compile(reg, re.IGNORECASE)


class DesignerRoutes:

    __slots__ = ('tdir', 'debug_mode', 
                'sortexDB', 'settings', 
                'dstpath', 'ask_mode',
                'ifiles', 'dst_ifiles',
                'rules', 'tmp_dstpath',
                'resorted_folder')

    def __init__(
        self, 
        target_dir: Path, 
        rules: RulesFields,
        debug_mode: bool = False,
        ask_mode=False, 
    ) -> None:

        self.tdir = target_dir.expanduser()
        self.debug_mode = debug_mode
        self.ask_mode = ask_mode
        self.dstpath = self.tdir / DESTINE_FOLDERNAME_FOR_SORTING
        self.rules = rules
        self.ifiles = self.rules['ignore.files']
        self.dst_ifiles = self.dstpath / DESTINE_FOLDERNAME_FOR_IGNORED_FILES
        self.tmp_dstpath = self.tdir / "sortex-tmp"
        self.resorted_folder = False
        """Later the sortex-tmp folder must be renamed by sorted-by-sortex"""

    def has_name_conflict(self, supposed_dst: Path):
        return supposed_dst.exists()

    def solve_name_conflict(self, src: str, dst: Path, stem=None, suffix=None):
        stem  = dst.stem if not stem else stem
        suffix = dst.suffix if not suffix else suffix
        src_hash = self.hashof(src)[:8]
        # move method support src and dst params of type Path.
        sh.move(src, dst.with_name(f'{stem}_{src_hash}{suffix}'))

    def check_tdir(self):
        """Raise an exception if `target_dir` is a unallowed directory for sort it."""
        mtch = any(self.tdir.is_relative_to(fpath) for fpath in ALLOWED_PARENT_FOLDERS_FOR_SCANNING)
        if not mtch:
            raise Exception(f'Sortex can not be runned at: {self.tdir}')

    def warn_if_has_ordination(self):
        if self.dstpath.exists():
            if self.ask_mode:
                # When the flag --asks has gone included
                print(f'Folder at {self.tdir} was already sorted by Sortex.')
                stdin = input("Do you want to continue? [Y/N]: ")
                if stdin.upper() != "Y":
                    print("Sortex stopped by user. Sort operation canceled.")
                    import sys
                    sys.exit(1)
                    # User accpeted sort it again.
                    # walk method does not walk on a folder with name sorted-by-sortex.
                    # eg: ~/messy_folder/sorted-by-sortex -> ~/messy_folder/sortex-tmp
                    self._prepare_target_dir_for_resort()
            else:
                self._prepare_target_dir_for_resort()


    def _prepare_target_dir_for_resort(self):
        # User accpeted sort it again.
        # walk method does not walk on a folder with name sorted-by-sortex.
        # eg: ~/messy_folder/sorted-by-sortex -> ~/messy_folder/sortex-tmp
        self.dstpath.rename(self.tmp_dstpath)
        self.dstpath = self.tmp_dstpath
        self.dst_ifiles = self.dstpath / DESTINE_FOLDERNAME_FOR_IGNORED_FILES
        self.resorted_folder = True

    def hashof(self, ct: str):
        return hashlib.md5(ct.encode()).hexdigest()


    def _get_blt_fdname(self, ext: str):
        embedding_mapping = BUILTIN_SETTINGS['mapping.rules']

        for fdn, regxp in embedding_mapping.items():
            ans = re.fullmatch(get_pattern(regxp), ext)
            if ans:
                return fdn

        return FOLDERNAME_FOR_UNKNOWN_EXTENSIONS


    def get_fdname_for_extension(self, ext: str):
        # user settings > builtin settings
        rules = self.rules.get('mapping.rules')

        if rules:
            for fdname, regexp in rules.items():
                ext_known = re.fullmatch(get_pattern(regexp), ext)
                if ext_known:
                    return fdname
            # If user not set a pattern matched, then use the builtin mapping
            return self._get_blt_fdname(ext)

        return self._get_blt_fdname(ext)


    def _clear_empty_folders(self):
        for entry in os.scandir(self.tdir):
            # remove empty folders that sortex let us.
            if entry.name in (DESTINE_FOLDERNAME_FOR_SORTING, DEFAULT_FILENAME_FOR_TEMP_SETTING_FILE):
                continue
            if not entry.is_dir(follow_symlinks=False):
                continue

            for root, dirs, _ in os.walk(entry.path, topdown=False):
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except OSError:
                        pass
            try:
                os.rmdir(entry.path)
            except OSError:
                pass
    
    def sort(self):
        self.check_tdir()

        self.warn_if_has_ordination()

        self.dstpath.mkdir(parents=True, exist_ok=True)
        self.dst_ifiles.mkdir(exist_ok=True)

        wdirs = Walker(
                        dirpath=self.tdir, debug_mode=self.debug_mode,
                        ignore_folders=self.ifiles, blt_ifolders=BUILTIN_SETTINGS
        )

        if self.resorted_folder:
            # cria o tmp, varre e mete no destino com sorted-by-sortex
            # depois apaga o tmp
            self.dstpath = self.tdir / DESTINE_FOLDERNAME_FOR_SORTING
            self.dst_ifiles = self.dstpath / DESTINE_FOLDERNAME_FOR_IGNORED_FILES
            self.dstpath.mkdir(parents=True, exist_ok=True)
            self.dst_ifiles.mkdir(exist_ok=True)


        for fname, fpath, fext, is_ifile in wdirs.walk():
            if is_ifile: # ignored_files like a folder or file
                # Ignored folders must be moved directly for sortex folder avoiding folder-leak.
                # NOTE: It is too important mainly with project folders like: ai-agent-vx.x.x.
                fdst = self.dst_ifiles / fname # ../sorted-by-sortex/ignored-files/.gitignore

                if self.has_name_conflict(supposed_dst=fdst): # Avoiding file leak
                    self.solve_name_conflict(src=fpath, dst=fdst)
                    continue

                # If scr=./a/b/file.txt, dst can be ./c/d, without filename
                # move method support src and dst params of type Path.
                sh.move(fpath, fdst)
                continue

            # Tasks for file not ignored. # sortex-by-sortex/assembly
            fdmatch = self.get_fdname_for_extension(fext[1:])
            fdst = self.dstpath / fdmatch

            # Allow use: "sublime-text/configurations": "(sublime-project|sublime-workspace)"
            if fdmatch.rfind('/') != -1:
                fdst.mkdir(parents=True, exist_ok=True)
            else:
                fdst.mkdir(exist_ok=True)

            # print(fdst)

            if self.has_name_conflict(supposed_dst=fdst / fname): # ./sortex-by-sortex/assembly/.gitignore
                # ./sortex-by-sortex/assembly/.gitignore_1ed23f..
                self.solve_name_conflict(fpath, fdst / fname)
                continue

            sh.move(fpath, fdst)
            continue

        self._clear_empty_folders()

    def rename_dspath_to_default_name(self):
        # eg: ?/sorted-tmp -> ?/sorted-by-sortex
        self.dstpath.rename(self.tdir / DESTINE_FOLDERNAME_FOR_SORTING)


# TRACEBACK = ChangeTraceback(
#     # rules_path=Path("~/Desktop/pop3/sortex-rules.json")
# )

# POP3 = DesignerRoutes(
#                 rules=TRACEBACK.get_user_rules,
#                 target_dir=Path('~/Desktop/pop3'),
#                 ask_mode=True
# )


# POP3.organize()
