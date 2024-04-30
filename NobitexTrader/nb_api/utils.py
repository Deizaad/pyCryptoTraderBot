import os


__all__ = ["clear_console"]


# Clear console function
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')