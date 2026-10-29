import tkinter as tk


class Paddle:
    def __init__(self, canvas, pos, width=120, height=20, speed=12):
        self.canvas = canvas
        self.pos = list(pos)
        self.width = width
        self.height = height
        self.speed = speed
        self.item = canvas.create_rectangle(
            pos[0] - width / 2, pos[1] - height / 2,
            pos[0] + width / 2, pos[1] + height / 2,
            fill="white", outline=""
        )

    def move(self, direction):
        left, _top, right, _bottom = self.canvas.coords(self.item)
        canvas_width = int(self.canvas.cget("width"))
        dx = direction * self.speed
        if left + dx < 0:
            dx = -left
        elif right + dx > canvas_width:
            dx = canvas_width - right
        self.canvas.move(self.item, dx, 0)
        self.pos[0] += dx

    def move_to(self, x):
        left, _top, right, _bottom = self.canvas.coords(self.item)
        canvas_width = int(self.canvas.cget("width"))
        x = max(self.width / 2, min(x, canvas_width - self.width / 2))
        dx = x - (left + right) / 2
        self.canvas.move(self.item, dx, 0)
        self.pos[0] = x


class Ball:
    def __init__(self, canvas, pos, radius=8, velocity=(4, -4)):
        self.canvas = canvas
        self.pos = list(pos)
        self.radius = radius
        self.velocity = list(velocity)
        self.active = True
        self.item = canvas.create_oval(
            pos[0] - radius, pos[1] - radius,
            pos[0] + radius, pos[1] + radius,
            fill="#ffd166", outline=""
        )

    def move(self):
        self.canvas.move(self.item, *self.velocity)
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]


class Brick:
    colours = {3: "#ef476f", 2: "#fca311", 1: "#06d6a0"}

    def __init__(self, canvas, pos, width=70, height=25, hits=1):
        self.canvas = canvas
        self.pos = list(pos)
        self.width = width
        self.height = height
        self.hits = hits
        self.colour = self.colours.get(hits, "#06d6a0")
        self.destroyed = False
        self.item = canvas.create_rectangle(
            pos[0] - width / 2, pos[1] - height / 2,
            pos[0] + width / 2, pos[1] + height / 2,
            fill=self.colour, outline="#101936"
        )

    def hit(self):
        self.hits -= 1
        if self.hits <= 0:
            self.destroyed = True
            self.canvas.delete(self.item)
        else:
            self.colour = self.colours.get(self.hits, "#06d6a0")
            self.canvas.itemconfigure(self.item, fill=self.colour)


