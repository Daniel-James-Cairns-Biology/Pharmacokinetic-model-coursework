# requires python 3.12

import random
import sys

import pygame


class Bone:
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size
    def draw(self, screen, color=(20, 255, 20)):
        pygame.draw.rect(screen, color, (self.pos[0], self.pos[1], self.size, self.size))


class Food:
    def __init__(self, screen_width, screen_height, size=20):
        x = round(random.randrange(0, screen_width - size) / size) * size
        y = round(random.randrange(0, screen_height - size) / size) * size
        self.bone = Bone((x, y), size)
    def draw(self, screen, color=(0, 200, 0)):
        self.bone.draw(screen, color)


class Snake:
    def __init__(self, start_pos, size):
        self.body = [Bone(start_pos, size)]
        self.direction = [0, 0]
        self.size = size
    def draw(self, screen, color=(255, 0, 127)):
        for bone in self.body:
            bone.draw(screen, color)
    def get_pos(self):
        return self.body[0].pos
    def change_direction(self, new_direction):
        if new_direction[0] != -self.direction[0] or new_direction[1] != -self.direction[1]:
            self.direction = new_direction
    def get_new_pos(self):
        curr_x, curr_y = self.body[0].pos
        dir_x, dir_y = self.direction
        new_x = curr_x + dir_x * self.size
        new_y = curr_y + dir_y * self.size
        return(new_x, new_y)
    def hits_side(self, screen_width, screen_height):
        x, y = self.get_pos()
        if x <0 or x>=screen_width or y <0 or y>=screen_height:
            return True
        else:
            return False
    def move_and_survive(self, screen_width, screen_height, food):
        new_x, new_y = self.get_new_pos()
        new_front = Bone((new_x, new_y), self.size)

        self.body.insert(0, new_front)

        if self.get_pos() == food.bone.pos:
            ate_food = True
        else:
            self.body.pop()
            ate_food = False

        if self.hits_side(screen_width, screen_height):
            return False, ate_food

        for bone in self.body[1:]:
            if self.body[0].pos == bone.pos:
                return False, ate_food

        return True, ate_food



pygame.init()
pygame.font.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


snake = Snake(start_pos=(300, 200), size=20)

food = Food(SCREEN_WIDTH, SCREEN_HEIGHT, size=20)

running = True

clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                snake.change_direction([0, -1])
            elif event.key == pygame.K_DOWN:
                snake.change_direction([0, 1])
            elif event.key == pygame.K_LEFT:
                snake.change_direction([-1, 0])
            elif event.key == pygame.K_RIGHT:
                snake.change_direction([1, 0])

    survived, ate_food = snake.move_and_survive(
        SCREEN_WIDTH, SCREEN_HEIGHT, food
    )

    if not survived:
        running = False

    if ate_food:
        food = Food(SCREEN_WIDTH, SCREEN_HEIGHT, size=20)

    screen.fill((0, 0, 0))

    snake.draw(screen)
    food.draw(screen)

    pygame.display.flip()

    clock.tick(10)

pygame.quit()
sys.exit()
