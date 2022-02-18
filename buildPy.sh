#!/bin/bash
pyinstaller -F \
    --hidden-import=pyqtgraph \
    --hidden-import=PySide2.QtXml \
    -n main \
    main.py