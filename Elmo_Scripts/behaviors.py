import random
import threading
from utils import get_unselected_blocks, get_unselected_positions
from state_machine import State
from session_logger import session_logger

# ---------------------------------------------------------
# ASYNCHRONOUS HELPERS (No Blocking/Threading)
# ---------------------------------------------------------

def gaze_at_participant_async(robot, ui):
    """
    Non-blocking version of look_at_participant.
    Runs the blocking head movement in a daemon thread so the UI stays responsive.
    Uses only the safe RobotController methods.
    """
    if robot is None: return
    threading.Thread(target=robot.look_at_participant, daemon=True).start()

def robot_speak_while_gaze(robot, state, ui, sound_title, duration=4000):
    """Helper to handle the 'is_hint_active' flag used by the loops."""
    state.is_hint_active = True
    if robot: robot.stop_idle()
    
    # 1. Asynchronous head movement
    gaze_at_participant_async(robot, ui)
    
    # 2. Synchronized audio
    ui.schedule(lambda: robot.play_sound(sound_title), 500)
    
    # Reset flag after sound finishes (standard hints are ~4s)
    ui.schedule(lambda: setattr(state, 'is_hint_active', False), duration)

# ---------------------------------------------------------
# DATA UTILS
# ---------------------------------------------------------

def update_countdown(state, steps, hint_steps):
    """Restores your countdown UI logic."""
    next_hint = None
    for h in hint_steps:
        if steps <= h:
            next_hint = h
            break
            
    if next_hint is not None:
        remaining_seconds = (next_hint - steps) // 2
        state.hint_countdown.set(f"Hint in: {remaining_seconds}s…")
    else:
        state.hint_countdown.set("")

def sequence_generator(n):
    colours = ["Azul", "Vermelho", "Amarelo", "Roxo", "Verde"]
    positions = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    
    if n <= len(colours):
        # Use sample (no repeats) so all blocks in a sequence are different colours
        selected_colours = random.sample(colours, k=n)
    else:
        # Use choices (with repeats) if sequence is longer, but ensure max 2 of same colour
        while True:
            selected_colours = random.choices(colours, k=n)
            if all(selected_colours.count(c) <= 2 for c in colours):
                break
                
    selected_positions = random.sample(positions, k=n)
    return selected_colours, selected_positions

# ---------------------------------------------------------
# INCORRECT POSITION
# ---------------------------------------------------------

