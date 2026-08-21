import ElmoV2API
import time
import random
import tkinter as tk
from playsound import playsound
import cv2
import threading
from PIL import Image, ImageTk
import queue
from gaze_behaviors import random_look_loop, look_at_participant, look_to_the_left, look_to_the_right, look_to_the_middle

# ------------------ Camera globals ------------------
latest_frame = None
camera_running = True
is_hint_active = False

def camera_capture():
    global latest_frame
    url = "http://192.168.0.107:8080/stream.mjpg"
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("Camera failed to open")
        return

    while camera_running:
        ret, frame = cap.read()
        if ret:
            # convert BGR -> RGB
            latest_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        time.sleep(0.01)  # 10 ms

    cap.release()

def update_camera_label():
    if latest_frame is not None:
        img = Image.fromarray(latest_frame)
        img = img.resize((500, 300))
        imgtk = ImageTk.PhotoImage(img)
        camera_label.imgtk = imgtk
        camera_label.config(image=imgtk)
    app.after(30, update_camera_label)  # refresh every 30ms

# ------------------ Robot speech ------------------
def say_intro(robot, on_done=None):
    def play_instructions():
        if robot:
            cmd_queue.put("stop")  # stop idle behavior to look at the participant during instructions
            look_at_participant(robot)
            app.after(3000, lambda: robot.play_sound("Instructions.wav"))
            app.after(10000, lambda: cmd_queue.put("start"))  # restart idle behavior after instructions
        else:
            playsound("Elmo_Speech/Instructions.wav")

        if on_done:
            threading.Timer(1, on_done).start()  # duration of instructions

    if robot:
        robot.play_sound("Intro.wav")
        threading.Timer(2, play_instructions).start()
    else:
        playsound("Elmo_Speech/Intro.wav")
        playsound("Elmo_Speech/Instructions.wav")
        if on_done:
            on_done()
    
# ROBOT SPEECH: FUNCTION TO MAKE ROBOT SAY THAT WE ARE MOVING INTO A NEW SEQUENCE
def new_sequence(robot):
    
    n = random.choice([1, 2, 3]) # WHICH VARIATION OF THE "NEXT SEQUENCE" SENTENCE WE'RE GOING TO SAY
    if robot is not None:
        if intro_var.get(): # if robot just said intro
            robot.play_sound(f"PrimeiraSequencia.wav") # FIRST SEQUENCE SOUND
        else:
            robot.play_sound(f"ProximaSequencia{n}.wav") # NEXT SEQUENCE SOUND
            
    else: # debug mode
        if intro_var.get():  # if robot just said intro
                playsound(f"Elmo_Speech/PrimeiraSequencia.wav") # FIRST SEQUENCE SOUND
        else:
            playsound(f"Elmo_Speech/ProximaSequencia{n}.wav") # NEXT SEQUENCE SOUND


def robot_speak_while_gaze(robot, sound_title):
    global is_hint_active

    if robot is not None:
        is_hint_active = True  # pause step counter

        def step_look():
            look_at_participant(robot)

        def step_sound():
            robot.play_sound(sound_title)

        def step_resume():
            global is_hint_active
            is_hint_active = False  # resume counting
            cmd_queue.put("start")
            print("is_hint_active set to false")

        app.after(300, step_look)
        app.after(2000, step_sound)
        app.after(7000, step_resume)


# ------------------ Robot logic ------------------
def incorrect_position(robot, position_which_is_wrong, steps=0):
    print(f"------- \INCORRECT POSITION, steps: {steps}") # for debugging
    condition = condition_var.get()
    positions = get_unselected_positions()
    if positions:
        is_wrong = positions[0] == position_which_is_wrong
    else:
        is_wrong = False
    wait_time = wait_time_var.get() # inter stimulus interval between hints, in seconds (default = 8 seconds, can be changed by the experimenter in the UI)

    hint_steps = [0, wait_time*2, wait_time*4] 

    if (steps > hint_steps[-1]) or not is_wrong or not picked_up_var.get():
        if picked_up_var.get():
            # either picked up a block from the board
            if not touched_wrong_block_var.get(): # picked up right block
                hesitant_cube(robot, steps=0)
        blocks = get_unselected_blocks()
        if blocks: # there are blocks wrong colour / unplaced
            if blocks[0] < positions[0]: # these blocks come first in the sequence than the misplaced positions
                if placed_var.get() and picked_up_var.get(): # the next logical step is not to place or pick up block --> correct misplaced blocks
                    incorrect_cube(robot, blocks[0], steps=0)
                elif picked_up_var.get() and not placed_var.get(): # next logical step is to place a block
                    hesitant_position(robot, steps=0)
                elif not picked_up_var.get(): # next logical step is to pick up a block
                    hesitant_cube(robot, steps=0)
            else:
                if placed_var.get() and picked_up_var.get(): # the next logical step is not to place or pick up block --> correct misplaced positions
                    incorrect_position(robot, positions[0], steps=0)
                elif picked_up_var.get() and not placed_var.get(): # next logical step is to place a block
                    hesitant_position(robot, steps=0)
                elif not picked_up_var.get(): # next logical step is to pick up a block
                    hesitant_cube(robot, steps=0)
        elif positions:
            if placed_var.get() and picked_up_var.get(): # the next logical step is not to place or pick up block --> correct misplaced positions
                incorrect_position(robot, positions[0], steps=0)
            elif picked_up_var.get() and not placed_var.get(): # next logical step is to place a block
                hesitant_position(robot, steps=0)
            elif not picked_up_var.get(): # next logical step is to pick up a block
                hesitant_cube(robot, steps=0)
        else: # in this case the woz should click next sequence
            return
    
    current_position = seq_position[positions[0]-1]
    
    # ---- Countdown logic ----
    if is_wrong:

        next_hint = None
        for h in hint_steps:
            if steps <= h:
                next_hint = h
                break

        if next_hint is not None:
            remaining_steps = next_hint - steps
            remaining_seconds = remaining_steps // 2
            hint_countdown_var.set(f"Hint in: {remaining_seconds}…")
        else:
            hint_countdown_var.set("")
    else:
        hint_countdown_var.set("")

    if condition == "Implicit" and is_wrong:
        if steps == hint_steps[0]:
            # First hint that the cube is on the wrong position
            robot_speak_while_gaze(robot, f"PosicaoErrada{position_which_is_wrong}Bloco.wav")

                
        elif steps == hint_steps[1]:
            # Second hint that the cube is on the wrong position
            if current_position in [1, 2, 3]:
                robot_speak_while_gaze(robot, "PosicaoCorretaLinhaCima.wav")
            elif current_position in [4, 5, 6]:
                robot_speak_while_gaze(robot, "PosicaoCorretaLinhaMeio.wav")
            elif current_position in [7, 8, 9]: 
                robot_speak_while_gaze(robot, "PosicaoCorretaLinhaBaixo.wav")

        elif steps == hint_steps[2]: 
            # Third hint that the cube is on the wrong position
            if current_position in [1, 4, 7]:
                robot_speak_while_gaze(robot, "PosicaoCorretaColunaEsquerda.wav") 
            elif current_position in [2, 5, 8]: 
                robot_speak_while_gaze(robot, "PosicaoCorretaColunaMeio.wav")  
            elif current_position in [3, 6, 9]: 
                robot_speak_while_gaze(robot, "PosicaoCorretaColunaDireita.wav")  
                
    elif condition == "Explicit" and is_wrong:
        if steps == hint_steps[0]:  # after 8 seconds
            robot_speak_while_gaze(robot, f"PosicaoErradaUps{position_which_is_wrong}.wav")  
        elif steps == hint_steps[1]:
            i = random.randint(1, 3)
            robot_speak_while_gaze(robot, f"QueresPista{i}.wav") 
            if robot is not None:
                robot.set_screen(image=f"posicao_{current_position}.png")
                app.after(4000, lambda: robot.set_screen(image="normal.png")) 
            else:
                print(f"Show image position {current_position}")

        elif steps == hint_steps[2]:
            robot_speak_while_gaze(robot, f"PodesMover{current_position}.wav") 

    elif condition == "Control" and is_wrong:
        if steps == hint_steps[0]:  # after 8 seconds
        #### *--/--* placed cube incorrectly *--/--*
            robot_speak_while_gaze(robot, "AlgumBlocoErrado.wav") 
        if steps == hint_steps[1]:  # after 8 seconds
        #### *--/--* placed cube incorrectly *--/--*
            if robot is not None:
                i = random.randint(1, 3)
                robot_speak_while_gaze(robot, f"Hmmm{i} .wav") 
            else:
                playsound(f"Elmo_Speech/Control/Hmmm{i} .wav")  
        if steps == hint_steps[2]:  # after 16 seconds
            if robot is not None:
                robot.play_sound("QueresVerificar.wav") 
            else:
                playsound("Elmo_Speech/Control/QueresVerificar.wav") 
    global is_hint_active
    while is_hint_active:
        a = 1
    else:
        app.after(500, incorrect_position, robot, position_which_is_wrong, steps+1)


