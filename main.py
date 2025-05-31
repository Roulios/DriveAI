import pygame
import os
import math
import sys
import neat
import numpy as np

# ------------------ TRACK CONFIGURATION ------------------
track_names = ["circuit_ovale.png","Circuit_Mans.png", "track.png", "circuit_spa.png"]
print("Choisissez un circuit :")
for i, name in enumerate(track_names):
    print(f"{i + 1} - {name}")
choice = int(input("Votre choix : ")) - 1

track_name = track_names[choice]

TRACKS = {
    "circuit_ovale.png": {
        "size": (1111, 750),
        "start_pos": (620, 630),
        "velocity": (-0.8, 0),
        "angle": 90,
        "rotation_vel": 5,
        "collision_colors": [(0, 71, 0, 255)],
        "finish_line": pygame.Rect(568, 543, 10, 180),
    },
    "Circuit_Mans.png": {
        "size": (1280, 768),
        "start_pos": (60, 435),
        "velocity": (0, -0.5),
        "angle": 0,
        "rotation_vel": 5,
        "collision_colors": [(106, 190, 48, 255)],
        "finish_line": pygame.Rect(32, 435, 65, 25),
    },
    "track.png": {
        "size": (1244, 1016),
        "start_pos": (490, 820),
        "velocity": (0.8, 0),
        "angle": -90,
        "rotation_vel": 5,
        "collision_colors": [(2, 105, 31, 255)],
        "finish_line": pygame.Rect(542, 765, 10, 110),
    },
    "circuit_spa.png": {
        "size": (1452, 772),
        "start_pos": (306, 591),
        "velocity": (-0.8, 0),
        "angle": 90,
        "rotation_vel": 5,
        "collision_colors": [(0, 71, 0, 255), (120, 67, 21, 255), (239, 228, 176, 255)],
        "finish_line": pygame.Rect(332, 556, 10, 110),
    }
    
}

track = TRACKS[track_name]

SCREEN_WIDTH, SCREEN_HEIGHT = track["size"]
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

GREEN = track["collision_colors"][0]
BLACK = (0, 0, 0)

TRACK = pygame.image.load(os.path.join("Assets", track_name))
finish_line_rect = track["finish_line"]

# On réduit le délai avant de compter la fitness (1 seconde)
START_RECORD_FINISH = 1000
best_time: float = 0

# === Ajout des vitesses maximale et minimale ===
MAX_SPEED = 2.0    # Vitesse maximale du vecteur
MIN_SPEED = 0.2    # Vitesse minimale du vecteur (jamais en-dessous)

pygame.init()

pygame_dir = os.path.split(pygame.base.__file__)[0]
pygame_default_font = os.path.join(pygame_dir, pygame.font.get_default_font())
print(pygame_default_font)

font = pygame.font.SysFont(pygame_default_font, 36)
clock = pygame.time.Clock()

def is_color_equal(color1, color2, tolerance):
    distance = np.array(color1) - np.array(color2)
    distance = distance ** 2
    distance = np.sqrt(distance.sum())
    return distance < tolerance

class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join("Assets", "GrandeF1pixelart.png"))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=track["start_pos"])
        self.vel_vector = pygame.math.Vector2(track["velocity"])
        self.angle = track["angle"]
        self.rotation_vel = track["rotation_vel"]
        self.direction = 0
        self.alive = True
        self.radars = []
        self.action = 0


        self.track_time_ms = 0
        self.previous_track_time_ms = 0

    def update(self, ge, i, time, best_time):
        try:
            self.radars.clear()
            self.update_speed()
            self.drive()
            self.rotate()
            for radar_angle in (-60, -30, 0, 30, 60):
                self.radar(radar_angle)
            self.collision(ge, i, time, best_time)
        except Exception:
            self.alive = False
            ge[i].fitness -= 20  # pénalité allégée

        if not self.alive:
            remove(i)       

    def update_speed(self):
        # Accélération ou freinage
        if self.action > 0:
            self.vel_vector *= 1.1
        if self.action < 0:
            self.vel_vector *= 0.8

        # Mise en place dd'une vitesse maximale et minimale
        speed = self.vel_vector.length()
        if speed > MAX_SPEED:
            self.vel_vector.scale_to_length(MAX_SPEED)
        elif speed < MIN_SPEED:
            self.vel_vector.scale_to_length(MIN_SPEED)

    def drive(self):
        self.rect.center += self.vel_vector * 6

    def collision(self, ge, i, time, best_time):
        # Immunité pendant le premier START_RECORD_FINISH ms
        if time < START_RECORD_FINISH:
            return

        length = 25
        collision_point_right = [
            int(self.rect.center[0] + math.sin(math.radians(-self.angle + 18)) * length),
            int(self.rect.center[1] - math.cos(math.radians(-self.angle + 18)) * length)
        ]
        collision_point_left = [
            int(self.rect.center[0] - math.sin(math.radians(self.angle + 18)) * length),
            int(self.rect.center[1] - math.cos(math.radians(self.angle + 18)) * length)
        ]

        # Collision bord d'écran
        if (
            collision_point_left[0] > SCREEN_WIDTH - 30 or
            collision_point_left[1] > SCREEN_HEIGHT - 30 or
            collision_point_right[0] > SCREEN_WIDTH - 30 or
            collision_point_right[1] > SCREEN_HEIGHT - 30
        ):
            self.alive = False
            ge[i].fitness -= 20
            return

        # Collision avec l'herbe (zones "collision_colors")
        if any(is_color_equal(SCREEN.get_at(collision_point_right), color, 20) for color in track["collision_colors"]) \
           or any(is_color_equal(SCREEN.get_at(collision_point_left), color, 20) for color in track["collision_colors"]):
            self.alive = False
            ge[i].fitness -= 20
            return

        # Passage de la ligne d'arrivée
        if self.rect.colliderect(finish_line_rect) and time > START_RECORD_FINISH and time > 20:
            if time < best_time or best_time == 0:
                best_time = time
            self.update_track_time(time, i)
            self.alive = False
            return

        # Dessin des points de collision (pour debug)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_right, 3)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_left, 3)

    def rotate(self):
        if self.direction == 1:
            self.angle -= self.rotation_vel
            self.vel_vector.rotate_ip(self.rotation_vel)
        elif self.direction == -1:
            self.angle += self.rotation_vel
            self.vel_vector.rotate_ip(-self.rotation_vel)
        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 0.1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def radar(self, radar_angle):
        length = 0
        x = int(self.rect.center[0])
        y = int(self.rect.center[1])
        if self.alive:
            while (
                0 <= x < SCREEN_WIDTH - 30 and
                0 <= y < SCREEN_HEIGHT - 30 and
                not any(is_color_equal(SCREEN.get_at((x, y)), color, 20) for color in track["collision_colors"]) and
                length < 60
            ):
                length += 1
                x = int(self.rect.center[0] + math.sin(math.radians(-self.angle - radar_angle)) * length)
                y = int(self.rect.center[1] - math.cos(math.radians(self.angle + radar_angle)) * length)
        pygame.draw.line(SCREEN, (255, 255, 255, 255), self.rect.center, (x, y), 1)
        pygame.draw.circle(SCREEN, (100, 0, 100, 0), (x, y), 3)
        dist = int(math.sqrt((self.rect.center[0] - x) ** 2 + (self.rect.center[1] - y) ** 2))
        self.radars.append([radar_angle, dist])

    def data(self):
        inputs = [0, 0, 0, 0, 0]
        for i, radar in enumerate(self.radars):
            inputs[i] = min(radar[1], 60) / 60.0 
        return inputs

    def update_track_time(self, time: float, i):
        if time < self.track_time_ms:
            self.track_time_ms = time
            ge[i].fitness += 150
        if self.previous_track_time_ms == 0 or self.track_time_ms < self.previous_track_time_ms:
            self.previous_track_time_ms = self.track_time_ms

