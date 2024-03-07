"""TODO list
1) Use native vectors to increase performance
2) Polar form when
3) Blast off animation
"""

import math
from collections import namedtuple
from enum import Enum
import random


import pygame

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600

GRAVITY_ACCELERATION = 9.8 * 2
GROUND_LEVEL = SCREEN_HEIGHT - 10
PARTICLE_VELOCITY = 250
PARTICLE_VELOCITY_NOISE = 25


PARTICLE_SIZE = 2

TRACE_LIFETIME = 0.45
TRACE_SIZE = 1
TRACE_LIFETIME_NOISE = 100  # %
TRACE_THRESHOLD = 0.4

DRAG = 25

Coordinate = namedtuple('Coordinate', ['x', 'y'])
Velocity = namedtuple('Velocity', ['x', 'y'])


class Colors(Enum):
    # 👀 -> misc/Colored-Fire-Spray-Bottles.png
    LITHIUM_PINK = (158, 44, 129)
    STRONTIUM_RED = (236, 60, 22)
    POTASSIUM_VIOLET = (243, 135, 112)
    SODIUM_YELLOW = (254, 230, 172)
    CALCIUM_ORANGE = (203, 64, 7)
    COPPER_GREEN = (77, 199, 46)


def random_velocity() -> Velocity:
    noise = random.randint(
        -PARTICLE_VELOCITY_NOISE, PARTICLE_VELOCITY_NOISE
    ) / 100

    particle_velocity = int(PARTICLE_VELOCITY * (1 + noise))

    random_x = random.randint(-particle_velocity, particle_velocity)

    return Velocity(
        random_x,
        math.sqrt(particle_velocity**2 - random_x**2) * random.choice((-1, 1))
    )


def random_lifetime() -> float:
    return random.randint(1500, 2000) / 1000


def random_amount() -> int:
    return random.randint(50, 80)


class Particle:
    def __init__(
            self, coordinate: Coordinate,
            velocity: Velocity = None,
            lifetime: int = None,
            color: Colors = None
    ):
        self.coordinate = coordinate

        # Let them be random if not provided
        self.velocity = velocity or random_velocity()
        self.lifetime = lifetime or random_lifetime()
        self.color = color or random.choice(list(Colors))

    @property
    def hit_ground(self) -> bool:
        return self.coordinate.y >= GROUND_LEVEL

    @property
    def burned(self) -> bool:
        return self.lifetime <= 0

    @property
    def full_velocity(self) -> float:
        return math.sqrt(self.velocity.x**2 + self.velocity.y**2)

    def tick(self, ticks: float) -> None:
        # First approach: velocity first
        # self.velocity = Velocity(
        #     self.velocity.x * (1 - DRAG / 1000),
        #     (self.velocity.y + GRAVITY_ACCELERATION * ticks / 1000) * (1 - DRAG / 1000)
        # )
        # self.coordinate = Coordinate(
        #     self.coordinate.x + self.velocity.x * ticks / 1000,
        #     self.coordinate.y + self.velocity.y * ticks / 1000
        # )

        # Second approach: coordinates first
        # self.coordinate = Coordinate(
        #     self.coordinate.x + self.velocity.x * ticks / 1000,
        #     self.coordinate.y + self.velocity.y * ticks / 1000
        # )
        # self.velocity = Velocity(
        #     self.velocity.x * (1 - DRAG / 1000),
        #     (self.velocity.y + GRAVITY_ACCELERATION * ticks / 1000) * (1 - DRAG / 1000)
        # )

        # Third approach: mean velocity
        previous_velocity = self.velocity
        self.velocity = Velocity(
            self.velocity.x * (1 - DRAG / 1000),
            self.velocity.y * (1 - DRAG / 1000) + GRAVITY_ACCELERATION * ticks / 1000
        )
        mean_velocity = Velocity(
            (previous_velocity.x + self.velocity.x) / 2,
            (previous_velocity.y + self.velocity.y) / 2
        )
        self.coordinate = Coordinate(
            self.coordinate.x + mean_velocity.x * ticks / 1000,
            self.coordinate.y + mean_velocity.y * ticks / 1000
        )

        self.lifetime -= ticks / 1000

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface, self.color.value, self.coordinate, PARTICLE_SIZE
        )

    def __repr__(self) -> str:
        return (
            f"Particle(coordinate={self.coordinate}, "
            f"velocity={self.velocity}, "
            f"lifetime={self.lifetime}, "
            f"color={self.color})"
        )