def incorrect_cube(robot, block_which_is_wrong, steps=0):

    print(f"------- \WRONG CUBE, steps: {steps}") # for debugging

    condition = condition_var.get()
    print(f"Experimental condition: {condition}") # for debugging
    blocks = get_unselected_blocks()
    is_wrong = blocks[0] == block_which_is_wrong
    wait_time = wait_time_var.get() # inter stimulus interval between hints, in seconds (default = 8 seconds, can be changed by the experimenter in the UI)
    current_block = seq_block[blocks[0]-1]
    current_block_var.set(current_block)

    if condition == "Implicit" and current_block in ["Verde", "Azul", "Roxo"]:
        hint_steps = [0, wait_time*2, wait_time*4, wait_time*8] 
    else:
        hint_steps = [0, wait_time*2, wait_time*4]

    if not is_wrong or steps > hint_steps[-1]:
        positions = get_unselected_positions()
        if picked_up_var.get() and not placed_var.get():
            # ou pegou num cubo do tabuleiro 
            if not touched_wrong_block_var.get():
                # ou num novo
                hesitant_position(robot, steps=0)
        elif blocks and any(positions):
            # ainda há blocos e posições errados ou unselected
            if positions[0] <= blocks[0]:
                incorrect_position(robot, positions[0], steps=0)
            else:
                incorrect_cube(robot, blocks[0], steps=0)
        elif positions:
            # ainda há posições errados ou unselected
            incorrect_position(robot, positions[0], steps=0)
        elif blocks:
            # ainda há blocos errados ou unselected
            incorrect_cube(robot, blocks[0], steps=0)
        else: #está na altura do woz carregar em "new_sequence"
            return

    if condition == "Implicit" and is_wrong:
        # next hint moments (adjust to match your logic)
        if steps == hint_steps[0]:
            set_available_colours(current_block)
            if robot is not None:
                robot_speak_while_gaze(robot, "BlocoErrado.wav") 
            else:
                playsound(f"Elmo_Speech/Implicit/BlocoErrado{block_which_is_wrong}.wav") 

        elif steps == hint_steps[1]:
            if current_block in ["Roxo", "Verde", "Azul"]:
                if robot is not None:
                    robot_speak_while_gaze(robot, "BlocoDireita.wav") 
                else:
                    playsound("Elmo_Speech/Implicit/BlocoDireita.wav") 
            elif current_block in ["Vermelho", "Amarelo"]:
                if robot is not None:
                    robot_speak_while_gaze(robot, "BlocoEsquerda.wav")
                else:
                    playsound("Elmo_Speech/Implicit/BlocoEsquerda.wav") 

        elif steps == hint_steps[2] or hint_steps[3]:
            colour= random.choice(colours_var)
            if robot is not None:
                robot_speak_while_gaze(robot, f"BlocoNo{colour}.wav")
            else:
                playsound(f"Elmo_Speech/Implicit/BlocoNo{colour}.wav") 
            colours_var.remove(colour)         
                
    elif condition == "Explicit" and is_wrong:
        if steps == hint_steps[0]:
            if robot is not None:
                robot_speak_while_gaze(robot, f"BlocoErradoUps{block_which_is_wrong}.wav")
            else:
                playsound(f"Elmo_Speech/BlocoErradoUps{block_which_is_wrong}.wav") 
        # the person still does not remember the colour of the block --> a bit more nudging
        if steps == hint_steps[1]:
            if robot is not None:
                i = random.randint(1, 3)
                robot.set_screen(image=f"olhos_{current_block}.png") # eyes turn the colour of the current block as a hint
                robot_speak_while_gaze(robot, f"QueresPista{i}")
                app.after(4000, lambda: robot.set_screen(image="normal.png") )
            else: 
                print(f"Show {current_block} eyes")
                set_status(f"Show {current_block} eyes") 
        if steps == hint_steps[2]:
            if robot is not None:
                robot_speak_while_gaze(robot, f"Bloco{current_block}.wav")
            else:
                playsound(f"Elmo_Speech/Explicit/Bloco{current_block}.wav") 

    elif condition == "Control" and is_wrong:
        if steps == hint_steps[0]:
            if robot is not None:
                robot_speak_while_gaze(robot, "AlgumBlocoErrado.wav")
            else:
                playsound("AlgumBlocoErrado")
        if steps == hint_steps[1]:
            i = random.randint(1, 3)
            if robot is not None:
                robot_speak_while_gaze(robot, f"Hmmm{i}.wav")
            else:
                playsound("Elmo_Speech/Control/Hmmm{i}.wav")  
            # the person still does not remember the colour of the block --> a bit more nudging
        elif steps == hint_steps[2]:
            if robot is not None:
                robot.play_sound("QueresVerificarCor.wav")  
            else:
                playsound("Elmo_Speech/Control/QueresVerificarCor.wav")
    if not is_hint_active:
        app.after(500, incorrect_cube, robot, block_which_is_wrong, steps+1)
    else:
        app.after(500, incorrect_cube, robot, block_which_is_wrong, steps)

