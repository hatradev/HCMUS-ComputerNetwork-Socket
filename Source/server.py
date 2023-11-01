from re import A
import socket
import threading
import pyodbc
import os
import time
import traceback

import tkinter as tk
from tkinter import messagebox
from tkinter import *
from tkinter import scrolledtext
from PIL import Image,ImageTk

#BASE SOCKET CONNECTION
HOST = "127.0.0.1"
PORT = 8000
ADDRESS = (HOST, PORT)
FORMAT = "utf8"

#DATABASE
DRIVE_NAME = 'ODBC Driver 17 for SQL Server'
SERVER_NAME = "TRAHOANG"
DATABASE_NAME = "FOODORDER"
UID_NAME = "Socket"
PWD = "123456"
#TABLE OF DATABASE
MENU = 'menu'
ACCOUNT = 'account'
ORDERLIST = 'orderlist'

#DATA
LiveTable = []
OffTable = []

#MENU
Menu = []

#ACTION
LOGIN = 'login'
LOGOUT = 'logout'
ORDER = 'order'
EXTRA = 'extra order'
STOP_CONNECTION = 'stop'

OK = 'True'
NO = 'False'
LOSE = 'LOSE'

CANCEL = 'Cancel'
CASH = "by cash"
CARD = "by credit card"

#----------------------DATA------------------------#
def convertMenuToString(Menu: list):
    res = ""
    for dish in Menu:
        res += str(dish[0]) + "," + dish[1] + "," + str(dish[2]) + "," + str(dish[3])
        if (dish != Menu[-1]):
            res += "."
    return res

def convertToList(msg: str):
    amount = []
    tmp = msg.split(",")
    for i in tmp:
        amount.append(int(i))
    return amount

def convertToBill(amount, Menu):
    res = ""
    for i in range(len(Menu)):
        if (amount[i] > 0):
            res += Menu[i][1] + "," + str(amount[i]) + "," + str(Menu[i][2]) + "," + str(amount[i]*Menu[i][2]) + "."
    l = len(res) - 1
    res = res[0:l]
    print(res)
    return res
#----------------------CONDITION BARRIER------------------#
#Hàm tính tổng giá tiền của một đơn hàng
def SumMoney(Amount: list):
    sum = 0
    for i in range(0, len(Amount)):
        sum += Amount[i]*Menu[i][2]
    return sum

#Hàm kiểm tra xem tài khoản ngân hàng có hợp lệ hay không
def BankCardCheck(card):
    if len(card) != 10:
        return False
    for i in card:
        if i not in "0123456789":
            return False
    return True

#Hàm kiểm tra xem còn có thể order thêm hay không
def TimeOrderCheck(table_name, time):
    conn = connectToDatabase()
    cursor = conn.cursor()
    cursor.execute(f"select * from {ORDERLIST} where table_name = (?)",table_name)
    data = cursor.fetchall()
    t = float(data[0][5])
    print(t);
    if time - t <= 7200:
        res = OK
    else:
        res = NO
    conn.close()
    return res

#Hàm tạo một string chứa thông tin bàn hiện có
def CreateTable(user, pwd):
    list = [user, pwd, 0]
    return list

#----------------------DATABASE----------------------#
#Hàm trả về kết nối tới database
def connectToDatabase():
    # print(pyodbc.drivers())
    conn = pyodbc.connect(f'DRIVER={DRIVE_NAME};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};UID={UID_NAME};PWD={PWD};')
    conn.autocommit = True
    #Dùng các thông số đã có trên database
    return conn#trả về connection tới database

#Hàm đọc thông tin đăng nhập của client
def LoginCheck(tablename, password):
    res = NO
    conn = connectToDatabase()
    cursor = conn.cursor()
    cursor.execute(f"select * from {ACCOUNT} where table_name =(?)", tablename)
    data = cursor.fetchall()
    if len(data) > 0:
        if data[0][1] == password:
            res = OK
    conn.close()
    return res

#Hàm đọc dữ liệu menu từ database
def getMenu():
    conn = connectToDatabase()
    cursor = conn.cursor()
    cursor.execute(f"select * from {MENU}")
    tmp = cursor.fetchall()
    conn.close()
    return tmp

#Hàm đưa dữ liệu order vào bảng trong database
def updateData(table_name, amount, time, status, pay_type):
    conn = connectToDatabase()
    cursor = conn.cursor()
    for i in range(0, len(amount)):
        cursor.execute(f"insert {ORDERLIST} values (?,?,?,?,?,?)", table_name, Menu[i][1], amount[i], status, pay_type, str(time))
    conn.close()
    return #không return gì cả

def LoadOrder(table_name, amount: list):
    conn = connectToDatabase()
    cursor = conn.cursor()
    cursor.execute(f"select * from {ORDERLIST} where table_name = (?)", table_name)
    x = cursor.fetchall()
    conn.close()
    a = []
    for i in range(0, len(amount)):
        a.append(amount[i] + x[i][2])
    return a
    
