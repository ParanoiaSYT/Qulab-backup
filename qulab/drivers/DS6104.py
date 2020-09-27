# -*- coding: utf-8 -*-
import numpy as np

from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):
    support_models = ['DS6104']

    quants = [

# Set the waveform of the specified channel to DC with the specified offset.
        QReal('wav_begin'
          set_cmd=':WAVeform:BEGin',),

        QReal('wav_data', ch = 1,
          set_cmd=':WAVeform:DATA?',),

        QReal('wav_end'
          set_cmd=':WAVeform:END',),

        QReal('wav_stat'
          set_cmd=':WAVeform:STATus?'),

        QReal('wav_points'
          set_cmd=':WAVeform:POINts %(value)s',
          get_cmd=':WAVeform:POINts?'),


        QOption('wav_format'
        set_cmd=':WAVeform:FORMat %(options)s', get_cmd=':WAVeform:FORMat?',
        options=[('WORD', 'WORD'), ('BYTE', 'BYTE')]),  # must set chanel

        QOption('wav_mod'
        set_cmd=':WAVeform:MODE %(options)s', get_cmd=':WAVeform:MODE?',
        options=[('NORMal', 'NORMal'), ('MAXimum', 'MAXimum'), ('RAW', 'RAW')]),  # must set chanel

        QOption('wav_sour'
        set_cmd=':WAVeform:SOURce %(options)s', get_cmd=':WAVeform:SOURce?',
        options=[('CHANnel1', 'CHANnel1'), ('CHANnel2', 'CHANnel2'), ('CHANnel3', 'CHANnel3'), ('CHANnel4', 'CHANnel4')]),  # must set chanel


    ]