def hesitant_position(robot, steps=0):
    """
    This function is called whenever the person has not yet placed a cube they have picked up and the next logical action is to place a cube
    Input variables:
        robot: robot API initialized or none for debug mode
    """

    print(f"------- \HESITANT POSIITON, steps: {steps}") # for debugging

    is_hesitant = picked_up_var.get() and not placed_var.get()  # keep running until placed_var is toggled
    print(f"Is hesitant: {is_hesitant}") # for debugging
    condition = condition_var.get() # experimental condition
    print(f"Experimental condition: {condition}") # for debugging

    positions = get_unselected_positions()
    current_position = seq_position[positions[0]-1]
    print(f"Current position: {current_position}") # for debugging

    wait_time = wait_time_var.get() # inter stimulus interval between hints, in seconds (default = 8 seconds, can be changed by the experimenter in the UI)

    # next hint moments (adjust to match your logic)
    hint_steps = [wait_time*2, wait_time*4]

    if steps > hint_steps[-1]+2*wait_time:  
        return
    
    if not is_hesitant:
        if not picked_up_var.get(): # if person placed and next logical action is to pick up cube
            hesitant_cube(robot, steps=1)
        else: # cubes are placed --> verify if correct
            positions = get_unselected_positions()
            if positions: # if there are any incorrect positions
                incorrect_position(robot, positions[0], steps=1)
            else: 
                blocks = get_unselected_blocks()
                if blocks: # if there are any incorrect blocks (colours)
                    incorrect_cube(robot, steps=1)
                else: # everything is correct --> woz should press new sequence button
                    return
    
    set_status("Waiting for cube drop-off") 

    # ---- Countdown logic ----
    if is_hesitant:

        next_hint = None
        for h in hint_steps:
            if steps <= h:
                next_hint = h
                break

        if next_hint is not None:
            remaining_steps = next_hint - steps
            remaining_seconds = remaining_steps // 2
            hint_countdown_var.set(f"Hint in: {remaining_seconds}…")
        else:
            hint_countdown_var.set("")
    else:
        hint_countdown_var.set("")

    if condition == "Implicit" and is_hesitant:
        if steps == hint_steps[0]:  
            if current_position in [1, 4, 7]: # left column 
                if robot is not None:
                    cmd_queue.put("stop")  # robot stop looking around
                    look_to_the_right(robot) # robot look at participant
                    robot.play_sound("PosicaoCorretaColunaEsquerda.wav") # robot say hint
                    # after delay: resume 
                    app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
                else: # debug mode
                    playsound("Elmo_Speech/Implicit/PosicaoCorretaColunaEsquerda.wav")  
            elif current_position in [2, 5, 8]: # middle  
                if robot is not None:
                    cmd_queue.put("stop")  # robot stop looking around
                    look_to_the_middle(robot) # robot look at participant
                    robot.play_sound("PosicaoCorretaColunaMeio.wav") # robot say hint
                    # after delay: resume 
                    app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
                else: # debug mode
                    playsound("Elmo_Speech/Implicit/PosicaoCorretaColunaMeio.wav") 
            elif current_position in [3, 6, 9]: # right column 
                if robot is not None:
                    cmd_queue.put("stop")  # robot stop looking around
                    look_to_the_left(robot) # robot look at participant
                    robot.play_sound("PosicaoCorretaColunaDireita.wav") # robot say hint
                    # after delay: resume 
                    app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
                else: # debug mode
                    playsound("Elmo_Speech/Implicit/PosicaoCorretaColunaDireita.wav") 
        elif steps == hint_steps[1]: 
            if current_position in [1, 2, 3]: # top row

                if robot is not None:
                    cmd_queue.put("stop")  # robot stop looking around
                    look_to_the_middle(robot) # robot look at participant
                    robot.play_sound("PosicaoCorretaLinhaCima.wav") # robot say hint
                    # after delay: resume 
                    app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
                else: # debug mode
                    playsound("Elmo_Speech/Implicit/PosicaoCorretaLinhaCima.wav") 

            elif current_position in [4, 5, 6]: # middle row
                if robot is not None:
                    cmd_queue.put("stop")  # robot stop looking around
                    look_to_the_middle(robot) # robot look at participant
                    robot.play_sound("PosicaoCorretaLinhaMeio.wav") # robot say hint
                    # after delay: resume 
                    app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
                else: # debug mode
                    playsound("Elmo_Speech/PosicaoCorretaLinhaMeio.wav") 

            elif current_position in [7, 8, 9]: # bottom row
                if robot is not None:
                    cmd_queue.put("stop")  # robot stop looking around
                    look_to_the_middle(robot) # robot look at participant
                    robot.play_sound("PosicaoCorretaLinhaBaixo.wav") # robot say hint
                    # after delay: resume 
                    app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
                else: # debug
                    playsound("Elmo_Speech/Implicit/PosicaoCorretaLinhaBaixo.wav")    
    elif condition == "Explicit" and is_hesitant:
        if steps == hint_steps[0]:  # after 8 seconds
            if robot is not None:
                robot.set_screen(image=f"posicao_{current_position}.png") # eyes turn the colour of the current block as a hint
            else:
                print(f"Setting image to {current_position}")

            i = random.randint(1, 3) 
            robot_speak_while_gaze(robot, f"QueresPista{i}")

            if robot is not None:
                app.after(2000, lambda: robot.set_screen(image="normal.png")) # start looking around, eyes normal again
        elif steps == hint_steps[1]:  # after 8 seconds
            if robot is not None:
                cmd_queue.put("stop")  # stop looking around
                if current_position in [1, 4, 7]:
                    look_to_the_right(robot)
                elif current_position in [2, 5, 8]:
                    look_to_the_middle(robot)
                else:
                    look_to_the_left(robot)
                i = random.randint(1, 3) 
                robot.play_sound(f"PosicaoCorreta{current_position}") # robot gives hint
                app.after(2000, lambda: cmd_queue.put("start")) # start looking around
            else: # debug mode
                playsound(f"Elmo_Speech/Explicit/PosicaoCorreta{current_position}.wav")
    elif condition == "Control" and is_hesitant:
        if steps == hint_steps[0]: 
            i = random.randint(1, 3)
            robot_speak_while_gaze(robot, f"Palpite{i}.wav")
            
        elif steps == hint_steps[1]: 
            i = random.randint(1, 3)
            robot_speak_while_gaze(robot, f"TempoPrecisares{i}.wav")
    
    # --------------------- Schedule next check ---------------------
    if not is_hint_active:
        app.after(500, hesitant_position, robot, steps+1)
    else:
        app.after(500, hesitant_position, robot, steps)

