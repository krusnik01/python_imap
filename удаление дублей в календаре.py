import email
import os
import pass_request
import sys
from datetime import datetime
import imaplib
from email.header import decode_header
from My_python_utils import ModuleLogs, read_csv

'''
Данный скрипт чистит календарь от:
    дублей,
    криво перенесенных встреч,
    а так же Canceled
'''
# константы
folders = ['Calendar', '&BBoEMAQ7BDUEPQQ0BDAEQARM-']
start_time = datetime.now()
max_size = 200 * 1024 * 1024  # мб в килобайты
# Если запуск руками то меняем на False
inposh = True


# Чистим каледарь
def clear_calendar(target_account):
    """
    Получаем аккаунт, для него создаётся отдельный лог
    парсится две папки из массива folders, если папки нет то пропускаем.
    Для каждой папки получаем список uid сообщений,
    если сообщение больше max_size то пропускаем его.

    """
    # Счётчики
    con_double, con_cancel, con_exch, skip = 0, 0, 0, 0
    acc_logs = ModuleLogs(f"{def_path_logs}\{os.path.basename(__file__).replace('.py', '')}", target_account)
    acc_logs.wr_log(f'Работаю с {target_account}')
    for folder in folders:
        event_dict = {}
        to_del = set()
        # Пытаемся зайти в папку календаря
        try:
            result = list(imap.select(f'~{target_account}/{folder}'))
        except imaplib.IMAP4.error as imap_err:
            acc_logs.wr_log(f'херня какая то {imap_err}')
            continue
        except imaplib.IMAP4.abort:
            return False
        # Если результат No то в след
        if result[0] == 'NO': continue
        # Получаем все uid
        try:
            msg_uid = imap.uid('search', 'all')[1][0].decode().split(' ')
        except imaplib.IMAP4.abort:
            return False
        acc_logs.wr_log(f'Всего событий {len(msg_uid)}')
        # Бежим по массиву uid
        for uid in msg_uid:
            acc_logs.wr_log(f'pars {uid}')
            # Скипаем события больше max_size
            try:
                msg_size = imap.uid('fetch', uid, '(RFC822.SIZE)')[1][0].decode()
            except AttributeError:
                continue
            except ValueError:
                continue
            except imaplib.IMAP4.abort:
                return False
            msg_size = (msg_size[msg_size.find('(') + 1:msg_size.rfind(')')].split(' '))[1]
            if int(msg_size) >= max_size:
                skip += 1
                continue

            # Получаем целое сообщение
            try:
                msg_imap = imap.uid('fetch', uid, '(RFC822)')[1]
            except imaplib.IMAP4.abort:
                return False
            try:
                msg_imap = email.message_from_bytes(msg_imap[0][1])
            except TypeError:
                continue

            # Получаем Subject
            try:
                Subject = (decode_header(msg_imap['Subject'])[0][0].decode()).lower()
            except AttributeError:
                Subject = (msg_imap['Subject'])
            except TypeError:
                Subject = (msg_imap['Subject'])
            except UnicodeDecodeError:
                Subject = (msg_imap['Subject'])

            # Если с Subject что то не так то удаляем либо пропускам
            if Subject is None:
                continue
            if 'Retrieval using the IMAP4' in Subject:
                con_exch += 1
                to_del.add(uid)
                continue
            if 'canceled:' in Subject:
                con_cancel += 1
                to_del.add(uid)
                continue

            # Получаем From
            try:
                From = (decode_header(msg_imap['From'])[0][0].decode()).lower()
            except AttributeError:
                From = msg_imap['From']
            except TypeError:
                From = msg_imap['From']
            # Если с From что то не так то пропускам
            if From is None:
                continue
            else:
                From = From.lower()

            # Получаем DTSTAMP
            ics_text = ''
            for part in msg_imap.walk():
                if part.get_content_subtype() == 'calendar' and part.get_content_maintype() == 'text':
                    ics_text = part.get_payload()
            # Обрезаем начало
            if len(ics_text) > 1:
                ics_text = ics_text[ics_text.find('DTSTAMP'):]
                DTSTAMP = ics_text[:ics_text.find('\n')]
            else:
                DTSTAMP = ''

            # Всё нормальные события добавляем в словарь
            event_dict[uid] = [Subject, From.lower(), DTSTAMP.lower()]

            # Перебираем словарь, ищем повторы
        while True:
            try:
                t_key, t_value = (event_dict.popitem())
                for key, value in event_dict.items():
                    if t_value[:-1] == value[:-1]:
                        acc_logs.wr_log(f"{t_key} и {key} равны")
                        if t_value[-1] == value[-1] or t_value[-1] > value[-1]:
                            acc_logs.wr_log(f'Удаляем {key}')
                            to_del.add(key)
                            con_double += 1
                        else:
                            acc_logs.wr_log(f'Удаляем {t_key}')
                            to_del.add(t_key)
                            con_double += 1
                            break
            except KeyError:
                break

        acc_logs.wr_log(f'К удалению {len(to_del)}')
        acc_logs.wr_log(f'double={con_double}, cancel={con_cancel}, broken={con_exch}, skip={skip}')
        global_log.wr_log(
            f'acc={target_account},всего событий {len(msg_uid)}, К_удалению={len(to_del)}, double={con_double}, cancel={con_cancel}, broken={con_exch}, skip={skip}',
            to_print=True)
        # Удаляем всё отобранные события
        for uid in to_del:
            try:
                acc_logs.wr_log(imap.uid('store', uid, '+flags \Deleted'))
            except imaplib.IMAP4.abort:
                return False

    acc_logs.wr_log('Очищаем помеченые дубли')
    try:
        acc_logs.wr_log(imap.expunge())
    except imaplib.IMAP4.error as err:
        acc_logs.wr_log(f'херня какая то {err}')
    except imaplib.IMAP4.abort:
        return False

    # Всегда пробуем закрыть папку/сессию с пользователем
    try:
        imap.close()
    except imaplib.IMAP4.error:
        return True
    except imaplib.IMAP4.abort:
        return False
    return True


