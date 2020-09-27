# -*- coding: utf-8 -*-
import numpy as np
from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):
    support_models = ['DP832']

    quants = [
        QOption('Output', value='ON',ch=1,
            set_cmd=':OUTP CH%(ch)d,%(option)s', options=[('OFF', 'OFF'), ('ON', 'ON')]),
        QReal('Offset', unit='V', ch=1,
          set_cmd='SOUR%(ch)d:VOLT %(value)f',
          get_cmd='SOUR%(ch)d:VOLT?'),
    ]