def incorrect_position(robot, state, ui, pos_idx, steps=0):
    wait_time = state.wait_time
    hint_steps = [0, wait_time * 2, wait_time * 4]

    if steps == 0:
        last_idx = getattr(state, "last_incorrect_pos_idx", None)
        if last_idx == pos_idx:
            count = getattr(state, "incorrect_pos_count", 0) + 1
        else:
            count = 1

        setattr(state, "last_incorrect_pos_idx", pos_idx)
        setattr(state, "incorrect_pos_count", count)

        if count == 2:
            steps = hint_steps[1]
        elif count >= 3:
            steps = hint_steps[2]

        session_logger.log(f"[BEHAVIOR] incorrect_position triggered (PosIdx={pos_idx}, Count={count})")
        if state.condition != "Control":
            colour = state.seq_block[pos_idx - 1]
            _colour_en = {"Verde": "green", "Azul": "blue", "Roxo": "purple", "Vermelho": "red", "Amarelo": "yellow"}
            if colour == "Roxo":
                robot.update_leds([[149, 28, 255]] * 169)
            elif colour == "Amarelo":
                robot.update_leds([[255,222,89]] * 169)
            else:
                robot.set_leds_icon(f"{_colour_en[colour]}.png")
        setattr(state, '_vfstep', -1)



    if state.current_state != State.INCORRECT_POSITION: return

    current_idx = None
    for i in range(len(state.block_check_vars)):
        if not state.block_check_vars[i].get() or not state.position_check_vars[i].get():
            current_idx = i
            break

    if current_idx is None or (current_idx + 1) != pos_idx: return

    wait_time = state.wait_time
    hint_steps = [0, wait_time * 2, wait_time * 4]

    if steps > hint_steps[-1]:
        state.transition(State.IDLE, robot, ui)
        return

    update_countdown(state, steps, hint_steps)
    current_pos_val = state.seq_position[pos_idx - 1]
    colour = state.seq_block[pos_idx - 1]

    i = random.randint(1, 3)

    if state.condition == "Implicit":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"PosicaoErrada{colour}_{i}.wav")
            steps += 1
        elif steps in hint_steps[1:] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            if getattr(state, '_vfstep', -1) != steps:
                setattr(state, '_vfstep', steps)
                robot_speak_while_gaze(robot, state, ui, f"VamosFocar{colour}{i}.wav", duration=3500)
            else:
                if steps == hint_steps[1]:
                    if current_pos_val in ["1", "2", "3"]: sound = f"PosicaoCorretaLinhaCima_{i}.wav"
                    elif current_pos_val in ["4", "5", "6"]: sound = f"PosicaoCorretaLinhaMeio_{i}.wav"
                    else: sound = f"PosicaoCorretaLinhaBaixo_{i}.wav"
                elif steps == hint_steps[2]:
                    if current_pos_val in ["1", "4", "7"]: sound = f"PosicaoCorretaColunaEsquerda_{i}.wav"
                    elif current_pos_val in ["2", "5", "8"]: sound = f"PosicaoCorretaColunaMeio_{i}.wav"
                    else: sound = f"PosicaoCorretaColunaDireita_{i}.wav"
                robot_speak_while_gaze(robot, state, ui, sound)
                steps += 1

    elif state.condition == "Explicit":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"PosicaoErradaUps{colour}_{i}.wav")
            steps += 1
        elif steps in hint_steps[1:] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            if getattr(state, '_vfstep', -1) != steps:
                setattr(state, '_vfstep', steps)
                robot_speak_while_gaze(robot, state, ui, f"VamosFocar{colour}{i}.wav", duration=3500)
            else:
                if steps == hint_steps[1]:
                    ui.schedule(lambda: robot.set_screen(image=f"posicao_{current_pos_val}.png"), 2000)
                    robot_speak_while_gaze(robot, state, ui, f"QueresPista{i}.wav")
                    ui.schedule(lambda: robot.set_screen(image="normal.png"), 8000)
                elif steps == hint_steps[2]:
                    robot_speak_while_gaze(robot, state, ui, f"PodesMover{current_pos_val}_{i}.wav")
                steps += 1

    elif state.condition == "Control":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"QueresVerificar{i}.wav")
            steps += 1
        elif steps == hint_steps[1] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"TempoPrecisares{i}.wav")
            steps += 1
        elif steps == hint_steps[2] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"TentaCompletar{i}.wav")
            steps += 1

    next_step = steps if state.is_hint_active else steps + 1
    ui.schedule(lambda: incorrect_position(robot, state, ui, pos_idx, next_step), 500)

# ---------------------------------------------------------
# INCORRECT CUBE
# ---------------------------------------------------------

