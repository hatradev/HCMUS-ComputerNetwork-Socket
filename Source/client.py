from re import I
import socket
import os

from tkinter import *
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.ttk import *
from tkinter import Scrollbar, messagebox
from PIL import ImageTk,Image

#BASE SOCKET CONNECTION
HOST = "127.0.0.1"
PORT = 8000
ADDRESS = (HOST, PORT)
FORMAT = "utf8"
FONT = 'Times New Roman'
SIZE = 14

#ACTION
LOGIN = 'login'
LOGOUT = 'logout'
ORDER = 'order'
EXTRA = 'extra order'
STOP_CONNECTION = 'stop'

OK = 'True'
NO = 'False'
LOSE = 'LOSE'

#-----------------------DATA-----------------------#
def convertToMenu(menu):
    Menu = []
    temp = menu.split(".")
    for i in range(0, len(temp)):
        x = temp[i].split(",")
        id = int(x[0])
        price = int(x[2])
        res = (id, x[1], price, x[3])
        Menu.append(res)       
    return Menu

def convertToString(list):
    res = ""
    for i in list:
        res += str(list.get(i)) + ","
    l = len(res) - 1
    res = res[0:l]
    return res

def convertToBill(msg):
    bill = []
    temp = msg.split(".")
    for i in range(0, len(temp)):
        x = temp[i].split(",")
        res = (x[0], x[1], x[2], x[3])
        bill.append(res)       
    return bill

#Hàm khởi tạo socket
def setup_socket():
    try:
        global client
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect(ADDRESS)
        print("Client:", client.getsockname())
    except:
        return False
    return True

#Hàm thiết kế login và gửi Table_name và password tới server
def loginApp(user, psw):
    try:        
        # print(user,psw,"---")
        option = LOGIN
        
        #send option
        client.sendall(option.encode(FORMAT))
        client.recv(1024).decode(FORMAT)
        
        #send username & password
        #user = int(user)
        client.sendall(user.encode(FORMAT))
        client.recv(1024).decode(FORMAT)
        client.sendall(psw.encode(FORMAT))
        client.recv(1024).decode(FORMAT)
        
        #receive response
        msg = client.recv(1024).decode(FORMAT)
        client.sendall(msg.encode(FORMAT))
        print("Kết quả LoginCheck: " + msg)
        
        return msg
    except:
        return NO

