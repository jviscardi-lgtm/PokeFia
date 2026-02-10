import streamlit as st
import random
import copy
import os
import time

# Importiamo le classi dal tuo file motore
from pokemon_engine import load_moves, load_gen1_pokemon, Battle, Pokemon, calculate_damage

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Pokémon AI Arena", page_icon="⚡", layout="centered")

# --- FUNZIONI DI UTILITÀ ---
def get_sprite_path(pokemon_id):
    filename = f"{pokemon_id:03d}MS.png"
    return os.path.join("sprites", filename)

def get_best_move_greedy(attacker, defender):
    best_move_idx = 0
    max_damage = -1
    if not attacker.moves: return 0
    for i, move in enumerate(attacker.moves):
        dmg, _ = calculate_damage(attacker, defender, move)
        if dmg > max_damage:
            max_damage = dmg
            best_move_idx = i
    return best_move_idx

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

# --- UI: TITOLO E ARENA ---
st.title("⚡ Pokémon AI Arena")
st.caption(f"Turno {st.session_state['turn']} | Greedy AI vs Umano")

col1, col_center, col2 = st.columns([1, 0.2, 1])

# --- GIOCATORE (SINISTRA) ---
with col1:
    st.markdown(f"### Tu: **{p1.name}**")
    sprite_path = get_sprite_path(p1.id)
    if os.path.exists(sprite_path): st.image(sprite_path, width=120)
    else: st.warning(f"No img: {p1.id}")
    
    hp_pct = max(0.0, p1.current_hp / p1.max_hp)
    st.progress(hp_pct, text=f"HP: {p1.current_hp}/{p1.max_hp}")
    st.code(f"{'/'.join(p1.types)}")

# --- AVVERSARIO (DESTRA) ---
with col2:
    st.markdown(f"### AI: **{p2.name}**")
    sprite_path_ai = get_sprite_path(p2.id)
    if os.path.exists(sprite_path_ai): st.image(sprite_path_ai, width=120)
    else: st.warning(f"No img: {p2.id}")
        
    hp_pct_ai = max(0.0, p2.current_hp / p2.max_hp)
    st.progress(hp_pct_ai, text=f"HP: {p2.current_hp}/{p2.max_hp}")
    st.code(f"{'/'.join(p2.types)}")

st.divider()

# --- LOGICA DEL TURNO (FUNZIONE CENTRALE) ---
def execute_turn(player_action_type, player_data):
    """
    player_action_type: "ATTACK" o "SWITCH"
    player_data: indice mossa (se ATTACK) o indice pokemon (se SWITCH)
    """
    current_logs = []
    current_logs.append(f"--- Turno {st.session_state['turn']} ---")
    
    # 1. SCELTA IA (GREEDY)
    # Nota: L'IA decide in base al pokemon che vede ORA in campo.
    # Se il giocatore scambia, l'IA colpirà il nuovo entrato.
    ai_move_idx = get_best_move_greedy(battle.p2_active, battle.p1_active)
    ai_move = battle.p2_active.moves[ai_move_idx]
    
    # 2. ESECUZIONE AZIONI
    
    # CASO A: IL GIOCATORE SCAMBIA
    if player_action_type == "SWITCH":
        new_pkmn = battle.team1[player_data]
        old_pkmn = battle.p1_active
        battle.p1_active = new_pkmn # Cambio effettivo
        current_logs.append(f"🔄 Hai ritirato {old_pkmn.name} e mandato in campo **{new_pkmn.name}**!")
        
        # L'IA attacca il NUOVO Pokémon (free hit)
        if not battle.p2_active.is_fainted():
            dmg, eff = calculate_damage(battle.p2_active, battle.p1_active, ai_move)
            eff_msg = " (Super Efficace!)" if eff > 1 else (" (Non efficace...)" if eff < 1 else "")
            current_logs.append(f"🤖 L'IA ({battle.p2_active.name}) usa {ai_move.name}{eff_msg} su {new_pkmn.name} entrante!")
            battle.p1_active.take_damage(dmg)
            current_logs.append(f"-> {battle.p1_active.name} subisce {dmg} danni.")

    # CASO B: IL GIOCATORE ATTACCA
    elif player_action_type == "ATTACK":
        player_move = battle.p1_active.moves[player_data]
        
        # Ordine di velocità
        if battle.p1_active.speed >= battle.p2_active.speed:
            order = [(battle.p1_active, battle.p2_active, player_move, "Tu"), 
                     (battle.p2_active, battle.p1_active, ai_move, "AI")]
        else:
            order = [(battle.p2_active, battle.p1_active, ai_move, "AI"), 
                     (battle.p1_active, battle.p2_active, player_move, "Tu")]
            
        for att, defe, move, who in order:
            if att.is_fainted() or defe.is_fainted(): continue
            
            dmg, eff = calculate_damage(att, defe, move)
            eff_msg = " (Super Efficace!)" if eff > 1 else (" (Non efficace...)" if eff < 1 else "")
            
            current_logs.append(f"**{who}** ({att.name}) usa {move.name}{eff_msg}")
            defe.take_damage(dmg)
            current_logs.append(f"-> {defe.name} subisce {dmg} danni.")
            
            if defe.is_fainted():
                current_logs.append(f"💀 {defe.name} è esausto!")

    # 3. GESTIONE KO E FINE PARTITA
    if battle.p1_active.is_fainted():
        # Controllo se hai perso
        next_p = battle.get_next_pokemon(battle.team1)
        if next_p:
            battle.p1_active = next_p
            current_logs.append(f"⚠️ {battle.p1_active.name} entra in campo forzatamente!")
        else:
            st.session_state['winner'] = "AI"
            st.session_state['game_over'] = True

    if battle.p2_active.is_fainted() and not st.session_state['game_over']:
        # Controllo se hai vinto
        next_p_ai = battle.get_next_pokemon(battle.team2)
        if next_p_ai:
            battle.p2_active = next_p_ai
            current_logs.append(f"⚠️ L'IA manda in campo {next_p_ai.name}!")
        else:
            st.session_state['winner'] = "PLAYER"
            st.session_state['game_over'] = True

    # Aggiornamento Sessione
    st.session_state['logs'] = current_logs + st.session_state['logs']
    st.session_state['turn'] += 1
    st.rerun()

