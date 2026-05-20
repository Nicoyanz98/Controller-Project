from abc import abstractmethod

class JoystickInput():    
    def __init__(self, name, data, symbol=None):
        self.name = name
        self.data = data
        if symbol:
            self.symbol = symbol
        else:
            self.symbol = name.replace('_', ' ').capitalize()
    
    @abstractmethod
    def resolve_for(self, map, controller_type):
        self.data.get_value_for(map, controller_type)

class JoystickData():
    def __init__(self, value):
        self.type_dependant = isinstance(value, list)
        self.value = value

    def _value_for(self, controller_type):
        return self.value[controller_type] if self.type_dependant else self.value

    @abstractmethod
    def get_value_for(self, map, controller_type):
        pass
    
class StickData(JoystickData):
    def get_value_for(self, map, controller_type):
        map.resolve_stick(self._value_for(controller_type))

class ButtonData(JoystickData):
    def get_value_for(self, map, controller_type):
        map.resolve_button(self._value_for(controller_type))

class DpadData(JoystickData):
    def get_value_for(self, map, controller_type):
        map.resolve_dpad(self._value_for(controller_type))

class TriggerData(JoystickData):
    def get_value_for(self, map, controller_type):
        map.resolve_trigger(self._value_for(controller_type))