import walker
from pathlib import Path as PurePath
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import MP3, HeaderNotFoundError
from mutagen import File as MutagenMechanismFile

class FileError(ValueError): pass

class File:
    """Collects indispensable data from music files"""
    __slots__ = ("path", "name", "extension", "is_valid", 
                 "has_metadata", "title", "albuns", 
                 "interprets", "_")

    def __init__(self, path: PurePath):
        self.path = path
        self.name = path.name
        self.extension = path.suffix[1:].lower()

        # Flags to control
        self.is_valid = True # Was it possible to open this file?
        "A file music is consider valid if at least it have interprets and albuns properties."
        self.has_metadata = True # Is it at least 1 tag?

        # Default values
        self.title = None
        self.albuns = None
        self.interprets = None

        self._ = self._load_metadata()

    
    def _load_metadata(self): 
        return self._tags()
    
    @property
    def get_tags(self):
        return self._

    def _tags(self):
        tags = {}
        try:
            match self.extension:
                case "mp3":
                    metadata = MP3(self.path)
                    tags['title'] = metadata.get('TIT2')
                    tags['albuns'] = metadata.get('TALB')
                    tags['interprets'] = metadata.get('TPE1')
                case "m4a":
                    metadata = MutagenMechanismFile(self.path)
                    tags['title'] = metadata.get('\xa9nam')
                    tags['albuns'] = metadata.get('\xa9alb')
                    tags['interprets'] = metadata.get('\xa9art')
            
            I = not tags['interprets']
            if (I and not tags['albuns']) or I:
                self.is_valid = False

            return tags
        except (HeaderNotFoundError, ID3NoHeaderError, FileError):
            self.is_valid = False
            self.has_metadata = False
            return 
    
    def define_destine(self):
        dst = self.path.parent

        if self.is_valid:
            dst /= self.get_tags['interprets'][0]
            dst /= self.get_tags['albuns'][0]
        else:
            dst /= "unknow_artists/"
        
        dst /= self.name
        
        return dst
