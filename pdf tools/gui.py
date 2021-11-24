from tkinter import *
from tkinter.ttk import *
import os


class SmartSlider:
    def __init__(self, window, start, end, orient='horizontal'):
        self.value = DoubleVar()
        self.value_string = StringVar()
        self.value_string.set(str(start))

        self.slider_label = Label(window, text=self.get_current_value())
        self.slider = Scale(window, from_=start, to_=end, orient=orient, variable=self.value,
                            command=self.slider_changed)
        self.slider_entry = Entry(window, textvariable=self.value_string)
        self.value_string.trace_add("write", self.text_changed)

    def get_current_value(self):
        return '{: .2f}'.format(self.value.get())

    def slider_changed(self, event):
        self.slider_label.configure(text=self.get_current_value())
        self.value_string.set(str(self.value.get()))

    def text_changed(self):
        print(float(self.value_string.get()))
        self.value.set(float(self.value_string.get()))

    def pack(self):
        self.slider_label.pack()
        self.slider.pack()
        self.slider_entry.pack()


images = os.listdir("outputs/br/swinfield/binary_images")

root = Tk()
root.geometry("500x500")

s = SmartSlider(root, 0, 1)
s.pack()
root.mainloop()
