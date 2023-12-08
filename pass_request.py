import sys
import socket
from tkinter import *
from tkinter import messagebox
from tkinter import ttk


def srv_check():
    """Проверка доступности серверов на площадках"""
    area01 = ["srv01", "srv02"]
    area02 = ["srv01", "srv02"]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    n = 0
    while n < len(area01) or n < len(area02):
        try:
            s.connect((area01[n], 106))
        except socket.error:
            area01.pop(n)
            try:
                s.connect((area02[n], 106))
            except socket.error:
                area02.pop(n)
            else:
                print('Работает площадка area02')
                working_servers = area02
                break
        else:
            print('Работает площадка area01')
            working_servers = area01
            break

    if "working_servers" not in vars():
        print('Беда! Ничего не работает')
        sys.exit()
    else:
        return working_servers


def request_pass():
    """Данная фунция вызывает окно ввода логина и пароля, а так же возможность выбора сервера активной площадки из списка"""
    working_servers = srv_check()
    srv_pass, srv_login, srv = "", "", ""

    def save_quit():
        global srv_pass, srv_login, srv
        srv_pass = input_pass.get()
        srv_login = input_login.get()
        srv = combobox.get()
        if len(srv_pass) > 0 and len(srv_login) > 0:
            app.destroy()
        else:
            messagebox.showerror('ОШИБКА', 'Введите данные')

    app = Tk()
    app.title('Ввод логина пароля')
    Label(app, text='Выберите Server').pack()
    cgp_serve_var = StringVar(value=working_servers[0])
    combobox = ttk.Combobox(app, textvariable=cgp_serve_var, values=working_servers)
    combobox.pack()
    Label(app, text='В ведите логин и пароль').pack()
    f_top = Frame(app)
    f_bot = Frame(app)
    input_pass = StringVar()
    input_login = StringVar()
    label_login = Label(f_top, text='Login')
    loginEntry = Entry(f_top, textvariable=input_login)
    f_top.pack()
    label_login.pack(side=LEFT)
    loginEntry.pack(side=LEFT)
    label_pass = Label(f_bot, text='Pass CGP')
    passEntry = Entry(f_bot, textvariable=input_pass, show='*')
    f_bot.pack()
    label_pass.pack(side=LEFT)
    passEntry.pack(side=LEFT)
    Button(app, text='Send', command=save_quit).pack(side=LEFT)
    Button(app, text='Exit', command=app.destroy).pack(side=RIGHT)
    app.mainloop()
    if (len(srv_pass) > 0 and len(srv_login)) > 0:
        return srv, srv_login, srv_pass
    else:
        return 'Выход'


if __name__ == "__main__":
    print(request_pass())


def returnDataProd():
    """ Данная функция возращает список серверов активной площадки и логин, пароль для них"""
    return_servers = srv_check()
    return_login = ''
    return_pass = ''
    return return_servers, return_login, return_pass
