import pygame
import os
import math
import sys
import neat
import numpy as np

SCREEN_WIDTH = 1452
SCREEN_HEIGHT = 776
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

GREEN = (0,80,0,255)
RED = (251,0,7,255)
YELLOW = (245,255,0,255)
BROWN = (123,68,12,255)
WHITE = (235,234,171,255)
GRAY = (45,45,45,255)



BLACK = (0, 0, 0)

TRACK = pygame.image.load(os.path.join("Assets", "circuit_spa.png"))
# Finish line rectangle
#finish_line_rect = pygame.Rect(540, 767, 17, 107)
finish_line_rect = pygame.Rect(325,550,25,107)
# Checkpoints
#checkpoint_line_rect = pygame.Rect(900,600, 200,10)
checkpoint_line_rect = pygame.Rect(110,560,70,2)
#checkpoint_line_rect_2 = pygame.Rect(500,100, 10,200)
checkpoint_line_rect_2 = pygame.Rect(268,413,70,2)
#checkpoint_line_rect_3 = pygame.Rect(240,600, 200,10)
checkpoint_line_rect_3 = pygame.Rect(0,0,1,1)
# Mur fictif au premier virage pour tuer les voitures au plus vite
mur = pygame.Rect(1100,600,300,300)

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
        self.rect = self.image.get_rect(center=(338, 595))
        self.vel_vector = pygame.math.Vector2(-0.8, 0)
        self.angle = 0
        self.rotation_vel = 5
        self.direction = 0
        self.alive = True
        self.radars = []
        self.action = 0 #-1 frein, 0 rien, 1 accel
        self.checkpoint_pass = [False,False]
        self.one_check = False

        self.colors = {
            "green":(GREEN,False),
            "red":(RED,True),
            "yellow":(YELLOW,True),
            "brown":(BROWN,False),
            "white":(WHITE,False),
            "gray":(GRAY,True)
        }
        #print(self.colors)

        length = 25
        self.length = length
        self.collision_point_right = [int(self.rect.center[0] - math.cos(math.radians(self.angle - 18)) * length),
                                 int(self.rect.center[1] + math.sin(math.radians(self.angle - 18)) * length)]
        self.collision_point_left = [int(self.rect.center[0] - math.cos(math.radians(self.angle + 18)) * length),
                                int(self.rect.center[1] + math.sin(math.radians(self.angle + 18)) * length)]
                        
        # Time gestion variables
        self.track_time_ms = 0
        self.previous_track_time_ms = 0

    def update(self,ge,i,time,best_time):
        self.radars.clear()
        self.update_speed()
        self.drive()
        self.rotate()
        for radar_angle in (-60, -30, 0, 30, 60):
            self.radar(radar_angle)
        self.data()

        self.kill_slow(ge,i,time)
        self.collision(ge,i,time,best_time)
        if not self.alive :
            remove(i)
        """

        founded = False
        for k,v in self.colors.items() : 
            if SCREEN.get_at((self.collision_point_left[0],self.collision_point_left[1])) == v[0]: 
                print(k)
                founded=True
            if SCREEN.get_at((self.collision_point_right[0],self.collision_point_right[1])) == v[0]: 
                print(k)
                founded=True
        if not founded : 
            print(SCREEN.get_at((self.collision_point_right[0],self.collision_point_right[1])))

        print("coucou")"""
        

    def update_speed(self) :
        if(self.action > 0) : 
            self.vel_vector = self.vel_vector * 1.1
        if(self.action < 0) :
            self.vel_vector = self.vel_vector*0.5   
        else :
            self.vel_vector = self.vel_vector *0.9

    def drive(self):
        self.rect.center += self.vel_vector * 6

    def collision(self,ge,i,time,best_time):
        length = 25
        collision_point_right = [int(self.rect.center[0] - math.cos(math.radians(self.angle - 18)) * length),
                                 int(self.rect.center[1] + math.sin(math.radians(self.angle - 18)) * length)]
        collision_point_left = [int(self.rect.center[0] - math.cos(math.radians(self.angle + 18)) * length),
                                int(self.rect.center[1] + math.sin(math.radians(self.angle + 18)) * length)]


 

        # Die on Collision

        # On est en dehors du cadre
        if collision_point_left[0] > SCREEN_WIDTH or collision_point_left[1] > SCREEN_HEIGHT \
        or collision_point_right[0] > SCREEN_WIDTH or collision_point_right[1] > SCREEN_HEIGHT :
            self.alive = False
            #remove(i)

        # On passe sur de l'herbe ou une bande blanche
        elif is_color_equal(SCREEN.get_at(collision_point_right),GREEN,10) \
        or is_color_equal(SCREEN.get_at(collision_point_left),GREEN,10) :
        
            ge[i].fitness -= 200
            self.alive = False
            #remove(i)

        #prend le mur
        elif self.rect.colliderect(mur) and (time > START_RECORD_FINISH) and self.alive:
            ge[i].fitness -= 200
            self.alive = False
            print('murhan')
           # remove(i)

       # Passe un check point 1
        elif self.rect.colliderect(checkpoint_line_rect) and (time > START_RECORD_FINISH) and not self.checkpoint_pass[0]:
            print("checkpoint 1 passed")
            self.checkpoint_pass.append(True)
            self.checkpoint_pass[0] = True
            ge[i].fitness += 20

        # Passe un check point 2
        elif self.rect.colliderect(checkpoint_line_rect_2) and (time > START_RECORD_FINISH)  and not self.checkpoint_pass[1]:
            print("checkpoint 2 passed")
            self.checkpoint_pass.append(True)
            self.checkpoint_pass[1] = True
            ge[i].fitness += 40

        # Passe un check point 3
        elif self.rect.colliderect(checkpoint_line_rect_3) and (time > START_RECORD_FINISH)  and not self.one_check:
            print("checkpoint 3 passed")
            self.checkpoint_pass.append(True)
            self.one_check = True
            ge[i].fitness += 60

        
            
        # If collision with the start line 
        elif (self.rect.colliderect(finish_line_rect) and (time > START_RECORD_FINISH) and self.one_check):
            # Check if the time is better than the best time ever recorded on every car
            if time < best_time or best_time == 0:
                best_time = time
                print(f"Best lap time upgraded !! New best lap : {best_time / 1000}s")
                
                
            # Lancer la fonction pour update le temps d'un tour de terrain
            self.update_track_time(time)
                
            print(f"Car {i} crossed the finish line at time {time / 1000}s")
            self.alive = False
            #remove(i)

               # Draw Collision Points
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_right, 3)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_left, 3)


    def kill_slow(self,ge,i,time) :

        #Tuer les voitures les plus lentes
        if abs(np.linalg.norm(self.vel_vector)) <0.1 :
            ge[i].fitness -= 400
            self.alive = False
            #remove(i)


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

            while x <1450 and y < 760 and not is_color_equal(SCREEN.get_at((x, y)),GREEN,10) and length < 100:
                length += 1
                x = int(self.rect.center[0] - math.cos(math.radians(self.angle + radar_angle)) * length)
                y = int(self.rect.center[1] + math.sin(math.radians(self.angle + radar_angle)) * length)

        # Draw Radar
      #  pygame.draw.line(SCREEN, (2, 105, 31, 255), self.rect.center, (0, 0), 10)
        pygame.draw.line(SCREEN, (255, 255, 255, 255), self.rect.center, (x, y), 1)
        pygame.draw.circle(SCREEN, (0, 255, 0, 0), (x, y), 3)
        

        dist = int(math.sqrt(math.pow(self.rect.center[0] - x, 2)
                             + math.pow(self.rect.center[1] - y, 2)))

        self.radars.append([radar_angle, dist])


    def data(self):
        input = [0, 0, 0, 0, 0]
        for i, radar in enumerate(self.radars):
            input[i] = int(radar[1])
        return input

    
    # Update best track time and give fitness depending how great is the time upgrade
    def update_track_time(self, time: float):

            if time < self.track_time_ms:
                self.track_time_ms = time
                
                # Calculate fitness gain
                # TODO: Faire un calcul correct pour le fitness
                ge[i].fitness += 100
            
            if self.previous_track_time_ms == 0 or self.track_time_ms < self.previous_track_time_ms:
                self.previous_track_time_ms = self.track_time_ms
            


