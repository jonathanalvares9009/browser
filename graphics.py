import platform
import tkinter
from tkinter import font
import browser

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 16, 21
SCROLL_STEP = 100


class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.in_body = False
        self.size = 16
        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, token):
        if isinstance(token, browser.Text) and self.in_body:
            self.text(token)
        elif isinstance(token, browser.Tag) and token.tag == "body":
            self.in_body = True
        elif isinstance(token, browser.Tag) and token.tag == "/body":
            in_body = False
        elif isinstance(token, browser.Tag) and token.tag == "i":
            self.style = "italic"
        elif isinstance(token, browser.Tag) and token.tag == "/i":
            self.style = "roman"
        elif isinstance(token, browser.Tag) and token.tag == "b":
            self.weight = "bold"
        elif isinstance(token, browser.Tag) and token.tag == "/b":
            self.weight = "normal"
        elif isinstance(token, browser.Tag) and token.tag == "small":
            self.size -= 2
        elif isinstance(token, browser.Tag) and token.tag == "/small":
            self.size += 2
        elif isinstance(token, browser.Tag) and token.tag == "big":
            self.size += 4
        elif isinstance(token, browser.Tag) and token.tag == "/big":
            self.size -= 4
        elif isinstance(token, browser.Tag) and token.tag == "br":
            self.flush()
        elif isinstance(token, browser.Tag) and token.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def text(self, tok):
        for word in tok.text.split():
            font = tkinter.font.Font(
                size=self.size,
                weight=self.weight,
                slant=self.style,
            )
            w = font.measure(word)
            if self.cursor_x + w > WIDTH - HSTEP:
                self.cursor_y += font.metrics("linespace") * 1.25
                self.cursor_x = HSTEP
            self.display_list.append(
                (self.cursor_x, self.cursor_y, word, font))
            self.cursor_x += w + font.measure(" ")
            self.line.append((self.cursor_x, word, font))
            if self.cursor_x + w > WIDTH - HSTEP:
                self.flush()

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        # for x, word, font in self.line:
        #     y = baseline - font.metrics("ascent")
        #     self.display_list.append((x, y, word, font))
        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent


class Browser:
    def __init__(self):
        self.height = HEIGHT
        self.width = WIDTH
        self.hstep = HSTEP
        self.vstep = VSTEP
        self.scroll_step = SCROLL_STEP
        self.font_size = 32
        self.tokens = []
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
        self.window.bind("<KeyPress>", self.onkeypress)

    def onresize(self, e):
        self.height = e.height
        self.width = e.width
        self.display_list = Layout(self.tokens).display_list
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

    def onkeypress(self, e):
        if e.char == '+' and self.font_size + 16 <= 100:
            self.font_size += 16
            self.vstep = self.font_size + 5
            self.hstep = self.font_size
        elif e.char == '-' and self.font_size - 16 >= 32:
            self.font_size -= 16
            self.vstep = self.font_size - 5
            self.hstep = self.font_size

        self.display_list = Layout(self.tokens).display_list
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c, s in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + self.vstep < self.scroll:
                continue
            self.canvas.create_text(
                x, y - self.scroll, text=c, font=s, anchor='nw')

    def load(self, url):
        headers, body = browser.request(url)
        tokens = browser.lex(body)
        self.tokens = tokens
        self.display_list = Layout(tokens).display_list
        self.draw()


if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1])
    tkinter.mainloop()
