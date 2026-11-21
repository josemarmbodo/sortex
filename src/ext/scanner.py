import os
from pathlib import Path
from collections import deque
# from ..sort.sorter import DEFAULT_FILENAME_FOR_TEMP_SETTING_FILE, DESTINE_FOLDERNAME_FOR_SORTING


class Walker:

	__slots__ = (
		'_dirpath',
		'blt_ifolders',
		'debug_mode',
		'ignored_folders',
		'dst_fdname'
	)

	def __init__(
		self, dirpath: Path,
		blt_ifolders,
		ignore_folders: set[str] = set(), 
		debug_mode: bool = False,
		dst_fdname=None
	) -> None:

		self._dirpath = dirpath
		self.debug_mode = debug_mode
		self.ignored_folders = ignore_folders
		self.blt_ifolders = blt_ifolders['ignore.files']
		self.dst_fdname = dst_fdname or "sorted-by-sortex"

	def walk(self):
		queue = deque([self._dirpath])

		while queue:
			current_dir = queue.popleft()

			try:
				for entry in os.scandir(current_dir):
					fname = entry.name
					fpath = entry.path
					fext = os.path.splitext(fpath)[1]
					# user settings > blt settings
					# fmatch in ..
					is_ignored_file = fname in self.ignored_folders or fname in self.blt_ifolders

					if entry.is_dir():
						if not is_ignored_file:
							queue.append(fpath)
						else:
							# Avoiding entering on sorted-by-sortex folder
							if fname != self.dst_fdname:
								yield fname, fpath, fext, is_ignored_file
					else:
						# Avoiding move sortex-rules.json setting file.
						# To import the constat DEFAULT_FILENAME_FOR_TEMP_SETTING_FILE could cause circular import error.
						if fname != "sortex-rules.json":
							yield fname, fpath, fext, is_ignored_file
			except PermissionError:
				if self.debug_mode:
					print(f'Failed scannering the folder at {current_dir}')