def check_posh(check):
    if check:
        ############################################################################
        ##Запускаем из поша
        ############################################################################
        # Путь до логов
        def_path_logs = sys.argv[1]
        # Какой аккаунт чистить?
        target = sys.argv[2]
        domen = sys.argv[3]
    else:
        ############################################################################
        ##Запускаем из руками
        ############################################################################
        # Какой аккаунт чистить?
        target = input('Какой аккаунт чистить?\n')
        def_path_logs = os.path.dirname(os.path.abspath(__file__)) + r'\Logs'
        domen = input('Введите домен\n')
    return def_path_logs, target, domen


def imap_con():
    imap_serv = None
    srv, srv_login, srv_passwd = pass_request.returnDataProd()
    for i in range(len(srv) + 1):
        imap_serv = imaplib.IMAP4(srv[i])
        try:
            imap_serv.login(user=srv_login, password=srv_passwd)
            # Включаем рассширеный режим
            imap_serv.enable("EXTENSIONS")
            global_log.wr_log(f"Используется {srv[i]}", to_print=True)
            break
        except imaplib.IMAP4.error as err:
            imap_serv = None
            continue
    return imap_serv


if __name__ == "__main__":
    def_path_logs, target, domen = (check_posh(inposh))

    # Общий лог
    global_log = ModuleLogs(fr"{def_path_logs}\{os.path.basename(__file__).replace('.py', '')}")
    try:
        # подключение к первому свободному серверу по imap
        imap = imap_con()
        if imap is None:
            raise IOError('no imap server')
        # в зависимости от того что передали в target действуем по разному
        if '@' in target:
            clear_calendar(target)
        elif '.csv' in target:
            CSVFile = read_csv(target)
            while True:
                try:
                    acc = next(CSVFile)['account']
                    if not clear_calendar(f'{acc}@{domen}'):
                        imap = imap_con()
                        if imap is None:
                            raise IOError('no imap server')
                except StopIteration:
                    break
    except IOError:
        global_log.wr_log(f'Сервер для подключения не найден')
    finally:
        if 'imap' in locals():
            # Всегда пробуем выйти
            imap.logout()
        if 'global_log' in locals():
            global_log.wr_log(f"Время работы скрипта : {(datetime.now() - start_time)}", to_print=True)
