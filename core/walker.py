from collections import deque as deque

class FileTreeWalker:
    
    def __init__(
            self, 
            dir_target, 
            extensions=None,
            exclude: set={}, 
            path_class=None,
            scandir_function=None, 
            descard_erros_like=(PermissionError, WindowsError)
        ): 
            self.at = dir_target
            self.extensions = extensions
            self.exclude = exclude # fast solicitations with set, O(1)
            self.descard_erros_like = descard_erros_like
            self.scandir_at = scandir_function
            self.path_class = path_class
        
            if not scandir_function:
                from os import scandir as A
                self.scandir_at = A

            if not path_class:
                from pathlib import Path as AAA
                self.path_class = AAA
    
    @property 
    def generate_paths(self):
        try:
            location_queue = deque({ self.at })
            while location_queue:
                location = location_queue.popleft()

                with self.scandir_at(location) as entries:
                    for metadata in entries:
                        isdir = metadata.is_dir()
                        if isdir and metadata.name not in self.exclude:
                            location_queue.append(metadata.path)
                        elif not isdir:
                            if self.extensions:
                                if self.path_class(metadata.path).suffix in self.extensions:
                                    yield metadata
                            else:
                                yield metadata
        except self.descard_erros_like as e:
            print(f'[Warn from FileTreeWalker]: {e}')