# --- INTERFACCIA COMANDI ---

if not st.session_state['game_over']:
    
    # 1. SEZIONE ATTACCO
    st.subheader("⚔️ Attacco")
    cols = st.columns(4)
    for i, move in enumerate(p1.moves):
        with cols[i]:
            if st.button(f"{move.name}\n({move.type})", key=f"btn_{i}", use_container_width=True):
                execute_turn("ATTACK", i)

    # 2. SEZIONE SCAMBIO (NUOVA!)
    with st.expander("🔄 Sostituisci Pokémon (Panchina)"):
        st.write("Scegli un Pokémon per sostituire quello attuale (perderai il turno di attacco):")
        bench_cols = st.columns(3) # Griglia per la panchina
        col_idx = 0
        
        for i, member in enumerate(battle.team1):
            # Non mostrare il pokemon attivo attuale e quelli morti
            if member != p1 and not member.is_fainted():
                with bench_cols[col_idx % 3]:
                    # Mostra piccola immagine e bottone
                    s_path = get_sprite_path(member.id)
                    if os.path.exists(s_path): st.image(s_path, width=50)
                    
                    if st.button(f"Entra {member.name}", key=f"switch_{i}"):
                        execute_turn("SWITCH", i)
                col_idx += 1
        
        if col_idx == 0:
            st.info("Non hai altri Pokémon disponibili in panchina!")

else:
    # SCHERMATA FINALE
    if st.session_state['winner'] == "PLAYER":
        st.balloons()
        st.success("🏆 VITTORIA! Hai sconfitto l'IA.")
    else:
        st.error("💀 SCONFITTA! L'IA ha vinto.")
    
    if st.button("Riavvia Partita"):
        del st.session_state['battle_system']
        st.rerun()

# --- LOG ---
st.markdown("---")
st.subheader("📜 Cronaca")
with st.container(height=300):
    for log in st.session_state['logs']:
        st.write(log)

# --- SIDEBAR (SQUADRE) ---
with st.sidebar:
    st.header("La tua Squadra")
    for p in battle.team1:
        icon = "🔴" if p == battle.p1_active else ("💀" if p.is_fainted() else "🟢")
        st.write(f"{icon} {p.name} ({p.current_hp}/{p.max_hp})")
    
    st.divider()
    st.header("Squadra Avversaria")
    for p in battle.team2:
        icon = "🔴" if p == battle.p2_active else ("💀" if p.is_fainted() else "🟢")
        st.write(f"{icon} {p.name} ({p.current_hp}/{p.max_hp})")