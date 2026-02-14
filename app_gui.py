import streamlit as st
import random
import copy
import os
import time

from pokemon_engine import load_moves, load_gen1_pokemon, Battle, Pokemon, calculate_damage
from ai_minimax import get_best_action_minimax  # <-- ATTENZIONE AL NUOVO NOME

st.set_page_config(page_title="Pokémon AI Arena", page_icon="⚡", layout="wide")

def get_sprite_path(pokemon_id):
    filename = f"{pokemon_id:03d}MS.png"
    return os.path.join("sprites", filename)

# --- ALGORITMO GREEDY (CON SWITCH VOLONTARIO) ---
def get_best_action_greedy(battle):
    p1 = battle.p1_active # Giocatore (Bersaglio)
    p2 = battle.p2_active # IA (Attaccante)
    
    best_move_idx = 0
    max_dmg = -1
    
    # 1. Cerca il miglior attacco del Pokemon in campo
    if p2.moves:
        for i, move in enumerate(p2.moves):
            dmg, _ = calculate_damage(p2, p1, move)
            if dmg > max_dmg:
                max_dmg = dmg
                best_move_idx = i
                
    # 2. LOGICA SWITCH GREEDY: Se faccio schifo a fare danno (< 15 o immune)
    if max_dmg < 15:
        best_bench_idx = -1
        best_bench_dmg = max_dmg
        
        # Guardo in panchina se c'è qualcuno di meglio
        for i, bench_mon in enumerate(battle.team2):
            if bench_mon != p2 and not bench_mon.is_fainted():
                for move in bench_mon.moves:
                    b_dmg, _ = calculate_damage(bench_mon, p1, move)
                    if b_dmg > best_bench_dmg:
                        best_bench_dmg = b_dmg
                        best_bench_idx = i
                        
        # Se in panchina c'è qualcuno che fa almeno 20 danni in più, CAMBIO!
        if best_bench_idx != -1 and best_bench_dmg > max_dmg + 20:
            return ("SWITCH", best_bench_idx)
            
    # Altrimenti, attacco normale
    return ("ATTACK", best_move_idx)

# --- INIZIALIZZAZIONE STATO ---
if 'battle_system' not in st.session_state:
    moves_db = load_moves('moves.json')
    pokedex = load_gen1_pokemon('pokedex.json', moves_db)
    
    player_team = copy.deepcopy(random.sample(pokedex, 6))
    ai_team = copy.deepcopy(random.sample(pokedex, 6))
    
    st.session_state['battle_system'] = Battle(player_team, ai_team)
    st.session_state['logs'] = ["Inizio della battaglia!"]
    st.session_state['game_over'] = False
    st.session_state['turn'] = 1
    st.session_state['winner'] = None

battle = st.session_state['battle_system']
p1 = battle.p1_active
p2 = battle.p2_active

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Impostazioni IA")
    ai_choice = st.radio("Cervello Avversario:", ("Greedy (Avido)", "Minimax (Intelligente)"))
    st.divider()
    
    st.subheader("La tua Squadra")
    for p in battle.team1:
        icon = "🔴" if p == battle.p1_active else ("💀" if p.is_fainted() else "🟢")
        with st.expander(f"{icon} {p.name} ({p.current_hp}/{p.max_hp})"):
            st.image(get_sprite_path(p.id), width=50)
            st.caption(f"Tipi: {'/'.join(p.types)}")
    
    st.divider()
    st.subheader("Squadra IA")
    for p in battle.team2:
        icon = "🔴" if p == battle.p2_active else ("💀" if p.is_fainted() else "🟢")
        with st.expander(f"{icon} {p.name} ({p.current_hp}/{p.max_hp})"):
            st.image(get_sprite_path(p.id), width=50)
            st.caption(f"Tipi: {'/'.join(p.types)}")

# --- UI CENTRALE ---
st.title("⚡ Pokémon AI Arena")
st.caption(f"Turno {st.session_state['turn']} | **{ai_choice}** vs Umano")

col1, col_center, col2 = st.columns([1, 0.2, 1])

with col1:
    st.markdown(f"### Tu: **{p1.name}**")
    if os.path.exists(get_sprite_path(p1.id)): st.image(get_sprite_path(p1.id), width=150)
    hp_pct = max(0.0, p1.current_hp / p1.max_hp)
    st.progress(hp_pct, text=f"HP: {p1.current_hp}/{p1.max_hp}")
    st.info(f"Atk: {p1.attack} | Def: {p1.defense} | SpA: {p1.sp_attack} | SpD: {p1.sp_defense} | Spe: {p1.speed}")

with col2:
    st.markdown(f"### AI: **{p2.name}**")
    if os.path.exists(get_sprite_path(p2.id)): st.image(get_sprite_path(p2.id), width=150)
    hp_pct_ai = max(0.0, p2.current_hp / p2.max_hp)
    st.progress(hp_pct_ai, text=f"HP: {p2.current_hp}/{p2.max_hp}")
    st.info(f"Atk: {p2.attack} | Def: {p2.defense} | SpA: {p2.sp_attack} | SpD: {p2.sp_defense} | Spe: {p2.speed}")

st.divider()

