from functools import partial

import hou
from PySide2 import QtCore, QtUiTools, QtWidgets, QtGui


def get_object_lights():
    result = []
    for type_name, node_type in hou.objNodeTypeCategory().nodeTypes().items():
        name_part = hou.hda.componentsFromFullNodeTypeName(type_name)[2]
        if "light" in name_part:
            result.extend(node_type.instances())
    return result


def get_lights():
    obj_types = hou.objNodeTypeCategory().nodeTypes().values()
    light_types = []
    for obj_type in obj_types:
        try:
            extra_nfo = obj_type.definition().extraInfo()
        except AttributeError:
            continue
        if extra_nfo.find("subtype=light") != -1:
            light_types.append(obj_type)

    result = []
    for light_type in light_types:
        result.extend(light_type.instances())
    return result


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.lights = get_object_lights()  # or get_lights()
        self.toggles = {}

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.setGeometry(800, 200, 550, 650)
        self.setWindowTitle('Light Mixer')
        
        self.button = QtWidgets.QPushButton("List lights")
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.button)
        self.main_layout.addSpacing(20)

        for light in self.lights:
            light_layout = QtWidgets.QVBoxLayout()
            light_details = QtWidgets.QHBoxLayout()

            # print(light)
            light_label = QtWidgets.QLabel(light.path())
            
            #disbale light checkbox
            checks  = QtWidgets.QVBoxLayout()
            check = QtWidgets.QCheckBox("Enabled", self)
            check.stateChanged.connect(
                partial(
                    self.set_value,
                    node_path=light.path(),
                    parameter="light_enable"
                ))
            check.toggle()
            self.toggles[light.name()] = {} 
            self.toggles[light.name()]['enable'] = check
            checks.addWidget(check)

            #isolate light checkbox
            # isolate  = QtWidgets.QHBoxLayout()
            check2 = QtWidgets.QCheckBox("Isolate", self)
            self.toggles[light.name()]['iso'] = check2
            check2.clicked.connect(
                partial(
                    self.isolate_light,
                    node_path=light.path(),
                    parameter="light_enable",
                ))
            checks.addWidget(check2)
            

            #light intensity
            intense_box = QtWidgets.QHBoxLayout()
            parm_label2 = QtWidgets.QLabel("light_intensity")
            spinbox2 = QtWidgets.QDoubleSpinBox()
            spinbox2.setMinimum(-10)
            spinbox2.setMaximum(10)
            spinbox2.setSingleStep(.5)
            spinbox2.setValue(light.parm("light_intensity").eval())
            spinbox2.valueChanged.connect(
                partial(
                    self.set_value,
                    node_path=light.path(),
                    parameter="light_intensity"
                )
            )
            intense_box.addWidget(parm_label2)
            intense_box.addWidget(spinbox2)

            #light exposure
            exp_box = QtWidgets.QHBoxLayout()
            parm_label = QtWidgets.QLabel("light_exposure")
            spinbox = QtWidgets.QDoubleSpinBox()
            spinbox.setMinimum(-10)
            spinbox.setMaximum(10)
            spinbox.setValue(light.parm("light_exposure").eval())
            spinbox.valueChanged.connect(
                partial(
                    self.set_value,
                    node_path=light.path(),
                    parameter="light_exposure"
                )
            )
            exp_box.addWidget(parm_label)
            exp_box.addWidget(spinbox)

            spin_box = QtWidgets.QVBoxLayout()
            spin_box.addLayout(intense_box)
            spin_box.addLayout(exp_box)
            

            #color picker
            color_layout = QtWidgets.QHBoxLayout()
            color_button = QtWidgets.QPushButton("") 
            
            #get current color from houdini
            current_color = QtGui.QColor()  
            current_color.setRedF(light.parm('light_colorr').eval())
            current_color.setGreenF(light.parm('light_colorg').eval())
            current_color.setBlueF(light.parm('light_colorb').eval())  
            
            color_button.setStyleSheet(f"background-color: rgb({light.parm('light_colorr').eval() * 255}, {light.parm('light_colorg').eval() * 255}, {light.parm('light_colorb').eval() * 255}); border-radius: 10px ;")
            color_button.setFixedSize(50, 50)
            color_button.clicked.connect(
                partial(
                    self.select_color,
                    light,
                    button=color_button,
                    current=current_color
                ))  
            color_layout.addWidget(color_button)
        
            #horizontal line
            h_line = QtWidgets.QFrame()
            h_line.setFrameShape(QtWidgets.QFrame.HLine)
            h_line.setFrameShadow(QtWidgets.QFrame.Sunken)

            #order the widgets will be added to the main vertical layout
            light_layout.addWidget(light_label)
            light_details.addSpacing(20)
            light_details.addLayout(checks)
            light_details.addLayout(spin_box)
            light_details.addSpacing(50)
            light_details.addLayout(color_layout)
            light_details.addSpacing(20)
            light_layout.addLayout(light_details)
            light_layout.addSpacing(20)
            light_layout.addWidget(h_line)
            light_layout.addStretch()
            self.main_layout.addLayout(light_layout)


    def connect_signals(self):
        self.button.clicked.connect(self.button_clicked)

    def button_clicked(self):
        print(self.lights)

    def set_value(self, value, node_path=None, parameter=None):
        light = hou.node(node_path)
        light.parm(parameter).set(float(value))

    def isolate_light(self, node_path=None, parameter=None):
        iso_light = hou.node(node_path)

        for light in self.lights:
            if self.toggles[iso_light.name()]['iso'].isChecked():
                if light == iso_light:
                    #set checkbox on enabled for selected light to checked in ui
                    self.toggles[light.name()]['enable'].setChecked(True)
                    #set enabled in Houdini
                    light.parm(parameter).set(2)
                else:
                    #disable checkbox for all other lights in ui
                    self.toggles[light.name()]['enable'].setChecked(False)
                    self.toggles[light.name()]['iso'].setChecked(False)
                    #disable in Houdini
                    light.parm(parameter).set(0)
            else:
                self.toggles[light.name()]['enable'].setChecked(True)
                light.parm(parameter).set(2)
    
    def select_color(self, light, button, current):

        color = QtWidgets.QColorDialog.getColor(current)

        if color.isValid():
            # show in widget
            button.setStyleSheet(f"background-color: rgb({color.redF() * 255}, {color.greenF() * 255}, {color.blueF() * 255}); border-radius: 10px ;")      
            
            #set parms in houdini
            light.parm("light_colorr").set(float(color.redF()))
            light.parm("light_colorb").set(float(color.blueF()))
            light.parm("light_colorg").set(float(color.greenF()))

    
def run():
    my_widget = MyWidget()
    my_widget.show()