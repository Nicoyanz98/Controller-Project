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
        return self.data.get_value_for(map, controller_type)

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
        return map.resolve_stick(self._value_for(controller_type))

class ButtonData(JoystickData):
    def get_value_for(self, map, controller_type):
        return map.resolve_button(self._value_for(controller_type))

class DpadData(JoystickData):
    def get_value_for(self, map, controller_type):
        return map.resolve_dpad(self._value_for(controller_type))

class TriggerData(JoystickData):
    def get_value_for(self, map, controller_type):
        return map.resolve_trigger(self._value_for(controller_type))
    
class JoystickCombination(JoystickInput):
    def __init__(self, name, combo):
        symbol = "+".join([joystick_input.symbol for joystick_input in combo])
        super().__init__(name, combo, symbol)
    
    def resolve_for(self, map, controller_type):
        pressed = True
        for joystick_input in self.data:
            pressed = pressed and joystick_input.resolve_for(map, controller_type)
        return pressed