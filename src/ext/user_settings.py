import json
import pickle
import hashlib
from pathlib import Path
from ..defaults.config import BUILTIN_SETTINGS
from collections import UserDict

HOME_USER = Path.home()

RULES_PATH = HOME_USER / ".config" / "sortex" / "rules.json"
CACHE_PATH = HOME_USER / ".cache" / "sortex"
CACHE_PATH.mkdir(parents=True, exist_ok=True)

CHANGES_TRACKING_PATH = CACHE_PATH / "user_settings_ctracking.txt"
CACHE_PATH = CACHE_PATH / "user_settings.pkl"


class RulesFields(UserDict):
	def __init__(self, rules):
		if not isinstance(rules, dict):
			raise ValueError("rules must be a dict object.")

		super().__init__(rules)
		self._solve_missing_fields()

	@property
	def _get_available_fields(self):
		return ("ignore.files", list), ("mapping.rules", dict)

	def _solve_missing_fields(self):
		available_fields = self._get_available_fields
		allowed_fields = dict(available_fields)

		for ukey in self.data:
			if ukey not in allowed_fields:
				raise ValueError(f'Unknown property, got "{ukey}". Consult the Sortex documentation.')

		for field, primitive_type in available_fields:
			if not self.get(field):
				self.setdefault(field, primitive_type())

class ChangeTraceback:
	"""Trace back changes from user setting file."""

	__slots__ = (
		'rules_path',
		'debug_mode',
		'user_rules',
		'make_traceback',
		'usr_rules_ct',
		'cache_footprint'
	)

	def __init__(self, rules_path=RULES_PATH, debug_mode=False) -> None:
		self.rules_path = rules_path.expanduser()
		self.debug_mode = debug_mode
		self.make_traceback = str(self.rules_path) == str(RULES_PATH)
		"No tracking must be runned if user specify a tem!porary settings file."
		self.usr_rules_ct = b""
		self.cache_footprint = ""
		"Avoid double compute of hash from user rules."

		# sortex --sort ./messy_folder --extract ./messy_folder/sortex-rules.json
		if self.make_traceback and self.rules_path.exists() and self.rules_path.stat().st_size:
			self.usr_rules_ct = self.rules_path.read_bytes()
			self.user_rules = self.traceback()
		else:
			self.make_traceback = False
			self.user_rules = self.user_rules_extractor()


	def user_rules_extractor(self, fromcache=False) -> RulesFields:
		if not self.rules_path.exists():
			# self.rules_path points to default path. But user does not set global settings.
			self.make_traceback = False
			return RulesFields({})
		
		if not self.make_traceback:
			ct = self.rules_path.read_bytes()

			if self.debug_mode:
				print(f'[user_settings.py] Extracting rules from temp setting file at {self.rules_path}')

			if not ct or len(ct) < 2: # 2 = len('{}')
				raise ValueError(f'Temporary settings file at "{self.rules_path}" is empty.')

			return RulesFields(json.loads(ct))
		
		ct = self.rules_path.read_bytes()

		if fromcache:
			if self.debug_mode:
				print(f'[user_settings.py] Extracted rules from cache at {CACHE_PATH}')
			try:
				return pickle.loads(CACHE_PATH.read_bytes())
			except:
				if self.debug_mode:
					print("[user_settings.py] Error to load the cache file. Recreating it.")
				self._prepare()

		if not ct:
			if self.debug_mode:
				print("[user_settings.py] No rule sort content in user global settings.")

			self.make_traceback = False
			return RulesFields({})

		self.usr_rules_ct = ct

		return RulesFields(json.loads(ct))


	@property
	def get_user_rules(self) -> RulesFields:
		return self.user_rules


	def save_changes(self):
		CACHE_PATH.write_bytes(pickle.dumps(self.user_rules))
		fcache = self.cache_footprint

		CHANGES_TRACKING_PATH.write_text(
			self.get_footprint if not fcache else fcache,
			encoding="utf-8"
		)


	@property
	def get_footprint(self):
		return hashlib.md5(self.usr_rules_ct).hexdigest()

	@property
	def get_ctracking(self):
		return CHANGES_TRACKING_PATH.read_text(encoding="utf-8")


	def cache_exists(self):
		return CACHE_PATH.exists() and CHANGES_TRACKING_PATH.exists()


	def has_changes(self):
		# on first execution
		if not self.cache_exists():
			return True

		current_footprint = self.get_footprint

		if current_footprint != self.get_ctracking:
			# inform that already is available footprint content
			self.cache_footprint = current_footprint
			return True

		return False


	def _prepare(self):
		self.user_rules = RulesFields(json.loads(self.usr_rules_ct))
		self.save_changes()


	def traceback(self):
		if self.has_changes():
			if self.debug_mode:
				print('[user_settings.py] Changes detected.')
			self._prepare()
			return self.user_rules

		if self.debug_mode:
			print('[user_settings.py] No changes detected.')
		return self.user_rules_extractor(fromcache=True)
