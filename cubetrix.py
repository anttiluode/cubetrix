from ursina import *
from ursina.prefabs.health_bar import HealthBar
import numpy as np
from scipy.ndimage import gaussian_filter
import random
from threading import Thread
import time
import os
import logging
import queue

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

# Disable logging for comtypes to prevent TTS-related errors
logging.getLogger('comtypes').setLevel(logging.ERROR)

# Initialize Ursina
app = Ursina()

# Global game instance
game = None

# Text-to-Speech Engine Initialization with Queue
class TTSEngine:
    def __init__(self):
        self.queue = queue.Queue()
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Slower speech rate for dramatic effect
            self.thread = Thread(target=self.run_engine)
            self.thread.daemon = True
            self.thread.start()
        except Exception as e:
            print(f"TTS Initialization Error: {e}")
            self.engine = None

    def run_engine(self):
        while True:
            text = self.queue.get()
            if text is None:
                break
            self.speak(text)
            self.queue.task_done()

    def speak(self, text):
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logging.error(f"TTS Error during speaking: {e}")

    def enqueue(self, text):
        if self.engine:
            self.queue.put(text)

tts_engine = TTSEngine()

def speak_async(text):
    try:
        if game and game.tts_enabled and tts_engine.engine:
            tts_engine.enqueue(text)
    except Exception as e:
        print(f"TTS Error: {e}")

# Hardcoded Quotes
NARRATIVE_QUOTES = [
    "You stuck your finger to a USB port and woke up in the Matrix.",
    "The cubes. They're getting closer.",
    "The cubes reminded you of Bob from accounting.",
    "What can a man do to get out of here?",
    "Yippie kai yay, Matrix cube!",
    "Is this real? Are we real? Are cubes real?",
    "The cubetrix never ends.",
    "You remember that time you deleted System32. Good times.",
    "The cubepocalypse is upon us!",
    "The cubes remind me of cubicle.",
    "These cubes are taking their geometry very seriously.",
    "I think I was a cube in my previous life.",
    "Surely the cubetrix has an ending.",
    "What if I am a cube myself.",
    "There are only so many cubes a man can take.",
    "This place reminds me of, never mind, it reminds me of nothing.",
    "The cubetrix smells kind of odd.",
    "At least Neo was living in a more realistic world.",
    "This simulation is lacking definition.",
    "Perhaps I should try to find a backdoor, there must be one.",
    "Is this a cube or am I dreaming.",
    "Look at those mountain tops, let's go chill there for a while, the cubes don't like them.",
    "In the digital world, everyone can hear you scream... in 8-bit."
]

ENEMY_DEATH_PHRASES = [
    "Enemy has fallen!",
    "Down goes the cube!",
    "Cube smashed!",
    "Boxes belong to recycling!",
    "I am sorry cube, but there is only infinite amount of space here!",
    "I did what I had to do!",
    "I hope you won't be back!",
    "Just give up already!",
    "Target neutralized!",
    "Cube destroyed!"
]

DEATH_PHRASES = [
    "Game over, man!",
    "Oh Johnny boy!",
    "Back to real world!",
    "Is reality any better?",
    "I have seen c beams glittering in the dark!",
    "It is time!",
    "Finally, a way out of cubetrix!",
    "Here comes the light!",
    "You met your end!",
    "System failure!",
    "Critical damage detected!"
]

