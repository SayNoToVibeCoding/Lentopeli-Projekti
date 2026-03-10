import mysql.connector
from mysql.connector import Error


def get_connection():
    #Connect to database
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            database="testi",
            user="root",
            password="roni1234",
            auth_plugin='mysql_native_password'
        )
        return connection
    except Error as e:
        if "Authentication plugin" in str(e):
            print("❌ Authentication plugin error detected!")
            print("Your MySQL user is configured with an unsupported authentication method.")
            print("\n🔧 Quick Fix - Run this SQL command in MySQL:")
            print("ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'roni1234';")
            print("FLUSH PRIVILEGES;")
        raise


def save_game(player_name, level, fuel, resources, current_planet_id):
    #Save game progress
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO Player (name, level, fuel, resources, current_planet_id)
        VALUES (%s, %s, %s, %s, %s) 
        ON DUPLICATE KEY UPDATE
            level = VALUES(level), 
            fuel = VALUES(fuel), 
            resources = VALUES(resources), 
            current_planet_id = VALUES(current_planet_id)
        """

        cursor.execute(sql, (player_name, level, fuel, resources, current_planet_id))
        conn.commit()
        print("✅ Game saved successfully!")

    except Error as e:
        print(f"❌ Error saving game: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def load_game(player_name):
    #Load game progress
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT level, fuel, resources, current_planet_id FROM Player WHERE name = %s"
        cursor.execute(sql, (player_name,))

        player_data = cursor.fetchone()

        if player_data:
            print(f"✅ Welcome back, {player_name}!")
            return player_data
        else:
            print("📝 No save file found for this player. Starting a new game!")
            return None

    except Error as e:
        print(f"❌ Error loading game: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_game(player_name):
    #Delete completed
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = "DELETE FROM Player WHERE name = %s"
        cursor.execute(sql, (player_name,))
        conn.commit()
        print(f"Game data for {player_name} deleted.")

    except Error as e:
        print(f"Error deleting game: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
