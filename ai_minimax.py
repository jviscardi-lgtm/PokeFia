import copy
import math
from pokemon_engine import calculate_damage

# --- 1. FUNZIONE DI VALUTAZIONE (EURISTICA) ---
def evaluate_board(battle):
    """
    Assegna un punteggio numerico allo stato attuale della battaglia.
    Valore Alto (+) = Bene per l'IA (Team 2)
    Valore Basso (-) = Bene per il Giocatore (Team 1)
    """
    
    # Se il Giocatore ha perso (tutti i pokemon morti), punteggio massimo per IA
    if all(p.is_fainted() for p in battle.team1):
        return 100000 
    
    # Se l'IA ha perso, punteggio minimo
    if all(p.is_fainted() for p in battle.team2):
        return -100000

    score = 0
    
    # Somma HP percentuali Team IA (Positivo)
    for p in battle.team2:
        if not p.is_fainted():
            score += (p.current_hp / p.max_hp) * 100
            score += 50 # Bonus per ogni Pokemon vivo
            
    # Somma HP percentuali Team Giocatore (Negativo)
    for p in battle.team1:
        if not p.is_fainted():
            score -= (p.current_hp / p.max_hp) * 100
            score -= 50 # Penalità per ogni nemico vivo

    return score

# --- 2. SIMULAZIONE DEL TURNO (MOTORE PREVISIONALE) ---
def simulate_turn(battle_state, ai_move_idx, player_move_idx):
    """
    Crea una copia della battaglia e simula un turno completo
    senza toccare la partita vera.
    """
    # 1. Copia profonda per non modificare il gioco reale (Costoso ma necessario)
    sim = copy.deepcopy(battle_state)
    
    ai_mon = sim.p2_active
    player_mon = sim.p1_active
    
    # Se uno dei due è morto nella simulazione precedente, il turno è "vuoto" o forziamo un cambio
    # Per semplicità del Minimax, se un pokemon è morto, consideriamo il turno finito.
    if ai_mon.is_fainted() or player_mon.is_fainted():
        return sim

    ai_move = ai_mon.moves[ai_move_idx]
    player_move = player_mon.moves[player_move_idx]
    
    # 2. Determina ordine (Speed Check)
    if ai_mon.speed >= player_mon.speed:
        first, second = (ai_mon, ai_move), (player_mon, player_move)
    else:
        first, second = (player_mon, player_move), (ai_mon, ai_move)
        
    # 3. Esegui mosse (Senza log grafici)
    # Primo attacco
    dmg1, _ = calculate_damage(first[0], second[0], first[1])
    second[0].take_damage(dmg1)
    
    # Secondo attacco (solo se il secondo è ancora vivo)
    if not second[0].is_fainted():
        dmg2, _ = calculate_damage(second[0], first[0], second[1])
        first[0].take_damage(dmg2)
        
    return sim

# --- 3. ALGORITMO MINIMAX (CON ALPHA-BETA) ---
def minimax(battle_node, depth, alpha, beta, is_maximizing):
    """
    depth: Quanti turni guardare avanti (es. 2 = IA mossa -> Player mossa -> Valutazione)
    is_maximizing: True se tocca all'IA decidere, False se stiamo simulando il Giocatore
    """
    
    # Caso Base: Raggiunta profondità massima o partita finita
    if depth == 0 or all(p.is_fainted() for p in battle_node.team1) or all(p.is_fainted() for p in battle_node.team2):
        return evaluate_board(battle_node)

    if is_maximizing:
        # --- TURNO IA (CERCA DI MASSIMIZZARE IL PUNTEGGIO) ---
        max_eval = -math.inf
        
        # L'IA prova tutte le sue mosse disponibili
        # (Nota: qui semplifichiamo ignorando gli switch per non esplodere la complessità)
        possible_moves = range(len(battle_node.p2_active.moves))
        
        for ai_idx in possible_moves:
            # Per ogni mossa dell'IA, dobbiamo vedere cosa risponde il Giocatore (Minimizing)
            # Invece di chiamare ricorsivamente subito, dobbiamo simulare la "risposta" simultanea.
            # Nel Minimax a turni simultanei, l'IA assume che per QUESTA mossa scelta (ai_idx),
            # il giocatore sceglierà la risposta peggiore possibile.
            
            worst_outcome_for_this_move = math.inf
            
            # Simuliamo contro tutte le mosse del giocatore
            for pl_idx in range(len(battle_node.p1_active.moves)):
                
                # Simula il turno (IA vs Player)
                sim_state = simulate_turn(battle_node, ai_idx, pl_idx)
                
                # Valuta lo stato risultante (scendendo di profondità)
                # Nota: Depth - 1 perché abbiamo simulato un turno completo (entrambi hanno mosso)
                eval_score = minimax(sim_state, depth - 1, alpha, beta, True) 
                
                # Troviamo la risposta peggiore del nemico a questa nostra mossa
                worst_outcome_for_this_move = min(worst_outcome_for_this_move, eval_score)
            
            # Tra tutte le mosse che posso fare, scelgo quella che ha il "peggior scenario" migliore (Maximin)
            max_eval = max(max_eval, worst_outcome_for_this_move)
            
            # Alpha-Beta Pruning
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
                
        return max_eval

    else:
        # In questa versione semplificata "Simultaneous Move", gestiamo tutto nel blocco maximizing.
        # Se volessimo fare turni alternati classici, useremmo questo blocco.
        # Per ora lasciamo pass, usiamo la logica Maximin sopra.
        pass

# --- 4. FUNZIONE PUBBLICA DA CHIAMARE NELLA GUI ---
def get_best_move_minimax(battle_state, depth=2):
    """
    Funzione principale chiamata dall'interfaccia.
    Restituisce l'indice della mossa migliore calcolata.
    Depth consigliata: 1 o 2 (Python è lento!)
    """
    best_move_idx = 0
    best_value = -math.inf
    
    alpha = -math.inf
    beta = math.inf
    
    # Prova tutte le mosse reali dell'IA (Livello Radice)
    available_moves = battle_state.p2_active.moves
    if not available_moves: return 0

    print(f"--- AVVIO MINIMAX (Depth {depth}) ---")
    
    for i, move in enumerate(available_moves):
        # 1. Per questa mossa, qual è il worst-case scenario?
        worst_case = math.inf
        
        # Contro tutte le mosse del giocatore
        for j, pl_move in enumerate(battle_state.p1_active.moves):
            sim_state = simulate_turn(battle_state, i, j)
            
            # Valuta ricorsivamente
            # Usiamo depth-1 perché il livello 1 è questo loop
            score = minimax(sim_state, depth - 1, alpha, beta, True)
            
            if score < worst_case:
                worst_case = score
        
        print(f"Mossa {i} ({move.name}): Valore Minimo Garantito = {worst_case:.1f}")
        
        # 2. Scegli la mossa con il worst-case più alto
        if worst_case > best_value:
            best_value = worst_case
            best_move_idx = i
            
    print(f"--> SCELTA MINIMAX: Mossa {best_move_idx} (Valore {best_value:.1f})")
    return best_move_idx