def remove(index):
    cars.pop(index)
    ge.pop(index)
    nets.pop(index)

def regenerate_map() :
    SCREEN.blit(TRACK, (0, 0))

    # Génération des checkpoints
    pygame.draw.rect(SCREEN, (0, 0, 230), checkpoint_line_rect )
    pygame.draw.rect(SCREEN, (0, 0, 230), checkpoint_line_rect_2)
    #pygame.draw.rect(SCREEN, (0, 0, 230), checkpoint_line_rect_3)

    #pygame.draw.rect(SCREEN, (250, 0, 0), mur)

            
    # Draw the track start line
    pygame.draw.rect(SCREEN, (255, 0, 230), finish_line_rect) # TODO merge Ysa: Check si la ligne finish_line_rect on en fait pas un checkpoint ?
    


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
        regenerate_map()



        for i, car in enumerate(cars):
            #ge[i].fitness += np.linalg.norm(car.sprite.vel_vector) **2 /2   # Increment fitness for each frame, this is a simple way to reward the car for staying alive

            
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
        for i, car in enumerate(cars):
           # car.sprite.image = pygame.transform.flip(car.sprite.image, True, False)
            car.draw(SCREEN)
            car.update(ge,i,time,best_time)
            
        # Cursor position
        # Position temps réel du curseur
        x, y = pygame.mouse.get_pos()

        text = font.render(f"Position souris : {x}, {y}", True, (0, 0, 0))
        SCREEN.blit(text, (100, 130))
            
        # Time gestion
        uptime_ms = pygame.time.get_ticks() - start_ticks
        uptime_sec = uptime_ms // 1000
        minutes = uptime_sec // 60
        seconds = uptime_sec % 60
        milliseconds = uptime_ms % 1000

        # Tue les voitures hors checkpoint
        if(uptime_sec % 7 == 0 and uptime_sec >0 and ok_check):
            for car in cars:
                i = 0
                check = False
                while i< len(car.sprite.checkpoint_pass) and not check :
                    if car.sprite.checkpoint_pass[i] :
                        car.sprite.checkpoint_pass[i] = False
                        check = True
                    i+=1
                if not check :
                    car.sprite.alive = False

                    """
                if(len(car.sprite.checkpoint_pass) == 0) :
                    #ge[i].fitness -= 500
                    car.sprite.alive = False
                    #remove(i)
                    #print(i)
                    print("Pas de check")
                   
                else :
                    car.sprite.checkpoint_pass=[]
                    #car.sprite.one_check = False
                    print("ça dépop")"""
            ok_check = False

        for i, car in enumerate(cars):
            if not car.sprite.alive : 
                remove(i)

        if(uptime_sec % 7 == 1) : 
            ok_check =True

        
            

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

    pop.run(eval_genomes, 100)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    run(config_path)
