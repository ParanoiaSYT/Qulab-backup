# -*- coding: utf-8 -*-
import numpy as np

from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):
    support_models = ['DG1062Z']

    quants = [
# Set the waveform offset voltage of the specified channel.
# Query the waveform offset voltage of the specified channel.
        # QReal('Voltage_Offset', unit='VDC',
        #   set_cmd=':SOUR1:VOLT:OFFS %(value).8e%(unit)s',
        #   get_cmd=':SOUR1:VOLT:OFFS?'),


# Set the waveform of the specified channel to DC with the specified offset.
        QReal('Offset', unit='V', ch = 1,
          set_cmd=':SOUR%(ch)d:APPL:DC 1,1, %(value).8e%(unit)s',
          get_cmd=':VOLT?'),

        # QOption('Output',
        #   set_cmd=':OUTP %(option)s', options=[('OFF', 'OFF'), ('ON', 'ON')]),

        QOption('Output',ch=1,
        set_cmd='OUTP%(ch)d %(option)s', get_cmd='OUTP%(ch)d?',
        options=[('OFF', 'OFF'), ('ON', 'ON')]),  # must set chanel


          
    ]