def incorrect_cube(robot, state, ui, block_idx, steps=0):
    wait_time = state.wait_time
    # Verde/Azul/Roxo in Implicit need a 4th step for the second colour exclusion
    _peek_block = state.seq_block[block_idx - 1]
    if state.condition == "Implicit" and _peek_block in ["Verde", "Azul", "Roxo"]:
        hint_steps = [0, wait_time * 2, wait_time * 4, wait_time * 6]
    else:
        hint_steps = [0, wait_time * 2, wait_time * 4]

    if steps == 0:
        last_idx = getattr(state, "last_incorrect_cube_idx", None)
        if last_idx == block_idx:
            count = getattr(state, "incorrect_cube_count", 0) + 1
        else:
            count = 1

        setattr(state, "last_incorrect_cube_idx", block_idx)
        setattr(state, "incorrect_cube_count", count)

        if count >= 2:
            steps = hint_steps[min(count - 1, len(hint_steps) - 1)]

        session_logger.log(f"[BEHAVIOR] incorrect_cube triggered (BlockIdx={block_idx}, Count={count})")
        if state.condition != "Control":
            position = state.seq_position[block_idx - 1]
            robot.set_leds_icon(f"{position}.png")
        setattr(state, '_vfstep', -1)

    if state.current_state != State.INCORRECT_CUBE: return

    current_idx = None
    for i in range(len(state.block_check_vars)):
        if not state.block_check_vars[i].get() or not state.position_check_vars[i].get():
            current_idx = i
            break

    if current_idx is None or (current_idx + 1) != block_idx: return

    wait_time = state.wait_time
    current_block = state.seq_block[block_idx - 1]
    if state.condition == "Implicit" and current_block in ["Verde", "Azul", "Roxo"]:
        hint_steps = [0, wait_time * 2, wait_time * 4, wait_time * 6]
    else:
        hint_steps = [0, wait_time * 2, wait_time * 4]

    if steps > hint_steps[-1]:
        state.transition(State.IDLE, robot, ui)
        return

    update_countdown(state, steps, hint_steps)

    i = random.randint(1,3)

    position = state.seq_position[block_idx - 1]

    if state.condition == "Implicit":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            state.set_available_colours(current_block)
            robot_speak_while_gaze(robot, state, ui, f"BlocoErradoPosicao{position}_{i}.wav")
            steps += 1
        elif steps in hint_steps[1:] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            if getattr(state, '_vfstep', -1) != steps:
                setattr(state, '_vfstep', steps)
                robot_speak_while_gaze(robot, state, ui, f"VamosFocar{position}_{i}.wav", duration=3500)
            else:
                if steps == hint_steps[1]:
                    sound = f"BlocoCertoDireita{i}.wav" if current_block in ["Verde", "Azul", "Roxo"] else f"BlocoCertoEsquerda{i}.wav"
                    robot_speak_while_gaze(robot, state, ui, sound)
                elif steps == hint_steps[2]:
                    if current_block in state.available_colours: state.available_colours.remove(current_block)
                    if state.available_colours:
                        colour = random.choice(state.available_colours)
                        state.available_colours.remove(colour)
                        robot_speak_while_gaze(robot, state, ui, f"BlocoCertoNo{colour}{i}.wav")
                elif len(hint_steps) > 3 and steps == hint_steps[3]:
                    if state.available_colours:
                        colour = random.choice(state.available_colours)
                        state.available_colours.remove(colour)
                        robot_speak_while_gaze(robot, state, ui, f"BlocoCertoNo{colour}{i}.wav")
                steps += 1

    elif state.condition == "Explicit":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"BlocoErradoUpsPosicao{position}_{i}.wav")
            steps += 1
        elif steps in hint_steps[1:] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            if getattr(state, '_vfstep', -1) != steps:
                setattr(state, '_vfstep', steps)
                robot_speak_while_gaze(robot, state, ui, f"VamosFocar{position}_{i}.wav", duration=3500)
            else:
                if steps == hint_steps[1]:
                    ui.schedule(lambda: robot.set_screen(image=f"olhos_{current_block}.png"), 2000)
                    robot_speak_while_gaze(robot, state, ui, f"QueresPista{i}.wav")
                    ui.schedule(lambda: robot.set_screen(image="normal.png"), 8000)
                elif steps == hint_steps[2]:
                    robot_speak_while_gaze(robot, state, ui, f"TrocaBloco{current_block}_{i}.wav")
                steps += 1

    elif state.condition == "Control":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"QueresVerificarCor{i}.wav")
            steps += 1
        elif steps == hint_steps[1] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"TempoPrecisares{i}.wav")
            steps += 1
        elif steps == hint_steps[2] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"TentaCompletarBloco{i}.wav")
            steps += 1

    next_step = steps if state.is_hint_active else steps + 1
    ui.schedule(lambda: incorrect_cube(robot, state, ui, block_idx, next_step), 500)

# ---------------------------------------------------------
# HESITANT CUBE
# ---------------------------------------------------------

