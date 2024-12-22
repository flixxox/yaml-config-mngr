# yaml-config-mngr
A yaml config manager in Python. It provides the Config object that provides some advanced config reading functionalities ontop of the dictionary interface.

It provides:
- Easy acces with a filesystem like referencing of variables
- Tidier and reusable configs by merging multiple smaller ones into a single large config
- Namespaces to avoid conflicts
- Avoiding multiple parameter definitions by reusing config parameters