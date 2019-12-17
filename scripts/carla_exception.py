class RestartTask(Exception):
    """Restart the simulation task in case the driver gets stuck"""
    pass


class NextTask(Exception):
    """Continue with the next task if you are in the final location"""
    pass


class LastTask(Exception):
    """Last task in the level where cyberattack will be performed"""
    pass
