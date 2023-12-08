import asyncio
import binascii
import os
import random
import socket
import string
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import imaplib
import email
import base64

'''
Скрипт проверки доступности почтового сервера Communigate
dns имя и имя главного домена должно быть в serv_dict
На вход передаются логин(без домена) и пароль УЗ 
Скрипт генерирует 3 сообщения со случайным текстом

'''
# Количество проверок
count_request = 3
time_out = 5

# Файл для записи резульататов
file_result = 'imap_chek'
# Файл для логов ошибок
error_log_file = 'imap_chek_error'
# Параметры входа для отправки/проверки письма
imap_login = ''
imap_pass = ''
# Area01
serv_dict = {'Area01-1': '1',
             'Area01-2': '2',
             # Area02
             'Area02-1': '1',
             'Area02-2': '2',
             }


def check_date():
    if os.path.exists(file_result):
        with open(file_result, mode='r') as f:
            if f.readline().split(' ')[0] != str(datetime.now().strftime("%d-%b-%Y")):
                with open(file_result, 'w') as f1:
                    f1.write('')
    if os.path.exists(error_log_file):
        with open(error_log_file, 'r') as f:
            if f.readline().split(' ')[0] != str(datetime.now().strftime("%d-%b-%Y")):
                with open(error_log_file, 'w') as f1:
                    f1.write('')


def err_log(data):
    with open(error_log_file, 'a') as log_file:
        log_file.write(f'{datetime.now().strftime("%d-%b-%Y %H:%M")}: {data} \n')


# Подключение к smtp серверу
def smtp_con(login, passwd):
    smtp_srv = smtplib.SMTP('localhost', port=25, timeout=5)
    smtp_srv.login(login, passwd)
    return smtp_srv


# генерация сообщения
def creat_msg(email_from, email_to, message_text):
    # Создание объекта сообщения
    msg_to_send = MIMEMultipart()

    # Настройка параметров сообщения
    msg_to_send["From"] = email_from
    msg_to_send["To"] = email_to
    msg_to_send["Subject"] = "Monitoring test message"

    msg_to_send.attach(MIMEText(message_text, "plain"))

    return msg_to_send


def imap_search(imap, compare_body, compare_sender):
    '''
    Функция ищет письмо письмо в ящике
    :param imap: сервер imap
    :param compare_body: тело сообщения
    :param compare_sender: отправитель
    :return: Найдено/Не найдено
    '''
    result = False
    try:
        imap.select("INBOX")
        uid_array = (imap.uid('search', "ALL"))[1][0].decode().split(' ')
        for uid in uid_array:
            msg_imap = imap.uid('fetch', uid, '(RFC822)')[1]
            msg_imap = email.message_from_bytes(msg_imap[0][1])
            # Отправитель
            msg_recever = msg_imap["Return-path"].replace('<', '').replace('>', '')
            if msg_recever != compare_sender: continue
            # Тело письма
            msg_body = ''
            for part in msg_imap.walk():
                if part.get_content_maintype() == 'text' and part.get_content_subtype() == 'plain':
                    try:
                        msg_body = (base64.b64decode(part.get_payload()).decode())
                    except binascii.Error as err:
                        msg_body = part.get_payload()
                    except UnicodeDecodeError as err:
                        msg_body = part.get_payload()
            if msg_body == compare_body and msg_recever == compare_sender:
                imap.uid('store', uid, '+flags \Deleted')
                result = True
                break
    except imaplib.IMAP4.error as err:
        err_log(err)
    finally:
        return result


async def main():
    '''
    Создаём письмо.
    Отправляем по SMTP
    Ищем в течении 60 сек

    :return: Время затраченное на поиск письма в сек
    '''
    res = False
    start_time = datetime.now()
    try:
        # Коннектимся к smtp
        smtp_server = smtp_con(server, imap_login, imap_pass)
        try:
            # Генерим уникальный текст
            message = ''.join(random.choice(string.ascii_letters + ' ') for _ in range(100))
            # Формируем письмо
            msg = creat_msg(imap_login, imap_login, message)
            # Отправка письма
            smtp_server.sendmail(imap_login, imap_login, msg.as_string())
            # Создаём IMAP подключение
            imap = imaplib.IMAP4_SSL(server)
            imap.login(imap_login, imap_pass)
            # Ищем time_out секунд засыпая каждый раз на 1сек.
            for i in range(1, time_out + 1):
                if imap_search(imap, message, imap_login):
                    res = True
                    break
                else:
                    await asyncio.sleep(1)
            # Выполяем логаут
            imap.expunge()
            imap.logout()
        except imaplib.IMAP4.error as err:
            err_log(err)
        finally:
            # Закрытие соединения
            smtp_server.quit()
    except TimeoutError:
        err_log('TimeoutError')
    except ConnectionRefusedError:
        err_log('ConnectionRefusedError')
    except smtplib.SMTPAuthenticationError as err:
        err_log(err.__dict__['smtp_error'].decode())
    # Проверяем если не нашли письмо то время ставим максимум
    if not res:
        job_time = 99999999
    else:
        job_time = (datetime.now() - start_time).microseconds / 1000
    return job_time


async def job_run(con):
    result_request = []
    async_dickt = {f'task{item}': asyncio.create_task(main()) for item in range(1, con + 1)}
    for i in range(1, con + 1):
        result_request.append(await async_dickt[f'task{i}'])
    return result_request


if __name__ == "__main__":
    # Проверяем файлы логов
    check_date()
    domen = serv_dict.get(socket.getfqdn().lower(), None)
    if domen is None:
        err_log('This server not in array')
        quit()
    server = socket.getfqdn().lower()
    imap_login += f'@{domen}'
    value = asyncio.run(job_run(count_request))
    value = round(sum(value) / count_request, )
    # Запись результата в файл
    with open(file_result, mode='a') as f:
        f.write(f'{datetime.now().strftime("%d-%b-%Y %H:%M")}={str(value)}\n')
