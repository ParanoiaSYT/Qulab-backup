# # -*- coding: utf-8 -*-
import numpy as np
import re
import time
from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector
#
#
class Driver(BaseDriver):
    error_command = ':SYST:ERR?'
    support_models = ['E4407B']

    quants = [
#         QOption('Sweep', value='ON',
#             set_cmd='INIT:CONT %(option)s', options=[('OFF', 'OFF'), ('ON', 'ON')]),
#         QOption('Trace Mode', value='WRIT',ch=1,
#             set_cmd='TRAC%(ch)d:MODE %(option)s',get_cmd='TRAC%(ch)d:MODE?',
#             options=[('Write', 'WRIT'), ('Maxhold', 'MAXH'),('Minhold','MINH'),
#             ('View','VIEW'),('Blank','BLAN'),('Videoavg','VID'),('Poweravg','POW')]),
        QOption('Marker', value='ON',
            set_cmd=':CALCulate:MARKer1:STATe %(option)s', options=[('OFF', 'OFF'), ('ON', 'ON')]),
        QString('Marker_center',set_cmd=':CALCulate:MARKer1:CENTer %(value)s',get_cmd=':CALCulate:MARKer1:X?'),
        QString('Marker_amp',set_cmd=':CALCulate:MARKer1:Y %(value)s',get_cmd=':CALCulate:MARKer1:Y?'),
        QReal('Marker_right',set_cmd=' :CALCulate:MARKer1:MAXimum:RIGHt %(value)s',get_cmd=':CALCulate:MARKer1:X?'),
        # QReal('Marker_center', unit='Hz', set_cmd=':CALCulate:MARKer1:X %(value)e', get_cmd=':CALCulate:MARKer1:X?'),

        QReal('Frequency_center', unit='Hz', set_cmd=':SENSe:FREQuency:Center %(value)e%(unit)s', get_cmd=':SENSe:FREQuency:Center?'),
        QReal('sweep_span', unit='Hz', set_cmd=':SENSe:FREQuency:SPAN %(value)e%(unit)s', get_cmd=':SENSe:FREQuency:SPAN?'),
        QInteger('sweep_point', set_cmd=':SENSe:SWEep:POINts %(value)d', get_cmd=':SENSe:SWEep:POINts?'),
        QInteger('repeats_Average', set_cmd=':SENSe:AVERage:COUNt %(value)d', get_cmd=':SENSe:AVERage:COUNt?'),


        # QReal('Frequency Start', unit='Hz', set_cmd='SENS:FREQ:STAR %(value)e%(unit)s', get_cmd='SENS:FREQ:STAR?'),

    #     QReal('Frequency Stop', unit='Hz', set_cmd='SENS:FREQ:STOP %(value)e%(unit)s', get_cmd='SENS:FREQ:STOP?'),
    #     QInteger('Sweep Points',value=601, set_cmd=':SWE:POIN %(value)d',get_cmd=':SWE:POIN?')
    ]
    #
    # def get_Trace(self, average=1, ch=1):
    #     '''Get the Trace Data '''
    #
    #     points=self.getValue('Sweep Points')
    #     #Stop the sweep
    #     self.setValue('Sweep', 'OFF')
    #     if average==1:
    #         self.setValue('Trace Mode','Write',ch=ch)
    #         self.write(':SWE:COUN 1')
    #     else:
    #         self.setValue('Trace Mode','Poweravg',ch=ch)
    #         self.write(':TRAC:AVER:COUN %d' % average)
    #         self.write(':SWE:COUN %d' % average)
    #         self.write(':TRAC:AVER:RES')
    #     #Begin a measurement
    #     self.write('INIT:IMM')
    #     self.write('*WAI')
    #     count=float(self.query('SWE:COUN:CURR?'))
    #     while  count < average:
    #         count=float(self.query('SWE:COUN:CURR?'))
    #         time.sleep(0.01)
    #     #Get the data
    #     self.write('FORMAT:BORD NORM')
    #     self.write('FORMAT ASCII')
    #     data_raw = self.query("TRAC:DATA? TRACE%d" % ch).strip('\n')
    #     _data = re.split(r",",data_raw[11:])
    #     data=[]
    #     for d in _data[:points]:
    #         data.append(float(d))
    #     #Start the sweep
    #     self.setValue('Sweep', 'ON')
    #     return np.array(data)
    #
    #
    # def get_Frequency(self):
    #     """Return the frequency of DSA measurement"""
    #
    #     freq_star=self.getValue('Frequency Start')
    #     freq_stop=self.getValue('Frequency Stop')
    #     sweep_point=self.getValue('Sweep Points')
    #     return np.array(np.linspace(freq_star,freq_stop,sweep_point))
    #
    # def get_SNR(self,signalfreqlist=[],signalbandwidth=10e6,average=1, ch=1):
    #     '''get SNR_dB '''
    #
    #     Y_unit =self.query(':UNIT:POW?;:UNIT:POW W').strip('\n')
    #     Frequency=self.get_Frequency()
    #     Spectrum=self.get_Trace(average=average, ch=ch)
    #     Signal_power=0
    #     Total_power=sum(Spectrum)
    #     for sf in signalfreqlist:
    #         for f in Frequency :
    #             if f > (sf-signalbandwidth/2) and f < (sf+signalbandwidth/2):
    #                 index = np.where(Frequency==f)
    #                 Signal_power = Signal_power + Spectrum[index]
    #     self.write(':UNIT:POW %s'%Y_unit)
    #     _SNR=Signal_power/(Total_power-Signal_power)
    #     SNR = 10*np.log10(_SNR)
    #     return SNR