#---------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("E-FOOD")
        self.geometry("700x700")
        self.iconbitmap(r'client.ico')
        self.resizable(width=False,height=False)
        
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill = "both", expand = True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames ={}
        for f in (LoginPage, OrderPage, PaymentPage, EndPage):
            frame = f(self.container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[f] = frame
        
        self.showPage(LoginPage)
        self.runClient()
    
    def showPage(self, frameClass):
        self.frames[frameClass].tkraise()

    def resetFrames(self):
        for f in (LoginPage, OrderPage, PaymentPage, EndPage):
            frame = self.frames[f]
            for widget in frame.winfo_children():
                widget.destroy()
        
        for f in (LoginPage, OrderPage, PaymentPage, EndPage):
            frame = f(self.container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[f] = frame
            
        self.showPage(LoginPage)
    
    #Hàm chạy tiến trình order
    def runClient(self):
        try:
            check = setup_socket()
            if check == True:
                self.showPage(LoginPage)
            else:
                messagebox.showerror('Có lỗi xảy ra', 'Không thể kết nối với server')
                return
        except:
            messagebox.showerror('Có lỗi xảy ra', 'Không thể kết nối với server')
        return #noreturn

    def login(self, curFrame):
        try:
            user = curFrame.entry_user.get()
            psw = curFrame.entry_pswd.get()

            if(user == "" or psw == ""):
                curFrame.login_notice["text"] = "Cần điền đủ các trường thông tin"
                curFrame.login_notice.config(bg="yellow")
                return
            
            msg = loginApp(user, psw)

            if(msg == OK):            
                #ORDER FOOD
                option = ORDER
                #send option
                client.sendall(option.encode(FORMAT))
                client.recv(1024).decode(FORMAT)
                print("Đã gửi option ORDER")
                self.showPage(OrderPage)
                return
            elif msg == LOSE:
                curFrame.login_notice["text"] = "Số bàn này đang hoạt động"
                curFrame.login_notice.config(bg="yellow")
                return
            else:
                curFrame.login_notice["text"] = "Sai số bàn hoặc mật khẩu"
                curFrame.login_notice.config(bg="yellow")
                return
        except:
            messagebox.showerror('Có lỗi xảy ra', 'Server không phản hồi')
            print("Error: Server is not responding")
    
    def handlePayment(self, curFrame):
        msg = OK
        #input cashtype
        cash = "0"
        key1 = curFrame.cash.get()
        key2 = curFrame.card.get()
        
        if key1 == key2:
            messagebox.showerror('Có lỗi xảy ra', 'Vui lòng chọn 1 hình thức thanh toán')
            return NO
        elif key2 == 1:
            cash = curFrame.cardnumber.get()
            if cash == "":
                messagebox.showerror('Có lỗi xảy ra', 'Vui lòng nhập số tài khoản')
                return NO           
        
        client.sendall(cash.encode(FORMAT))
        client.recv(1024).decode(FORMAT)
        print("Đã gửi thông tin thanh toán " + cash)
        #receive response
        msg = client.recv(1024).decode(FORMAT)
        client.sendall(msg.encode(FORMAT))
        
        print("Kết quả kiểm tra thanh toán: " + msg)
        if msg == NO:
            messagebox.showerror('Có lỗi xảy ra', 'Thẻ không hợp lệ')
        return msg
    
    def getData(self, curFrame):
        #receive menu
        menu = client.recv(1024).decode(FORMAT)
        client.sendall(menu.encode(FORMAT))
        MENU = convertToMenu(menu)
        
        print("Đã nhận được MENU:")
        print(MENU)
        
        self.Price = {}
        self.Note = {}
        
        dishCount = len(MENU)
        
        for i in range(dishCount):
            foodname = MENU[i][1]
            curFrame.amount[foodname] = 0
            curFrame.amount2[foodname] = 0
            curFrame.link_img[foodname] = './Image/' + ((foodname).lower()).replace(" ", "") + ".jpg"
            curFrame.listMenu.insert(END, foodname)
            self.Price[foodname] = MENU[i][2]
            if MENU[i][3] == "None":
                self.Note[foodname] = ""
            else:
                self.Note[foodname] = MENU[i][3]
        
        curFrame.button_or.place(x = 40, y = 550)
        curFrame.button_order.place(x = 40, y = 550)
        curFrame.listMenu.place(x=40, y=125)
 
    def orderFood(self, curFrame):
        curFrame.food_title.place(x=320, y=125)
        curFrame.food_price.place(x=320, y=180)
        curFrame.food_note.place(x=320, y=220)
        curFrame.food_amount.place(x=380, y=250)
        curFrame.incre_button.place(x=440, y=255)
        curFrame.decre_button.place(x=320, y=255)
        curFrame.food.place(x = 300, y = 320)
        curFrame.finish_button.place(x=320, y = 550)
        
        food = curFrame.listMenu.get(ANCHOR)
        curFrame.food_title.config(text=food)
        curFrame.food_price.config(text=str(self.Price[food]))
        curFrame.food_note.config(text=str(self.Note[food]))
        curFrame.food_amount.config(text=str(curFrame.amount[food]))
        
        pic = Image.open(curFrame.link_img[food])
        resize = pic.resize((300, 200), Image.ANTIALIAS)
        foodimg = ImageTk.PhotoImage(resize)
        curFrame.food.config(image=foodimg)
        curFrame.food.image = foodimg
        
        return
    
    def checkPay(self, curFrame):
        #send amount of dish
        a = {}
        for i in curFrame.amount:
            a[i] = curFrame.amount[i] - curFrame.amount2[i]
        print(a)
        msg = convertToString(a)
        client.sendall(msg.encode(FORMAT))
        client.recv(1024).decode(FORMAT)
        
        print("Đã gửi thông tin order: " + msg)
        
        curFrame.button_extra.place(x = 40, y = 550)
        curFrame.food_title.place(x = 1000, y = 1000)
        curFrame.food_price.place(x = 1000, y = 1000)
        curFrame.food_note.place(x = 1000, y = 1000)
        curFrame.food_amount.place(x = 1000, y = 1000)
        curFrame.incre_button.place(x = 1000, y = 1000)
        curFrame.decre_button.place(x = 1000, y = 1000)
        curFrame.food.place(x = 1000, y = 1000)
        curFrame.finish_button.place(x = 1000, y = 1000)
        
        self.showPage(PaymentPage)
        return
    
    def getBill(self, curFrame):
        #receive bill
        bill = client.recv(1024).decode(FORMAT)
        client.sendall(bill.encode(FORMAT))
        #receive Total Money
        Money = client.recv(1024).decode(FORMAT)
        client.sendall(Money.encode(FORMAT))
        
        print("Đã nhận được hóa đơn: " + Money)
        print(bill)
        
        BILL = convertToBill(bill)
        
        #fix data
        foodname = ""
        amount = ""
        price = ""
        sum = ""
        
        for dish in BILL:
            foodname += dish[0] + "\n"
            amount += dish[1] + "\n"
            price += dish[2] + "\n"
            sum += dish[3] + "\n"
        
        sum += "\nTổng tiền: " + Money
        
        #assign data
        curFrame.foodname.config(text = foodname)
        curFrame.amount.config(text = amount)
        curFrame.price.config(text = price)
        curFrame.sum.config(text = sum)
        
        #display
        foodbg = ImageTk.PhotoImage(Image.open("Bill Page.png"))
        curFrame.background.config(image=foodbg)
        curFrame.background.image = foodbg
        
        curFrame.foodname.place(x=100, y=250)
        curFrame.amount.place(x=290, y=250)
        curFrame.price.place(x=405, y=250)
        curFrame.sum.place(x=540, y=250)
        
        curFrame.finish_button.pack(side=BOTTOM)
        curFrame.ac_button.place(x=1000, y=1000)
        curFrame.checkbox1.pack(side=BOTTOM)
        curFrame.cardnumber.pack(side=BOTTOM)
        curFrame.checkbox2.pack(side=BOTTOM)
        curFrame.type.pack(side=BOTTOM)
         
    def exportBill(self, curFrame):
        #pay
        check = self.handlePayment(curFrame)
        if check == OK:
            self.showPage(EndPage)
        
            foodbg = ImageTk.PhotoImage(Image.open("Login Page.png"))
            curFrame.background.config(image=foodbg)
            curFrame.background.image = foodbg
            
            curFrame.foodname.place(x=1000, y=1000)
            curFrame.amount.place(x=1000, y=1000)
            curFrame.price.place(x=1000, y=1000)
            curFrame.sum.place(x=1000, y=1000)
            
            curFrame.finish_button.place(x=1000, y=1000)
            curFrame.checkbox1.place(x=1000, y=1000)
            curFrame.cardnumber.place(x=1000, y=1000)
            curFrame.checkbox2.place(x=1000, y=1000)
            curFrame.type.place(x=1000, y=1000)
            
            curFrame.ac_button.pack(pady=150)
        
        return   
    
    def fixData(self, curFrame):
        curFrame.listMenu.place(x=40, y=125)
        curFrame.button_extra.place(x = 1000, y = 1000)
        curFrame.food_title.place(x = 1000, y = 1000)
        curFrame.food_price.place(x = 1000, y = 1000)
        curFrame.food_note.place(x = 1000, y = 1000)
        curFrame.food_amount.place(x = 1000, y = 1000)
        curFrame.incre_button.place(x = 1000, y = 1000)
        curFrame.decre_button.place(x = 1000, y = 1000)
        curFrame.food.place(x = 1000, y = 1000)
        curFrame.finish_button.place(x = 1000, y = 1000)
        curFrame.button_order.place(x = 40, y = 550)
        
        for i in curFrame.amount:
            curFrame.amount2[i] = curFrame.amount.get(i)
        print(curFrame.amount)
        print(curFrame.amount2)
        return
    
    def extraOrder(self):
        option = EXTRA
        
        #send option
        client.sendall(option.encode(FORMAT))
        client.recv(1024).decode(FORMAT)
        print("Đã gửi option Order thêm")
        
        #receive response
        msg = client.recv(1024).decode(FORMAT)
        client.sendall(msg.encode(FORMAT))
        print("Kết quả kiểm tra thời gian: " + msg)
        
        if msg == NO:
            messagebox.showerror('Có lỗi xảy ra', 'Đã qua thời gian để order thêm')
            return
        
        self.showPage(OrderPage)
        return
    
    def logOut(self):
        option = LOGOUT
        #send option
        client.sendall(option.encode(FORMAT))
        client.recv(1024).decode(FORMAT)
        self.resetFrames()
        return
    
    def appClose(self):
        if messagebox.askokcancel("Thoát chương trình", " Bạn có chắc chắn muốn thoát? "):
            self.destroy()
            try:
                option = STOP_CONNECTION
                client.sendall(option.encode(FORMAT))
                client.recv(1024).decode(FORMAT)
                client.close()
            except:
                pass
    
class LoginPage(tk.Frame):
    def __init__(self, parent, appController):
        tk.Frame.__init__(self,parent)
        self.grid(row=0, column=0, sticky="nsew")
        self.configure(bg="#a8b7ff")
        
        imgBg = ImageTk.PhotoImage(Image.open("Login Page.png"))
        background = tk.Label(self,image=imgBg)
        background.image = imgBg
        background.place(x = 0, y = 0)
        
        label_title = tk.Label(self, text="E-Food", bg="white", font=("Arial Bold", 20))
        label_user = tk.Label(self, text="Table", bg="white")
        label_pswd = tk.Label(self, text="Key", bg="white")
        
        self.login_notice = tk.Label(self,text="", bg="white")
        self.entry_user = tk.Entry(self,width=20,bg='light yellow')
        self.entry_pswd = tk.Entry(self,width=20,bg='light yellow')

        button_log = tk.Button(self,text="LOG IN",command=lambda: appController.login(self)) 
        button_log.configure(width=10)
        
        label_title.place(x=310, y=280)
        label_user.place(x=295, y=330)
        label_pswd.place(x=295, y=370)
        
        self.entry_user.place(x=345, y=330)
        self.entry_pswd.place(x=345, y=370)
        
        self.login_notice.place(x=280, y=400)
        button_log.place(x=310, y=420)
        
class OrderPage(tk.Frame):
    def __init__(self,parent, appController):
        tk.Frame.__init__(self, parent)
        self.grid(row=0, column=0, sticky="nsew")
        imgBg = ImageTk.PhotoImage(Image.open("Order Page.png"))
        background = tk.Label(self,image=imgBg)
        background.image = imgBg
        background.place(x = 0, y = 0)
        
        pic = Image.open("./Image/none.jpg")
        resize = pic.resize((300, 200), Image.ANTIALIAS)
        foodimg = ImageTk.PhotoImage(resize)
        self.food = tk.Label(self,image=foodimg)
        self.food.image = foodimg
        
        self.listMenu = Listbox(self, width=30, height=25, bg="white")
        self.amount = {}
        self.amount2 = {}
        self.link_img = {}
        
        self.food_title = tk.Label(self, font=('Arial Bold', 20), text = "",bg="white")
        self.food_price = tk.Label(self, font=('Arial', 20), text = "",bg="white")
        self.food_note = tk.Label(self, font=('Arial', 16), text = "",bg="white")
        self.food_amount = tk.Label(self, font=('Arial', 20), text = "",bg="white")
        
        self.button_or = tk.Button(self,text="Bắt đầu",command=lambda: appController.getData(self)) 
        self.button_or.configure(width=25)
        self.button_or.pack(pady=150)
        
        self.incre_button = tk.Button(self,command=lambda: self.increFood(self.food_title["text"]), text='+', width=5)
        self.decre_button = tk.Button(self,command=lambda: self.decreFood(self.food_title["text"]), text='-', width=5)
        
        self.button_order = tk.Button(self,text="Chọn món",command=lambda: appController.orderFood(self)) 
        self.button_order.configure(width=25)
        
        self.finish_button = tk.Button(self,command=lambda: appController.checkPay(self), text='Thanh toán', width=15, font=('Arial', 13))
        
        self.button_extra = tk.Button(self,text="Bắt đầu order thêm",command=lambda: appController.fixData(self)) 
        self.button_extra.configure(width=25)
    
    def increFood(self, foodname):
        value = self.amount[foodname]
        value = value + 1
        self.amount[foodname] = value
        self.food_amount.config(text=(str(value)))
        return
    
    def decreFood(self, foodname):
        value = self.amount[foodname]
        value = value - 1
        if value < self.amount2[foodname]:
            value = self.amount2[foodname]
        self.amount[foodname] = value
        
        self.food_amount.config(text=(str(value)))
        return
                
class PaymentPage(tk.Frame):
    def __init__(self,parent, appController):
        tk.Frame.__init__(self, parent)
        self.grid(row=0, column=0, sticky="nsew")
        imgBg = ImageTk.PhotoImage(Image.open("Login Page.png"))
        self.background = tk.Label(self,image=imgBg)
        self.background.image = imgBg
        self.background.place(x = 0, y = 0)
        
        self.foodname = tk.Label(self, font=('Arial', 10), text = "",bg="white")
        self.amount = tk.Label(self, font=('Arial', 10), text = "",bg="white")
        self.price = tk.Label(self, font=('Arial', 10), text = "",bg="white")
        self.sum = tk.Label(self, font=('Arial', 10), text = "",bg="white")
        
        self.type = tk.Label(self, font=('Arial', 12), text = "Hình thức thanh toán",bg="white")
        
        self.cash = IntVar()
        self.card = IntVar()
        self.checkbox1 = tk.Checkbutton(self, text="Thanh toán bằng tiền mặt", variable=self.cash, font=('Arial', 10))
        self.checkbox2 = tk.Checkbutton(self, text="Thanh toán bằng thẻ tín dụng", variable=self.card, font=('Arial', 10))
        
        self.ac_button = tk.Button(self,command=lambda: appController.getBill(self), text='Xác nhận thanh toán', width=20, font=('Arial', 20))
        self.ac_button.pack(pady=150)
        
        self.cardnumber = tk.Entry(self,width=20,text = "Số tài khoản ", bg='light yellow')
        self.finish_button = tk.Button(self,command=lambda: appController.exportBill(self), text='Hoàn tất', width=10, font=('Arial', 12))
        
class EndPage(tk.Frame):
    def __init__(self,parent, appController):
        tk.Frame.__init__(self, parent)
        self.grid(row=0, column=0, sticky="nsew")
        imgBg = ImageTk.PhotoImage(Image.open("Login Page.png"))
        self.background = tk.Label(self,image=imgBg)
        self.background.image = imgBg
        self.background.place(x = 0, y = 0)
        
        self.logout = tk.Label(self,text="CHÚC QUÝ KHÁCH NGON MIỆNG!", font=('Arial Bold', 20),bg="white") 
        self.logout.pack(pady=150)
        
        self.logout = tk.Button(self,text="LOG OUT",command=lambda: appController.logOut()) 
        self.logout.configure(width=15)
        self.logout.place(x=300, y=300)
        
        self.extra = tk.Button(self,text="ORDER THÊM",command=lambda: appController.extraOrder()) 
        self.extra.configure(width=15)
        self.extra.place(x=300, y= 330)
#-------------------------MAIN------------------------------
app = App()
app.protocol("WM_DELETE_WINDOW", app.appClose)
app.mainloop()