class GameConfig:
    sound_enabled = True
    text_to_speech_enabled = True  # Enabled by default
    quote_interval = 20
    pickup_interval = 15
    pickup_timer = 0
    gravity = -20  # Gravity constant
    jump_force = 15  # Increased jump force for higher jumps

    @classmethod
    def initialize_sounds(cls, game):
        game.background_music = None
        game.shoot_sound = None
        game.footstep_sound = None
        game.death_sound = None
        game.cube_death_sound = None
        game.start_sound = None
        game.jump_sound = None
        game.attack_sound = None

        if cls.sound_enabled:
            try:
                # Check if assets directory exists
                if not os.path.exists('assets'):
                    os.makedirs('assets')
                    print("Created assets directory. Please add sound files.")
                    return

                # Load all required sound files with error handling
                game.start_sound = Audio('assets/start.ogg', loop=False, autoplay=False, volume=1.0)
            except Exception as e:
                print(f"Failed to load start.ogg: {e}")

            try:
                game.background_music = Audio('assets/game.ogg', loop=True, autoplay=False, volume=0.5)
            except Exception as e:
                print(f"Failed to load game.ogg: {e}")

            try:
                game.shoot_sound = Audio('assets/shoot.ogg', loop=False, autoplay=False, volume=0.8)
            except Exception as e:
                print(f"Failed to load shoot.ogg: {e}")

            try:
                game.footstep_sound = Audio('assets/step.ogg', loop=True, autoplay=False, volume=0.5)
            except Exception as e:
                print(f"Failed to load step.ogg: {e}")

            try:
                game.death_sound = Audio('assets/death.ogg', loop=False, autoplay=False, volume=1.0)
            except Exception as e:
                print(f"Failed to load death.ogg: {e}")

            try:
                game.cube_death_sound = Audio('assets/cubedeath.ogg', loop=False, autoplay=False, volume=1.0)
            except Exception as e:
                print(f"Failed to load cubedeath.ogg: {e}")

            try:
                game.jump_sound = Audio('assets/jump.ogg', loop=False, autoplay=False, volume=1.0)
            except Exception as e:
                print(f"Failed to load jump.ogg: {e}")

            try:
                game.attack_sound = Audio('assets/attack.ogg', loop=False, autoplay=False, volume=1.0)
            except Exception as e:
                print(f"Failed to load attack.ogg: {e}")

    @classmethod
    def play_sound(cls, sound, volume=1.0):
        if cls.sound_enabled and sound:
            try:
                sound.volume = volume
                sound.play()
            except Exception as e:
                logging.error(f"Failed to play sound: {e}")

    @classmethod
    def stop_sound(cls, sound):
        if sound:
            try:
                sound.stop()
            except Exception as e:
                logging.error(f"Failed to stop sound: {e}")

class ThinkingField:
    def __init__(self, size=(64, 64), correlation_length=3.0, amplitude=10.0):
        self.size = size
        self.correlation_length = correlation_length
        self.amplitude = amplitude
        self.field = self.initialize_field()

    def initialize_field(self):
        field = np.random.randn(*self.size)
        return self.apply_spatial_correlation(field)

    def apply_spatial_correlation(self, field):
        smoothed_field = gaussian_filter(field, sigma=self.correlation_length)
        smoothed_field *= self.amplitude / (smoothed_field.std() + 1e-7)
        return smoothed_field

    def get_height(self, x, z):
        try:
            x = int(x) % self.size[0]
            z = int(z) % self.size[1]
            return self.field[x, z]
        except:
            return 0

class HealthPill(Entity):
    def __init__(self, position):
        super().__init__(
            model='sphere',
            color=color.green,
            scale=(0.5, 0.2, 0.2),
            position=position,
            collider='box'
        )
        self.rotation_y = random.randint(0, 360)
        self.heal_amount = 50

    def update(self):
        self.rotation_y += 100 * time.dt
        if self.intersects(game.player).hit:
            GameConfig.play_sound(Audio('assets/nom.ogg', autoplay=False), volume=1.0)
            game.player.heal(self.heal_amount)
            destroy(self)

    def take_damage(self, amount):
        if amount >= 1:
            GameConfig.play_sound(Audio('assets/nom.ogg', autoplay=False), volume=1.0)
            game.player.heal(self.heal_amount)
            destroy(self)

class ArmorPickup(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.azure,
            scale=0.3,
            position=position,
            collider='box'
        )
        self.rotation_y = random.randint(0, 360)
        self.armor_amount = 50

    def update(self):
        self.rotation_y += 100 * time.dt
        if self.intersects(game.player).hit:
            GameConfig.play_sound(Audio('assets/armor.ogg', autoplay=False), volume=1.0)
            game.player.add_armor(self.armor_amount)
            destroy(self)

    def take_damage(self, amount):
        if amount >= 1:
            GameConfig.play_sound(Audio('assets/armor.ogg', autoplay=False), volume=1.0)
            game.player.add_armor(self.armor_amount)
            destroy(self)

