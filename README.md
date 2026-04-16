**Sortex** - *A smart, fast, and secure file organizer.*

### Why Sortex and the Problems It Solves
Sortex is highly focused on performance and security. A file organizer has multiple applications, and each requires specific specializations to maximize resource utilization. With this in mind, the system currently handles *music*, *documents* and *installers* directories. Sortex is designed to be cross-platform and to run background processes, organizing explicitly defined directories. Initially, the focus will be on *single-core* machines, later scaling to *multi-core* architectures following a `Divide and Conquer` strategy.

### Current Status
Sortex is currently under development. The initial release will focus on *single-core* machines and the organization of document directories.

### Configuration
To use Sortex, we recommend using a `.toml` file for customization. Example:
```toml
[threads-section]
# Integer to be used as an argument in the ThreadPoolExecutor instance. Two worker is recommended to Celeron.
max_workers = 10

[directories-section]
# Target directory
sort_directory = '~/downloads/musics'
# List of directories to exclude
exclude_directories = ['.git', '.venv', '__pycache__']
```
Python provides a native library for parsing `.toml` files. Furthermore, these files are widely used for system configuration. It is highly recommended to use native solutions, particularly `tomllib`, which is implemented in C.

### Technical Decisions
Instead of creating a separate backup folder and organizing the target directory, Sortex will create an *organized* folder within the parent directory. This avoids an estimated complexity of ~2n steps for backups, where *n* is the number of files to organize. Imagine a scenario with 100 files in a directory. If Sortex were to implement a backup mechanism and then organize the folder, it would require two operating system calls per file:
- `One to copy and move the file to the backup folder.`
- `Another to copy and move the file to the organized folder.`

This results in 2 calls per file, meaning ~2n = 2 x 100 = 200 operations. With the implemented approach, only ~n operations are required per file, as it simply involves moving the file to its corresponding folder. This yields O(n) complexity, which is significantly faster under these circumstances.

### Threads
An excellent way to enhance system performance is by utilizing threads, as the application tends to be heavily *I/O bound*. Threads take advantage of this by releasing the *GIL* (Global Interpreter Lock) during wait times, allowing for true concurrency on *single-core* processors without the associated overhead.

### Features
- *Integration with the `watchdog` library for background directory monitoring and organization.*