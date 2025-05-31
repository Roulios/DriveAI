import pygame
import os
import math
import sys
import neat
import numpy as np

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

GREEN = (106,190,48,255)
GRAY = (105,106,106,255)



BLACK = (0, 0, 0)

TRACK = pygame.image.load(os.path.join("Assets", "Circuit_Mans.png"))
# Finish line rectangle
finish_line_rect = pygame.Rect(35,435,55,20)

# Event creation, this even will be rigger when the car touch the standing line
LAP_START = pygame.USEREVENT + 1

# Time when a collision with the line isn't consider as a finish
START_RECORD_FINISH = 3000

best_time : float = 0

# Init pygame
pygame.init()

#Get pygame default font
pygame_dir = os.path.split(pygame.base.__file__)[0]
pygame_default_font = os.path.join(pygame_dir, pygame.font.get_default_font())
print(pygame_default_font)

font = pygame.font.SysFont(pygame_default_font, 36)

clock = pygame.time.Clock()

def is_color_equal(color1,color2,tolerance) : 
    distance = np.array(color1)-np.array(color2)
    distance = distance**2
    distance = np.sqrt(distance.sum())
    return distance < tolerance




class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join("Assets", "GrandeF1pixelart.png"))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(60,435))
        self.vel_vector = pygame.math.Vector2(0, -0.8)
        self.angle = 0
        self.rotation_vel = 5
        self.direction = 0
        self.alive = True
        self.radars = []
        self.action = 0 #-1 frein, 0 rien, 1 acceleration
        self.finish_line = False
        # Time gestion variables
        self.track_time_ms = 0
        self.previous_track_time_ms = 0

    def update(self,ge,i,time,best_time):
        try :
            self.radars.clear()
            self.update_speed()
            self.drive()
            self.rotate()
            for radar_angle in (-60, -30, 0, 30, 60):
                self.radar(radar_angle)
            self.data()

            self.kill_slow(ge,i,time)
            self.collision(ge,i,time,best_time)

        except :
            self.alive = False
            ge[i].fitness -=400

        if not self.alive and not self.finish_line:
           remove(i)

        
    def update_speed(self) :
        if(self.action > 0) : 
            self.vel_vector = self.vel_vector * 1.1
        if(self.action < 0) :
            self.vel_vector = self.vel_vector*0.5   


    def drive(self):
        self.rect.center += self.vel_vector * 6


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
        if self.alive :

              while x <SCREEN_WIDTH-30 and y < SCREEN_HEIGHT-30 and not is_color_equal(SCREEN.get_at((x, y)),GREEN,20) and length < 250:
                length += 1
                x = int(self.rect.center[0] + math.sin(math.radians(-self.angle - radar_angle)) * length)
                y = int(self.rect.center[1] - math.cos(math.radians(self.angle + radar_angle)) * length)

        # Draw Radar
        pygame.draw.line(SCREEN, (255, 255, 255, 255), self.rect.center, (x, y), 1)
        pygame.draw.circle(SCREEN, (100, 0, 100, 0), (x, y), 3)

        dist = int(math.sqrt(math.pow(self.rect.center[0] - x, 2)
                             + math.pow(self.rect.center[1] - y, 2)))

        self.radars.append([radar_angle, dist])


    def data(self):
        input = [0, 0, 0, 0, 0]
        for i, radar in enumerate(self.radars):
            input[i] = int(radar[1])
        return input
    


    def kill_slow(self,ge,i,time) :

        #Tuer les voitures les plus lentes
        if abs(np.linalg.norm(self.vel_vector)) <0.2 :
            ge[i].fitness -= 200
            self.alive = False


    def collision(self,ge,i,time,best_time):
        length = 25
        collision_point_right = [int(self.rect.center[0] + math.sin(math.radians(-self.angle +  18)) * length),
                                 int(self.rect.center[1] - math.cos(math.radians(-self.angle + 18)) * length)]
        collision_point_left = [int(self.rect.center[0] - math.sin(math.radians(self.angle + 18)) * length),
                                int(self.rect.center[1] - math.cos(math.radians(self.angle + 18)) * length)]
 
        # Die on Collision

        # On passe sur de l'herbe
        if is_color_equal(SCREEN.get_at(collision_point_right),GREEN,20) \
        or is_color_equal(SCREEN.get_at(collision_point_left),GREEN,20) :
        
            ge[i].fitness -= 200
            self.alive = False
        
            
        # If collision with the start line 
        elif (self.rect.colliderect(finish_line_rect) and (time > START_RECORD_FINISH) and time > 10000):
            # Check if the time is better than the best time ever recorded on every car
            if time < best_time or best_time == 0:
                best_time = time
                print(f"Best lap time upgraded !! New best lap : {best_time / 1000}s")
                
                
            # Lancer la fonction pour update le temps d'un tour de terrain
            self.update_track_time(time,i)
                
            print(f"Car {i} crossed the finish line at time {time / 1000}s")
            self.alive = False
            self.finish_line = True


        # Draw Collision Points
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_right, 3)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_left, 3)


    
    # Update best track time and give fitness depending how great is the time upgrade
    def update_track_time(self, time: float,i):
            if time < self.track_time_ms:
                self.track_time_ms = time
                
                # Calculate fitness gain
                ge[i].fitness += 400
            
            if self.previous_track_time_ms == 0 or self.track_time_ms < self.previous_track_time_ms:
                self.previous_track_time_ms = self.track_time_ms
            


def remove(index):
    cars.pop(index)
    ge.pop(index)
    nets.pop(index)


def eval_genomes(genomes, config):

    global cars, ge, nets

    cars = []
    ge = []
    nets = []
    
    # Start of the game
    start_ticks = pygame.time.get_ticks()
    
    for genome_id, genome in genomes:
        cars.append(pygame.sprite.GroupSingle(Car()))
        ge.append(genome)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0    

    
    # Record of the best time ever recorded
    global best_time
    
    run = True
    while run and len(cars) > 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == LAP_START:
                pass
        
        # Regénère tous les élémetns graphiques liées au circuit
        SCREEN.blit(TRACK, (0, 0))


        for i, car in enumerate(cars):
            ge[i].fitness += np.linalg.norm(car.sprite.vel_vector) **2   /4# Increment fitness for each frame, this is a simple way to reward the car for staying alive
            
            time = pygame.time.get_ticks() - start_ticks

          
        # Choix des directions et des actions
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
        arrive = False
        for i, car in enumerate(cars):
            car.draw(SCREEN)
            car.update(ge,i,time,best_time)
            arrive = car.sprite.finish_line
            if arrive :
                break
            
        # Tuer toutes les voitures encore sur la piste après l'arrivée de la première voiture sur la ligne
        if arrive : 
            i = 0
            while len(cars)>0 :
                remove(i)

            
        # Time gestion
        uptime_ms = pygame.time.get_ticks() - start_ticks
        uptime_sec = uptime_ms // 1000
        minutes = uptime_sec // 60
        seconds = uptime_sec % 60
        milliseconds = uptime_ms % 1000
            

        # Display uptime
        uptime_text = font.render(f"Uptime: {minutes:02}:{seconds:02}:{milliseconds:02}", True, BLACK)

        # Show uptime on top left corner
        SCREEN.blit(uptime_text, (120, 80))
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

    pop.run(eval_genomes, 1000)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    run(config_path)