class Enemy(Entity):
    def __init__(self, position):
        # Randomize size and color
        size = random.uniform(1.5, 4)  # Increased maximum size
        color_options = [
            color.red, color.blue, color.green, color.yellow, color.orange,
            color.magenta, color.cyan, color.gray, color.white
        ]
        color_choice = random.choice(color_options)
        super().__init__(
            model='cube',
            color=color_choice,
            scale=(size, size * 2, size),  # Taller scale for diversity
            position=position,
            collider='box'
        )
        self.original_color = color_choice  # Store original color for color transitions
        self.health = 100
        self.speed = 6  # Increased speed
        self.search_radius = 25  # Slightly increased search radius
        self.attack_range = 5
        self.attack_cooldown = 1.5  # Reduced cooldown
        self.attack_timer = 0
        base_damage = 15  # Increased base damage
        self.damage = base_damage * (size / 1.5)  # Scale damage based on size
        
        # Physics properties
        self.velocity = Vec3(0, 0, 0)
        self.acceleration = Vec3(0, -20, 0)  # Gravity
        self.is_grounded = False

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()
            return
        health_ratio = self.health / 100
        # Darken color as health decreases
        self.color = lerp(color.white, self.original_color, health_ratio)

    def die(self):
        speak_async(random.choice(ENEMY_DEATH_PHRASES))
        if game.cube_death_sound:
            GameConfig.play_sound(game.cube_death_sound)
            
        if random.random() < 0.3:
            if random.random() < 0.7:
                HealthPill(position=self.position)
            else:
                ArmorPickup(position=self.position)
        if game:
            game.score += 50
        destroy(self)
        if self in game.enemies:
            game.enemies.remove(self)

    def attack(self):
        if hasattr(game.player, 'take_damage'):
            game.player.take_damage(self.damage)
            if game.attack_sound:
                GameConfig.play_sound(game.attack_sound)

    def update(self):
        if not game.player or game.game_over or game.game_paused:
            return

        # Apply physics
        if not self.is_grounded:
            self.velocity += self.acceleration * time.dt
            self.y += self.velocity.y * time.dt

        # Ground check and get terrain color
        ground_height = game.field.get_height(self.x, self.z) + 1
        terrain_color = game.get_color_from_height(ground_height - 1)
        
        # Set grounded state
        if self.y <= ground_height:
            self.y = ground_height
            self.velocity.y = 0
            self.is_grounded = True
        else:
            self.is_grounded = False

        # Don't proceed if on snow (white terrain)
        if terrain_color == color.rgb(1, 1, 1):
            return

        # AI behavior
        distance_vec = game.player.position - self.position
        dist = distance_vec.length()

        # Only proceed if within search radius
        if dist < self.search_radius:
            # Line of sight check
            hit_info = raycast(self.position, distance_vec.normalized(), distance=dist, ignore=[self])
            
            # Move towards player if we have line of sight
            if hit_info.hit and hit_info.entity == game.player:
                # Calculate direction to player
                direction = distance_vec.normalized()
                
                # Set target velocity based on direction and speed
                target_velocity = direction * self.speed
                current_velocity = Vec3(self.velocity.x, 0, self.velocity.z)
                
                # Apply acceleration towards target velocity
                acceleration = (target_velocity - current_velocity) * 5
                self.velocity.x += acceleration.x * time.dt
                self.velocity.z += acceleration.z * time.dt
                
                # Update position
                self.x += self.velocity.x * time.dt
                self.z += self.velocity.z * time.dt

                # Attack if in range
                if dist < self.attack_range:
                    self.attack_timer -= time.dt
                    if self.attack_timer <= 0:
                        self.attack()
                        self.attack_timer = self.attack_cooldown

        # Prevent enemies from piling up
        for enemy in game.enemies:
            if enemy != self:
                repel_distance = (enemy.position - self.position).length()
                if repel_distance < 1.5:
                    repel_dir = (self.position - enemy.position).normalized()
                    self.position += repel_dir * time.dt * 2

class Bullet(Entity):
    def __init__(self, position, direction):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.3,
            position=position,
            collider='sphere'
        )
        self.direction = direction
        self.speed = 50
        self.lifetime = 2
        self.damage = 25
        
        # Add trail effect
        self.trail = Entity(
            parent=self,
            model='cube',
            color=color.orange,
            scale=(0.1, 0.1, 0.5)
        )

    def update(self):
        self.lifetime -= time.dt
        if self.lifetime <= 0:
            destroy(self.trail)
            destroy(self)
            return

        # Update bullet position with physics
        ray = raycast(self.position, self.direction, distance=self.speed * time.dt, ignore=[self, game.player])
        if ray.hit:
            if hasattr(ray.entity, 'take_damage'):
                ray.entity.take_damage(self.damage)
                # Add impact effect
                impact = Entity(
                    model='sphere',
                    color=color.yellow,
                    scale=0.5,
                    position=ray.world_point
                )
                impact.animate_scale(0, duration=0.2)
                destroy(impact, delay=0.2)
            destroy(self.trail)
            destroy(self)
            return

        self.position += self.direction * self.speed * time.dt
        
        # Update trail position
        self.trail.look_at(self.position + self.direction)

