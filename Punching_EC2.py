# -*- coding: utf-8 -*-
"""Ponto de entrada compatível: from Punching_EC2 import PuncoamentoEC2."""
from punching.core import PuncoamentoEC2
from punching.version import VERSION as __version__

if __name__=='__main__':
    from punching.cli import main
    main()