def hesitant_cube(robot, steps=0): 
    """
    This function is called whenever the person has not yet picked up a cube and the next logical action is to pick up a cube
    Input variables:
        robot: robot API initialized or none for debug mode
    """
    print(f"------- \HESITANT CUBE, steps: {steps}") # for debugging

    condition = condition_var.get()
    print(f"Experimental condition: {condition}") # for debugging

    is_hesitant = not picked_up_var.get() 
    print(f"Is hesitant: {is_hesitant}") # for debugging
    
    blocks = get_unselected_blocks()
    current_block = seq_block[blocks[0]-1]
    current_block_var.set(current_block)
    print(f"Current block: {current_block}") # for debugging

    wait_time = wait_time_var.get() # inter stimulus interval between hints, in seconds (default = 8 seconds, can be changed by the experimenter in the UI)

    # next hint moments (adjust to match your logic)
    if current_block in ["Verde", "Azul", "Roxo"] and condition == "Implicit":
        hint_steps = [wait_time*2, wait_time*4, wait_time*8] 
    elif (current_block in ["Amarelo", "Vermelho"] and condition == "Implicit") or (condition == "Explicit") or (condition == "Control"):
        hint_steps = [wait_time*2, wait_time*4]

    # define max steps depending on block
    n_steps_list = len(hint_steps)

    if steps > hint_steps[-1]:  # 16 steps = 8 seconds * 2s per check
        return
    
    if not is_hesitant: # cube has been picked up
        if placed_var.get(): # cube has been placed
            positions = get_unselected_positions()
            if positions: # some of the positions in the sequence are wrong
                incorrect_position(robot, steps=0)
            else: 
                blocks = get_unselected_blocks()
                if blocks: # some of the blocks in the sequence are of the wrong colour
                    incorrect_cube(robot, steps=0)
                else: # no positions or blocks are wrong --> researcher should click next sequence
                    return

        else:
            hesitant_position(robot, steps=0)
    

    set_status("Waiting for cube pick-up")

    # ---- Countdown logic ----
    if is_hesitant:

        next_hint = None
        for h in hint_steps:
            if steps <= h:
                next_hint = h
                break

        if next_hint is not None:
            remaining_steps = next_hint - steps
            remaining_seconds = remaining_steps // 2
            hint_countdown_var.set(f"Hint in: {remaining_seconds}…")
        else:
            hint_countdown_var.set("")
    else:
        hint_countdown_var.set("")

    if condition == "Implicit" and is_hesitant:

        # Hint 1: Right/Left 
        if steps == hint_steps[0]:
            set_available_colours(current_block)
            print(f"Current step: {steps}, Current block: {current_block}") # for debugging
            if current_block in ["Verde", "Azul", "Roxo"]:

                if robot is not None:

                    cmd_queue.put("stop")  # robot stop looking around
                    look_to_the_left(robot) # robot look to the right block
                    robot.play_sound("BlocoDireita.wav") # robot give hint

                    # resume after delay (adjust duration to your audio length)
                    app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
                else: # debug mode
                    playsound("Elmo_Speech/Implicit/BlocoDireita.wav") 
            elif current_block in ["Amarelo", "Vermelho"]:
                if robot is not None:
                    cmd_queue.put("stop")  # robot stop looking around
                    look_to_the_right(robot) # robot look to the right block
                    robot.play_sound("BlocoEsquerda.wav") # robot give hint

                    # resume after delay (adjust duration to your audio length)
                    app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
                else: # debug mode
                    playsound("Elmo_Speech/Implicit/BlocoEsquerda.wav") 
            
        # Hint 2: Exclude wrong block
        elif (steps == hint_steps[1] or (n_steps_list>2 and steps == hint_steps[2])) and any(colours_var):
            print(f"Current step: {steps}, Current block: {current_block}") # for debugging
            print(colours_var) # for debugging

            if current_block in colours_var:
                colours_var.remove(current_block)
            
            colour = random.choice(colours_var)
            print(f"Colour given as a hint: {colour}") # for debugging
            colours_var.remove(colour)

            if robot:
                robot_speak_while_gaze(robot, f"BlocoNo{colour}.wav")
                
            else:
                playsound(f"Elmo_Speech/Implicit/BlocoNo{colour}.wav") 
    elif condition == "Explicit" and is_hesitant:

        if steps == hint_steps[0]:
            if robot is not None:
                robot.set_screen(image=f"olhos_{current_block}.png") # eyes turn the colour of the current block as a hint
                robot_speak_while_gaze(robot, f"QueresPista{i}")
                robot.set_screen(image=f"olhos_{current_block}.png") # eyes turn the colour of the current block as a hint
                # resume after delay (adjust duration to your audio length)
                app.after(3000, lambda: (
                    robot.set_screen(image="normal.png")
                )) # start looking around, eyes normal again

            else: 
                print(f"Show {current_block} eyes")
                set_status(f"Show {current_block} eyes")
                i = random.randint(1, 3) 
                playsound(f"QueresPista{i}")

        elif steps == hint_steps[1]:  
            if robot is not None:
                robot_speak_while_gaze(robot, f"Bloco{current_block}.wav")
            else:
                playsound(f"Elmo_Speech/Explicit/Bloco{current_block}.wav") 
    elif condition == "Control" and is_hesitant:
        if steps == hint_steps[0]:  
            if robot is not None:
                cmd_queue.put("stop")  # robot stop looking around
                look_at_participant(robot) # robot look at participant
                i = random.randint(1, 3)
                robot.play_sound(f"PensaCor{i}.wav") # robot speaks
                # after delay: resume 
                app.after(2000, lambda: cmd_queue.put("start")) # robot start looking around
            else:
                playsound("Elmo_Speech/Control/PensaCor.wav") 

        elif steps ==  hint_steps[1]:
            if robot is not None:
                i = random.randint(1, 3)
                robot_speak_while_gaze(robot, f"TempoPrecisares{i}.wav")
            else:
                playsound("Elmo_Speech/Control/TempoPrecisares.wav")   

    # --------------------- Schedule next check ---------------------
    if not is_hint_active:
        app.after(500, hesitant_cube, robot, steps + 1)
    else: 
        app.after(500, hesitant_cube, robot, steps)

    


