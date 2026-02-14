import copy
import math
from pokemon_engine import calculate_damage

def evaluate_board(battle):
    if all(p.is_fainted() for p in battle.team1): return 100000 
    if all(p.is_fainted() for p in battle.team2): return -100000

    score = 0
    # IA HP (Massimizzare)
    for p in battle.team2:
        if not p.is_fainted():
            score += (p.current_hp / p.max_hp) * 100
            score += 50 
            
    # Player HP (Minimizzare)
    for p in battle.team1:
        if not p.is_fainted():
            score -= (p.current_hp / p.max_hp) * 100
            score -= 50

    return score

def get_possible_actions(team, active_mon):
    """Restituisce una lista di tuple: ("ATTACK", idx) o ("SWITCH", idx)"""
    actions = []
    
    # Aggiungi attacchi
    for i in range(len(active_mon.moves)):
        actions.append(("ATTACK", i))
        
    # Aggiungi cambi (solo verso pokemon vivi e non già in campo)
    for i, mon in enumerate(team):
        if mon != active_mon and not mon.is_fainted():
            actions.append(("SWITCH", i))
            
    return actions

def simulate_turn(battle_state, ai_action, player_action):
    """Simula un turno completo con risoluzione simultanea"""
    sim = copy.deepcopy(battle_state)
    
    # 1. Risolvi Cambi
    if ai_action[0] == "SWITCH":
        sim.p2_active = sim.team2[ai_action[1]]
    if player_action[0] == "SWITCH":
        sim.p1_active = sim.team1[player_action[1]]

    # 2. Risolvi Attacchi
    attackers = []
    if player_action[0] == "ATTACK" and not sim.p1_active.is_fainted():
        attackers.append((sim.p1_active, sim.p2_active, sim.p1_active.moves[player_action[1]]))
    if ai_action[0] == "ATTACK" and not sim.p2_active.is_fainted():
        attackers.append((sim.p2_active, sim.p1_active, sim.p2_active.moves[ai_action[1]]))

    attackers.sort(key=lambda x: x[0].speed, reverse=True)

    for att, defe, move in attackers:
        if att.is_fainted() or defe.is_fainted(): continue
        dmg, _ = calculate_damage(att, defe, move)
        defe.take_damage(dmg)

    return sim

def minimax(battle_node, depth, alpha, beta, is_maximizing):
    if depth == 0 or all(p.is_fainted() for p in battle_node.team1) or all(p.is_fainted() for p in battle_node.team2):
        return evaluate_board(battle_node)

    if is_maximizing:
        max_eval = -math.inf
        ai_actions = get_possible_actions(battle_node.team2, battle_node.p2_active)
        pl_actions = get_possible_actions(battle_node.team1, battle_node.p1_active)
        
        for ai_act in ai_actions:
            worst_outcome = math.inf
            for pl_act in pl_actions:
                sim_state = simulate_turn(battle_node, ai_act, pl_act)
                eval_score = minimax(sim_state, depth - 1, alpha, beta, True) 
                worst_outcome = min(worst_outcome, eval_score)
            
            max_eval = max(max_eval, worst_outcome)
            alpha = max(alpha, max_eval)
            if beta <= alpha: break
                
        return max_eval

def get_best_action_minimax(battle_state, depth=2):
    """Ritorna la tupla migliore per l'IA, es: ("SWITCH", 3)"""
    best_action = ("ATTACK", 0)
    best_value = -math.inf
    alpha = -math.inf
    beta = math.inf
    
    ai_actions = get_possible_actions(battle_state.team2, battle_state.p2_active)
    pl_actions = get_possible_actions(battle_state.team1, battle_state.p1_active)

    if not ai_actions: return best_action

    for ai_act in ai_actions:
        worst_case = math.inf
        
        for pl_act in pl_actions:
            sim_state = simulate_turn(battle_state, ai_act, pl_act)
            score = minimax(sim_state, depth - 1, alpha, beta, True)
            if score < worst_case:
                worst_case = score
        
        if worst_case > best_value:
            best_value = worst_case
            best_action = ai_act
            
    return best_action