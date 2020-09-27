# -*- coding: utf-8 -*-
import numpy as np

from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):

	support_models = ['SIM900']
	'''SRS SIM900 seris DC voltage source'''
	quants = [
		QReal('Offset', value=0, unit='V', ch=1,
			set_cmd='SNDT %(ch)d,"VOLT %(value).2f"',
			get_cmd='SNDT %(ch)d,"VOLT?"'),

		QOption('Output', ch=1,
			set_cmd='SNDT %(ch)d,"%(option)s"',
			get_cmd='SNDT %(ch)d,"EXON?"',
			options=[('OFF', 'OPOF'), ('ON', 'OPON')]),
	]
	
