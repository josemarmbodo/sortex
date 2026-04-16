def load_settings(pathname: str | None = None):
    """
    Load and returns the custom user settings from `toml` file.

    Parameters
    ==========
    pathname: Pathname of the user settings. If not defined, default settings will be used.
    >>> from blusk.core.settings import load_settings
    >>> load_settings() # using default settings
    >>> load_settings("~/custom_settings.toml") # using custom file
    """    

    with open(pathname if pathname else "./config/default.toml", "rb") as f:
        # tomlib is lazily imported to avoid memory overhead on failure
        return __import__("tomllib").load(f)
