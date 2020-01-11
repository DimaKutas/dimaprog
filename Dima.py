from tkinter import *
from tkinter import filedialog as fd
import random
global m, n, count, mas
arr = []
n = 2.0
m = 1.0
count = 0
mas = 0


root = Tk()

root.title("Randomization")
root.resizable(width=False, height=False)
root.geometry('340x350+0+0')
#Текстовые поля
text = Text(width=18, height=1, padx="20", pady = "10" )
text.grid(rowspan =  5, columnspan=4 , padx="20", pady = "8" )


text4 = Text(width=18, height=4, padx="20", pady = "8" )
text4.grid( columnspan=3 , padx="20", pady = "8" )
scroll = Scrollbar(command=text4.yview)
scroll.grid(row = 5, column = 1, ipady = "22", sticky = "ew")
text4.config(yscrollcommand=scroll.set)

text5 = Text(width=18, height=4, padx="20", pady = "8" )
text5.grid(columnspan=1 , padx="20", pady = "8", row = 7, column = 0)

text1 = Text(width=4, height=1 , padx="0")
text1.grid(row = 2, column = 5)

text2 = Text(width=4, height=1 , padx="0")
text2.grid(row = 3, column = 5)



def insert_a():
    global count
    global mas
    
    k = int(text1.get(1.0, END))
    e = int(text2.get(1.0, END))
    text.delete(1.0, END)
    m = random.randint(k, e)
    arr.append(m)
    print(arr)
    text.insert(END, m)
    text4.delete(1.0, END)
    text4.insert(END, arr)
    count = count + 1
    mas = mas + m
    #logik()


    

def stat():
    global count, mas
    text5.delete(1.0, END)
    text5.insert(END,"AVG: ")
    text5.insert(END, mas/count)
    text5.insert(END, "\n")
    text5.insert(END, "MAX: ")
    text5.insert(END, max(arr))
    text5.insert(END, "\n")
    text5.insert(END, "MIN: ")
    text5.insert(END, min(arr))

    

    
#Подписи
    # Надпись Range
g0 = Label(text="Range:", font="Arial 14")
g0.grid(row = 1, column = 4)
    # Надпись Min
g1 = Label(text="Min", font="Arial 14")
g1.grid(row = 2, column = 4)
    # Надпись Max
g2 = Label(text="Max", font="Arial 14")
g2.grid(row = 3, column = 4)
    # Надпись Statistic
g1 = Label(text="Statistic:                      ", font="Arial 14")
g1.grid(row = 6, column = 0)
    # Надпись Сurrent value
g4 = Label(text = " Сurrent value :            ", font = "Arial 14")
g4.grid(row = 1, column = 0)
    # Надпись LOG's
g5 = Label(text = " LOG's:                          ", font = "Arial 14")
g5.grid(row = 4, column = 0)


#Кнопки
    #Кнопка Generate
l1 = Button(text="Generate", command=insert_a)
l1.config(width=7, height=1)
l1.grid(row=4, column=4)
#Кнопка Generate
     #Statistic
g6 = Button(text="Generate\nStatistic", command=stat)
g6.grid(row=6, column=4)
g6.config(width=7, height=2)

root.mainloop()