class Trace:
    def __init__(self, coordinate: Coordinate, color: Colors):
        self.coordinate = coordinate
        lifetime_noise = random.randint(
            -TRACE_LIFETIME_NOISE, TRACE_LIFETIME_NOISE
        ) / 100
        self.lifetime = TRACE_LIFETIME * (1 + lifetime_noise)
        self.color = color

    @property
    def burned(self) -> bool:
        return self.lifetime <= 0

    def tick(self, ticks: float) -> None:
        self.lifetime -= ticks / 1000


class Crisp(Particle):
    """Particle-like object, but it will be drawn only after end of lifetime
    for a short amount of time, `lifetime` increased on this short amount by
    redefinition of `burned` property.

    # TODO: redesign
    Better not to inherit from Particle, because it has different mechanic and
    `burned` property does not represent life cycle of `Crisp`. Instead, common
    abstract ancestor must be implemented for physics emulation (which is the
    same for any physical particle) and inherit usual particle and `crisp` from
    such ancestor.
    """
    @property
    def burned(self) -> bool:
        return self.lifetime <= -0.1

    def draw(self, surface: pygame.Surface) -> None:
        if self.lifetime > 0:
            return

        pygame.draw.circle(
            surface, self.color.value, self.coordinate, PARTICLE_SIZE * 1.5
        )


class Firework:
    def __init__(
            self, initial_coordinate: Coordinate, colors: list[Colors] = None,
            do_blast_off: bool = False
    ):
        self.coordinate = initial_coordinate
        self.do_blast_off = do_blast_off

        self.particles: list[Particle] = []
        self.traces: list[Trace] = []
        self.boomed = False
        self.colors = colors

    def boom(self):
        self.particles = [
            Particle(self.coordinate, color=self.colors and random.choice(self.colors)) for _ in range(random_amount())
        ]
        self.particles.extend(
            Crisp(self.coordinate, color=self.colors and random.choice(self.colors)) for _ in range(random_amount())
        )

    def run(self, ticks):
        if self.do_blast_off:
            # TODO blast_off and fly animation
            raise NotImplementedError()

        if not self.boomed:
            self.boom()
            self.boomed = True

        live_particles = []
        for particle in self.particles:
            if type(particle) == Particle:
                if random.random() > TRACE_THRESHOLD:
                    self.traces.append(Trace(particle.coordinate, particle.color))
            particle.tick(ticks)

            if particle.burned or particle.hit_ground:
                continue

            live_particles.append(particle)
        self.particles = live_particles

        live_traces = []
        for trace in self.traces:
            trace.tick(ticks)

            if not trace.burned:
                live_traces.append(trace)

        self.traces = live_traces

    def draw(self, screen: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(screen)
        for trace in self.traces:
            pygame.draw.circle(
                screen,
                trace.color.value,
                (trace.coordinate.x, trace.coordinate.y),
                TRACE_SIZE
            )


def fps_counter(clock: pygame.time.Clock, surface: pygame.Surface):
    fps = str(int(clock.get_fps()))
    font = pygame.font.SysFont("Arial", 18, bold=True)
    fps_t = font.render(fps, 1, pygame.Color("YELLOW"))
    surface.blit(fps_t, (0, 0))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Firework Simulation")
    clock = pygame.time.Clock()
    fireworks: list[Firework] = []
    running = True
    while running:
        screen.fill((0, 0, 0))
        fps_counter(clock, screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                fireworks.append(
                    Firework(  # Firework with defined colors
                        Coordinate(*event.pos), colors=random.sample(list(Colors), 2)
                    )
                    # Firework(Coordinate(*event.pos))  # Mix
                )

        pygame.draw.line(
            screen,
            (100, 100, 100),
            (0, GROUND_LEVEL),
            (SCREEN_WIDTH, GROUND_LEVEL)
        )

        dt = clock.tick(90)
        live_fireworks: list[Firework] = []
        for firework in fireworks:
            firework.run(dt)
            firework.draw(screen)
            if firework.particles or firework.traces:
                live_fireworks.append(firework)
        fireworks = live_fireworks

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