def say_bye(robot):
    if robot is not None:
        try:
            robot.play_sound("Goodbye.wav")
        except Exception as e:
            print(f"[Robot error] {e}")
            playsound("Elmo_Speech/Goodbye.wav")
    else:
        playsound("Elmo_Speech/Goodbye.wav")

def sequence_generator(n):
    """
    Randomly generates a sequence of n length of colouVermelho cubes on the board.
    """

    colours = ["Azul", "Vermelho", "Amarelo", "Roxo", "Verde"]
    positions = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    global seq_block, seq_position

    if n<=5:
        seq_block = random.sample(colours, k=n)
    else:
        seq_block = random.choices(colours, k=n)
    
    seq_position = random.sample(positions, k=n)

    global current_index
    current_index = 0
    global trial_index
    trial_index += 1
    trial_var.set(f"Trial {trial_index}") # update trial number = number of sequences the person did so far + 1


    return seq_block, seq_position

def say_sequence(robot, seq_block, seq_position, n):
    isi = isi_var.get()  # seconds


    def play_go_signal():
        if robot:

            i = random.randint(1, 3)
            ## with distraction
            #robot.play_sound("distractor.wav")
            #app.after(4000, lambda i=i: robot.play_sound(f"JaPodes{i}.wav"))

            ## without distraction
            robot.play_sound(f"JaPodes{i}.wav")

            robot.set_screen(image="normal.png")
            robot.set_pan_torque(True)
            robot.set_tilt_torque(True)
            cmd_queue.put("start")
            
            app.after(4000, lambda: hesitant_cube(robot, steps=0))  # start checking for hesitation after the go signal
        else:
            playsound("Elmo_Speech/JaPodes.wav")

    def speak_item(i):
        if i >= n:
            threading.Timer(0.5, play_go_signal).start()
            return

        if robot:
            
            robot.set_screen(
                text=f"{i+1}. O bloco {seq_block[i].lower()} vai para a posição {seq_position[i]}."
            )
            robot.play_sound(f"Bloco{seq_block[i]}Posicao{seq_position[i]}.wav")
        else:
            playsound(f"Elmo_Speech/Sequencias/Bloco{seq_block[i]}Posicao{seq_position[i]}.wav")

        # schedule next item after audio + ISI
        threading.Timer(3 + isi, lambda: speak_item(i + 1)).start()

    # ---- preparation phase ----
    if robot:
        cmd_queue.put("stop")
        look_at_participant(robot)
        print("looking at participant")

        threading.Timer(1, lambda: speak_item(0)).start()
    else:
        speak_item(0)

# ---------- Button functions ----------

def get_unselected_positions():
    return [
        i + 1
        for i, var in enumerate(position_check_vars)
        if not var.get()
    ]

def get_unselected_blocks():
    return [i+1 for i, var in enumerate(block_check_vars) if not var.get()]

# check if the person picked up the cube
def on_picked_up_toggle():

    # the person picked up the cube (picked_up toggle is true)  
    if picked_up_var.get():
        print("Picked up cube → stop hesitant_cube, start hesitant_position")
        hesitant_position(robot, steps=0)
        set_status("Cube picked up → waiting for placement")
    #else:
    #    hesitant_cube(robot, steps=0) # picked up was toggled off → means that next logical action is to pick up a cube

def on_placed_toggle():
    if placed_var.get():  # participant placed cube
        print("Placed cube → stop hesitant_position, check cube")
        # hesitant_position will automatically stop since is_hesitant is now False
        incorrect_position(robot, steps=0)
        set_status("Cube placed → checking correctness")

def on_wrong_block_toggle():
    print("Touched wrong block --> saying that")
    set_status("Touched wrong block --> saying that")
    print(touched_wrong_block_var.get())
    if touched_wrong_block_var.get():
        if robot:
            condition = condition_var.get()
            print(condition)

            print("Stop looking")
            cmd_queue.put("stop")

            # Step 1: look at participant after a short delay
            def step_look():
                print("Looking at participant")
                look_at_participant(robot)

            # Step 2: play sound depending on condition
            def step_sound():
                if condition == "Implicit":
                    print("MexesteErrado")
                    robot.play_sound("MexesteErrado.wav")

                elif condition == "Explicit":
                    robot.play_sound("NaoEsseBloco.wav")

                elif condition == "Control":
                    i = random.randint(1, 3)
                    robot.play_sound(f"Hmmm{i}.wav")           

            app.after(300, step_look)  # small delay to ensure "stop" is processed

            app.after(2000, step_sound)  # wait before speaking

            # Step 3: resume looking
            def step_resume():
                print("Start looking again")
                cmd_queue.put("start")

            app.after(10000, step_resume)
        else:
            if condition == "Implicit":
                playsound("MexesteErrado.wav")
            elif condition == "Explicit":
                playsound("NaoEsseBloco.wav")
            elif condition == "Control":
                i = random.randint(1, 3)
                playsound(f"Hmmm{i}.wav")

def say_clean_board(robot):
    n = random.choice([1, 2, 3]) # WHICH VARIATION OF THE "CLEAN BOARD" SENTENCE WE'RE GOING TO SAY
    if robot is not None:
        robot.play_sound(f"LimpaTabuleiro{n}.wav") 
    else:
        playsound(f"Elmo_Speech/LimpaTabuleiro{n}.wav")
    app.after(9000, lambda: btn_new_sequence())


def update_intro_text():
    if intro_var.get():
        intro_text_var.set("Yes")
    else:
        intro_text_var.set("No")

def set_available_colours(current_block):
    global colours_var

    if current_block in ["Verde", "Azul", "Roxo"]:
        base = ["Verde", "Azul", "Roxo"]
    else:
        base = ["Vermelho", "Amarelo"]

    colours_var.clear()
    colours_var.extend(base)
    print(colours_var) # for debugging

def update_sequence_checkboxes():
    # limpar antigos
    for widget in blocks_frame.winfo_children():
        widget.destroy()
    for widget in positions_frame.winfo_children():
        widget.destroy()

    n = int(n_var.get())

    global block_check_vars, position_check_vars
    block_check_vars = []
    position_check_vars = []

    for i in range(n):
        # bloco
        b_var = tk.BooleanVar(value=False)
        block_check_vars.append(b_var)

        tk.Checkbutton(
            blocks_frame,
            text=f"B{i+1}",
            variable=b_var,
            bg=PANEL,
            fg=PRIMARY,
            selectcolor="white",
            font=("Arial", 12),
            bd=0,
            highlightthickness=0
        ).pack(side="left", padx=5)

        # posição
        p_var = tk.BooleanVar(value=False)
        position_check_vars.append(p_var)

        tk.Checkbutton(
            positions_frame,
            text=f"P{i+1}",
            variable=p_var,
            bg=PANEL,
            fg=PRIMARY,
            selectcolor="white",
            font=("Arial", 12),
            bd=0,
            highlightthickness=0
        ).pack(side="left", padx=5)



