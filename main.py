import pygame
import os
import math
import sys
import neat

SCREEN_WIDTH = 1244
SCREEN_HEIGHT = 1016
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

TRACK = pygame.image.load(os.path.join("Assets", "track.png"))

# Init pygame
pygame.init()

#Get pygame default font
pygame_dir = os.path.split(pygame.base.__file__)[0]
pygame_default_font = os.path.join(pygame_dir, pygame.font.get_default_font())
print(pygame_default_font)

font = pygame.font.SysFont(pygame_default_font, 36)

clock = pygame.time.Clock()

# Start of the game
start_ticks = pygame.time.get_ticks()




class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join("Assets", "car.png"))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(490, 820))
        self.vel_vector = pygame.math.Vector2(0.8, 0)
        self.angle = 0
        self.rotation_vel = 5
        self.direction = 0
        self.alive = True
        self.radars = []
        self.action = 0 #-1 frein, 0 rien, 1 accel
        self.checkpoint_pass = []

    def update(self):
        self.radars.clear()
        self.update_speed()
        self.drive()
        self.rotate()
        for radar_angle in (-60, -30, 0, 30, 60):
            self.radar(radar_angle)
        self.collision()
        self.data()

    def update_speed(self) :
        if(self.action > 0) : 
            self.vel_vector = self.vel_vector * 1.1
        if(self.action < 0) :
            self.vel_vector = self.vel_vector*0.5   
        else :
            self.vel_vector - self.vel_vector *0.9

    def drive(self):
        self.rect.center += self.vel_vector * 6

    def collision(self):
        length = 40
        collision_point_right = [int(self.rect.center[0] + math.cos(math.radians(self.angle + 18)) * length),
                                 int(self.rect.center[1] - math.sin(math.radians(self.angle + 18)) * length)]
        collision_point_left = [int(self.rect.center[0] + math.cos(math.radians(self.angle - 18)) * length),
                                int(self.rect.center[1] - math.sin(math.radians(self.angle - 18)) * length)]

        # Passe un check point - violet
        if SCREEN.get_at(collision_point_right) == pygame.Color(255, 0, 255, 255) \
                or SCREEN.get_at(collision_point_left) == pygame.Color(255, 0, 255, 255):
            self.checkpoint_pass.append(True)


        # Die on Collision
        if SCREEN.get_at(collision_point_right) == pygame.Color(2, 105, 31, 255) \
                or SCREEN.get_at(collision_point_left) == pygame.Color(2, 105, 31, 255):
            self.alive = False

        # Draw Collision Points
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_right, 4)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_left, 4)

    def rotate(self):
        if self.direction == 1:
            self.angle -= self.rotation_vel
            self.vel_vector.rotate_ip(self.rotation_vel)
        if self.direction == -1:
            self.angle += self.rotation_vel
            self.vel_vector.rotate_ip(-self.rotation_vel)

        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 0.1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def radar(self, radar_angle):
        length = 0
        x = int(self.rect.center[0])
        y = int(self.rect.center[1])

        while not SCREEN.get_at((x, y)) == pygame.Color(2, 105, 31, 255) and length < 200:
            length += 1
            x = int(self.rect.center[0] + math.cos(math.radians(self.angle + radar_angle)) * length)
            y = int(self.rect.center[1] - math.sin(math.radians(self.angle + radar_angle)) * length)

        # Draw Radar
       # pygame.draw.line(SCREEN, (255, 255, 255, 255), self.rect.center, (x, y), 1)
        #pygame.draw.circle(SCREEN, (0, 255, 0, 0), (x, y), 3)
        #pygame.draw.line(SCREEN, (255, 0, 255, 255), (100,1), (100, 100), 1)
        

        dist = int(math.sqrt(math.pow(self.rect.center[0] - x, 2)
                             + math.pow(self.rect.center[1] - y, 2)))

        self.radars.append([radar_angle, dist])

    def data(self):
        input = [0, 0, 0, 0, 0]
        for i, radar in enumerate(self.radars):
            input[i] = int(radar[1])
        return input


def remove(index):
    cars.pop(index)
    ge.pop(index)
    nets.pop(index)


def eval_genomes(genomes, config):

    global cars, ge, nets

    cars = []
    ge = []
    nets = []

    for genome_id, genome in genomes:
        cars.append(pygame.sprite.GroupSingle(Car()))
        ge.append(genome)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0

    run = True
    while run:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        SCREEN.blit(TRACK, (0, 0))
        # Génération des checkpoints
        pygame.draw.line(SCREEN, (255, 0, 255, 255), (900,700), (1500, 700), 1)

        if len(cars) == 0:
            break

        for i, car in enumerate(cars):
            ge[i].fitness += 1
            if not car.sprite.alive:
                remove(i)

        for i, car in enumerate(cars):
            output = nets[i].activate(car.sprite.data())
            if output[0] > 0.7:
                car.sprite.direction = 1
            if output[1] > 0.7:
                car.sprite.direction = -1
            if output[0] <= 0.7 and output[1] <= 0.7:
                car.sprite.direction = 0
            if output[2] > 0.7:
                car.sprite.action = 1
            if output[3] > 0.7:
                car.sprite.action = -1
            if output[2] <= 0.7 and output[3] <= 0.7:
                car.sprite.action = 0

        # Update
        for car in cars:
            car.draw(SCREEN)
            car.update()
            
        # Time gestion
        uptime_ms = pygame.time.get_ticks() - start_ticks
        uptime_sec = uptime_ms // 1000
        minutes = uptime_sec // 60
        seconds = uptime_sec % 60
        milliseconds = uptime_ms % 1000

        #Tuer les voitures les plus lentes
        if(uptime_sec % 15 == 0):
            for car in cars :
                if(len(car.sprite.checkpoint_pass) == 0) :
                    car.sprite.alive = False
                else :
                    car.sprite.checkpoint_pass.pop(len(car.sprite.checkpoint_pass))
        

        # Display uptime
        uptime_text = font.render(f"Uptime: {minutes:02}:{seconds:02}:{milliseconds:02}", True, BLACK)

        # Show uptime on top left corner
        SCREEN.blit(uptime_text, (100, 80))
        pygame.display.flip()

        clock.tick(60)
        
        pygame.display.update()


# Setup NEAT Neural Network
def run(config_path):
    global pop
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    pop = neat.Population(config)

    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    pop.run(eval_genomes, 50)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    run(config_path)