def hesitant_cube(robot, state, ui, steps=0):
    if steps == 0: session_logger.log("[BEHAVIOR] hesitant_cube triggered")
    if state.current_state != State.HESITANT_CUBE: return

    # Warm-up delay
    if steps == 0:
        ui.schedule(lambda: hesitant_cube(robot, state, ui, 1), 2500)
        return

    blocks = get_unselected_blocks(state.block_check_vars)
    if not blocks: return
    current_block = state.seq_block[blocks[0]-1]
    wait_time = state.wait_time

    if state.condition == "Implicit" and current_block in ["Verde", "Azul", "Roxo"]: hint_steps = [wait_time, wait_time*2, wait_time*4]
    else: hint_steps = [wait_time, wait_time*2]

    if steps > hint_steps[-1]:
        state.transition(State.IDLE, robot, ui)
        return

    update_countdown(state, steps, hint_steps)

    i = random.randint(1, 3)

    if state.condition == "Implicit":
        if steps == hint_steps[0] and not state.is_hint_active:
            state.set_available_colours(current_block)
            state.is_hint_active = True
            robot.set_screen(image="tears.png")
            robot.stop_idle()
            if current_block in ["Verde", "Azul", "Roxo"]:
                threading.Thread(target=robot.look_left, daemon=True).start()
                ui.schedule(lambda: robot.play_sound(f"FaltaUmDireita{i}.wav"), 1000)
            else:
                threading.Thread(target=robot.look_right, daemon=True).start()
                ui.schedule(lambda: robot.play_sound(f"FaltaUmEsquerda{i}.wav"), 1000)
            steps += 1
            ui.schedule(lambda: robot.resume_idle(), 5000)
            ui.schedule(lambda: setattr(state, 'is_hint_active', False), 5500)
        elif steps in hint_steps[1:] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            if current_block in state.available_colours: state.available_colours.remove(current_block)
            if state.available_colours:
                col = random.choice(state.available_colours)
                state.available_colours.remove(col)
                robot_speak_while_gaze(robot, state, ui, f"BlocoCertoNo{col}{i}.wav")
            steps += 1

    elif state.condition == "Explicit":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="tears.png")
            ui.schedule(lambda: robot.set_screen(image=f"olhos_{current_block}.png"), 2000)
            robot_speak_while_gaze(robot, state, ui, f"FaltaQueresPista{i}.wav")
            steps += 1
            ui.schedule(lambda: robot.set_screen(image="normal.png"), 8000)
        elif steps == hint_steps[1] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"Bloco{current_block}_{i}.wav")
            steps += 1

    elif state.condition == "Control":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="tears.png")
            robot_speak_while_gaze(robot, state, ui, f"PensaCor{i}.wav")
            steps += 1
            ui.schedule(lambda: robot.set_screen(image="normal.png"), 4500)
        elif steps == hint_steps[1] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"TempoPrecisares{i}.wav")
            steps += 1

    next_step = steps if state.is_hint_active else steps + 1
    ui.schedule(lambda: hesitant_cube(robot, state, ui, next_step), 500)

# ---------------------------------------------------------
# HESITANT POSITION
# ---------------------------------------------------------

