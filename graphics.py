import platform
import tkinter
import browser

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 26, 36
SCROLL_STEP = 100


class Browser:
    def __init__(self):
        self.height = HEIGHT
        self.width = WIDTH
        self.hstep = HSTEP
        self.vstep = VSTEP
        self.scroll_step = SCROLL_STEP
        self.font_size = 32
        self.text = ""
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.width,
            height=self.height
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mouse_scroll)
        self.window.bind("<Configure>", self.onresize)

    def onresize(self, e):
        self.height = e.height
        self.width = e.width
        self.display_list = self.layout()
        self.draw()

    def mouse_scroll(self, e):
        scroll_amount = 0
        if platform.system() == "Windows":
            scroll_amount = int(-1 * (e.delta / 120))
        elif platform.system() == "Darwin":
            scroll_amount = -1 * e.delta

        if scroll_amount > 0 and scroll_amount <= 3:
            self.scroll += scroll_amount * 100
        elif scroll_amount > 0:
            scroll_amount = 3
            self.scroll += scroll_amount * 100
        elif scroll_amount < 0 and scroll_amount >= -3 and self.scroll + scroll_amount * 100 >= 0:
            self.scroll += scroll_amount * 100
        elif self.scroll + scroll_amount * 100 >= 0:
            scroll_amount = -3
            self.scroll += scroll_amount * 100
        self.draw()

    def scrolldown(self, e):
        self.scroll += self.scroll_step
        self.draw()

    def scrollup(self, e):
        if self.scroll - self.scroll_step >= 0:
            self.scroll -= self.scroll_step
            self.draw()

    def layout(self):
        display_list = []
        cursor_x, cursor_y = self.hstep, self.vstep
        for c in self.text:
            if c == '\n':
                cursor_y += self.vstep
                cursor_x = self.hstep
                continue
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += self.hstep
            if cursor_x >= self.width - self.hstep:
                cursor_y += self.vstep
                cursor_x = self.hstep
        return display_list

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + self.vstep < self.scroll:
                continue
            self.canvas.create_text(
                x, y - self.scroll, text=c, font=("TkDefaultFont", self.font_size))

    def load(self, url):
        headers, body = browser.request(url)
        text = browser.lex(body)
        self.text = text
        self.display_list = self.layout()
        self.draw()


if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1])
    tkinter.mainloop()