#Hàm xóa dữ liệu của bàn cũ để order cho khách mới trong database
def deleteOldData(table_name):
    conn = connectToDatabase()
    cursor = conn.cursor()
    cursor.execute(f"select count(*) from {ORDERLIST} where table_name = (?)",table_name)
    count = cursor.fetchall()
    print(count)
    if count[0][0] <= 0:
        return OK
    else:
        cursor.execute(f"delete from {ORDERLIST} where table_name = (?)", table_name)
        return OK

#----------------------CONNECTION---------------------#
#Hàm cho phép client login sau khi kiểm tra thông tin đăng nhập là chính xác
def ClientLogin(conn: socket):
    user = conn.recv(1024).decode(FORMAT)
    conn.sendall(user.encode(FORMAT))
    psw = conn.recv(1024).decode(FORMAT)
    conn.sendall(psw.encode(FORMAT))
    
    msg = LoginCheck(user, psw)
    
    if (msg == OK):
        tb = CreateTable(user, psw)
        if tb in LiveTable:
            msg = LOSE
    
    #send response
    conn.sendall(msg.encode(FORMAT))
    conn.recv(1024).decode(FORMAT)
    print("LOGIN: Kiểm tra ",user,"---",psw,":",msg)
    #Thêm client vào trong mảng table 
    if msg == OK:
        LiveTable.append(tb)
    else:
        return -1
    print(LiveTable)
    return int(user)

#Hàm xóa client khỏi mảng Table khi client logout
def removeClient(table_name):
    for client in LiveTable:
        if client[0] == str(table_name):
            OffTable.append(client)
            LiveTable.remove(client)
            return

#STATUS:
#[0]: Chua thanh toan
#[1]: Chua xac nhan thong tin tai khoan
#[2]: Da thanh toan
def handlePayment(conn, table_name, Amount, extra):
    #receive payment type
    card = conn.recv(1024).decode(FORMAT)
    conn.sendall(card.encode(FORMAT))
    
    if card == "0":
        pay_type = CASH
        status = 2
        msg = OK
    else:
        pay_type = CARD + ":" + card
        if BankCardCheck(card) == True:
            status = 2
            msg = OK
        else:
            status = 1
            msg = NO
    
    print("Kiểm tra hình thức thanh toán: " + msg + " " + pay_type)
    #send response: Card is (not) accepted
    conn.sendall(msg.encode(FORMAT))
    conn.recv(1024).decode(FORMAT)
      
    if msg == OK:
        print(extra)
        if (extra == True):
            a = LoadOrder(table_name, Amount)
            if deleteOldData(table_name) == OK:
                print(a)
                updateData(table_name, a, time.time(), status, pay_type)
        else:
            x = deleteOldData(table_name)
            print(x)
            updateData(table_name, Amount, time.time(), status, pay_type)
        print("Update dữ liệu order lên DTB Thành công")
    
    return msg

#Hàm kiểm soát một Client khi nhận được kết nối và gửi menu tới cho Client đó
def HandleOrder(conn: socket, table_name, extra):
    if extra == False:
        menu = convertMenuToString(Menu)
        
        #send menu to client
        conn.sendall(menu.encode(FORMAT))
        conn.recv(1024).decode(FORMAT)
        print("Đã gửi MENU cho client")
    
    #receive amount
    msg = conn.recv(1024).decode(FORMAT)
    print(msg)
    Amount = convertToList(msg)
    conn.sendall(msg.encode(FORMAT))
    print("Đã nhận số lượng Order")

    bill = convertToBill(Amount, Menu)
    #send bill to client
    conn.sendall(bill.encode(FORMAT))
    conn.recv(1024).decode(FORMAT)
    print("Đã gửi hóa đơn thành công")
    
    #Tong so tien
    TotalMoney = SumMoney(Amount)
    conn.sendall(str(TotalMoney).encode(FORMAT))
    conn.recv(1024).decode(FORMAT)
    print("Đã gửi tổng số tiền thành công")
    
    try:
        while True:
            if handlePayment(conn, table_name, Amount, extra) == OK:
                return
    except:
        return #Không return gì

#-----------------------FRONT-END--------------------------#
def changeOnHover(button, colorOnHover, colorOnLeave): # Hàm thay đổi màu khi di chuột vào và ra khỏi button
    # adjusting backgroung of the widget
    # background on entering widget
    button.bind("<Enter>", func=lambda e: button.config(
        background=colorOnHover))

    # background color on leving widget
    button.bind("<Leave>", func=lambda e: button.config(
        background=colorOnLeave))

def ask_exit(exit_button):
    check_quit=messagebox.askokcancel("Thoát", "Bạn chắc chắc muốn thoát chương trình ?")
    if check_quit==True:
        root.destroy()
        exit()
        
def exit_button():
    exit_button=Button(root, command=lambda: ask_exit(exit_button),text='Exit',activebackground='Light salmon',fg='black',font=('Arial',10))
    exit_button.place(x=523,y=102)
    changeOnHover(exit_button, 'DarkOliveGreen1','SystemButtonFace')

