import streamlit as st
import random
import copy
import os
import time

# Importiamo le classi dal tuo file motore
from pokemon_engine import load_moves, load_gen1_pokemon, Battle, Pokemon, calculate_damage
# Importiamo l'IA Minimax
from ai_minimax import get_best_move_minimax

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Pokémon AI Arena", page_icon="⚡", layout="wide") # Layout wide per più spazio

# --- FUNZIONI DI UTILITÀ ---
def get_sprite_path(pokemon_id):
    filename = f"{pokemon_id:03d}MS.png"
    return os.path.join("sprites", filename)

# --- ALGORITMO GREEDY ---
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

# --- SIDEBAR: SELETTORE AI E SQUADRE DETTAGLIATE ---
with st.sidebar:
    st.header("⚙️ Impostazioni IA")
    
    # SELETTORE IA
    ai_choice = st.radio(
        "Cervello Avversario:",
        ("Greedy (Avido)", "Minimax (Intelligente)")
    )
    
    st.divider()
    
    # SQUADRA GIOCATORE CON STATS
    st.subheader("La tua Squadra")
    for p in battle.team1:
        icon = "🔴" if p == battle.p1_active else ("💀" if p.is_fainted() else "🟢")
        
        # Usa un expander per nascondere le stats e aprirle al click
        with st.expander(f"{icon} {p.name} ({p.current_hp}/{p.max_hp})"):
            st.image(get_sprite_path(p.id), width=50)
            st.caption(f"ATK: {p.attack} | DEF: {p.defense}")
            st.caption(f"SPA: {p.sp_attack} | SPD: {p.sp_defense}")
            st.caption(f"SPE: {p.speed}")
            st.caption(f"Tipi: {'/'.join(p.types)}")
    
    st.divider()
    
    # SQUADRA AVVERSARIA CON STATS
    st.subheader("Squadra Avversaria")
    for p in battle.team2:
        icon = "🔴" if p == battle.p2_active else ("💀" if p.is_fainted() else "🟢")
        with st.expander(f"{icon} {p.name} ({p.current_hp}/{p.max_hp})"):
            st.image(get_sprite_path(p.id), width=50)
            st.caption(f"ATK: {p.attack} | DEF: {p.defense}")
            st.caption(f"SPA: {p.sp_attack} | SPD: {p.sp_defense}")
            st.caption(f"SPE: {p.speed}")
            st.caption(f"Tipi: {'/'.join(p.types)}")

# --- UI CENTRALE ---
st.title("⚡ Pokémon AI Arena")
st.caption(f"Turno {st.session_state['turn']} | **{ai_choice}** vs Umano")

col1, col_center, col2 = st.columns([1, 0.2, 1])

# --- GIOCATORE (SINISTRA) ---
with col1:
    st.markdown(f"### Tu: **{p1.name}**")
    sprite_path = get_sprite_path(p1.id)
    if os.path.exists(sprite_path): st.image(sprite_path, width=150)
    else: st.warning(f"No img: {p1.id}")
    
    hp_pct = max(0.0, p1.current_hp / p1.max_hp)
    st.progress(hp_pct, text=f"HP: {p1.current_hp}/{p1.max_hp}")
    # Mostriamo le stats attive anche qui per comodità
    st.info(f"Atk: {p1.attack} | Def: {p1.defense} | SpA: {p1.sp_attack} | SpD: {p1.sp_defense} | Spe: {p1.speed}")

# --- AVVERSARIO (DESTRA) ---
with col2:
    st.markdown(f"### AI: **{p2.name}**")
    sprite_path_ai = get_sprite_path(p2.id)
    if os.path.exists(sprite_path_ai): st.image(sprite_path_ai, width=150)
    else: st.warning(f"No img: {p2.id}")
        
    hp_pct_ai = max(0.0, p2.current_hp / p2.max_hp)
    st.progress(hp_pct_ai, text=f"HP: {p2.current_hp}/{p2.max_hp}")
    st.info(f"Atk: {p2.attack} | Def: {p2.defense} | SpA: {p2.sp_attack} | SpD: {p2.sp_defense} | Spe: {p2.speed}")

st.divider()

