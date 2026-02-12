import json
import random
import os
import math
import copy

# --- 0. CLASSI BASE ---

class Move:
    def __init__(self, name, type, power, accuracy, category):
        self.name = name
        self.type = type
        self.power = power
        self.accuracy = accuracy
        self.category = category    
    def __repr__(self):
        return f"{self.name} ({self.type}, {self.category})"

class Pokemon:
    def __init__(self, p_id, name, types, hp, atk, dfs, sp_atk, sp_dfs, speed, moves):
        self.id = p_id 
        self.name = name
        self.types = types
        self.max_hp = hp
        self.current_hp = hp
        self.attack = atk
        self.defense = dfs
        self.sp_attack = sp_atk
        self.sp_defense = sp_dfs
        self.speed = speed
        self.moves = moves

    def is_fainted(self):
        return self.current_hp <= 0

    def take_damage(self, amount):
        self.current_hp -= amount
        if self.current_hp < 0: self.current_hp = 0

    def __repr__(self):
        # Rappresentazione stringa per i log
        return f"{self.name} (HP: {self.current_hp}/{self.max_hp})"

# Tabella Tipi 
TYPE_CHART = {
    "Normal":   {"Rock": 0.5, "Ghost": 0.0, "Steel": 0.5},
    "Fire":     {"Fire": 0.5, "Water": 0.5, "Grass": 2.0, "Ice": 2.0, "Bug": 2.0, "Rock": 0.5, "Dragon": 0.5, "Steel": 2.0},
    "Water":    {"Fire": 2.0, "Water": 0.5, "Grass": 0.5, "Ground": 2.0, "Rock": 2.0, "Dragon": 0.5},
    "Electric": {"Water": 2.0, "Electric": 0.5, "Grass": 0.5, "Ground": 0.0, "Flying": 2.0, "Dragon": 0.5},
    "Grass":    {"Fire": 0.5, "Water": 2.0, "Grass": 0.5, "Poison": 0.5, "Ground": 2.0, "Flying": 0.5, "Bug": 0.5, "Rock": 2.0, "Dragon": 0.5, "Steel": 0.5},
    "Ice":      {"Fire": 0.5, "Water": 0.5, "Grass": 2.0, "Ice": 0.5, "Ground": 2.0, "Flying": 2.0, "Dragon": 2.0, "Steel": 0.5},
    "Fighting": {"Normal": 2.0, "Ice": 2.0, "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Rock": 2.0, "Ghost": 0.0, "Dark": 2.0, "Steel": 2.0, "Fairy": 0.5},
    "Poison":   {"Grass": 2.0, "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0.0, "Fairy": 2.0},
    "Ground":   {"Fire": 2.0, "Electric": 2.0, "Grass": 0.5, "Poison": 2.0, "Flying": 0.0, "Bug": 0.5, "Rock": 2.0, "Steel": 2.0},
    "Flying":   {"Electric": 0.5, "Grass": 2.0, "Fighting": 2.0, "Bug": 2.0, "Rock": 0.5, "Steel": 0.5},
    "Psychic":  {"Fighting": 2.0, "Poison": 2.0, "Psychic": 0.5, "Dark": 0.0, "Steel": 0.5},
    "Bug":      {"Fire": 0.5, "Grass": 2.0, "Fighting": 0.5, "Poison": 0.5, "Flying": 0.5, "Psychic": 2.0, "Ghost": 0.5, "Dark": 2.0, "Steel": 0.5, "Fairy": 0.5},
    "Rock":     {"Fire": 2.0, "Ice": 2.0, "Fighting": 0.5, "Ground": 0.5, "Flying": 2.0, "Bug": 2.0, "Steel": 0.5},
    "Ghost":    {"Normal": 0.0, "Psychic": 2.0, "Ghost": 2.0, "Dark": 0.5},
    "Dragon":   {"Dragon": 2.0, "Steel": 0.5, "Fairy": 0.0},
    "Steel":    {"Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Ice": 2.0, "Rock": 2.0, "Steel": 0.5, "Fairy": 2.0},
    "Dark":     {"Fighting": 0.5, "Psychic": 2.0, "Ghost": 2.0, "Dark": 0.5, "Fairy": 0.5},
    "Fairy":    {"Fire": 0.5, "Fighting": 2.0, "Poison": 0.5, "Dragon": 2.0, "Dark": 2.0, "Steel": 0.5}
}

def get_type_effectiveness(move_type, target_types):
    modifier = 1.0
    for t_type in target_types:
        if move_type in TYPE_CHART and t_type in TYPE_CHART[move_type]:
            modifier *= TYPE_CHART[move_type][t_type]
    return modifier

def calculate_damage(attacker, defender, move):
    
    hit_chance = random.randint(1, 100)
    if hit_chance > move.accuracy:
        return 0, -1.0 # Miss (Colpo fallito)
    cat = move.category.lower()
    if cat in ["speciale", "special"]:
        # Mossa Speciale: usa Sp. Atk vs Sp. Def
        atk_stat = attacker.sp_attack
        def_stat = defender.sp_defense
    else:
        # Mossa Fisica (o default): usa Attack vs Defense
        # (Include "Fisico", "Physical" e casi strani)
        atk_stat = attacker.attack
        def_stat = defender.defense
        
    stab = 1.5 if move.type in attacker.types else 1.0
    effectiveness = get_type_effectiveness(move.type, defender.types)
    random_factor = random.uniform(0.85, 1.0)
    
    # Livello ipotetico 50
    base_dmg = ((2 * 50 / 5 + 2) * move.power * (atk_stat / def_stat) / 50 + 2)
    final_damage = int(base_dmg * stab * effectiveness * random_factor)
    
    return final_damage, effectiveness

# --- 1. CARICAMENTO DATI ---

# --- CARICAMENTO MOSSE "BLINDATO" ---
def load_moves(filename='moves.json'):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_moves = json.load(f)
    except FileNotFoundError:
        print(f"ERRORE: File {filename} non trovato.")
        return []

    valid_moves = []
    for m in raw_moves:
        if 'power' in m and m['power'] is not None:
            category = m.get('category', 'Fisico')
            

            raw_acc = m.get('accuracy')
            if raw_acc is None:
                accuracy = 100
            else:
                accuracy = raw_acc
            
            valid_moves.append(Move(
                m['ename'], 
                m['type'], 
                m['power'], 
                accuracy, 
                category
            ))
    return valid_moves

def convert_hp(base, level=50):
    return int(((base * 2 + 31) * level / 100) + level + 10)

def convert_stat(base, level=50):
    return int(((base * 2 + 31) * level / 100) + 5)


def load_gen1_pokemon(filename='pokedex.json', all_moves=[]):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        return []

    my_pokedex = []
    for p in raw_data:
        if p['id'] > 151: break
        stats = p['base']
        p_types = p['type']
        
        compatible = [m for m in all_moves if m.type in p_types or m.type == "Normal"]
        
        if len(compatible) >= 4:
            my_moves = random.sample(compatible, 4)
        else:
            normal_moves = [m for m in all_moves if m.type == "Normal"]
            needed = 4 - len(compatible)
            fillers = random.sample(normal_moves, needed) if len(normal_moves) >= needed else normal_moves
            my_moves = compatible + fillers
        real_hp = convert_hp(stats['HP'])
        real_atk = convert_stat(stats['Attack'])
        real_def = convert_stat(stats['Defense'])
        real_sp_atk = convert_stat(stats['Sp. Attack'])
        real_sp_def = convert_stat(stats['Sp. Defense'])
        real_speed = convert_stat(stats['Speed'])
        new_mon = Pokemon(p['id'],
            p['name'], p_types, 
            real_hp,     
            real_atk, 
            real_def,
            real_sp_atk, 
            real_sp_def, 
            real_speed, 
            my_moves
        )
        my_pokedex.append(new_mon)
    return my_pokedex

def get_best_move_greedy(attacker, defender):
    best_move_idx = 0
    max_damage = -1
    for i, move in enumerate(attacker.moves):
        predicted_damage, _ = calculate_damage(attacker, defender, move)
        if predicted_damage > max_damage:
            max_damage = predicted_damage
            best_move_idx = i
    return best_move_idx

# --- 2. MOTORE DI BATTAGLIA ---

class Battle:
    def __init__(self, team1, team2):
        self.team1 = team1 
        self.team2 = team2 
        self.p1_active = team1[0]
        self.p2_active = team2[0]
        self.turn_count = 0

    def get_next_pokemon(self, team):
        for p in team:
            if not p.is_fainted(): return p
        return None

    def play_turn(self, action_p1, action_p2):
        # action_p1/p2: ["ATTACK", move_idx] oppure ["SWITCH", team_idx]
        
        self.turn_count += 1
        print(f"\n=========================================")
        print(f"               TURNO {self.turn_count}")
        print(f"=========================================")
        
        # LOG STATO CORRENTE
        print(f"TUA SQUADRA: {self.p1_active.name} (HP: {self.p1_active.current_hp}/{self.p1_active.max_hp})")
        print(f"AVVERSARIO:  {self.p2_active.name} (HP: {self.p2_active.current_hp}/{self.p2_active.max_hp})")
        print("-" * 41)

        p1_switched = False
        p2_switched = False

        # --- 1. GESTIONE SWITCH (Priorità assoluta) ---
        
        if action_p1[0] == "SWITCH":
            idx = action_p1[1]
            if 0 <= idx < len(self.team1) and not self.team1[idx].is_fainted():
                old_mon = self.p1_active
                self.p1_active = self.team1[idx]
                print(f">>> GIOCATORE richiama {old_mon.name}!")
                print(f">>> Vai {self.p1_active.name}!")
                p1_switched = True

        if action_p2[0] == "SWITCH":
            idx = action_p2[1]
            if 0 <= idx < len(self.team2) and not self.team2[idx].is_fainted():
                old_mon = self.p2_active
                self.p2_active = self.team2[idx]
                print(f">>> L'AVVERSARIO richiama {old_mon.name}!")
                print(f">>> L'avversario manda in campo {self.p2_active.name}!")
                p2_switched = True

        if p1_switched and p2_switched:
            return "CONTINUE"

        # --- 2. GESTIONE ATTACCHI ---
        order = []
        
        # Se P1 NON ha cambiato, attacca
        if not p1_switched:
            move = self.p1_active.moves[action_p1[1] % len(self.p1_active.moves)]
            order.append((self.p1_active, self.p2_active, move, "TU"))
            
        # Se P2 NON ha cambiato, attacca
        if not p2_switched:
            move = self.p2_active.moves[action_p2[1] % len(self.p2_active.moves)]
            # Il target è sempre il Pokemon ATTIVO corrente (che potrebbe essere appena entrato)
            target = self.p1_active 
            order.append((self.p2_active, target, move, "AVVERSARIO"))

        # Speed Check
        if len(order) == 2:
            if order[0][0].speed < order[1][0].speed:
                order.reverse()
            elif order[0][0].speed == order[1][0].speed:
                 if random.random() > 0.5: order.reverse()

        # Esecuzione
        for attacker, defender, move, role in order:
            if attacker.is_fainted(): continue 
            
            # Recalcolo target dinamico (nel caso P1 attacchi per primo e uccida P2, o viceversa)
            real_defender = self.p2_active if role == "TU" else self.p1_active
            
            if real_defender.is_fainted(): continue 

            print(f"\n[{role}] {attacker.name} usa {move.name}!")
            dmg, eff = calculate_damage(attacker, real_defender, move)
            
            if eff > 1.0: print(" -> È super efficace!")
            elif eff == 0.0: print(" -> Non ha effetto...")
            elif eff < 1.0: print(" -> Non è molto efficace...")
            
            real_defender.take_damage(dmg)
            print(f" -> {real_defender.name} subisce {dmg} danni.")
            
            if real_defender.is_fainted():
                print(f" -> {real_defender.name} è esausto!")

        # --- 3. CHECK FINE TURNO ---
        
        if self.p1_active.is_fainted():
            new_p = self.get_next_pokemon(self.team1)
            if new_p:
                self.p1_active = new_p
                print(f"\n!!! Il tuo Pokémon è esausto. Mandi in campo {new_p.name}!")
            else:
                print("\nNON HAI PIÙ POKÉMON! HAI PERSO!")
                return "AI_WINS"

        if self.p2_active.is_fainted():
            new_p = self.get_next_pokemon(self.team2)
            if new_p:
                self.p2_active = new_p
                print(f"\n!!! Il Pokémon avversario è esausto. Entra {new_p.name}!")
            else:
                print("\nL'AVVERSARIO NON HA PIÙ POKÉMON! HAI VINTO!")
                return "PLAYER_WINS"

        return "CONTINUE"

# --- 3. MAIN INTERATTIVO ---

if __name__ == "__main__":
    print("\n*******************************************")
    print("* POKEMON BATTLE SIMULATOR 1.0       *")
    print("*******************************************")
    
    moves_db = load_moves('moves.json')
    pokedex = load_gen1_pokemon('pokedex.json', moves_db)
    
    if not pokedex: 
        print("Errore: Pokedex vuoto. Controlla i file JSON.")
        exit()
    
    # Squadre casuali
    player_team = copy.deepcopy(random.sample(pokedex, 6))
    ai_team = copy.deepcopy(random.sample(pokedex, 6))
    
    # --- STAMPA INIZIALE SQUADRE (Quella che ti piaceva!) ---
    print("\n[LA TUA SQUADRA]")
    for p in player_team:
        types_str = "/".join(p.types)
        print(f" - {p.name:<12} | HP: {p.max_hp:<3} | Type: {types_str}")

    print("\n[SQUADRA AVVERSARIA]")
    for p in ai_team:
        types_str = "/".join(p.types)
        print(f" - {p.name:<12} | HP: {p.max_hp:<3} | Type: {types_str}")
    
    print("\nPREMI INVIO PER INIZIARE LA BATTAGLIA!")
    input()

    battle = Battle(player_team, ai_team)
    game_state = "CONTINUE"
    
    while game_state == "CONTINUE":
        
        current_mon = battle.p1_active
        
        print(f"\n--- Cosa deve fare {current_mon.name}? ---")
        print("1. ATTACCA")
        print("2. CAMBIA POKÉMON")
        
        valid_turn = False
        p1_action = []

        while not valid_turn:
            choice = input("> Scelta: ")
            
            if choice == "1":
                # MENU ATTACCO CON DETTAGLI
                print(f"\nMosse disponibili per {current_mon.name}:")
                for i, m in enumerate(current_mon.moves):
                    # Qui mostriamo Potenza, Tipo e Precisione
                    print(f" [{i}] {m.name:<15} (Tipo: {m.type:<8} | Pot: {m.power:<3})")
                
                try:
                    m_idx = int(input("> Scegli mossa (0-3): "))
                    if 0 <= m_idx < len(current_mon.moves):
                        p1_action = ["ATTACK", m_idx]
                        valid_turn = True
                    else:
                        print("Mossa inesistente.")
                except ValueError:
                    print("Inserisci un numero valido.")

            elif choice == "2":
                # MENU CAMBIO
                print("\n--- Seleziona Pokémon per il cambio ---")
                available_switch = False
                for i, p in enumerate(player_team):
                    status = "ESAUSTO" if p.is_fainted() else f"{p.current_hp}/{p.max_hp} HP"
                    tag = " <-- IN CAMPO" if p == current_mon else ""
                    print(f" [{i}] {p.name:<12} {status} {tag}")
                    
                    if not p.is_fainted() and p != current_mon:
                        available_switch = True
                
                if not available_switch:
                    print("Non puoi cambiare! Gli altri sono esausti o sei già solo.")
                    continue

                try:
                    s_idx = int(input("> Numero Pokémon: "))
                    if 0 <= s_idx < len(player_team):
                        target = player_team[s_idx]
                        if target.is_fainted():
                            print("Non puoi mandare un Pokémon esausto!")
                        elif target == current_mon:
                            print("È già in battaglia!")
                        else:
                            p1_action = ["SWITCH", s_idx]
                            valid_turn = True
                    else:
                        print("Numero non valido.")
                except ValueError:
                    print("Inserisci un numero.")
            
            else:
                print("Scrivi '1' per attaccare o '2' per cambiare.")

        # AI LOGIC
        if len(battle.p2_active.moves) > 0:
            ai_move_idx = get_best_move_greedy(battle.p2_active, battle.p1_active)
            ai_action = ["ATTACK", ai_move_idx]
        else:
            ai_action = ["ATTACK", 0]
        
        # ESECUZIONE
        game_state = battle.play_turn(p1_action, ai_action)
        
        if game_state == "CONTINUE":
            input("\n[Premi INVIO per il prossimo turno...]")