from fabric.core.service import Service, Signal, Property

class AudioService(Service):
    def __init__(self):
        super().__init__()
