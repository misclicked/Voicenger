# coding=utf-8
import re
from gtts import gTTS
import tempfile
from pygame import mixer
import langid
from fbchat import Client
from bs4 import BeautifulSoup
import requests
import tkinter as tk
from PIL import Image
from PIL import ImageTk
import webbrowser
import tkinter.messagebox
from tkinter import END
import threading
import logging
import sys
from msilib.schema import ListBox
from warnings import catch_warnings
from fbchat.models import *
import json

class PrintLogger(): # create file like object
    def __init__(self, labelText): # pass reference to text widget
        self.labelText = labelText # keep ref

    def write(self, text):
        if text.isspace() == False:
            self.labelText.set(text)

    def flush(self): # needed for file like object
        pass

def say(text):
    with tempfile.NamedTemporaryFile(delete=True) as temp:
        ttss = []
        flag = False
        lang = langid.classify(text)[0]
        if lang == 'zh':
            if lang == 'zh':
                lang = 'zh-tw'
                flag = True
        if flag == True:
            try:
                ttss.append(gTTS(text,'zh-tw'))
            except:
                ttss.append(gTTS(text))
        else:
            try:
                ttss.append(gTTS(text,lang))
            except:
                ttss.append(gTTS(text))
        filename = "{}.mp3".format(temp.name)
        with open(filename, 'wb') as fp:
            for tts in ttss:
                tts._tokenize = lambda text: [text]
                tts.write_to_fp(fp)
        mixer.init()
        mixer.music.load(filename)
        mixer.music.play()
        while mixer.music.get_busy() == True:
            continue
        mixer.quit()

# Subclass fbchat.Client and override required methods
class EchoBot(Client):
    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        self.markAsDelivered(thread_id, message_object.uid)
        self.markAsRead(thread_id)

        text = message_object.text
        if text == "":
            return
        if author_id != self.uid:
            if author_id in self.idName:
                name = self.idName[author_id]
            else:
                page = requests.get('https://www.facebook.com/'+author_id, cookies = self.session)
                name = BeautifulSoup(page.text, "lxml").title.string;
                self.idName[author_id] = name
            say(text)
            try:
                self.msglist.insert(END, name+": "+text)
            except Exception as ex:
                self.msglist.insert(END, name+": 訊息包含不支援之符號")
            self.msglist.yview(END)
        else:
            if(message_object.text == 'Logout'):
                self.logout()
                print("logged out")



window = tk.Tk()
window.title('Welcome to Voicenger')
window.geometry('500x400')

# welcome image
canvas = tk.Canvas(window, height=200, width=500)
img = Image.open('logo.png')
img = img.resize((200,200), Image.ANTIALIAS)
image_file = ImageTk.PhotoImage(img)
image = canvas.create_image(150,0, anchor='nw', image=image_file)
canvas.pack(side='top')
savedEmail = ""
savedPwd = ""
savedSaveOption = False
try:
    with open('config.json') as json_file:  
        data = json.load(json_file)
        savedEmail = data['config'][0]['email']
        savedPwd = data['config'][0]['password']
        savedSaveOption = data['config'][0]['save']
except:
    savedEmail = "example@gmail.com"
if savedEmail == "":
    savedEmail = "example@gmail.com"
    savedPwd = ""
    savedSaveOption = False
# user information
label_email = tk.Label(window, text='FB email: ')
label_email.place(x=95, y= 250)
label_pwd = tk.Label(window, text='Password: ')
label_pwd.place(x=95, y= 290)

var_usr_name = tk.StringVar()
var_usr_name.set(savedEmail)
entry_usr_name = tk.Entry(window, textvariable=var_usr_name)
entry_usr_name.place(x=205, y=250)
var_usr_pwd = tk.StringVar()
var_usr_pwd.set(savedPwd)
entry_usr_pwd = tk.Entry(window, textvariable=var_usr_pwd, show='*')
entry_usr_pwd.place(x=205, y=290)

def usr_login():
    def login():
        global client
        logined = False
        try:
            email = var_usr_name.get()
            pwd = entry_usr_pwd.get()
            client = EchoBot(email, pwd)
            client.session = client.getSession()
            client.idName = {}
            client.msglist = msglist
            hideAll()
            frame.pack()
            window.title('Welcome to Voicenger - logged as '+email)
            logined = True
            if saveStatus.get():
                data = {}
                data['config'] = []
                data['config'].append({
                    'email': email,
                    'password': pwd,
                    'save': True
                    })
                with open('config.json', 'w') as outfile:  
                    json.dump(data, outfile, indent=4)
            client.listen()
        except Exception as e:
            if logined == True:
                tk.messagebox.showinfo(title='Info', message='Logged Out')
            else:
                tk.messagebox.showinfo(title='Info', message=str(e))
            msglist.delete(0,END)
            logined = False
            frame.pack_forget()
            showAll()
            btn_login["state"] = "normal"
    btn_login["state"] = "disabled"
    t = threading.Thread(target = login)
    t.start()
def usr_sign_up():
    url = "https://www.facebook.com/r.php"
    webbrowser.open_new_tab(url)
def usr_logout():
    tk.messagebox.showinfo(title='Info', message='Please Log out via sending a message \"Logout\" to yourself.')
    url = "https://www.facebook.com/messages/t/"+client.uid
    webbrowser.open_new_tab(url)
    
saveStatus = tk.IntVar()
if savedSaveOption == True:
    saveStatus.set(1)
ckb_save_usr_info = tk.Checkbutton(window, text = "Save email and password", variable = saveStatus)
ckb_save_usr_info.place(x=190, y=305)

# login and sign up button
btn_login = tk.Button(window, text='Login', command=usr_login)
btn_login.place(x=170, y=330)
btn_sign_up = tk.Button(window, text='Sign up', command=usr_sign_up)
btn_sign_up.place(x=270, y=330)

labelText = tk.StringVar()
depositLabel = tk.Label(window, textvariable=labelText)
depositLabel.place(x=0,y=380)
pl = PrintLogger(labelText)
sys.stdout = pl
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

frame = tk.Frame(window)
frame.pack()

msglist = tk.Listbox(frame, width = 40, height = 10)
msglist.pack(side="left", fill="y")

scrollbar = tk.Scrollbar(frame, orient="vertical")
scrollbar.config(command=msglist.yview)
scrollbar.pack(side="right", fill="y")



btn_logout = tk.Button(window, text='Logout', command=usr_logout)
btn_logout.pack(side="right")

btn_logout.pack_forget()
frame.pack_forget()

    
def showAll():  
    btn_login.place(x=170, y=330)
    btn_sign_up.place(x=270, y=330)
    entry_usr_pwd.place(x=205, y=290)
    entry_usr_name.place(x=205, y=250)
    label_email.place(x=95, y= 250)
    label_pwd.place(x=95, y= 290)
    btn_logout.pack_forget()
def hideAll():
    btn_login.place_forget()
    btn_sign_up.place_forget()
    entry_usr_pwd.place_forget()
    entry_usr_name.place_forget()
    label_email.place_forget()
    label_pwd.place_forget()
    btn_logout.pack(side="right")
    
    
window.mainloop()