def remove(index):
    cars.pop(index)
    ge.pop(index)
    nets.pop(index)

def regenerate_map():
    SCREEN.blit(TRACK, (0, 0))
    pygame.draw.rect(SCREEN, (255, 0, 230), finish_line_rect)

def eval_genomes(genomes, config):
    global cars, ge, nets
    cars = []
    ge = []
    nets = []

    # Initialisation des génomes et stockage des informations de distance
    for genome_id, genome in genomes:
        car_sprite = pygame.sprite.GroupSingle(Car())
        cars.append(car_sprite)
        ge.append(genome)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0.0

        # Stocke la position initiale pour le calcul de distance
        genome.prev_pos = pygame.math.Vector2(car_sprite.sprite.rect.center)
        genome.max_dist = 0.0

    global best_time
    run = True

    start_ticks = pygame.time.get_ticks()

    while run and len(cars) > 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        regenerate_map()

        current_time = pygame.time.get_ticks() - start_ticks

        # Calcul de la distance parcourue pour chaque voiture
        for i, car_sprite in enumerate(cars):
            sprite = car_sprite.sprite
            genome = ge[i]

            curr_pos = pygame.math.Vector2(sprite.rect.center)
            prev_pos = genome.prev_pos
            dist_delta = (curr_pos - prev_pos).length()
            genome.prev_pos = pygame.math.Vector2(curr_pos)
            genome.max_dist += dist_delta

            # Récompense proportionnelle à la distance à chaque frame
            genome.fitness += dist_delta * 0.1

        # Mise à jour des actions et des collisions
        for i, car_sprite in enumerate(cars):
            sprite = car_sprite.sprite
            genome = ge[i]

            inputs = sprite.data()
            output = nets[i].activate(inputs)

            # Sorties binaires (seuils à 0.7 pour la prise de décision)
            sprite.direction = 1 if output[0] > 0.7 else -1 if output[1] > 0.7 else 0
            sprite.action = 1 if output[2] > 0.7 else -1 if output[3] > 0.7 else 0

            sprite.update(ge, i, current_time, best_time)

        # Dessine chaque voiture après mise à jour
        for car_sprite in cars:
            car_sprite.draw(SCREEN)

        # Supprime graphiquement les voitures mortes (fitness déjà calculée)
        for j in reversed(range(len(cars))):
            if not cars[j].sprite.alive:
                cars.pop(j)
                nets.pop(j)
                # ge[j] reste pour la fitness finale

        # Affichage de l'uptime et des infos de la souris pour debug
        uptime_ms = pygame.time.get_ticks() - start_ticks
        uptime_sec = uptime_ms // 1000
        minutes = uptime_sec // 60
        seconds = uptime_sec % 60
        milliseconds = uptime_ms % 1000

        uptime_text = font.render(f"Uptime: {minutes:02}:{seconds:02}:{milliseconds:02}", True, BLACK)
        SCREEN.blit(uptime_text, (100, 80))

        pygame.display.flip()
        clock.tick(60)
        pygame.display.update()

    # À la fin de la génération, bonus/pénalité selon la distance maximale atteinte
    LONGUEUR_CIRCUIT_APPROX = 3500 
    for genome in ge:
        if genome.max_dist >= LONGUEUR_CIRCUIT_APPROX:
            genome.fitness += 50  # bonus pour avoir parcouru une grande distance 
        else:
            genome.fitness -= 5  # petite pénalité si faible distance parcourue

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
    pop.run(eval_genomes, 1000)

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    run(config_path)
