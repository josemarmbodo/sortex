import argparse
from ..api import (
					Path, DesignerRoutes, RULES_PATH, ChangeTraceback,
					ALLOWED_PARENT_FOLDERS_FOR_SCANNING, sh, __version__,
					DEFAULT_NAME_FOR_TEMP_SETTING_FILE)

def _check_path(p: Path):
	if not p.exists():
		raise NotADirectoryError(f"{p} does not exists.")

	if not p.is_file():
		raise IsADirectoryError(f"{p} is a directory."
						" Excepted a file path contains the sortex configurations.")

def is_tmp_file_on_1st_level(tdir: Path, tmpf: Path):
	return tmpf.is_relative_to(tdir) and tmpf.parent == tdir

def main():
	parser = argparse.ArgumentParser(
		description='Sortex-v2.1.1 - A fast file organizer.'
	)

	parser.add_argument(
		'-s',
		'--sort',
		help='Organize the target directory.'
	)

	parser.add_argument(
		'-dm', 
		'--debug-mode',
		help='Enable the debug mode.',
		action='store_true'
	)

	parser.add_argument(
		'-ask', 
		'--ask-mode', 
		help='Enable the ask mode.'
		'Ask mode allows gie you a chance case you run the sortex in folder already sorted by him.',
		action='store_true'
	)

	parser.add_argument(
		'-mg',
		'--make-global',
		help='Make your local configuration file for global configuration file.'
	)

	parser.add_argument(
		'-e',
		'--extract',
		help='Extract rules from your local or temporary configuration file.'
		'Note: Just your global file is used for trace back changes and sync it with iternal cache.'
	)

	parser.add_argument(
		'-w',
		'--which-global-settings',
		help='Show absolute path of your global configuration file.',
		action='store_true'
	)

	parser.add_argument(
		'-v',
		'--version',
		help='Show the Sortex version and exit.',
		action='store_true'
	)

	args = parser.parse_args()

	if args.version:
		print(__version__)
		return

	modules = {
		"ask_mode_enabled": args.ask_mode,
		"which_global_settings": args.which_global_settings,
		"debug_mode_enabled": args.debug_mode,
		"extract_mode_enabled": args.extract,
	}

	for mode, activers in modules.items():
		if activers:
			modules[mode] = True


	if modules['which_global_settings']:
		print(RULES_PATH)
		return

	if args.make_global:
		cpath = Path(args.make_global).expanduser()
		_check_path(cpath)

		if not any(cpath.parent == fd for fd in ALLOWED_PARENT_FOLDERS_FOR_SCANNING):
			raise RuntimeError(f"Invalid path. Got: {cpath}")

		# Move to ~/.config/sortex
		rp = RULES_PATH.parent
		rp.mkdir(parents=True, exist_ok=True)
		sh.move(src=cpath, dst=rp / "rules.json")
		return

	
	if args.sort:
		extract_path = RULES_PATH
		target_dir = Path(args.sort).expanduser()

		if not target_dir.exists():
			raise NotADirectoryError(f"{target_dir} does not exists.")

		if modules['extract_mode_enabled']:
			# Especial enviroment variable for easy iclusion of use of target_dir. $/ = target_dir			
			if args.extract.startswith("$/"):
				args.extract = f"{args.sort}/{args.extract[2:]}"

			# File finded with `--extract` flag are considering tmp file and local file of rules.
			# Sortex does not trace back changes on tmp/local file of rules.
			extract_path = Path(args.extract)

			_is_tmp_file_on_1st_level = is_tmp_file_on_1st_level(target_dir, extract_path) 

			# If extracted file is under tdir folder, it must be named by sortex-rules.json, otherwise it will be provide by Walker.walk()
			# yield of file paths to DesignerRoutes.sort and it will be deleted by _clear_empty_folders method from DesignerRoutes.
			if _is_tmp_file_on_1st_level and extract_path.stem != DEFAULT_NAME_FOR_TEMP_SETTING_FILE:
				raise Exception(f'File name must be named by "{DEFAULT_NAME_FOR_TEMP_SETTING_FILE}" with extension ".json" for permanence reasons, got {extract_path}')

			# For Walker.walk ignore it, it must be named by sortex-rules.json. So, check your extension.
			suffix = extract_path.suffix
			if suffix != ".json":
				raise Exception(f"\".json\" extension required, got \"{suffix}\" from {extract_path}")

			# If tmp file is under from target_dir and not on 1st level, the file will be deleted by _clear_empty_folders
			# or on best case, will be inside of $/sortex-tmp folder.
			if extract_path.is_relative_to(target_dir) and not _is_tmp_file_on_1st_level:
				raise Exception(f"Your tmp file, must be replaced at this context from {extract_path} at {target_dir / extract_path.name}, for safety reasons.")

			# If tmp file is not inside of  target_dir, its name and extension does not interest for sortex, but yes for clearly reasons for user.
			# Walker.walk walks inside of target_dir, so, does not exists probabilities of it to be deleted by sortex unless user delete it.
			_check_path(extract_path)

		traceback_handler = ChangeTraceback(
											rules_path=extract_path, 
											debug_mode=modules['debug_mode_enabled'])
		drouter_interface = DesignerRoutes(
											target_dir=target_dir,
											rules=traceback_handler.get_user_rules,
											debug_mode=modules['debug_mode_enabled'],
											ask_mode=modules['ask_mode_enabled'])

		drouter_interface.sort()


if __name__ == '__main__':
	main()