if __name__ == '__main__':
    # We will pass the robot's IP in ter terminal as an argument
    # Note that you need to connect to the app first to discover the IP of the robot
    #robot_ip = sys.argv[1]
    robot_ip = "192.168.0.107"

    debug = False

    if debug:
        robot = None
    else:
        # Initiate the API to communicate with RES request with the robots
        robot = ElmoV2API.ElmoV2API(robot_ip, debug=False)

        robot.enable_behavior("look_around", False)
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)

        # start new idle behavior in a separate thread
        cmd_queue = queue.Queue()

        behavior_thread = threading.Thread(
            target=random_look_loop,
            args=(robot, cmd_queue),
            daemon=True
        )
        behavior_thread.start()

        print("Starting robot gaze behavior")
        cmd_queue.put("start")
        

    # ---------- BUTTON CALLBACKS ----------

    def btn_intro():
        
        say_intro(robot)
        intro_var.set(True)
        update_intro_text()
        set_status("Intro was said → waiting for button press to present first sequence ")

    def btn_new_sequence():

        if clean_board_var.get():

            set_status("Presenting sequence")
            new_sequence(robot) # speech: "let's go to the next sequence?"
            current_position_var.set("None")
            current_block_var.set("None")
            if intro_var.get(): # if right after intro (intro_var = true), say something difference: "let's go to the 1st sequence?"
                intro_var.set(False)
            n = int(n_var.get()) # get new sequence length
            seq_block, seq_position  = sequence_generator(n) # generate sequence
            update_sequence_display(seq_block, seq_position) # update sequence on UI
            update_sequence_checkboxes() # update sequence checkboxes on UI
            app.after(2000, lambda: say_sequence(robot, seq_block, seq_position, n)) # make robot say sequence
        else:
            say_clean_board(robot)
        

    def update_sequence_display(seq_block, seq_position):
        lines = []
        for i, (b, p) in enumerate(zip(seq_block, seq_position)):
            lines.append(f"{i+1}. {b} → posição {p}")
        
        sequence_display_var.set("\n".join(lines))

        current_block_var.set(seq_block[current_index])
        current_position_var.set(str(seq_position[current_index]))

    def btn_bye():
        say_bye(robot)
        app.after(2000, app.destroy)  # waits 2 seconds, then closes

    def set_status(text):
        status_var.set(text)

    def update_condition_style(*args):
        c = condition_var.get()

        if c == "Control":
            color = "#e0e0e0"
        elif c == "Explicit":
            color = "#cfe8ff"
        elif c == "Implicit":
            color = "#ffd6f5"

        # Condition panel
        frame_condition.config(bg=color)
        for child in frame_condition.winfo_children():
            child.config(bg=color)

        # Status panel
        status_frame.config(bg=color)
        for child in status_frame.winfo_children():
            child.config(bg=color)

    # function to apply volume change
    def apply_volume():
        v = int(volume_var.get())
        if robot is not None:
            try:
                robot.set_volume(v)
                set_status(f"Volume set to {v}")
            except Exception as e:
                print(f"[Robot error] {e}")
        else:
            set_status(f"(Debug) Volume would be {v}")

    def on_volume_change(value):
        apply_volume()

    
    # ------ aux var ----
    global colours_var
    colours_var = []

    global trial_index 
    trial_index = 0 # initialize trial index at the beginning of the experiment

    # ---------- UI ----------

    app = tk.Tk()
    app.title("Robot Control Panel")
    app.state("zoomed")

    # ---------- COLORS ----------
    SECONDARY = "#FFC7FF"
    PRIMARY = "#2b2b2b"
    BG = "#E0EEF3"
    PANEL = "#FFC7FF"
    TEXT = "#2b2b2b"
    CONTROL_BG = "white"
    CONTROL_ACTIVE = "#f4f4f4"
    BORDER = "#d0d0d0"
    TITLE_FONT = ("Arial", 15, "bold")

    BG = "#f4f7fa"
    PANEL = "#ffe6ff"
    SECONDARY = "#ffb3ff"
    PRIMARY = "#2b2b2b"

    STATUS_BG = "#ffd9ff"
    STATUS_BORDER = "#e3a8e3"

    app.tk_setPalette(background=BG)
    app.option_add("*Button.Background", SECONDARY)
    app.option_add("*Button.Foreground", PRIMARY)

    # ---------- MAIN CONTAINER ----------
    main = tk.Frame(app, bg=BG)
    main.pack(expand=True)

    content = tk.Frame(main, bg=BG)
    content.pack(pady=20)

    # ---------- TITLE ----------
    tk.Label(
        content,
        text="Memory Game: Robot Control Panel",
        font=("Courier", 20, "bold"),
        bg=BG,
        fg=PRIMARY
    ).pack(pady=(0, 15))

    #----------- STATUS BAR ----------

    hint_countdown_var = tk.StringVar()

    status_var = tk.StringVar(value="Idle")

    status_frame = tk.Frame(content, bg=STATUS_BG, bd=1, relief="solid")
    status_frame.pack(fill="x", pady=(0, 15), padx=5)

    tk.Label(
        status_frame,
        text="Robot State:",
        font=("Arial", 13),
        bg=STATUS_BG,
        fg=PRIMARY
    ).pack(side="left", padx=(10,5), pady=6)

    tk.Label(
        status_frame,
        textvariable=status_var,
        font=("Courier", 13, "bold"),
        bg=STATUS_BG,
        fg=PRIMARY
    ).pack(side="left", padx=5)

    hint_label = tk.Label(
        status_frame,
        textvariable=hint_countdown_var,
        font=("Arial", 14, "bold"),
        fg="#ff66cc",
        bg=STATUS_BG
    )
    hint_label.pack(side="right", padx=10)

    # ---------- HELPER ----------
    def panel(title, parent):
        outer = tk.Frame(parent, bg=PANEL, bd=0)#, height=120)
        #outer.grid_propagate(False)

        header = tk.Label(
            outer,
            text=title,
            font=("Arial", 14, "bold"),
            bg="#ffb3ff",   # darker pink header
            fg=PRIMARY,
            padx=10,
            pady=2
        )
        header.pack(fill="x")

        body = tk.Frame(outer, bg=PANEL)
        body.pack(fill="both", expand=True, padx=15, pady=10)

        return outer

    def centered_dropdown(parent, variable, options, width=6):
        menu = tk.OptionMenu(parent, variable, *options)
        
        menu.config(
            width=width,
            bg="white",
            fg=PRIMARY,
            font=("Courier New", 13, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=0,
            activebackground="white",
            activeforeground=PRIMARY
        )
        
        menu["menu"].config(
            bg="white",
            fg=PRIMARY,
            font=("Arial", 13)
        )
        
        return menu
    
    def ui_button(parent, text, command, width=18):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 13, "bold"),
            bg=SECONDARY,
            fg=PRIMARY,
            activebackground="#ffb3ff",
            activeforeground=PRIMARY,
            highlightthickness=0,
            bd=0,
            padx=14,
            pady=8,
            width=width,
            relief="flat",
        )
    
    def on_enter(e):
        e.widget.config(bg="#ffb3ff")

    def on_leave(e):
        e.widget.config(bg=SECONDARY)


    # ---------- CONDITION + VOLUME ROW ----------
    row_top_controls = tk.Frame(content, bg=BG)
    row_top_controls.pack(fill="x", pady=5)

    row_top_controls.columnconfigure((0,1,2,3), weight=1)

    # ---------- CONDITION ----------
    condition_var = tk.StringVar(value="Control")
    CONDITION_OPTIONS = ["Control", "Explicit", "Implicit"]

    frame_condition = panel("Condition", row_top_controls)
    frame_condition.grid(row=0, column=0, sticky="new", padx=5)

    condition_menu = centered_dropdown(frame_condition, condition_var, CONDITION_OPTIONS, width=20)
    condition_menu.pack(pady=5)

    condition_var.trace_add("write", update_condition_style)
    update_condition_style()

    # ---------- VOLUME ----------
    volume_var = tk.IntVar(value=25)

    frame_volume = panel("Volume", row_top_controls)
    frame_volume.grid(row=0, column=1, sticky="new", padx=5)

    volume_row = tk.Frame(frame_volume, bg=PANEL)
    volume_row.pack(pady=15)

    tk.Label(
        volume_row,
        text="Robot Volume:",
        font=("Arial", 13),
        bg=PANEL,
        fg=PRIMARY
    ).pack(side="left", padx=(0,10))

    volume_slider = tk.Scale(
        volume_row,
        from_=0,
        to=100,
        orient="horizontal",
        variable=volume_var,
        bg=PANEL,
        fg=PRIMARY,
        highlightthickness=0,
        length=220,
        command=on_volume_change
    )
    volume_slider.pack(side="left", padx=10)

    volume_button = ui_button(
        volume_row,
        text="Apply",
        command=apply_volume,
        width=10
    )
    volume_button.pack(side="left", padx=10)

    # ---------- INTRO + GOODBYE SIDE BY SIDE ----------
    row_intro_bye = tk.Frame(row_top_controls, bg=BG)
    row_intro_bye.grid(row=1, column=0, columnspan=4, sticky="new", pady=15, padx=15)

    # ----- INTRO PANEL -----
    intro_var = tk.BooleanVar(value=False)
    intro_text_var = tk.StringVar(value="No")

    frame_intro = panel("Intro", row_top_controls)
    frame_intro.grid(row=0, column=2, sticky="new", padx=5)

    intro_row = tk.Frame(frame_intro, bg=PANEL)
    intro_row.pack(pady=15)

    intro_button = ui_button(
        intro_row,
        text="Say Intro",
        command=btn_intro,
        width=16,
    )
    intro_button.pack(side="left", padx=15, pady=5)

    tk.Label(
        intro_row,
        text="Intro was said?",
        font=("Arial", 13),
        bg=PANEL,
        fg=PRIMARY,
        highlightbackground=PANEL,
        relief="flat"
    ).pack(side="left", padx=(15,5))

    tk.Label(
        intro_row,
        textvariable=intro_text_var,
        font=("Courier New", 13, "bold"),
        bg=PANEL,
        fg=PRIMARY,
        highlightbackground=PANEL,
        relief="flat"
    ).pack(side="left")

    # ----- GOODBYE PANEL -----
    frame_bye = panel("Finish", row_top_controls)
    frame_bye.grid(row=0, column=3, sticky="new", padx=5)

    bye_button = ui_button(
        frame_bye,
        text="Say Goodbye",
        command=btn_bye
    )
    bye_button.pack(pady=5)

    

    # ---------- NEW SEQUENCE PANEL ----------
    isi_var = tk.IntVar(value=2)
    n_var = tk.IntVar(value=3)
    wait_time_var = tk.IntVar(value=4)

    POSITION_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    WAIT_OPTIONS = [2, 3, 4, 8, 16]

    # ---------- NEW SEQUENCE PANEL ----------
    frame_new_sequence = panel("New Sequence", content)
    frame_new_sequence.pack(pady=5, fill="x")

    # Container to center the row
    row_ns_container = tk.Frame(frame_new_sequence, bg=PANEL)
    row_ns_container.pack(fill="x")

    # Inner row for widgets
    row_ns = tk.Frame(row_ns_container, bg=PANEL)
    row_ns.pack(pady=5)  # no 'side', so the whole row is centered

    # ---------- ISI ----------
    tk.Label(row_ns, text="ISI (s):", font=("Arial", 13), bg=PANEL, fg=PRIMARY).pack(side="left", padx=(0,5))
    isi_menu = centered_dropdown(row_ns, isi_var, [1,2,5])
    isi_menu.pack(side="left", padx=(20, 5))

    # ---------- Sequence Length ----------
    tk.Label(row_ns, text="Sequence Length:", font=("Arial", 13), bg=PANEL, fg=PRIMARY).pack(side="left", padx=(20,5))
    length_menu = centered_dropdown(row_ns, n_var, POSITION_OPTIONS)
    length_menu.pack(side="left", padx=5)

    # ---------- Wait Time ----------
    tk.Label(row_ns, text="Wait Time (s):", font=("Arial", 13), bg=PANEL, fg=PRIMARY).pack(side="left", padx=(20,5))
    wait_menu = centered_dropdown(row_ns, wait_time_var, WAIT_OPTIONS)
    wait_menu.pack(side="left", padx=(20, 5))

    # ---------- New Sequence Button ----------
    ns_button = ui_button(
        row_ns,
        text="New Sequence",
        width=16,
        command=btn_new_sequence
    )
    ns_button.pack(side="left", padx=(20, 20))

    # ---------- board clean ----------
    clean_board_var = tk.BooleanVar(value=True)
    
    tk.Checkbutton(
        row_ns,
        text="Board Clean?",
        variable=clean_board_var,
        bg=PANEL,                 # panel background
        fg=PRIMARY,
        selectcolor="white",      # checkbox square color (important!)
        activebackground=PANEL,
        font=("Arial", 13),
        bd=0,
        highlightthickness=0
    ).pack(side="left", padx=(20, 5))

    # ---------- touched wrong block on board ----------
    touched_wrong_block_var = tk.BooleanVar(value=False)
    
    tk.Checkbutton(
        row_ns,
        text="Touched wrong block?",
        variable=touched_wrong_block_var,
        bg=PANEL,                 # panel background
        fg=PRIMARY,
        selectcolor="white",      # checkbox square color (important!)
        activebackground=PANEL,
        font=("Arial", 13),
        bd=0,
        highlightthickness=0,
        command=on_wrong_block_toggle
    ).pack(side="left", padx=(20, 5))

    # ---------- SINGLE ROW FOR ALL FOUR PANELS ----------
    row_all_panels = tk.Frame(content, bg=BG)
    row_all_panels.pack(fill="x", pady=10)

    row_all_panels.columnconfigure((0,1,2,3,4), weight=1)

    # ----- Current Trial panel -----
    trial_var = tk.StringVar(value="No trial yet")
    frame_trial = panel("Current Trial", row_all_panels)
    frame_trial.grid(row=0, column=0, sticky="new", padx=5)

    tk.Label(
        frame_trial,
        textvariable=trial_var,
        font=("Courier New", 13, "bold"),
        justify="center",
        bg="white",
        relief="solid",
        bd=1,
        padx=10,
        pady=8,
        fg=TEXT
    ).pack(pady=5, padx=5, fill="x")

    # ----- Current Sequence panel -----
    sequence_display_var = tk.StringVar(value="No sequence yet")
    frame_sequence = panel("Current Sequence", row_all_panels)
    frame_sequence.grid(row=0, column=1, sticky="new", padx=5)

    tk.Label(
        frame_sequence,
        textvariable=sequence_display_var,
        font=("Courier New", 13, "bold"),
        justify="center",
        bg="white",
        relief="solid",
        bd=1,
        padx=10,
        pady=8,
        fg=TEXT
    ).pack(pady=5, padx=5, fill="x")


    # ----- Target Block panel -----
    current_block_var = tk.StringVar(value="None")
    frame_target_block = panel("Target Block", row_all_panels)
    frame_target_block.grid(row=0, column=2, sticky="new", padx=5)

    tk.Label(
        frame_target_block,
        textvariable=current_block_var,
        font=("Courier New", 13, "bold"),
        justify="center",
        bg="white",
        relief="solid",
        bd=1,
        padx=10,
        pady=8,
        fg=TEXT
    ).pack(pady=5, padx=5)
    frame_target_block.config(highlightbackground="#ff66cc", highlightthickness=2)


    # ----- Target Position panel -----
    current_position_var = tk.StringVar(value="None")
    frame_target_position = panel("Target Position", row_all_panels)
    frame_target_position.grid(row=0, column=3, sticky="new", padx=5)

    tk.Label(
        frame_target_position,
        textvariable=current_position_var,
        font=("Courier New", 13, "bold"),
        justify="center",
        bg="white",
        relief="solid",
        bd=1,
        padx=10,
        pady=8,
        fg=TEXT
    ).pack(pady=5, padx=5)
    frame_target_position.config(highlightbackground="#ff66cc", highlightthickness=2)

    # ---------- BOARD STATE ----------
    picked_up_var = tk.BooleanVar(value=False)
    placed_var = tk.BooleanVar(value=False)
    correct_block_var = tk.BooleanVar(value=True)
    correct_block_position_var = tk.BooleanVar(value=True)
    



    #row2 = tk.Frame(content, bg=PANEL)
    #row2.pack(fill="x", pady=5)

    #frame_state = panel("Board State", row2)
    #frame_state.pack(fill="x", padx=10)

    #state_row = tk.Frame(frame_state, bg=PANEL)
    #state_row.pack(pady=5)

    

    #tk.Checkbutton(
    #    state_row,
    #    text="Correct Block?",
    #    variable=correct_block_var,
    #    bg=PANEL,                 # panel background
    #    fg=PRIMARY,
    #    selectcolor="white",      # checkbox square color (important!)
    #    activebackground=PANEL,
    #    font=("Arial", 13),
    #    bd=0,
    #    highlightthickness=0,
    #    command=on_correct_block_toggle
    #).pack(side="left", padx=15)

    #tk.Checkbutton(
    #    state_row,
    #    text="Correct Block Position?",
    #    variable=correct_block_position_var,
    #    bg=PANEL,                 # panel background
    #    fg=PRIMARY,
    #    selectcolor="white",      # checkbox square color (important!)
    #    activebackground=PANEL,
    #    font=("Arial", 13),
    #    bd=0,
    #    highlightthickness=0,
    #    command=on_correct_block_position_toggle
    #).pack(side="left", padx=15)


    # ---------- SEQUENCE CHECKBOXES ----------
    frame_sequence_checks = panel("Sequence Progress", row_all_panels)
    frame_sequence_checks.grid(row=0, column=4, sticky="new", padx=5)

    tk.Checkbutton(
        frame_sequence_checks,
        text="Picked Up Block?",
        variable=picked_up_var,
        bg=PANEL,                 # panel background
        fg=PRIMARY,
        selectcolor="white",      # checkbox square color (important!)
        activebackground=PANEL,
        font=("Arial", 13),
        bd=0,
        highlightthickness=0,
        command=on_picked_up_toggle
    ).pack(pady=5)

    tk.Checkbutton(
        frame_sequence_checks,
        text="Placed Block?",
        variable=placed_var,
        bg=PANEL,                 # panel background
        fg=PRIMARY,
        selectcolor="white",      # checkbox square color (important!)
        activebackground=PANEL,
        font=("Arial", 13),
        bd=0,
        highlightthickness=0,
        command=on_placed_toggle
    ).pack(pady=5)

    blocks_frame = tk.Frame(frame_sequence_checks, bg=PANEL)
    blocks_frame.pack(pady=5)

    positions_frame = tk.Frame(frame_sequence_checks, bg=PANEL)
    positions_frame.pack(pady=5)

    # ------------------ BIND BUTTONS

    # ------------------ CAMERA ------------------

    camera_label = tk.Label(content, bg="black")
    camera_label.pack(padx=10, pady=10)

    # Start camera thread
    threading.Thread(target=camera_capture, daemon=True).start()
    update_camera_label()

    # Stop camera when closing
    def on_close():
        global camera_running
        camera_running = False

        print("Stopping robot gaze behavior")
        cmd_queue.put("stop")

        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_close)
    #app.mainloop()

    for btn in [intro_button, ns_button, bye_button]:
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    

    app.mainloop()