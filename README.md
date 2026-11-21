# Sortex v2.1.1

A fast, command-line file organizer that sorts a messy directory into tidy folders based on file extensions. Sortex has **no third-party dependencies**, a small readable codebase, and a rules system you can customize with a single JSON file.

```bash
sortex --sort ~/Downloads
```

## Why Sortex

* **Works out of the box:** 52 built-in categories (Pictures, Videos, Audio, PDFs, Spreadsheets, Archives, Fonts, and dozens of programming languages) cover most real-world folders. Your first run uses these defaults, with no setup and no configuration file.
* **Yours to customize:** Add or override categories with a simple `extension -> folder` mapping. Your rules always take priority over the built-in ones, and anything you don't define falls back to the defaults.
* **Project-friendly:** Build and tooling folders (`.git`, `node_modules`, `.venv`, `dist`, ...) are never opened. They are moved as a whole into an `ignored-files` folder, so they are not torn apart. You can extend that list with your own folder names.
* **Nothing gets overwritten:** When two files would end up with the same name, Sortex keeps both by appending a short MD5-based suffix (e.g. `report_1ed23f9a.pdf`) derived from the source file's path.
* **Safe by design:** Sortex only runs inside your standard user folders (`Pictures`, `Videos`, `Music`, `Downloads`, `Documents`, `Desktop`), so it cannot be pointed at a system directory by accident.
* **Safe to re-run:** Running Sortex again on an already-sorted folder re-applies your current rules to everything, so tweaking your configuration and sorting again just works. An optional ask mode (`--ask-mode`) lets you confirm first.
* **Tidy results:** Empty leftover folders are cleaned up automatically after sorting.

## Under the Hood

* **Lazy, low-memory pipeline:** Directory scanning is a generator (`yield`), so files are processed as they are discovered instead of building huge in-memory lists. This keeps memory usage flat on folders with thousands of files.
* **Iterative BFS scanning:** Uses `collections.deque` and `os.scandir` instead of recursion, which sidesteps Python's recursion limit and keeps disk reads fast. Unreadable folders are skipped (and reported in debug mode) rather than crashing the run.
* **Cached pattern matching:** Extension patterns are compiled once and reused through `functools.lru_cache`, so repeated lookups stay cheap.
* **Smart config detection:** The global configuration file is fingerprinted with MD5. Sortex re-parses your rules only when the file actually changed, and otherwise loads them from a local cache in `~/.cache/sortex/`.
* **Performance:** In the author's stress test on a single-core machine, a full sorting run finished in about **3 seconds** with a peak memory footprint of **504 MiB**. (No benchmark script is included in the repository yet, so treat this as an indicative figure.)

## Installation

Sortex needs **Python 3.10 or newer** (developed on 3.10, also verified on 3.12) and nothing else: it relies only on the standard library.

```bash
git clone https://github.com/josemarmbodo/sortex.git
cd sortex
python3 -m pip install -e .
```

That is all the setup there is. Confirm that it works:

```bash
sortex --version
```

## Usage

Sort a folder:

```bash
sortex --sort ~/Downloads
```

Sortex creates a `sorted-by-sortex` folder inside the target directory and groups your files there by category:

```
~/Downloads/sorted-by-sortex/
├── Pictures/
├── PDFs/
├── Videos/
├── Python/
├── unknown-extensions/   # extensions no rule matches
└── ignored-files/        # folders and files on the ignore list
```

### Command-line options

| Option | Description |
| --- | --- |
| `-s`, `--sort <dir>` | Organize the target directory. |
| `-dm`, `--debug-mode` | Print detailed diagnostics (config changes, skipped folders). |
| `-ask`, `--ask-mode` | Ask for confirmation when the folder was already sorted by Sortex. |
| `-mg`, `--make-global <file>` | Promote a local configuration file to your global configuration. |
| `-e`, `--extract <file>` | Use a temporary configuration file for this run only. |
| `-w`, `--which-global-settings` | Show where your global configuration file lives. |
| `-v`, `--version` | Show the Sortex version. |

## Configuration

Custom configuration is **optional**. If you have not created any, Sortex uses the 52 built-in categories and the built-in ignore list (40 entries), starting with your very first run. To change something, create a rules file with one or both of these fields:

```json
{
  "ignore.files": ["my-project", "keep-me.txt"],
  "mapping.rules": {
    "Invoices": "(inv|invoice)",
    "sublime-text/configurations": "(sublime-project|sublime-workspace)"
  }
}
```

* **`mapping.rules`**: maps a destination folder to a regular expression that matches file extensions (without the dot, case-insensitive). Folder names may contain `/` to create nested folders.
* **`ignore.files`**: names of files or folders to leave untouched. They are added on top of the built-in ignore list.

There are two ways to provide your rules:

1. **Global (recommended):** One configuration for every run, stored at `~/.config/sortex/rules.json`. To create it from a local file:
   ```bash
   sortex --make-global ~/Downloads/my-rules.json
   ```
   Use `sortex --which-global-settings` at any time to print the exact path.

2. **Temporary, for one run:** Point `--extract` at a rules file. It is not saved anywhere and changes nothing for later runs.
   ```bash
   sortex --sort ~/Downloads --extract '$/sortex-rules.json'
   ```
   `$/` is a shortcut for the target directory (keep the quotes so your shell leaves it alone). A few simple rules keep the file safe:
   * If it lives **directly inside the target directory**, it must be named `sortex-rules.json`. Sortex never moves a file with that name while sorting.
   * It cannot live in a **subfolder** of the target directory.
   * If it lives **anywhere else**, it can have any name, as long as it ends in `.json`.

## Before You Run It

Sortex **moves** your files, and there is currently no dry-run mode and no undo. A few things worth knowing first:

* Try it on a small, non-critical folder the first time, and back up anything irreplaceable.
* Any folder that is not on the ignore list is opened and its files are sorted individually. If you keep project folders inside the target directory, add their names to `ignore.files` so they stay in one piece.
* `--make-global` *moves* (not copies) your file to `~/.config/sortex/rules.json`, and the source file must sit directly inside one of the supported user folders.
* Sortex has been developed in a Unix environment; behavior on Windows has not been verified.
* The MD5-based suffix makes name collisions very unlikely, but it is a shortened hash (8 characters), not an absolute guarantee.

## License

Released under the terms of the [LICENSE](LICENSE) file.