class Player(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.health = 100
        self.max_health = 100
        self.armor = 100
        self.max_armor = 100
        self.status_text = Text(
            parent=camera.ui,
            text=self.get_status_text(),
            position=(-0.7, -0.4),
            origin=(-0.5, 0.5),
            color=color.white
        )
        # Removed level_text
        self.score = 0
        self.score_text = Text(
            parent=camera.ui,
            text=f'Score: {self.score}',
            position=(0.7, 0.4),
            origin=(0.5, 0.5),
            color=color.white
        )
        self.collider = 'box'
        self.is_moving = False
        self.step_timer = 0
        self.is_dead = False
        self.velocity_y = 0
        self.is_grounded = False

    def get_status_text(self):
        return f'Health: {int(self.health)} | Armor: {int(self.armor)}'

    def take_damage(self, amount):
        amount = amount * 0.4  # Reduce damage to 40% of original
        if self.armor > 0:
            armor_damage = min(self.armor, amount * 0.7)  # Armor absorbs 70% of damage
            self.armor = max(0, self.armor - armor_damage)
            amount = max(0, amount - armor_damage)
        self.health = max(0, self.health - amount)
        self.status_text.text = self.get_status_text()
        if self.health <= 0:
            self.die()

    def heal(self, amount):
        if self.health > 0:  # Only heal if not dead
            self.health = min(self.max_health, self.health + amount)
            self.status_text.text = self.get_status_text()

    def add_armor(self, amount):
        self.armor = min(self.max_armor, self.armor + amount)
        self.status_text.text = self.get_status_text()

    def update_bars(self):
        self.status_text.text = self.get_status_text()
        self.score_text.text = f'Score: {self.score}'

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            GameConfig.stop_sound(game.background_music)
            GameConfig.play_sound(game.death_sound)
            speak_async(random.choice(DEATH_PHRASES))
            game.show_game_over()
            mouse.locked = False

    def jump(self):
        if self.is_grounded:  # Remove cooldown check
            self.velocity_y = GameConfig.jump_force
            self.is_grounded = False
            if game.jump_sound:
                GameConfig.play_sound(game.jump_sound)

    def update(self):
        if self.is_dead:
            return

        # Apply gravity
        if not self.is_grounded:
            self.velocity_y += GameConfig.gravity * time.dt

        # Update position
        self.y += self.velocity_y * time.dt

        # Ground check
        ground_height = game.field.get_height(self.x, self.z) + 1
        if self.y <= ground_height:
            self.y = ground_height
            self.velocity_y = 0
            self.is_grounded = True
        else:
            self.is_grounded = False

class Weapon(Entity):
    def __init__(self, game_instance):
        super().__init__(
            parent=camera.ui,
            model='cube',  # Using 'cube' as a placeholder
            color=color.gray,
            scale=(0.15, 0.15, 0.7),  # Shorter and slimmer
            position=(0.5, -0.25, 0.5),
            rotation=(45, 0, 0)  # Diagonal barrel
        )
        self.game = game_instance
        self.cooldown = 0.2
        self.timer = 0
        
        # Simplified weapon: single diagonal barrel
        self.barrel = Entity(
            parent=self,
            model='cube',  # Replaced 'cone' with 'cube'
            color=color.black,
            scale=(0.05, 0.05, 0.3),  # Adjusted scale for better appearance
            position=(0, 0, 0.35),
            rotation=(90, 0, 0)
        )
        
        # Optionally, add a sight or other parts for better appearance
        self.sight = Entity(
            parent=self,
            model='cube',
            color=color.red,
            scale=(0.05, 0.05, 0.05),
            position=(0, 0.1, 0)
        )

    def shoot(self):
        if self.timer <= 0 and not self.game.game_over:
            self.timer = self.cooldown
            if self.game.shoot_sound:
                GameConfig.play_sound(self.game.shoot_sound)
                
            # Create two slightly spread bullets for better fire pattern
            bullet_direction = camera.forward
            spread = 0.02  # Small spread amount
            
            # Center bullet
            Bullet(
                position=camera.world_position + bullet_direction * 2,
                direction=bullet_direction
            )
            
            # Side bullets with spread
            left_dir = bullet_direction + Vec3(random.uniform(-spread, spread), 
                                            random.uniform(-spread, spread), 
                                            random.uniform(-spread, spread))
            right_dir = bullet_direction + Vec3(random.uniform(-spread, spread), 
                                             random.uniform(-spread, spread), 
                                             random.uniform(-spread, spread))
            
            Bullet(position=camera.world_position + left_dir * 2, direction=left_dir)
            Bullet(position=camera.world_position + right_dir * 2, direction=right_dir)

            # Simple recoil animation
            self.animate_rotation((45, 0, -10), duration=0.05)
            self.animate_rotation((45, 0, 0), delay=0.05, duration=0.1)
            self.animate_position(self.position - Vec3(0.05, 0, 0), duration=0.05)
            self.animate_position(self.position, delay=0.05, duration=0.1)

    def update(self):
        if self.timer > 0:
            self.timer -= time.dt

class ButtonList(Entity):
    def __init__(self, button_dict, y=0, parent=None):
        super().__init__(parent=parent)
        self.buttons = []
        self.start_y = y
        self.spacing = 0.1
        for i, (text, function) in enumerate(button_dict.items()):
            btn = Button(text=text, scale=(0.2, 0.05), y=self.start_y - i * self.spacing, parent=self)
            btn.on_click = function
            self.buttons.append(btn)

class MainMenu(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        
        # Create main menu and help menu entities
        self.main_menu = Entity(parent=self, enabled=True)
        self.help_menu = Entity(parent=self, enabled=False)

        # Main Menu Setup
        self.setup_main_menu()
        
        # Help Menu Setup
        self.setup_help_menu()

    def setup_main_menu(self):
        # Title with shadow effect
        Text(
            text='CUBETRIX',
            parent=self.main_menu,
            scale=5,
            y=.3,
            origin=(0,0),
            color=color.black,
            font='VeraMono.ttf'
        )
        Text(
            text='CUBETRIX',
            parent=self.main_menu,
            scale=5,
            y=.31,
            origin=(0,0),
            color=color.red,
            font='VeraMono.ttf'
        )

        # Main menu buttons
        self.button_list = ButtonList(
            button_dict={
                'Start Game': self.start_game,
                'Help': self.show_help,
                f'Sound: {"ON" if GameConfig.sound_enabled else "OFF"}': self.toggle_sound,
                f'Speech: {"ON" if GameConfig.text_to_speech_enabled else "OFF"}': self.toggle_speech,
                'Quit': application.quit
            },
            y=0,
            parent=self.main_menu
        )

    def setup_help_menu(self):
        # Help menu title
        Text(
            text='How to Play',
            parent=self.help_menu,
            scale=3,
            y=.3,
            origin=(0,0),
            color=color.black
        )

        # Help menu content
        help_text = """
Controls:
WASD - Move
SPACE - Jump
SHIFT - Run
Left Click - Shoot

Tips:
- Shoot health pills and armor pickups to collect them
- Red cubes can't reach snowy peaks
- Collect green health pills and blue armor
- Use high ground to your advantage
- Keep moving to survive longer
"""
        Text(
            text=help_text,
            parent=self.help_menu,
            scale=1.2,
            y=0,
            origin=(0,0),
            color=color.black
        )

        # Back button
        Button(
            text='Back',
            parent=self.help_menu,
            scale=(0.1, 0.05),
            position=(0, -.3),
            color=color.azure,
            on_click=self.show_main_menu
        )

    def start_game(self):
        self.main_menu.enabled = False
        self.help_menu.enabled = False
        game.start_game()

    def show_help(self):
        self.main_menu.enabled = False
        self.help_menu.enabled = True

    def show_main_menu(self):
        self.help_menu.enabled = False
        self.main_menu.enabled = True

    def toggle_sound(self):
        GameConfig.sound_enabled = not GameConfig.sound_enabled
        for button in self.button_list.buttons:
            if button.text.startswith('Sound:'):
                button.text = f'Sound: {"ON" if GameConfig.sound_enabled else "OFF"}'
        if GameConfig.sound_enabled and game.background_music and not game.background_music.playing:
            GameConfig.play_sound(game.background_music)
        elif not GameConfig.sound_enabled and game.background_music:
            GameConfig.stop_sound(game.background_music)

    def toggle_speech(self):
        GameConfig.text_to_speech_enabled = not GameConfig.text_to_speech_enabled
        if game:
            game.tts_enabled = GameConfig.text_to_speech_enabled
        for button in self.button_list.buttons:
            if button.text.startswith('Speech:'):
                button.text = f'Speech: {"ON" if GameConfig.text_to_speech_enabled else "OFF"}'

class ThinkingFieldsGame(Entity):
    def __init__(self):
        super().__init__()
        global game
        game = self

        # Enable/disable features
        self.tts_enabled = GameConfig.text_to_speech_enabled

        self.game_started = False
        self.game_paused = False
        self.game_over = False

        # Initialize field and terrain
        self.field = ThinkingField(size=(64, 64), correlation_length=4.0, amplitude=8.0)
        self.terrain_chunks = {}
        self.chunk_size = 16
        self.render_distance = 3

        # Create sky
        self.sky = Sky()

        # Initialize sounds
        GameConfig.initialize_sounds(self)

        # Create player
        self.player = Player(model='cube', color=color.azure, position=(32, 5, 32), scale=(1, 2, 1))

        self.camera_pivot = Entity(parent=self.player, y=1.5)
        camera.parent = self.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = 90

        # Initialize other components
        self.weapon = Weapon(self)
        self.weapon.enabled = False  # Initially hidden
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 3  # Reduced spawn interval

        self.quote_timer = 0
        self.current_quote_index = 0

        # Use hardcoded quotes
        self.quotes = NARRATIVE_QUOTES
        self.enemy_death_phrases = ENEMY_DEATH_PHRASES
        self.death_phrases = DEATH_PHRASES

        # Create menu
        self.menu = MainMenu()
        self.game_over_entity = None
        GameConfig.pickup_timer = 0

        # Initialize Score
        self.score = 0

    def get_color_from_height(self, height):
        if height < 1:
            return color.rgb(0.6, 0.3, 0.2)  # Brown for low areas
        elif height < 3:
            return color.rgb(0.9, 0.8, 0.5)  # Sand
        elif height < 7:
            return color.rgb(0.2, 0.8, 0.2)  # Grass
        elif height < 10:
            return color.rgb(0.5, 0.5, 0.5)  # Mountain
        else:
            return color.rgb(1, 1, 1)  # Snow

    def reset_game(self):
        # Destroy existing enemies and pickups
        [destroy(e) for e in self.enemies]
        self.enemies = []
        for e in scene.entities:
            if isinstance(e, (HealthPill, ArmorPickup, Bullet, Enemy)):
                destroy(e)

        # Reset player stats and position
        self.player.health = self.player.max_health
        self.player.armor = self.player.max_armor
        self.player.update_bars()
        self.player.position = Vec3(32, 5, 32)
        self.player.is_dead = False
        self.player.score = 0
        self.player.update_bars()

        # Reset camera
        camera.parent = self.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = 90

        # Reset game state
        self.game_over = False
        if self.game_over_entity:
            destroy(self.game_over_entity)
            self.game_over_entity = None

        # Spawn initial enemies
        self.spawn_initial_enemies()

        # Play background music if enabled
        if GameConfig.sound_enabled and self.background_music:
            GameConfig.play_sound(self.background_music)

        # Lock mouse
        mouse.locked = True

        # Enable the weapon
        self.weapon.enabled = True

    def spawn_initial_enemies(self):
        for _ in range(8):  # Increased initial spawn count
            self.spawn_enemy()

    def spawn_enemy(self):
        # Ensure enemies spawn at a minimum distance from the player
        min_distance = 15  # Minimum spawn distance
        max_distance = 30  # Maximum spawn distance
        spawn_distance = random.uniform(min_distance, max_distance)
        angle = random.uniform(0, 360)

        # If player is running, spawn enemies in front
        if held_keys['shift']:
            angle = self.camera_pivot.rotation_y  # Spawn in the direction the player is facing

        x = self.player.x + spawn_distance * np.cos(np.radians(angle))
        z = self.player.z + spawn_distance * np.sin(np.radians(angle))
        y = self.field.get_height(x, z) + 20  # Spawn high above to fall from the sky

        # Additional check to prevent spawning too close (overlap with player)
        distance_from_player = (Vec3(x, y, z) - self.player.position).length()
        if distance_from_player < min_distance:
            # Adjust position further away
            adjustment_distance = min_distance - distance_from_player + 1
            x += adjustment_distance * np.cos(np.radians(angle))
            z += adjustment_distance * np.sin(np.radians(angle))
            y = self.field.get_height(x, z) + 20  # Maintain high spawn position

        enemy = Enemy(position=(x, y, z))
        enemy.game = self
        self.enemies.append(enemy)
        print(f"Spawned enemy at position: ({x:.2f}, {y:.2f}, {z:.2f})")  # Debugging statement

    def spawn_pickup(self):
        spawn_pos = self.player.position + Vec3(
            random.uniform(-20, 20),
            20,
            random.uniform(-20, 20)
        )
        if random.random() < 0.7:
            HealthPill(position=spawn_pos)
        else:
            ArmorPickup(position=spawn_pos)

    def update_terrain(self):
        player_chunk_x = int(self.player.x // self.chunk_size)
        player_chunk_z = int(self.player.z // self.chunk_size)

        for dx in range(-self.render_distance, self.render_distance + 1):
            for dz in range(-self.render_distance, self.render_distance + 1):
                chunk_x = player_chunk_x + dx
                chunk_z = player_chunk_z + dz
                self.generate_chunk(chunk_x, chunk_z)

        # Clean up old chunks
        for (chunk_x, chunk_z) in list(self.terrain_chunks.keys()):
            if abs(chunk_x - player_chunk_x) > self.render_distance or \
               abs(chunk_z - player_chunk_z) > self.render_distance:
                destroy(self.terrain_chunks[(chunk_x, chunk_z)])
                del self.terrain_chunks[(chunk_x, chunk_z)]

    def generate_chunk(self, chunk_x, chunk_z):
        if (chunk_x, chunk_z) in self.terrain_chunks:
            return

        vertices = []
        triangles = []
        colors = []
        uvs = []

        for x in range(self.chunk_size):
            for z in range(self.chunk_size):
                world_x = chunk_x * self.chunk_size + x
                world_z = chunk_z * self.chunk_size + z

                h1 = self.field.get_height(world_x, world_z)
                h2 = self.field.get_height(world_x + 1, world_z)
                h3 = self.field.get_height(world_x, world_z + 1)
                h4 = self.field.get_height(world_x + 1, world_z + 1)

                vertices.extend([
                    Vec3(x, h1, z),
                    Vec3(x + 1, h2, z),
                    Vec3(x, h3, z + 1),
                    Vec3(x + 1, h4, z + 1)
                ])

                offset = len(vertices) - 4
                triangles.extend([
                    (offset, offset + 1, offset + 2),
                    (offset + 1, offset + 3, offset + 2)
                ])

                uvs.extend([
                    (x / self.chunk_size, z / self.chunk_size),
                    ((x + 1) / self.chunk_size, z / self.chunk_size),
                    (x / self.chunk_size, (z + 1) / self.chunk_size),
                    ((x + 1) / self.chunk_size, (z + 1) / self.chunk_size)
                ])

                for h in [h1, h2, h3, h4]:
                    colors.append(self.get_color_from_height(h))

        chunk = Entity(
            model=Mesh(vertices=vertices, triangles=triangles, colors=colors, uvs=uvs),
            collider='mesh',
            position=Vec3(chunk_x * self.chunk_size, 0, chunk_z * self.chunk_size)
        )
        self.terrain_chunks[(chunk_x, chunk_z)] = chunk

    def show_game_over(self):
        self.game_over = True
        time.time_scale = 0.2
        self.game_over_entity = Text(
            text='GAME OVER\nPress R to Restart\nPress ESC for Menu',
            origin=(0, 0),
            scale=2,
            color=color.red,
            background=True
        )
        mouse.locked = False
        # Hide the weapon when game is over
        self.weapon.enabled = False

    def start_game(self):
        if not self.game_started:
            self.game_started = True
            self.game_paused = False

            # Play start sound
            if GameConfig.sound_enabled and self.start_sound:
                GameConfig.play_sound(self.start_sound)

            # Play background music if enabled and not already playing
            if GameConfig.sound_enabled and self.background_music and not self.background_music.playing:
                GameConfig.play_sound(self.background_music)

            # Spawn initial enemies
            self.spawn_initial_enemies()

            # Lock mouse
            mouse.locked = True

            # Enable the weapon
            self.weapon.enabled = True

            # Play introductory voice message
            speak_async("You put your finger in a USB socket and found yourself in CubeTrix.")

    def pause_game(self):
        self.game_paused = True
        mouse.locked = False
        # Removed background_music.pause() to keep music playing when in menu

        # Hide the weapon when paused
        self.weapon.enabled = False

    def resume_game(self):
        if self.game_started and not self.game_over:
            self.game_paused = False
            mouse.locked = True
            if GameConfig.sound_enabled and self.background_music and not self.background_music.playing:
                GameConfig.play_sound(self.background_music)
            
            # Show the weapon when resumed
            self.weapon.enabled = True

    def input(self, key):
        if key == 'escape':
            if self.game_over:
                self.menu.main_menu.enabled = True
                self.game_over = False
                if self.game_over_entity:
                    destroy(self.game_over_entity)
                    self.game_over_entity = None
                # Hide the weapon when returning to menu
                self.weapon.enabled = False
            elif self.game_started:
                if self.game_paused:
                    self.resume_game()
                else:
                    self.pause_game()
                    self.menu.main_menu.enabled = True

        if key == 'space' and self.game_started and not self.game_paused:
            if self.player:
                self.player.jump()

        if key == 'left mouse down' and self.game_started and not self.game_paused:
            if self.weapon:
                self.weapon.shoot()

        if key == 'r' and self.game_over:
            self.reset_game()
            speak_async("Welcome back to CubeTrix!")

    def update_enemies(self):
        for enemy in self.enemies[:]:
            distance = (enemy.position - self.player.position).length()
            if distance > 50:  # Maximum distance before despawning
                destroy(enemy)
                self.enemies.remove(enemy)

    def update(self):
        if not self.game_started or self.game_paused or self.game_over:
            return

        # Set time scale to normal as levels are removed
        time.time_scale = 1.0

        # Update player physics
        if self.player:
            self.player.update()

        # Update terrain
        self.update_terrain()

        # Update enemies
        for enemy in self.enemies:
            enemy.update()

        # Despawn enemies far from the player
        self.update_enemies()

        # Handle pickup spawning
        GameConfig.pickup_timer += time.dt
        if GameConfig.pickup_timer >= GameConfig.pickup_interval:
            GameConfig.pickup_timer = 0
            self.spawn_pickup()

        # Handle quotes
        self.quote_timer += time.dt
        if self.quote_timer >= GameConfig.quote_interval:
            self.quote_timer = 0
            self.current_quote_index = (self.current_quote_index + 1) % len(self.quotes)
            speak_async(self.quotes[self.current_quote_index])

        # Handle enemy spawning
        self.enemy_spawn_timer += time.dt
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0
            self.spawn_enemy()

        # Handle player movement
        move_direction = Vec3(
            self.camera_pivot.forward * (held_keys['w'] - held_keys['s']) +
            self.camera_pivot.right * (held_keys['d'] - held_keys['a'])
        ).normalized()

        # Implement running only when shift is held
        run_multiplier = 2 if held_keys['shift'] else 1

        if move_direction.length() > 0:
            self.player.position += move_direction * 5 * time.dt * run_multiplier
            self.player.is_moving = True
            # Play footstep sound if not already playing
            if GameConfig.sound_enabled and self.footstep_sound and not self.footstep_sound.playing:
                GameConfig.play_sound(self.footstep_sound, volume=0.5)
        else:
            self.player.is_moving = False
            # Stop footstep sound if playing
            if GameConfig.sound_enabled and self.footstep_sound and self.footstep_sound.playing:
                GameConfig.stop_sound(self.footstep_sound)

        # Handle camera rotation
        if mouse.locked:
            self.camera_pivot.rotation_x -= mouse.velocity.y * 40
            self.camera_pivot.rotation_y += mouse.velocity.x * 40
            self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

class GameApp:
    def __init__(self):
        window.title = 'CubeTrix'
        window.borderless = False
        window.fullscreen = False
        window.exit_button.visible = False
        window.fps_counter.enabled = False  # Disable FPS counter
        window.size = (1536, 864)  # Width, Height
        window.position = (192, 108)
        # Set a valid icon if available
        # window.icon = 'assets/ursina.ico'  # Uncomment and set path if you have an icon
        # Initialize game
        self.game = ThinkingFieldsGame()

    def run(self):
        app.run()

if __name__ == '__main__':
    game_app = GameApp()
    game_app.run()