def hesitant_position(robot, state, ui, steps=0):
    if steps == 0: session_logger.log("[BEHAVIOR] hesitant_position triggered")
    if state.current_state != State.HESITANT_POSITION: return

    # Warm-up delay
    if steps == 0:
        ui.schedule(lambda: hesitant_position(robot, state, ui, 1), 2500)
        return

    positions = get_unselected_positions(state.position_check_vars)
    if not positions: return
    current_pos_val = state.seq_position[positions[0]-1]
    wait_time = state.wait_time
    hint_steps = [wait_time * 2, wait_time * 4]

    if steps > hint_steps[-1] + (2 * wait_time):
        state.transition(State.IDLE, robot, ui)
        return

    update_countdown(state, steps, hint_steps)

    i = random.randint(1,3)

    if state.condition == "Implicit":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="tears.png")
            if current_pos_val in ["1", "2", "3"]: sound = f"PosicaoCorretaLinhaCima{i}.wav"
            elif current_pos_val in ["4", "5", "6"]: sound = f"PosicaoCorretaLinhaMeio{i}.wav"
            else: sound = f"PosicaoCorretaLinhaBaixo{i}.wav"
            robot_speak_while_gaze(robot, state, ui, sound)
            steps += 1
            ui.schedule(lambda: robot.resume_idle(), 3000)
        elif steps == hint_steps[1] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            state.is_hint_active = True
            robot.stop_idle()
            if current_pos_val in ["1", "4", "7"]:
                threading.Thread(target=robot.look_right, daemon=True).start()
                sound = f"PosicaoCorretaColunaEsquerda{i}.wav"
            elif current_pos_val in ["2", "5", "8"]:
                threading.Thread(target=robot.look_middle, daemon=True).start()
                sound = f"PosicaoCorretaColunaMeio{i}.wav"
            else:
                threading.Thread(target=robot.look_left, daemon=True).start()
                sound = f"PosicaoCorretaColunaDireita{i}.wav"
            ui.schedule(lambda: robot.play_sound(sound), 1000)
            steps += 1
            ui.schedule(lambda: robot.resume_idle(), 5000)
            ui.schedule(lambda: setattr(state, 'is_hint_active', False), 5500)

    elif state.condition == "Explicit":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="tears.png")
            ui.schedule(lambda: robot.set_screen(image=f"posicao_{current_pos_val}.png"), 2000)
            robot_speak_while_gaze(robot, state, ui, f"QueresPistaPosicao{random.randint(1,3)}.wav")
            steps += 1
            ui.schedule(lambda: robot.set_screen(image="normal.png"), 8000)
        elif steps == hint_steps[1] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"PodesMover{current_pos_val}_{i}.wav")
            steps += 1

    elif state.condition == "Control":
        if steps == hint_steps[0] and not state.is_hint_active:
            robot.set_screen(image="tears.png")
            robot_speak_while_gaze(robot, state, ui, f"Palpite{random.randint(1,3)}.wav")
            steps += 1
            ui.schedule(lambda: robot.set_screen(image="normal.png"), 4500)
        elif steps == hint_steps[1] and not state.is_hint_active:
            robot.set_screen(image="thinking.png")
            robot_speak_while_gaze(robot, state, ui, f"TempoPrecisares{random.randint(1,3)}.wav")
            steps += 1

    next_step = steps if state.is_hint_active else steps + 1
    ui.schedule(lambda: hesitant_position(robot, state, ui, next_step), 500)

# ---------------------------------------------------------
# SPECIAL STATES (Intro, Sequence, Wrong Block)
# ---------------------------------------------------------

def touched_wrong_block_behavior(robot, state, ui):
    session_logger.log("[BEHAVIOR] touched_wrong_block_behavior triggered")
    state.is_hint_active = True
    robot.stop_idle()
    gaze_at_participant_async(robot, ui)

    i = random.randint(1, 3)
    
    if state.condition == "Explicit": sound = f"NaoEsseBloco{i}.wav"
    elif state.condition == "Implicit": sound = f"MexesteErrado{i}.wav"
    else: sound = f"Hmmm{i}.wav"
        
    ui.schedule(lambda: robot.play_sound(sound), 1000)
    ui.schedule(lambda: robot.resume_idle(), 5000)
    ui.schedule(lambda: setattr(state, 'is_hint_active', False), 5500)
    
    def reset_wrong_block():
        state.touched_wrong_block = False
        if hasattr(state, 'twb_var_ref'): state.twb_var_ref.set(False)
        state.transition(State.IDLE, robot, ui)
        
    ui.schedule(reset_wrong_block, 6000)

def say_intro(robot, state, ui, on_done=None):
    session_logger.log("[BEHAVIOR] say_intro triggered")
    state.is_hint_active = True
    robot.stop_idle()
    gaze_at_participant_async(robot, ui)
    
    def play_instructions():
        robot_speak_while_gaze(robot, state, ui, "Instructions.wav", duration=15000)
        ui.schedule(lambda: robot.resume_idle(), 14000)
        ui.schedule(lambda: setattr(state, 'is_hint_active', False), 15000)
        if on_done: ui.schedule(on_done, 15500)

    ui.schedule(lambda: robot_speak_while_gaze(robot, state, ui, "Intro.wav", duration=5000), 1500)
    ui.schedule(play_instructions, 6500)

