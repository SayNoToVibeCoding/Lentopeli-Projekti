import random
import mysql.connector
from mysql.connector import Error
from game_utils import save_game, load_game, delete_game


class SpaceGame:
    def __init__(self, db_config):
        #Mysql connection
        try:
            db_config['auth_plugin'] = 'mysql_native_password'
            self.db = mysql.connector.connect(**db_config)
            self.cursor = self.db.cursor(dictionary=True)

            self.game_id = None
            self.fuel = 100
            self.max_fuel = 100
            self.round = 1
            self.resources = {'Water': 0, 'Food': 0, 'Technology': 0}
            self.planets_visited = []
            self.player_name = None

            print("Connected to database")
        except Error as e:
            print(f"Failed to connect to database: {e}")
            raise

    def create_game(self):
        #New game
        try:
            query = """
                    INSERT INTO game (co2_consumed, co2_budget, screen_name, location)
                    VALUES (0, 100, %s, 'Earth') \
                    """
            self.cursor.execute(query, (self.player_name,))
            self.db.commit()
            self.game_id = self.cursor.lastrowid

            # Resources
            for resource_name in ['Water', 'Food', 'Technology']:
                self.cursor.execute("SELECT id FROM resource WHERE name = %s", (resource_name,))
                result = self.cursor.fetchone()

                if not result:
                    print(f"Warning: Resource '{resource_name}' not found")
                    continue

                self.cursor.execute("""
                                    INSERT INTO game_resource (game_id, resource_id, amount)
                                    VALUES (%s, %s, 0)
                                    """, (self.game_id, result['id']))

            self.db.commit()
        except Error as e:
            print(f"Error creating game: {e}")
            self.db.rollback()

    def get_planets(self):
        #Randomize planets
        try:
            query = "SELECT ident, name, elevation_ft FROM airport ORDER BY RAND() LIMIT 5"
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching planets: {e}")
            return []

    def prepare_planets(self, planets):
        #Randomize planet data
        prepared = []

        for planet in planets:
            prepared.append({
                'ident': planet['ident'],
                'name': planet['name'],
                'elevation': planet['elevation_ft'],
                'fuel_cost': random.randint(5, 30),
                'rewards': {
                    'Water': random.randint(0, 5),
                    'Food': random.randint(0, 5),
                    'Technology': random.randint(0, 5)
                }
            })

        return prepared

    def show_round_info(self, planets):
        #Display player data and destinations
        print("\n" + "=" * 70)
        print(f"ROUND {self.round}")
        print("=" * 70)
        print(f"Fuel: {self.fuel}% / {self.max_fuel}%")
        print(
            f"Resources - Water: {self.resources['Water']} | Food: {self.resources['Food']} | Tech: {self.resources['Technology']}")
        print("\n" + "-" * 70)
        print("PLANETS TO EXPLORE:")
        print("-" * 70)

        for i, planet in enumerate(planets, 1):
            print(f"\n{i}. {planet['name'].upper()} (ID: {planet['ident']})")
            print(f"   Elevation: {planet['elevation']} ft")
            print(f"   Fuel needed: {planet['fuel_cost']}%")

            water, food, tech = planet['rewards']['Water'], planet['rewards']['Food'], planet['rewards']['Technology']
            print(f"   Rewards: Water +{water} | Food +{food} | Tech +{tech}")

        print("\n" + "-" * 70)

    def random_event(self):
        #Roll event
        roll = random.randint(1, 6)
        print(f"\nDice roll: {roll}")

        try:
            self.cursor.execute("SELECT id, name, description, fuel_effect FROM event ORDER BY RAND() LIMIT 1")
            event = self.cursor.fetchone()

            if event:
                print(f"\nEvent: {event['name']}")
                print(f"{event['description']}")

                if event['fuel_effect'] != 0:
                    self.fuel += event['fuel_effect']
                    effect_type = "gained" if event['fuel_effect'] > 0 else "lost"
                    print(f"Fuel {effect_type}: {abs(event['fuel_effect'])}%")

                self.cursor.execute("""
                                    INSERT INTO game_event (game_id, event_id, round)
                                    VALUES (%s, %s, %s)
                                    """, (self.game_id, event['id'], self.round))
                self.db.commit()

        except Error as e:
            print(f"Event error: {e}")

        return roll

    def travel_to(self, planet):
        #Travel to planet
        cost = planet['fuel_cost']

        print(f"\nTraveling to {planet['name'].upper()}...")

        if self.fuel < cost:
            print(f"Not enough fuel! Need {cost}% but have {self.fuel}%")
            return False

        self.fuel -= cost
        print(f"Fuel used: {cost}% (remaining: {self.fuel}%)")

        print("\nResources found:")
        got_anything = False
        for resource_type, amount in planet['rewards'].items():
            if amount > 0:
                self.resources[resource_type] += amount
                print(f"  {resource_type}: +{amount}")
                got_anything = True

        if not got_anything:
            print("  Nothing of value here...")

        self.planets_visited.append(planet['name'])
        return True

    def check_victory(self):
        #Check WinCon
        has_water = self.resources['Water'] >= 10
        has_food = self.resources['Food'] >= 10
        has_tech = self.resources['Technology'] >= 10
        enough_planets = len(self.planets_visited) >= 5

        return has_water and has_food and has_tech and enough_planets

    def run(self):
        #DA LOOP
        print("\n" + "=" * 70)
        print("SPACE EXPLORATION GAME")
        print("=" * 70)
        print("\nYour mission: Find a suitable planet for humanity")
        print("Collect resources and manage your fuel carefully.\n")

        self.player_name = input("Enter your pilot name: ")

        # Try to load existing save
        save_file = load_game(self.player_name)
        if save_file:
            self.fuel = save_file['fuel']
            self.round = save_file['level']
        else:
            self.create_game()

        # Game loop
        while True:
            planets = self.get_planets()
            if not planets:
                print("Error: Could not load planets. Check database connection.")
                break

            planets_data = self.prepare_planets(planets)

            # Filter planets based fuel
            affordable_planets = [p for p in planets_data if p['fuel_cost'] <= self.fuel]

            if not affordable_planets:
                print("\n" + "=" * 70)
                print("GAME OVER - Not enough fuel to reach any planet")
                print(f"You explored {self.round} rounds.")
                print("=" * 70)
                save_game(self.player_name, self.round, self.fuel, sum(self.resources.values()), 1)
                break

            self.show_round_info(affordable_planets)

            # Get player choice
            while True:
                try:
                    choice = int(input(f"Choose planet (1-{len(affordable_planets)}): "))
                    if 1 <= choice <= len(affordable_planets):
                        break
                    print(f"Enter a number between 1 and {len(affordable_planets)}")
                except ValueError:
                    print("Invalid input")

            selected = affordable_planets[choice - 1]

            # Try to travel
            if not self.travel_to(selected):
                continue

            self.random_event()

            # Check if out of fuel after event
            if self.fuel <= 0:
                print("\n" + "=" * 70)
                print("GAME OVER - Out of fuel")
                print(f"You explored {self.round} rounds before running out of fuel.")
                print("=" * 70)
                save_game(self.player_name, self.round, self.fuel, sum(self.resources.values()), 1)
                delete_game(self.player_name)
                break

            # Check wincon
            if self.check_victory():
                print("\n" + "=" * 70)
                print("SUCCESS!")
                print("You found a suitable planet for humanity to colonize.")
                print(f"Water: {self.resources['Water']} | Food: {self.resources['Food']} | Tech: {self.resources['Technology']}")
                print("=" * 70)
                save_game(self.player_name, self.round, self.fuel, sum(self.resources.values()), 1)
                delete_game(self.player_name)
                break

            save_game(self.player_name, self.round, self.fuel, sum(self.resources.values()), 1)

            self.round += 1
            input("\nPress Enter for next round...")

        self.cursor.close()
        self.db.close()

if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'roni1234',
        'database': 'testi'
    }

    try:
        game = SpaceGame(db_config)
        game.run()
    except KeyboardInterrupt:
        print("\nQuitting...")
    except Exception as e:
        print(f"Error: {e}")
