import random
import copy
import os
import time
import csv

from pokemon_engine import load_moves, load_gen1_pokemon, Battle, calculate_damage
from ai_minimax import get_best_action_minimax

# --- 1. DEFINIZIONE IA GREEDY ---
def get_best_action_greedy(battle):
    p1 = battle.p1_active 
    p2 = battle.p2_active 
    best_move_idx = 0
    max_dmg = -1
    
    if p2.moves:
        for i, move in enumerate(p2.moves):
            dmg, _ = calculate_damage(p2, p1, move)
            if dmg > max_dmg:
                max_dmg = dmg
                best_move_idx = i
                
    if max_dmg < 15:
        best_bench_idx = -1
        best_bench_dmg = max_dmg
        for i, bench_mon in enumerate(battle.team2):
            if bench_mon != p2 and not bench_mon.is_fainted():
                for move in bench_mon.moves:
                    b_dmg, _ = calculate_damage(bench_mon, p1, move)
                    if b_dmg > best_bench_dmg:
                        best_bench_dmg = b_dmg
                        best_bench_idx = i
        if best_bench_idx != -1 and best_bench_dmg > max_dmg + 20:
            return ("SWITCH", best_bench_idx)
            
    return ("ATTACK", best_move_idx)


# --- 2. FUNZIONE PER CREARE SQUADRE FISSE ---
def build_specific_team(pokedex, pokemon_names):
    team = []
    for name in pokemon_names:
        for p in pokedex:
            if p.name == name:
                team.append(copy.deepcopy(p))
                break
    return team

# --- 3. CONFIGURAZIONE DEL TEST ---
MATCHES_PER_TEAM = 10
MINIMAX_DEPTH = 2     
OUTPUT_FILE = 'stress_test_results.csv'

# Definiamo le due squadre per il test
TEAM_1_NAMES = ["Charizard", "Alakazam", "Gengar", "Jolteon", "Machamp", "Aerodactyl"] # Offensivo
TEAM_2_NAMES = ["Snorlax", "Lapras", "Venusaur", "Slowbro", "Muk", "Clefable"]         # Difensivo

def run_stress_test():
    total_games = MATCHES_PER_TEAM * 2
    print(f"🔄 Avvio Stress Test: {total_games} Partite (Mirror Match)")
    print(f"🧠 IA 1 (Greedy) vs IA 2 (Minimax Depth {MINIMAX_DEPTH})")
    print("-" * 50)
    
    moves_db = load_moves('moves.json')
    pokedex = load_gen1_pokemon('pokedex.json', moves_db)
    
    # Costruiamo i team dal Pokedex
    team_offensive = build_specific_team(pokedex, TEAM_1_NAMES)
    team_defensive = build_specific_team(pokedex, TEAM_2_NAMES)
    
    scenarios = [
        {"nome": "Offensivo", "team": team_offensive},
        {"nome": "Difensivo", "team": team_defensive}
    ]
    
    all_results = []
    game_counter = 1

    # --- CICLO SUI DUE SCENARI (SQUADRE) ---
    for scenario in scenarios:
        team_type = scenario["nome"]
        base_team = scenario["team"]
        print(f"\n⚔️ INIZIO TEST SCENARIO: TEAM {team_type.upper()}")
        
        # --- CICLO SULLE 10 PARTITE PER SQUADRA ---
        for i in range(MATCHES_PER_TEAM):
            print(f"  -> Partita {game_counter}/{total_games} in corso... (Team {team_type})", end="\r")
            
            # Ricreiamo copie fresche dei team per ogni partita
            team_greedy = copy.deepcopy(base_team)
            team_minimax = copy.deepcopy(base_team)
            
            battle = Battle(team_greedy, team_minimax)
            
            turns = 0
            greedy_times = []
            minimax_times = []
            greedy_switches = 0
            minimax_switches = 0
            greedy_misses = 0
            minimax_misses = 0
            
            game_over = False
            winner = None

            # --- LOOP DELLA BATTAGLIA ---
            while not game_over:
                turns += 1
                
                # 1. SCELTA GREEDY
                start_time = time.time()
                battle_copy = copy.copy(battle)
                battle_copy.p1_active = battle.p2_active
                battle_copy.p2_active = battle.p1_active
                battle_copy.team2 = battle.team1
                
                action_greedy = get_best_action_greedy(battle_copy)
                greedy_times.append(time.time() - start_time)
                if action_greedy[0] == "SWITCH": greedy_switches += 1

                # 2. SCELTA MINIMAX
                start_time = time.time()
                action_minimax = get_best_action_minimax(battle, depth=MINIMAX_DEPTH)
                minimax_times.append(time.time() - start_time)
                if action_minimax[0] == "SWITCH": minimax_switches += 1
                
                # 3. RISOLUZIONE
                if action_greedy[0] == "SWITCH":
                    battle.p1_active = battle.team1[action_greedy[1]]
                if action_minimax[0] == "SWITCH":
                    battle.p2_active = battle.team2[action_minimax[1]]
                    
                attackers = []
                if action_greedy[0] == "ATTACK" and not battle.p1_active.is_fainted():
                    attackers.append((battle.p1_active, battle.p2_active, battle.p1_active.moves[action_greedy[1]], "Greedy"))
                if action_minimax[0] == "ATTACK" and not battle.p2_active.is_fainted():
                    attackers.append((battle.p2_active, battle.p1_active, battle.p2_active.moves[action_minimax[1]], "Minimax"))
                    
                attackers.sort(key=lambda x: x[0].speed, reverse=True)
                
                for att, defe, move, who in attackers:
                    if att.is_fainted() or defe.is_fainted(): continue
                    dmg, eff = calculate_damage(att, defe, move)
                    
                    if eff == -1.0:
                        if who == "Greedy": greedy_misses += 1
                        else: minimax_misses += 1
                        continue
                    defe.take_damage(dmg)

                # 4. GESTIONE KO
                if battle.p1_active.is_fainted():
                    next_p = battle.get_next_pokemon(battle.team1)
                    if next_p: battle.p1_active = next_p
                    else:
                        winner = "Minimax"
                        game_over = True

                if battle.p2_active.is_fainted() and not game_over:
                    next_p = battle.get_next_pokemon(battle.team2)
                    if next_p: battle.p2_active = next_p
                    else:
                        winner = "Greedy"
                        game_over = True
                        
                # Anti-Stallo
                if turns > 150:
                    winner = "Draw"
                    game_over = True

            # SALVATAGGIO STATISTICHE
            avg_greedy_time = sum(greedy_times) / len(greedy_times) if greedy_times else 0
            avg_minimax_time = sum(minimax_times) / len(minimax_times) if minimax_times else 0
            
            all_results.append({
                "Game_ID": game_counter,
                "Team_Type": team_type, # <-- NUOVO: Tracciamo che squadra stavano usando!
                "Winner": winner,
                "Turns": turns,
                "Greedy_Avg_Time_s": round(avg_greedy_time, 5),
                "Minimax_Avg_Time_s": round(avg_minimax_time, 5),
                "Greedy_Switches": greedy_switches,
                "Minimax_Switches": minimax_switches,
                "Greedy_Misses": greedy_misses,
                "Minimax_Misses": minimax_misses
            })
            game_counter += 1

    # --- ESPORTAZIONE CSV ---
    print("\n✅ Simulazione completata! Salvataggio dati in corso...")
    keys = all_results[0].keys()
    with open(OUTPUT_FILE, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_results)
        
    print(f"📊 Dati salvati con successo in: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_stress_test()