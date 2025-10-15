class NeedsYaw:
    def yaw(self, angle: float) -> 'NeedsPitch':
        return NeedsPitch(angle)


class NeedsPitch:
    def __init__(self, yaw: float):
        self._yaw = yaw

    def pitch(self, angle: float) -> 'NeedsRoll':
        return NeedsRoll(self._yaw, angle)


class NeedsRoll:
    def __init__(self, yaw: float, pitch: float):
        self._yaw = yaw
        self._pitch = pitch

    def roll(self, angle: float) -> 'Complete':
        return Complete(self._yaw, self._pitch, angle)


class Complete:
    def __init__(self, yaw: float, pitch: float, roll: float):
        self._yaw = yaw
        self._pitch = pitch
        self._roll = roll

    def build(self) -> 'Rotation':
        return Rotation(self._yaw, self._pitch, self._roll)


class Rotation:
    def __init__(self, yaw: float, pitch: float, roll: float):
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def __repr__(self) -> str:
        return f'Rotation(yaw={self.yaw}, pitch={self.pitch}, roll={self.roll})'


rotation = NeedsYaw().yaw(90.0).pitch(45.0).roll(30.0).build()
print(rotation)