# --- LOGICA DEL TURNO ---
def execute_turn(player_action_type, player_data):
    current_logs = []
    current_logs.append(f"--- Turno {st.session_state['turn']} ---")
    
    # 1. SCELTA IA (DINAMICA BASATA SULLA SIDEBAR)
    start_time = time.time() # Misuriamo quanto ci mette (utile per il prof!)
    
    if ai_choice == "Greedy (Avido)":
        ai_move_idx = get_best_move_greedy(battle.p2_active, battle.p1_active)
        ai_algo_name = "Greedy"
    else:
        # DEPTH 2 per renderlo intelligente
        ai_move_idx = get_best_move_minimax(battle, depth=2)
        ai_algo_name = "Minimax (D2)"
        
    elapsed = time.time() - start_time
    # Scriviamo nel log quanto ci ha messo (ottimo per la metrica "Performance"!)
    current_logs.append(f"🧠 {ai_algo_name} ha pensato per {elapsed:.2f}s")
        
    ai_move = battle.p2_active.moves[ai_move_idx]
    
    # 2. ESECUZIONE AZIONI
    
    # CASO A: SWITCH
    if player_action_type == "SWITCH":
        new_pkmn = battle.team1[player_data]
        old_pkmn = battle.p1_active
        battle.p1_active = new_pkmn 
        current_logs.append(f"🔄 Hai scambiato {old_pkmn.name} con **{new_pkmn.name}**!")
        
        if not battle.p2_active.is_fainted():
            dmg, eff = calculate_damage(battle.p2_active, battle.p1_active, ai_move)
            if eff == -1.0:
                current_logs.append(f"❌ L'IA usa {ai_move.name} ma fallisce!")
            else:
                eff_msg = " (Super Efficace!)" if eff > 1 else (" (Non efficace...)" if eff < 1 else "")
                current_logs.append(f"🤖 L'IA ({battle.p2_active.name}) usa {ai_move.name}{eff_msg} sul nuovo entrato!")
                battle.p1_active.take_damage(dmg)
                current_logs.append(f"-> {battle.p1_active.name} subisce {dmg} danni.")

    # CASO B: ATTACCO
    elif player_action_type == "ATTACK":
        player_move = battle.p1_active.moves[player_data]
        
        if battle.p1_active.speed >= battle.p2_active.speed:
            order = [(battle.p1_active, battle.p2_active, player_move, "Tu"), 
                     (battle.p2_active, battle.p1_active, ai_move, "AI")]
        else:
            order = [(battle.p2_active, battle.p1_active, ai_move, "AI"), 
                     (battle.p1_active, battle.p2_active, player_move, "Tu")]
            
        for att, defe, move, who in order:
            if att.is_fainted() or defe.is_fainted(): continue
            
            dmg, eff = calculate_damage(att, defe, move)
            
            if eff == -1.0:
                current_logs.append(f"❌ **{who}** ({att.name}) usa {move.name} ma fallisce!")
                continue
                
            eff_msg = " (Super Efficace!)" if eff > 1 else (" (Non efficace...)" if eff < 1 else "")
            
            current_logs.append(f"**{who}** ({att.name}) usa {move.name}{eff_msg}")
            defe.take_damage(dmg)
            current_logs.append(f"-> {defe.name} subisce {dmg} danni.")
            
            if defe.is_fainted():
                current_logs.append(f"💀 {defe.name} è esausto!")

    # 3. GESTIONE KO E VITTORIA
    if battle.p1_active.is_fainted():
        next_p = battle.get_next_pokemon(battle.team1)
        if next_p:
            battle.p1_active = next_p
            current_logs.append(f"⚠️ {battle.p1_active.name} entra in campo!")
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
    
    st.subheader("⚔️ Scegli Mossa")
    
    # CSS per rendere i bottoni più carini (Opzionale)
    st.markdown("""
        <style>
        div.stButton > button {height: 80px;}
        </style>""", unsafe_allow_html=True)
        
    cols = st.columns(4)
    for i, move in enumerate(p1.moves):
        with cols[i]:
            # LOGICA ICONE E CATEGORIA
            cat_lower = move.category.lower()
            if cat_lower in ["fisico", "physical"]:
                cat_icon = "💥" # Fisico
            elif cat_lower in ["speciale", "special"]:
                cat_icon = "✨" # Speciale
            else:
                cat_icon = "⚪" # Stato
            
            # FORMATTAZIONE PULSANTE CON DATI
            # Es: Lanciafiamme (Fire)
            # Pow: 90 | Acc: 100 | ✨
            btn_label = f"{move.name} ({move.type})\nPow: {move.power} | Acc: {move.accuracy}% | {cat_icon}"
            
            if st.button(btn_label, key=f"btn_{i}", use_container_width=True):
                execute_turn("ATTACK", i)
                
    with st.expander("🔄 Sostituisci Pokémon (Panchina)"):
        st.write("Scegli un Pokémon per sostituire quello attuale (perderai il turno di attacco):")
        bench_cols = st.columns(6)
        
        displayed_count = 0
        for i, member in enumerate(battle.team1):
            if member != p1 and not member.is_fainted():
                with bench_cols[displayed_count]:
                    s_path = get_sprite_path(member.id)
                    if os.path.exists(s_path): st.image(s_path, width=60)
                    if st.button(f"{member.name}", key=f"switch_{i}"):
                        execute_turn("SWITCH", i)
                    # Mostra mini stats
                    st.caption(f"HP: {member.current_hp}")
                displayed_count += 1
        
        if displayed_count == 0:
            st.info("Non hai altri Pokémon disponibili!")

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