def say_sequence(robot, state, ui, seq_block, seq_position, n):
    session_logger.log(f"[BEHAVIOR] say_sequence triggered for {n} items")
    state.is_hint_active = True
    robot.stop_idle()
    gaze_at_participant_async(robot, ui)
    isi = getattr(state, "isi", 2)

    def play_go_signal():
        if getattr(state, "sequence_aborted", False): return
        robot.set_screen(image="normal.png")
        robot_speak_while_gaze(robot, state, ui, f"JaPodes{random.randint(1,3)}.wav")
        ui.schedule(lambda: robot.resume_idle(), 4000)
        ui.schedule(lambda: (setattr(state, 'is_sequence_active', False), state.check_logic_gate(robot, ui)), 4500)

    def speak_item(i):
        if getattr(state, "sequence_aborted", False): return
        if i >= n:
            ui.schedule(play_go_signal, 500)
            return
        image_name = f"bloco_{seq_block[i].lower()}_posicao_{seq_position[i]}.png"
        robot.set_screen(image=image_name)
        robot_speak_while_gaze(robot, state, ui, f"Bloco{seq_block[i]}Posicao{seq_position[i]}.wav", duration=(3+isi)*1000)
        ui.schedule(lambda: speak_item(i + 1), int((3 + isi) * 1000))

    ui.schedule(lambda: speak_item(0), 2500)

def forgot_sequence_behavior(robot, state, ui):
    from state_machine import State
    session_logger.log("[BEHAVIOR] forgot_sequence_behavior triggered")
    robot.stop_idle()
    gaze_at_participant_async(robot, ui)
    
    i = random.randint(1,3)
    if state.condition == "Implicit":
        ui.schedule(lambda: robot_speak_while_gaze(robot, state, ui, f"PerdemosOrdem{i}.wav"), 1000)
    elif state.condition == "Explicit":
        ui.schedule(lambda: robot_speak_while_gaze(robot, state, ui, f"SequenciaAssim{i}.wav"), 1000)
    else:  # Control condition
        ui.schedule(lambda: robot_speak_while_gaze(robot, state, ui, f"TentaLembrar{i}.wav"), 1000)
        ui.schedule(lambda: robot.resume_idle(), 5500)
        from state_machine import State
        ui.schedule(lambda: state.transition(State.IDLE, robot, ui), 6000)
        return
        
    isi = getattr(state, "isi", 2)
    def play_end_signal():
        if getattr(state, "forgot_aborted", False): return
        robot.set_screen(image="normal.png")
        if state.condition == "Implicit":
            robot_speak_while_gaze(robot, state, ui, f"ConseguesDaqui{random.randint(1,3)}.wav")
        else:
            robot_speak_while_gaze(robot, state, ui, f"PodesColocar{i}.wav")
        ui.schedule(lambda: robot.resume_idle(), 4500)
        ui.schedule(lambda: state.transition(State.IDLE, robot, ui), 5000)

    def speak_item(idx):
        if getattr(state, "forgot_aborted", False): return
        
        limit = getattr(state, "forgot_sequence_level", 2) if state.condition == "Implicit" else len(state.seq_block)
        max_limit = max(1, len(state.seq_block) - 1) if state.condition == "Implicit" else len(state.seq_block)
        limit = min(limit, max_limit)
        
        if idx >= limit:
            if state.condition == "Implicit" and getattr(state, "forgot_sequence_level", 2) < max_limit:
                state.forgot_sequence_level = getattr(state, "forgot_sequence_level", 2) + 1
            ui.schedule(play_end_signal, 500)
            return
            
        image_name = f"bloco_{state.seq_block[idx].lower()}_posicao_{state.seq_position[idx]}.png"
        robot.set_screen(image=image_name)
        robot_speak_while_gaze(robot, state, ui, f"Bloco{state.seq_block[idx]}Posicao{state.seq_position[idx]}.wav", duration=(3+isi)*1000)
        ui.schedule(lambda: speak_item(idx + 1), int((3 + isi) * 1000))
        
    # Greatly increase padding to ensure audio completes gracefully before stacking speech requests
    ui.schedule(lambda: speak_item(0), 9000)