# --- LOGICA DEL TURNO (RISOLUZIONE SIMULTANEA) ---
def execute_turn(player_action_type, player_data):
    current_logs = []
    current_logs.append(f"--- Turno {st.session_state['turn']} ---")
    
    player_action = (player_action_type, player_data)
    
    # 1. L'IA DECIDE LA SUA AZIONE (Tupla: "ATTACK" o "SWITCH")
    start_time = time.time()
    if ai_choice == "Greedy (Avido)":
        ai_action = get_best_action_greedy(battle)
        ai_algo_name = "Greedy"
    else:
        ai_action = get_best_action_minimax(battle, depth=2)
        ai_algo_name = "Minimax"
    elapsed = time.time() - start_time
    current_logs.append(f"🧠 {ai_algo_name} ha pensato per {elapsed:.2f}s")
    
    # 2. RISOLUZIONE DEI CAMBI (Priority 1)
    if player_action[0] == "SWITCH":
        battle.p1_active = battle.team1[player_action[1]]
        current_logs.append(f"🔄 Hai scambiato con **{battle.p1_active.name}**!")
        
    if ai_action[0] == "SWITCH":
        battle.p2_active = battle.team2[ai_action[1]]
        current_logs.append(f"🤖 L'IA scambia con **{battle.p2_active.name}**!")

    # 3. RISOLUZIONE DEGLI ATTACCHI (Priority 2)
    attackers = [] # Lista di chi deve attaccare questo turno
    
    if player_action[0] == "ATTACK" and not battle.p1_active.is_fainted():
        move = battle.p1_active.moves[player_action[1]]
        attackers.append((battle.p1_active, battle.p2_active, move, "Tu"))
        
    if ai_action[0] == "ATTACK" and not battle.p2_active.is_fainted():
        move = battle.p2_active.moves[ai_action[1]]
        attackers.append((battle.p2_active, battle.p1_active, move, "AI"))
        
    # Ordiniamo in base alla velocità (decrescente)
    attackers.sort(key=lambda x: x[0].speed, reverse=True)
    
    # Eseguiamo gli attacchi
    for att, defe, move, who in attackers:
        if att.is_fainted() or defe.is_fainted(): continue
        
        dmg, eff = calculate_damage(att, defe, move)
        
        if eff == -1.0:
            current_logs.append(f"❌ **{who}** ({att.name}) usa {move.name} ma fallisce!")
            continue
            
        if eff > 1: eff_msg = " (Super Efficace!)"
        elif eff == 0: eff_msg = " (Non ha effetto!)"
        elif eff < 1: eff_msg = " (Non molto efficace...)"
        else: eff_msg = ""
        
        current_logs.append(f"**{who}** ({att.name}) usa {move.name}{eff_msg}")
        defe.take_damage(dmg)
        if dmg > 0: current_logs.append(f"-> {defe.name} subisce {dmg} danni.")
        
        if defe.is_fainted():
            current_logs.append(f"💀 {defe.name} è esausto!")

    # 4. GESTIONE KO FORZATI
    if battle.p1_active.is_fainted():
        next_p = battle.get_next_pokemon(battle.team1)
        if next_p:
            battle.p1_active = next_p
            current_logs.append(f"⚠️ {battle.p1_active.name} entra in campo forzatamente!")
        else:
            st.session_state['winner'] = "AI"
            st.session_state['game_over'] = True

    if battle.p2_active.is_fainted() and not st.session_state['game_over']:
        next_p_ai = battle.get_next_pokemon(battle.team2)
        if next_p_ai:
            battle.p2_active = next_p_ai
            current_logs.append(f"⚠️ L'IA manda in campo {next_p_ai.name}!")
        else:
            st.session_state['winner'] = "PLAYER"
            st.session_state['game_over'] = True

    st.session_state['logs'] = current_logs + st.session_state['logs']
    st.session_state['turn'] += 1
    st.rerun()

# --- INTERFACCIA COMANDI ---
if not st.session_state['game_over']:
    st.subheader("⚔️ Scegli Azione")
    st.markdown("<style>div.stButton > button {height: 80px;}</style>", unsafe_allow_html=True)
        
    cols = st.columns(4)
    for i, move in enumerate(p1.moves):
        with cols[i]:
            cat_icon = "💥" if move.category.lower() in ["fisico", "physical"] else ("✨" if move.category.lower() in ["speciale", "special"] else "⚪")
            btn_label = f"{move.name} ({move.type})\nPow: {move.power} | Acc: {move.accuracy}% | {cat_icon}"
            if st.button(btn_label, key=f"btn_{i}", use_container_width=True):
                execute_turn("ATTACK", i)
                
    with st.expander("🔄 Sostituisci Pokémon (Panchina)"):
        bench_cols = st.columns(6)
        displayed_count = 0
        for i, member in enumerate(battle.team1):
            if member != p1 and not member.is_fainted():
                with bench_cols[displayed_count]:
                    if os.path.exists(get_sprite_path(member.id)): st.image(get_sprite_path(member.id), width=60)
                    if st.button(f"{member.name}", key=f"switch_{i}"):
                        execute_turn("SWITCH", i)
                    st.caption(f"HP: {member.current_hp}")
                displayed_count += 1
        if displayed_count == 0: st.info("Non hai altri Pokémon disponibili!")
else:
    if st.session_state['winner'] == "PLAYER":
        st.balloons()
        st.success("🏆 VITTORIA! Hai sconfitto l'IA.")
    else:
        st.error("💀 SCONFITTA! L'IA ha vinto.")
    if st.button("Riavvia Partita"):
        del st.session_state['battle_system']
        st.rerun()

st.markdown("---")
st.subheader("📜 Cronaca")
with st.container(height=300):
    for log in st.session_state['logs']:
        st.write(log)