import os 
import time
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_character_codes():
    try:
        response = requests.get('https://www.e7vau.lt/static/portraits.json')
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al obtener los códigos de personajes: {e}")
        return {}

def get_character_names(battle, team_class, character_codes):
    selected_characters = []
    banned_characters = []
    prebanned_characters = []
    
    try:
        ul_elements = battle.find_elements(By.CSS_SELECTOR, f'div.battle-result-detail > {team_class} > ul')
        
        for ul in ul_elements:
            li_elements = ul.find_elements(By.TAG_NAME, 'li')
            for li in li_elements:
                try:
                    tooltip_id = li.get_attribute('data-tooltip-id')
                    img = li.find_element(By.CSS_SELECTOR, 'span > img')
                    alt_text = img.get_attribute('alt')

                    character_name = character_codes.get(alt_text, {}).get('name', 'Unknown')
                    
                    classes = li.get_attribute('class').split()
                    if 'ban' in classes:
                        banned_characters.append(character_name)
                    elif 'preban-hero' in classes:
                        prebanned_characters.append(character_name)
                    else:
                        selected_characters.append(character_name)

                except Exception as e:
                    print(f"Error al obtener la información del héroe: {e}")
                    continue

    except Exception as e:
        print(f"Error al procesar los ul del equipo {team_class}: {e}")
    
    return selected_characters, banned_characters, prebanned_characters

def process_battles(driver, wait, character_codes):
    results = []
    
    try:
        battle_info_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#battleList > ul > li.battle-info')))
        
        for i, battle in enumerate(battle_info_elements):
            battle_class = battle.get_attribute("class")
            battle_text = battle.text
            
            if "Turns 0" in battle_text:
                continue
            
            win_status = 1 if 'win' in battle_class else 0

            # Obtener la información del equipo propio
            selected_characters, banned_characters, prebanned_characters = get_character_names(battle, '.my-team.w-100', character_codes)
            own_characters = selected_characters[:4]  # Obtener hasta 4 personajes
            own_banned = banned_characters[:1]  # Obtener hasta 1 personaje baneado
            own_preban = prebanned_characters[:2]  # Obtener hasta 2 personajes prebaneados
            
            # Obtener la información del equipo enemigo
            opponent_characters, opponent_banned, opponent_preban = get_character_names(battle, '.enemy-team.w-100', character_codes)
            opponent_characters = opponent_characters[:4]  # Obtener hasta 4 personajes
            opponent_banned = opponent_banned[:1]  # Obtener hasta 1 personaje baneado
            opponent_preban = opponent_preban[:2]  # Obtener hasta 2 personajes prebaneados

            results.append({
                "player_id": i + 1,
                "character_1": own_characters[0] if len(own_characters) > 0 else "",
                "character_2": own_characters[1] if len(own_characters) > 1 else "",
                "character_3": own_characters[2] if len(own_characters) > 2 else "",
                "character_4": own_characters[3] if len(own_characters) > 3 else "",
                "banned_character": own_banned[0] if len(own_banned) > 0 else "",
                "win": win_status,
                "opponent_character_1": opponent_characters[0] if len(opponent_characters) > 0 else "",
                "opponent_character_2": opponent_characters[1] if len(opponent_characters) > 1 else "",
                "opponent_character_3": opponent_characters[2] if len(opponent_characters) > 2 else "",
                "opponent_character_4": opponent_characters[3] if len(opponent_characters) > 3 else "",
                "opponent_banned_character": opponent_banned[0] if len(opponent_banned) > 0 else "",
                "preban_1": own_preban[0] if len(own_preban) > 0 else "",
                "preban_2": own_preban[1] if len(own_preban) > 1 else "",
                "opponent_preban_1": opponent_preban[0] if len(opponent_preban) > 0 else "",
                "opponent_preban_2": opponent_preban[1] if len(opponent_preban) > 1 else ""
            })

    except Exception as e:
        print("No se pudieron encontrar las partidas:", e)

    return results

def save_to_csv(results, filename):
    """
    Guarda los resultados en un archivo CSV.
    
    :param results: Lista de diccionarios con los datos de las partidas.
    :param filename: Nombre del archivo CSV a guardar.
    """
    # Crear el directorio si no existe
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    fieldnames = [
        "player_id",
        "character_1",
        "character_2",
        "character_3",
        "character_4",
        "banned_character",
        "win",
        "opponent_character_1",
        "opponent_character_2",
        "opponent_character_3",
        "opponent_character_4",
        "opponent_banned_character",
        "preban_1",
        "preban_2",
        "opponent_preban_1",
        "opponent_preban_2"
    ]
    
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    except PermissionError as e:
        print(f"Error al guardar el archivo CSV: {e}")

# Usar una ruta absoluta o una ruta en el directorio actual
csv_filename = '../data/battle_data.csv'  # Cambia esto a la ruta deseada

def main():
    # Obtener los códigos de personajes
    character_codes = fetch_character_codes()
    
    # Configuración de Selenium (usando Chrome)
    options = webdriver.ChromeOptions()
    options.add_argument('start-fullscreen')  # Ejecutar sin abrir el navegador
    driver = webdriver.Chrome(options=options)

    # URL del historial de partidas
    url = "https://epic7.gg.onstove.com/en/battlerecord/world_kor/119456895"
    driver.get(url)

    # Esperar a que la página cargue completamente
    wait = WebDriverWait(driver, 10)
    time.sleep(5)  # Espera adicional para asegurar que todo el contenido esté cargado

    # Procesar las batallas
    results = process_battles(driver, wait, character_codes)

    # Guardar los resultados en un archivo CSV
    save_to_csv(results, csv_filename)

    # Cerrar el navegador
    driver.quit()

if __name__ == "__main__":
    main()