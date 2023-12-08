import csv, os, inspect
from datetime import datetime


# Чтение csv файла
def read_csv(CSVFile):
    with open(CSVFile, encoding='UTF-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            yield row


# Модуль логирования
class ModuleLogs:
    def __init__(self, path_logs='', file_name=inspect.stack()[-1][1].split('\\')[-1].replace(".py", "")):
        if len(path_logs) > 0:
            path_logs += '\\'
            if not os.path.exists(path_logs):
                os.makedirs(path_logs)

        self.path_logs = f'{path_logs}{file_name}_{datetime.now().strftime("%Y.%m.%d")}-1.log'
        while os.path.isfile(self.path_logs):
            self.path_logs = self.path_logs[:-5] + str(int(self.path_logs[-5]) + 1) + self.path_logs[-4:]

    def wr_log(self, data, to_print=False):
        open_file = open(self.path_logs, 'a')
        open_file.write(f'{datetime.now().strftime("%d-%b-%Y %H:%M")}: {data} \n')
        open_file.close()
        if to_print:
            print(data)


if __name__ == "__main__":
    pass