class BrickBreaker:
    def __init__(self, root):
        self.root = root
        self.width = 800
        self.height = 600
        self.running = True
        self.score = 0
        self.lives = 3

        root.title("Brick Breaker")
        root.resizable(False, False)
        self.canvas = tk.Canvas(
            root, width=self.width, height=self.height,
            bg="#101936", highlightthickness=0
        )
        self.canvas.pack()

        self.score_text = self.canvas.create_text(
            20, 18, anchor="nw", fill="white",
            font=("Arial", 16, "bold")
        )
        self.status_text = self.canvas.create_text(
            self.width / 2, self.height / 2,
            fill="white", font=("Arial", 28, "bold")
        )

        self.keys = set()
        root.bind("<KeyPress-Left>", lambda _event: self.keys.add("left"))
        root.bind("<KeyRelease-Left>", lambda _event: self.keys.discard("left"))
        root.bind("<KeyPress-Right>", lambda _event: self.keys.add("right"))
        root.bind("<KeyRelease-Right>", lambda _event: self.keys.discard("right"))
        root.bind("<Motion>", self.move_mouse)
        root.bind("<space>", self.start_or_restart)
        root.bind("<Escape>", lambda _event: root.destroy())

        self.reset_round()
        self.update()

    def reset_round(self):
        if hasattr(self, "paddle"):
            self.canvas.delete(self.paddle.item)
        if hasattr(self, "ball"):
            self.canvas.delete(self.ball.item)
        self.paddle = Paddle(self.canvas, (self.width / 2, 560))
        self.ball = Ball(self.canvas, (self.width / 2, 530), velocity=(4, -4))
        self.started = False
        self.canvas.itemconfigure(self.status_text, text="Press SPACE to launch")
        self.update_score()

    def reset_game(self):
        for brick in getattr(self, "bricks", []):
            if not brick.destroyed:
                self.canvas.delete(brick.item)
        self.score = 0
        self.lives = 3
        self.make_bricks()
        self.reset_round()

    def make_bricks(self):
        self.bricks = []
        for row in range(5):
            for column in range(9):
                x = 80 + column * 80
                y = 70 + row * 35
                hits = 1 if row < 2 else (2 if row < 4 else 3)
                self.bricks.append(Brick(self.canvas, (x, y), hits=hits))

    def move_mouse(self, event):
        self.paddle.move_to(event.x)

    def start_or_restart(self, _event=None):
        if not self.running:
            self.reset_game()
            self.running = True
        elif not self.started:
            self.started = True
            self.canvas.itemconfigure(self.status_text, text="")

    def update_score(self):
        self.canvas.itemconfigure(
            self.score_text,
            text=f"Score: {self.score}   Lives: {self.lives}"
        )

    def rectangles_overlap(self, item1, item2):
        left1, top1, right1, bottom1 = self.canvas.bbox(item1)
        left2, top2, right2, bottom2 = self.canvas.bbox(item2)
        return not (right1 < left2 or right2 < left1 or
                    bottom1 < top2 or bottom2 < top1)

    def update(self):
        if "left" in self.keys:
            self.paddle.move(-1)
        if "right" in self.keys:
            self.paddle.move(1)

        if self.started and self.running:
            self.move_ball()
        self.root.after(16, self.update)

    def move_ball(self):
        self.ball.move()
        left, top, right, bottom = self.canvas.coords(self.ball.item)

        if left <= 0:
            self.ball.velocity[0] = abs(self.ball.velocity[0])
            self.canvas.move(self.ball.item, -left, 0)
        elif right >= self.width:
            self.ball.velocity[0] = -abs(self.ball.velocity[0])
            self.canvas.move(self.ball.item, self.width - right, 0)
        if top <= 0:
            self.ball.velocity[1] = abs(self.ball.velocity[1])
            self.canvas.move(self.ball.item, 0, -top)

        if self.rectangles_overlap(self.ball.item, self.paddle.item):
            self.ball.velocity[1] = -abs(self.ball.velocity[1])
            paddle_left, _top, paddle_right, _bottom = self.canvas.coords(self.paddle.item)
            paddle_centre = (paddle_left + paddle_right) / 2
            offset = (self.ball.pos[0] - paddle_centre) / (self.paddle.width / 2)
            self.ball.velocity[0] = 5 * max(-1, min(offset, 1))
            if self.ball.velocity[0] == 0:
                self.ball.velocity[0] = 4
            self.canvas.move(self.ball.item, 0, -10)

        for brick in self.bricks:
            if not brick.destroyed and self.rectangles_overlap(self.ball.item, brick.item):
                brick.hit()
                self.score += 1
                self.ball.velocity[1] *= -1
                self.update_score()
                break

        if bottom >= self.height:
            self.lives -= 1
            self.update_score()
            if self.lives <= 0:
                self.running = False
                self.canvas.itemconfigure(
                    self.status_text,
                    text=f"Game over - Score: {self.score}\nPress SPACE to play again"
                )
            else:
                self.reset_round()

        if all(brick.destroyed for brick in self.bricks):
            self.running = False
            self.canvas.itemconfigure(
                self.status_text,
                text=f"You win! - Score: {self.score}\nPress SPACE to play again"
            )


if __name__ == "__main__":
    root = tk.Tk()
    game = BrickBreaker(root)
    game.make_bricks()
    root.mainloop()
