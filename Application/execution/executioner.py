import asyncio


from Application.configs.config import Executioner as exe
from Application.data.data_manager import DataManager


# class Executioner:
# Define jobs and their order based on ExecutionMode
if exe.MODE == 'live':
    def job():


elif exe.MODE == 'backtest':
    def job():


elif exe.MODE == 'forwardtest':
    def job():


elif exe.MODE == 'setuptest':
    def job():


else:



def main():
    data = DataManager()
    data.initiate()
    data.live_update()


    job()

if __name__ == '__main__':
    main()