def __list_all_modules():
    from os.path import dirname, basename, isfile
    import glob
    mod_paths = glob.glob(dirname(__file__) + '/*.py')
    return [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith('.py') and not f.endswith('__init__.py')
    ]


ALL_MODULES = sorted(__list_all_modules())
__all__ = ALL_MODULES + ['ALL_MODULES']
