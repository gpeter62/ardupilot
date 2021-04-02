#!/usr/bin/env python

from lxml import etree

from emit import Emit
from param import known_param_fields, known_units

# Emit APM documentation in an machine readable XML format
class XmlEmit(Emit):
    def __init__(self):
        Emit.__init__(self)
        self.wiki_fname = 'apm.pdef.xml'
        self.f = open(self.wiki_fname, mode='w')
        self.preamble = '''<?xml version="1.0" encoding="utf-8"?>
<!-- Dynamically generated list of documented parameters (generated by param_parse.py) -->
'''
        self.f.write(self.preamble)
        self.paramfile = etree.Element('paramfile')
        self.vehicles = etree.SubElement(self.paramfile, 'vehicles')
        self.libraries = etree.SubElement(self.paramfile, 'libraries')
        self.current_element = self.vehicles

    def close(self):
        # etree.indent(self.paramfile)  # not available on thor, Ubuntu 16.04
        pretty_xml = etree.tostring(self.paramfile, pretty_print=True, encoding='unicode')
        self.f.write(pretty_xml)
        self.f.close()

    def emit_comment(self, s):
        self.f.write("<!-- " + s + " -->")

    def start_libraries(self):
        self.current_element = self.libraries

    def emit(self, g):
        xml_parameters = etree.SubElement(self.current_element, 'parameters', name=g.name)  # i.e. ArduPlane

        for param in g.params:
            # Begin our parameter node
            if hasattr(param, 'DisplayName'):
                xml_param = etree.SubElement(xml_parameters, 'param', humanName=param.DisplayName, name=param.name)  # i.e. ArduPlane (ArduPlane:FOOPARM)
            else:
                xml_param = etree.SubElement(xml_parameters, 'param', name=param.name)

            if hasattr(param, 'Description'):
                xml_param.set('documentation', param.Description)  # i.e. parameter docs
            if hasattr(param, 'User'):
                xml_param.set('user', param.User)  # i.e. Standard or Advanced

            if hasattr(param, 'Calibration'):
                xml_param.set('calibration', param.Calibration)

            # Add values as chidren of this node
            for field in param.__dict__.keys():
                if field not in ['name', 'DisplayName', 'Description', 'User'] and field in known_param_fields:
                    if field == 'Values' and Emit.prog_values_field.match(param.__dict__[field]):
                        xml_values = etree.SubElement(xml_param, 'values')
                        values = (param.__dict__[field]).split(',')
                        for value in values:
                            v = value.split(':')
                            if len(v) != 2:
                                raise ValueError("Bad value (%s)" % v)
                            # i.e. numeric value, string label
                            xml_value = etree.SubElement(xml_values, 'value', code=v[0])
                            xml_value.text = v[1]

                    elif field == 'Units':
                        abreviated_units = param.__dict__[field]
                        if abreviated_units != '':
                            units = known_units[abreviated_units]   # use the known_units dictionary to convert the abreviated unit into a full textual one
                            xml_field1 = etree.SubElement(xml_param, 'field', name=field)  # i.e. A/s
                            xml_field1.text = abreviated_units
                            xml_field2 = etree.SubElement(xml_param, 'field', name='UnitText')  # i.e. ampere per second
                            xml_field2.text = units
                    else:
                        xml_field = etree.SubElement(xml_param, 'field', name=field)
                        xml_field.text = param.__dict__[field]

            if xml_param.text is None and not len(xml_param):
                xml_param.text = '\n'  # add </param> on next line in case of empty element.