def mainServer() : #Dùng Thread để kết nối các client khi Ip nhaapjd dúng
    global root
    root=tk.Tk() #Khởi tạo widget 
    root.geometry('750x500') 
    root.title("Food Order Server")
    root.iconbitmap(r'server.ico')
    root.resizable(False,False)
    
    load = Image.open("Food Order Server.png") # 4 dòng: lấy và hiển thị hình ảnh trong widget
    render = ImageTk.PhotoImage(load)
    img = Label(root, image=render)
    img.place(x=0, y=0)
   
    group1 = LabelFrame(root, text=" Connected", padx=5, pady=5) # 2 dòng tạo Frame thứ 1
    group1.grid(row=1, column=0, columnspan= 2, padx=82, pady=135, sticky= W + N + S)
    txtbox = scrolledtext.ScrolledText(group1, width=30, height=15) # 2 dòng tạo text box thứ 1 với thanh scroll bar
    txtbox.grid(row=1, column=0, sticky=E + W + N + S)
    txtbox.config(state='disabled')
    
    group2 = LabelFrame(root, text=" Disconnected", padx=5, pady=5) # 2 dòng tạo Frame thứ 2
    group2.grid(row=1, column=1, columnspan= 2, padx=408, pady=135, sticky=E + W + N + S)
    txtbox_2 = scrolledtext.ScrolledText(group2, width=30, height=15) # 2 dòng tạo text box thứ 2 với thanh scroll bar
    txtbox_2.grid(row=1, column=1, sticky=E + W + N + S)
    txtbox_2.config(state='disabled')

    def startOrderThread():
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            s.bind(ADDRESS)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Có lỗi xảy ra', 'Không thực hiện bind địa chỉ được')
            root.destroy()
            exit(1)
        
        s.listen()

        def handleClient(conn: socket, addr):
            table = -1
            while(True):
                try:
                    #receive option
                    option = conn.recv(1024).decode(FORMAT)
                    conn.sendall(option.encode(FORMAT))
                    print("-----------" + option + "------------")
                    if(option == LOGIN):
                        table = ClientLogin(conn)
                        print("Kết thúc Login")
                        
                    if(option == STOP_CONNECTION):
                        break
                    
                    if(option == ORDER):
                        HandleOrder(conn, table, False)
                        print("Kết thúc Order")
                        
                    if(option == EXTRA):
                        print("Bắt đầu order thêm")
                        current = time.time()
                        print(current)
                        msg = TimeOrderCheck(table, current)
                        print(msg)
                        #send response
                        conn.sendall(msg.encode(FORMAT))
                        conn.recv(1024).decode(FORMAT)
                        
                        print("Extra Order: KQ kiểm tra thời gian " + msg)
                        if msg == OK:
                            HandleOrder(conn, table, True)
                            
                        print("Kết thúc ExtraOrder")
                        
                    if(option == LOGOUT):
                        removeClient(table)
                        print("LOGOUT")
                    
                except:
                    break
                    
                
            text_2 = "Disconnect"+str(addr)+"\n"
            txtbox_2.config(state="normal")
            txtbox_2.insert(tk.END,text_2) 
            txtbox_2.config(state='disabled')
            conn.close()
            removeClient(table)
            
            conn.close()
            return #noreturn
        
        txtbox.config(state='normal')
        txtbox.insert(tk.END,"Chờ kết nối...\n") #In trạng thái đang chờ
        txtbox.config(state='disabled')
        
        while(True):
            try:
                conn,addr = s.accept()
                thr = threading.Thread(target=handleClient,args=(conn,addr))
                thr.daemon = False
                thr.start()
                
                text_1 = "Connect: " +str(addr)+"\n"
                txtbox.config(state='normal')
                txtbox.insert(tk.END,text_1) # Thêm thông báo kết nối vào cuối của box trên
                txtbox.config(state='disabled')
                print("Đã kết nối với " + str(addr))
            except:
                break

    def start_thread_socket(): #Tạo thread khởi động socket ( phải tách ra thread riêng vì lồng vòng lặp với mainloop)
        start_button.config(state='disabled')
        changeOnHover(start_button,'SystemButtonFace','SystemButtonFace')
        thread_start_socket=threading.Thread(target=startOrderThread, daemon=True)
        thread_start_socket.start()
        
    def Create_start_socket_button():
        global start_button
        start_button = Button(root, command=start_thread_socket, text='Start', activebackground='Light salmon',fg='black', font=('Arial', 10))
        start_button.place(x=196, y=102)
        changeOnHover(start_button,'DarkOliveGreen1','SystemButtonFace')
        
    Create_start_socket_button()
    exit_button()
    
    def on_closing():
        check=messagebox.askokcancel("Thoát chương trình", " Bạn có chắc chắn muốn thoát? ")
        if check==True:
            root.destroy()
            exit()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

#------------------------MAIN-----------------------------#

# #Chạy front_end của server và tiến trình order
Menu = getMenu()
mainServer()