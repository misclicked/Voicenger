# coding=utf-8
from gtts import gTTS
import re
import tempfile
import playsound
import langid
from fbchat import Client, Message, ThreadType
from bs4 import BeautifulSoup
import requests
import tkinter as tk
from PIL import Image
from PIL import ImageTk
import webbrowser
import tkinter.messagebox
from tkinter import END
import logging
import sys
import json
import threading
import clipboard

class PrintLogger(): # create file like object
    def __init__(self, labelText): # pass reference to text widget
        self.labelText = labelText # keep ref

    def write(self, text):
        if text.isspace() == False:
            self.labelText.set(text)

    def flush(self): # needed for file like object
        pass

def say(text, name):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    with tempfile.NamedTemporaryFile(delete=True) as temp:
        ttss = []
        langName = langid.classify(name)[0]
        if langName == 'zh':
            if langName == 'zh':
                langName = 'zh-tw'
        if re.match(regex, text) is not None:
            ttss.append(gTTS(name, langName))
            ttss.append(gTTS('傳送了一個連結', 'zh-tw'))
        else:
            try:
                lang = langid.classify(text)[0]
                if lang == 'zh':
                    if lang == 'zh':
                        lang = 'zh-tw'
                ttss.append(gTTS(text,lang))
            except:
                try:
                    ttss.append(gTTS(text))
                except:
                    ttss.append(gTTS(name, langName))
                    ttss.append(gTTS('傳送了一則非文字訊息', 'zh-tw'))
        filename = "{}.mp3".format(temp.name)
        with open(filename, 'wb') as fp:
            for tts in ttss:
                try:
                    tts._tokenize = lambda text: [text]
                    tts.write_to_fp(fp)
                except:
                    ttss.append(gTTS('ERROR', 'zh-tw'))
        return threading.Thread(target = lambda :playsound.playsound(filename, True))


# Subclass fbchat.Client and override required methods
class VoiceBot(Client):
    Debug = False
    idName = {}
    session = None
    msglist = None
    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        self.markAsDelivered(thread_id, message_object.uid)
        #self.markAsRead(thread_id)
        text = message_object.text
        if text == "":
            return
        if (author_id != self.uid) or self.Debug:
            if author_id in self.idName:
                name = self.idName[author_id]
            else:
                page = requests.get('https://www.facebook.com/'+author_id, cookies = self.session)
                name = BeautifulSoup(page.text, "lxml").title.string
                self.idName[author_id] = name
            self.sayThread = say(text, name)
            self.sayThread.start()
            try:
                self.msglist.insert(END, name+": "+text)
            except Exception as ex:
                self.msglist.insert(END, name+": 訊息包含不支援之符號")
            if DNDStatus.get() and thread_type is not ThreadType.GROUP:
                self.send(Message(text="Auto reply: "+DNDStr), thread_id=thread_id, thread_type=thread_type)
            self.msglist.data.append([thread_id, thread_type, name, message_object.text])
            self.msglist.yview(END)
            self.sayThread.wait()
        else:
            if(message_object.text == 'Logout'):
                self.logout()
                print("logged out")



window = tk.Tk()
window.title('Welcome to Voicenger')
window.geometry('500x450')

# welcome image
canvas = tk.Canvas(window, height=200, width=500)
img = Image.open('logo.png')
img = img.resize((200,200), Image.ANTIALIAS)
image_file = ImageTk.PhotoImage(img)
image = canvas.create_image(150,0, anchor='nw', image=image_file)
canvas.pack(side='top')
try:
    with open('config.json') as json_file:  
        data = json.load(json_file)
        if 'config' not in data:
            savedEmail = "example@gmail.com"
            savedPwd = ""
            savedSaveOption = False
            DNDStr = "This user is now in DND mode."
        else:
            if 'email' not in data['config'][0]:
                savedEmail = "example@gmail.com"
            else:
                savedEmail = data['config'][0]['email']
            if 'password' not in data['config'][0]:
                savedPwd = ""
            else:
                savedPwd = data['config'][0]['password']
            if 'save' not in data['config'][0]:
                savedSaveOption = False
            else:
                savedSaveOption = data['config'][0]['save']
            if 'DNDStr' not in data['config'][0]:
                DNDStr = "This user is now in DND mode."
            else:
                DNDStr = data['config'][0]['DNDStr']
        if 'dev' not in data:
            Debug = False
        else:
            if 'Debug' not in data['dev'][0]:
                Debug = False
            else:
                Debug = data['dev'][0]['Debug']
except:
    savedEmail = "example@gmail.com"
    savedPwd = ""
    savedSaveOption = False
    Debug = False

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
        global logined
        logined = False
        try:
            email = var_usr_name.get()
            pwd = entry_usr_pwd.get()
            client = VoiceBot(email, pwd)
            client.session = client.getSession()
            client.idName = {}
            msglist.data = []
            client.msglist = msglist
            client.Debug = Debug
            hideAll()
            frame.pack()
            window.title('Voicenger - Login as '+email)
            logined = True
            if saveStatus.get():
                data = {}
                data['config'] = []
                data['config'].append({
                    'email': email,
                    'password': pwd,
                    'save': True,
                    'DNDStr': DNDStr
                    })
                data['dev'] = []
                data['dev'].append({
                    'Debug': Debug,
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
    client.stopListening()
    client.logout()
    tk.messagebox.showinfo(title='Info', message='Logged Out')
    msglist.delete(0,END)
    frame.pack_forget()
    showAll()
    btn_login["state"] = "normal"
    
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
depositLabel.place(x=0,y=430)
pl = PrintLogger(labelText)
sys.stdout = pl
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

frame = tk.Frame(window)
frame.pack()

def onSelect(evt):
    w = evt.widget
    index = int(w.curselection()[0])
    value = w.get(index)
    clipboard.copy(w.data[index][3])
    print(f'You selected item {value}, message copied to clipboard')
    #threading.Thread(target = lambda :client.send(Message(text="test"), thread_id=w.data[index][0], thread_type=w.data[index][1])).start()


msglist = tk.Listbox(frame, width = 45, height = 10)
msglist.bind('<<ListboxSelect>>', onSelect)

scrollbary = tk.Scrollbar(frame, orient="vertical")
scrollbary.config(command=msglist.yview)

scrollbarx = tk.Scrollbar(frame, orient="horizontal")
scrollbarx.config(command=msglist.xview)

DNDStatus = tk.IntVar()
ckb_save_usr_info = tk.Checkbutton(frame, text = "DND mode", variable = DNDStatus)

ckb_save_usr_info.pack(side="bottom")
scrollbarx.pack(side="bottom", fill="x")
msglist.pack(side="left", fill="y")
scrollbary.pack(side="right", fill="y")




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

threading.Thread(target=lambda:(
    langid.classify("This is a test"),
    langid.classify("測試"))).start()
window.mainloop()
if 'client' in globals() :
    client.stopListening()
    client.logout()
sys.exit()
