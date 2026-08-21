from enum import Enum, auto
import random
from session_logger import session_logger

class State(Enum):
    IDLE = auto()
    INTRO = auto()
    NEW_SEQUENCE = auto()
    CHECK_CUBE = auto()
    HESITANT_CUBE = auto()
    HESITANT_POSITION = auto()
    INCORRECT_POSITION = auto()
    INCORRECT_CUBE = auto()
    SAY_GOODBYE = auto()
    TOUCHED_WRONG_BLOCK = auto()
    SAYING_BOARD_CLEAN = auto()
    EARLY_START = auto()
    FORGOT_SEQUENCE = auto()

class GameState:
    def __init__(self):
        self.current_state = State.IDLE
        
        # Sequence Data
        self.seq_block = []
        self.seq_position = []
        self.trial_index = 0
        self.sequence_length = 3
        self.is_sequence_active = False # Flag to prevent overlapping announcements
        
        # Experiment Settings
        self.condition = "Implicit"
        self.wait_time = 4
        self.isi = 2
        
        # Interaction Flags
        self.picked_up = False
        self.placed = False
        self.touched_wrong_block = False
        
        # UI References (Assigned during GUI creation)
        self.block_check_vars = []
        self.position_check_vars = []
        self.available_colours = ["Verde", "Azul", "Roxo", "Vermelho", "Amarelo"]
        
        self.finish_announced = False # Guard for sequence finished audio
        self.board_clean_said = False # Ensure first LimpaTabuleiro is version 1

    def reset_trial_flags(self):
        """Call this at the start of every sequence OR item completion."""
        self.picked_up = False
        self.placed = False
        self.touched_wrong_block = False
        self.available_colours = ["Verde", "Azul", "Roxo", "Vermelho", "Amarelo"]
        
        # UI Sync: Reset the checkbuttons if they exist
        if hasattr(self, 'p_var_ref'): self.p_var_ref.set(False)
        if hasattr(self, 'pl_var_ref'): self.pl_var_ref.set(False)

    def set_available_colours(self, current_block):
        if current_block in ["Verde", "Azul", "Roxo"]:
            self.available_colours = ["Verde", "Azul", "Roxo"]
        else:
            self.available_colours = ["Vermelho", "Amarelo"]

    def transition(self, new_state, robot, ui, *args):
        """
        The 'Brain' of the app. 
        Changes the state and immediately triggers the associated behavior.
        """
        if self.current_state == new_state and new_state != State.NEW_SEQUENCE:
            return # Avoid redundant transitions
            
        print(f"[STATE] Transitioning from {self.current_state.name} to {new_state.name}")
        session_logger.log(f"[STATE] Transitioning from {self.current_state.name} to {new_state.name}")
        self.current_state = new_state
        
        # Clear the hint countdown label unless we are in a hint-giving state
        hint_states = [State.HESITANT_CUBE, State.HESITANT_POSITION, State.INCORRECT_CUBE, State.INCORRECT_POSITION]
        if new_state not in hint_states and hasattr(self, 'hint_countdown'):
            self.hint_countdown.set("")
        
        # Import inside the method to avoid circular imports at the top of the file
        import behaviors 

        if new_state == State.IDLE:
            robot.resume_idle()

        elif new_state == State.INTRO:
            behaviors.say_intro(robot, self, ui, on_done=lambda: self.transition(State.IDLE, robot, ui))
            
        elif new_state == State.TOUCHED_WRONG_BLOCK:
            behaviors.touched_wrong_block_behavior(robot, self, ui)
            
        elif new_state == State.NEW_SEQUENCE:
            import behaviors
            
            # --- Relocated SequenciaTerminada with Guard & Auto-Increment ---
            is_first = len(self.seq_block) == 0
            if not is_first and not self.finish_announced and not getattr(self, "was_early_start", False):
                session_logger.log("[STATE] Announcing Sequence Finished before check")
                
                # Auto-increment if previous was completed cleanly
                all_checked = all(v.get() for v in self.block_check_vars) and all(v.get() for v in self.position_check_vars)
                was_early = getattr(self, "was_early_start", False)
                
                if all_checked and not was_early:
                    if self.sequence_length < 9:
                        self.sequence_length += 1
                        if hasattr(self, 'seq_length_var_ref'): self.seq_length_var_ref.set(self.sequence_length)
                        session_logger.log(f"[STATE] Auto-incremented sequence length to {self.sequence_length}")
                
                # Determine milestone audio for the upcoming sequence length
                milestone_sound = None
                if self.trial_index >= 2:
                    if self.sequence_length == 5:
                        milestone_sound = "JaVaisAMeio.wav"
                    elif self.sequence_length == 9:
                        milestone_sound = "UltimoNivel.wav"

                if all_checked:
                    robot.set_screen(image="love.png")
                    behaviors.robot_speak_while_gaze(robot, self, ui, f"SequenciaTerminada{random.randint(1,3)}.wav", duration=4000)
                    ui.schedule(lambda: behaviors.robot_speak_while_gaze(robot, self, ui, f"Boa{random.randint(1,3)}.wav", duration=4000), 3500)
                    ui.schedule(lambda: robot.set_screen(image="normal.png"), 8000)
                    self.finish_announced = True
                    if milestone_sound:
                        ms = milestone_sound
                        # Start milestone at 8000ms (sound at 8500ms): gives ~1500ms gap after Boa (~3s file ending ~7000ms)
                        # Transition at 13000ms: milestone (8500ms + ~4-5s) ends ~12500-13500ms, ProximaSequencia at 15000ms
                        ui.schedule(lambda: behaviors.robot_speak_while_gaze(robot, self, ui, ms, duration=5000), 8000)
                        ui.schedule(lambda: self.transition(State.NEW_SEQUENCE, robot, ui), 13000)
                    else:
                        ui.schedule(lambda: self.transition(State.NEW_SEQUENCE, robot, ui), 7000)
                else:
                    robot.set_screen(image="love.png")
                    behaviors.robot_speak_while_gaze(robot, self, ui, f"SequenciaTerminada{random.randint(1,3)}.wav")
                    ui.schedule(lambda: robot.set_screen(image="normal.png"), 4500)
                    self.finish_announced = True
                    if milestone_sound:
                        ms = milestone_sound
                        # Start milestone at 5000ms (sound at 5500ms): gives ~1000ms gap after SequenciaTerminada (~4s file ending ~4500ms)
                        # Transition at 10500ms: milestone (5500ms + ~4-5s) ends ~9500-10500ms, ProximaSequencia at 12500ms
                        ui.schedule(lambda: behaviors.robot_speak_while_gaze(robot, self, ui, ms, duration=5000), 5000)
                        ui.schedule(lambda: self.transition(State.NEW_SEQUENCE, robot, ui), 10500)
                    else:
                        ui.schedule(lambda: self.transition(State.NEW_SEQUENCE, robot, ui), 4500)
                return

            # 0. Check if board is clean
            if hasattr(self, 'clean_board_var_ref') and not self.clean_board_var_ref.get():
                session_logger.log("[STATE] New Sequence blocked: Board is not clean")
                self.transition(State.SAYING_BOARD_CLEAN, robot, ui)
                return

            # 1. Guard against overlapping sequences
            if self.is_sequence_active:
                print("[STATE] Sequence announcement already in progress. Ignoring call.")
                return 

            self.is_sequence_active = True
            self.trial_index += 1
            session_logger.log(f"[STATE] Trial index is now {self.trial_index}")
            self.reset_trial_flags()
            import behaviors
            import gui

            # Use the length currently stored in the state (updated by the dropdown)
            current_len = self.sequence_length
            
            #  Determine if it's the first sequence or a subsequent one
            # We track this by checking if a sequence already exists
            is_first = len(self.seq_block) == 0
            
            # --- Status Reset ---
            # Reset logically and visually when a new sequence begins
            self.sequence_aborted = False
            self.forgot_aborted = False
            self.forgot_sequence_level = 2
            self.picked_up = False
            self.placed = False
            self.touched_wrong_block = False
            if hasattr(self, 'p_var_ref'): self.p_var_ref.set(False)
            if hasattr(self, 'pl_var_ref'): self.pl_var_ref.set(False)
            # --------------------

            # 2. Generate the logic
            blocks, positions = behaviors.sequence_generator(current_len)
            self.seq_block = blocks
            self.seq_position = positions
            session_logger.log(f"[SEQUENCE] Length {current_len}: Blocks {self.seq_block}, Positions {self.seq_position}")
            
            # 3. FIX: Trigger the UI to draw the checkboxes
            # Ensure 'controls_frame_ref' was saved in gui.py!
            gui.rebuild_sequence_widgets(robot, self, ui, self.controls_frame_ref)
            
            # 4. Robot looks at the participant BEFORE starting the intro sound
            robot.stop_idle()
            behaviors.gaze_at_participant_async(robot, ui)
            
            if is_first:
                # Delay the intro sound slightly to ensure the head starts moving first
                ui.schedule(lambda: robot.play_sound("PrimeiraSequencia.wav"), 2000)
                # Wait 5.5 seconds total for the look + intro sound to finish 
                ui.schedule(lambda: behaviors.say_sequence(robot, self, ui, blocks, positions, len(blocks)), 5500)
            else:
                if getattr(self, "was_early_start", False):
                    ui.schedule(lambda: behaviors.say_sequence(robot, self, ui, blocks, positions, len(blocks)), 2000)
                else:
                    # SequenciaTerminada moved to start of state logic
                    ui.schedule(lambda: robot.play_sound(f"ProximaSequencia{random.randint(1,3)}.wav"), 2000)
                    ui.schedule(lambda: behaviors.say_sequence(robot, self, ui, blocks, positions, len(blocks)), 5500)
                    
            self.was_early_start = False
            self.finish_announced = False # Reset for next completion cycle
            
        elif new_state == State.HESITANT_CUBE:
            ui.schedule(lambda: behaviors.hesitant_cube(robot, self, ui), 100)
            
        elif new_state == State.HESITANT_POSITION:
            ui.schedule(lambda: behaviors.hesitant_position(robot, self, ui), 100)
            
        elif new_state == State.INCORRECT_CUBE:
            # args would be the block_which_is_wrong
            behaviors.incorrect_cube(robot, self, ui, *args)
            
        elif new_state == State.INCORRECT_POSITION:
            # args would be the pos_idx
            behaviors.incorrect_position(robot, self, ui, *args)

        elif new_state == State.SAY_GOODBYE:
            import behaviors
            import gui
            behaviors.robot_speak_while_gaze(robot, self, ui, "Goodbye.wav")
            # Clear countdown and reset state
            if hasattr(self, 'hint_countdown'): self.hint_countdown.set("")
            if hasattr(self, 'sequence_container'):
                gui.clear_frame(self.sequence_container)
            self.board_clean_said = False # reset for next session
            self.transition(State.IDLE, robot, ui)
            
        elif new_state == State.SAYING_BOARD_CLEAN:
            import behaviors
            if getattr(self, "board_clean_said", False):
                audio = f"LimpaTabuleiro{random.randint(1,3)}.wav"
            else:
                audio = "LimpaTabuleiro1.wav"
                self.board_clean_said = True
            behaviors.robot_speak_while_gaze(robot, self, ui, audio)
            ui.schedule(lambda: self.transition(State.IDLE, robot, ui), 4500)
            
        elif new_state == State.EARLY_START:
            import behaviors
            self.was_early_start = True
            self.sequence_aborted = True
            self.forgot_aborted = True
            self.is_sequence_active = False
            if robot: robot.set_screen(image="normal.png")
            behaviors.robot_speak_while_gaze(robot, self, ui, "Espera3.wav")
            ui.schedule(lambda: self.transition(State.IDLE, robot, ui), 4500)
            
        elif new_state == State.FORGOT_SEQUENCE:
            if len(self.seq_block) == 0:
                print("[STATE] No active sequence exists. Ignoring FORGOT_SEQUENCE.")
                return
            import behaviors
            self.sequence_aborted = True
            self.forgot_aborted = False
            self.is_sequence_active = False
            behaviors.forgot_sequence_behavior(robot, self, ui)
    
    def check_logic_gate(self, robot, ui):
        """
        Main dispatcher for monitoring participant progress and triggering hints.
        Follows the logic matrix from handwritten specifications.
        """
        session_logger.log(f"[LOGIC] Check Gate: PickedUp={self.picked_up}, Placed={self.placed}, WrongBlock={self.touched_wrong_block}")
        # HIGH PRIORITY: Manual Error Overrides (Touched Wrong Block)
        if self.touched_wrong_block:
            self.transition(State.TOUCHED_WRONG_BLOCK, robot, ui)
            return

        # 1. Identify the 'current target item' index (the first item with an unticked block or position)
        current_idx = None # 0-indexed
        for i in range(len(self.block_check_vars)):
            if not self.block_check_vars[i].get() or not self.position_check_vars[i].get():
                current_idx = i
                break

        # Case 1: All items are checked (Game Finished)
        if current_idx is None:
            self.transition(State.IDLE, robot, ui)
            return

        # Properties of the current item being worked on
        b_checked = self.block_check_vars[current_idx].get()
        p_checked = self.position_check_vars[current_idx].get()

        # Case 2: Guard against interrupting the initial sequence RECITATION
        if self.is_sequence_active:
            return
        
        # ---------------------------------------------------------
        # Case 3: REACTIVE TRANSITION LOGIC
        # ---------------------------------------------------------
        
        # A. PLACED: High priority (Incorrect Cube / Position)
        if self.placed:
            if not b_checked:
                self.transition(State.INCORRECT_CUBE, robot, ui, current_idx + 1)
            else:
                self.transition(State.INCORRECT_POSITION, robot, ui, current_idx + 1)
            return

        # B. PICKED UP: Helps with the target position
        if self.picked_up:
            self.transition(State.HESITANT_POSITION, robot, ui)
            return

        # C. IDLEBOARD: Fallback logic for hesitant states
        if not b_checked:
            self.transition(State.HESITANT_CUBE, robot, ui)
        elif not p_checked:
            self.transition(State.HESITANT_POSITION, robot, ui)
        else:
            self.transition(State.IDLE, robot, ui)