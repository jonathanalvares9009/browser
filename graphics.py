import tkinter
import browser

WIDTH, HEIGHT = 800, 600


def layout(text):
    display_list = []
    HSTEP, VSTEP = 13, 18
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()

    def draw(self):
        for x, y, c in self.display_list:
            self.canvas.create_text(x, y, text=c)

    def load(self, url):
        headers, body = browser.request(url)
        text = browser.lex(body)
        self.display_list = layout(text)
        self.draw()


if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1])
    tkinter.mainloop()
