import tkinter as tk
from state_machine import State
from config import *
import random
import os
from session_logger import session_logger

# ---------------------------
# UI WRAPPER
# ---------------------------
class UI:
    def __init__(self, app):
        self.app = app
        self.after_ids = []

    def schedule(self, func, delay_ms):
        tid_box = []
        def wrapped():
            if tid_box[0] in self.after_ids:
                self.after_ids.remove(tid_box[0])
            func()
        tid = self.app.after(delay_ms, wrapped)
        tid_box.append(tid)
        self.after_ids.append(tid)

    def cancel_all(self):
        for tid in self.after_ids:
            self.app.after_cancel(tid)
        self.after_ids.clear()

# ---------------------------
# DYNAMIC WIDGETS
# ---------------------------
def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def rebuild_sequence_widgets(robot, state, ui, controls_frame):
    """Creates checkboxes only when a sequence is generated."""
    # Ensure the container exists on the left panel
    if not hasattr(state, 'sequence_container') or state.sequence_container.master != controls_frame:
        state.sequence_container = tk.Frame(controls_frame, bg=PANEL)
        state.sequence_container.pack(pady=10)
    
    # Clear any old checkboxes from previous rounds
    for widget in state.sequence_container.winfo_children():
        widget.destroy()
    
    state.block_check_vars = []
    state.position_check_vars = []
    cb_style = {"bg": PANEL, "fg": PRIMARY, "selectcolor": "white", "activebackground": PANEL, "font": ("Helvetica", 12)}

    # Sequence Progress List
    tk.Label(state.sequence_container, text="SEQUENCE PROGRESS:", bg=PANEL, font=("Helvetica", 12, "bold"), fg="#d000d0").pack(pady=(10,5), anchor="w", padx=10)
    
    for i in range(len(state.seq_block)):
        row_frame = tk.Frame(state.sequence_container, bg=PANEL)
        row_frame.pack(anchor="w", padx=20, pady=2)
        
        # Block Checkbox
        b_var = tk.BooleanVar(value=True)
        state.block_check_vars.append(b_var)

        def on_b_click(v=b_var, idx=i):
            if v.get(): state.reset_trial_flags()
            session_logger.log(f"[UI] Block B{idx+1} checkbox set to {v.get()}")
            state.check_logic_gate(robot, ui)

        tk.Checkbutton(
            row_frame, text=f"{state.seq_block[i]}", variable=b_var, 
            command=on_b_click, 
            **cb_style, width=10, anchor="w"
        ).pack(side="left")

        # Position Checkbox
        p_var = tk.BooleanVar(value=True)
        state.position_check_vars.append(p_var)
        
        def on_p_click(v=p_var, idx=i):
            if v.get(): state.reset_trial_flags()
            session_logger.log(f"[UI] Position P{idx+1} checkbox set to {v.get()}")
            state.check_logic_gate(robot, ui)

        tk.Checkbutton(
            row_frame, text=f"P{state.seq_position[i]}", variable=p_var, 
            command=on_p_click, 
            **cb_style, width=5, anchor="w"
        ).pack(side="left", padx=(10, 0))
    
    # Ensure canvas scroll region is updated
    if hasattr(state, 'canvas_ref'):
        ui.app.update_idletasks()
        state.canvas_ref.configure(scrollregion=state.canvas_ref.bbox("all"))
# ---------------------------
# CALLBACKS
# ---------------------------
def on_picked_up_toggle(robot, state, ui, var):
    state.picked_up = var.get()
    session_logger.log(f"[UI] Picked Up Cube toggled: {state.picked_up}")
    if state.picked_up:
        state.placed = False
    # Delay check to allow experimenter to update other boxes
    ui.schedule(lambda: state.check_logic_gate(robot, ui), 2500)

def on_placed_toggle(robot, state, ui, var):
    state.placed = var.get()
    session_logger.log(f"[UI] Placed Cube toggled: {state.placed}")
    if state.placed:
        state.picked_up = False
    # Delay check to allow experimenter to update other boxes (wizard needs time!)
    ui.schedule(lambda: state.check_logic_gate(robot, ui), 4000)

def on_wrong_block_toggle(robot, state, ui, var):
    state.touched_wrong_block = var.get()
    session_logger.log(f"[UI] Touched Wrong Block toggled: {state.touched_wrong_block}")
    if state.touched_wrong_block:
        # Let the state machine handle the formal transition and audio
        state.check_logic_gate(robot, ui)
    else:
        # Returning to re-evaluation after manual override is cleared
        state.transition(State.IDLE, robot, ui)
        ui.schedule(lambda: state.check_logic_gate(robot, ui), 1000)

# ---------------------------
# MAIN GUI CREATION
# ---------------------------
def create_gui(robot, state, ui, camera=None):
    app = ui.app
    app.title("Elmo Game Master")
    app.geometry("1400x950")
    app.configure(bg=BG)

    # Header
    header = tk.Frame(app, bg=PRIMARY, height=60)
    header.pack(fill="x")
    tk.Label(header, text="ELMO PROMOTING AUTONOMY", fg="white", bg=PRIMARY, font=("Helvetica", 18, "bold")).pack(pady=15)

    content = tk.Frame(app, bg=BG)
    content.pack(fill="both", expand=True, padx=20, pady=20)

    # Container for Canvas + Scrollbar
    left_container = tk.Frame(content, bg=PANEL)
    left_container.pack(side="left", fill="both")

    # Canvas with vertical scrolling
    # Width 350 for the checkboxes + some padding
    canvas = tk.Canvas(left_container, bg=PANEL, highlightthickness=0, width=350)
    state.canvas_ref = canvas # Store for later updates
    scrollbar = tk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Inner frame that actually holds everything
    left_panel = tk.Frame(canvas, bg=PANEL, padx=20, pady=20)
    canvas.create_window((0,0), window=left_panel, anchor="nw")
    
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    left_panel.bind("<Configure>", on_configure)

    # Mac MouseWheel bind - apply globally or to interaction panels
    def _on_mousewheel(event):
        # canvas.yview_scroll(-1 if event.delta > 0 else 1, "units") # Simplest logic
        canvas.yview_scroll(int(-1 * event.delta), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # IMPORTANT: The state needs to "remember" this frame to draw into it later
    state.controls_frame_ref = left_panel

    # DARKER PINK for titles and buttons
    ACCENT_PINK = "#d000d0"

    button_style = {
        "bg": ACCENT_PINK, "fg": "black", "font": ("Helvetica", 12),
        "activebackground": "#ff80ff", "bd": 1, "width": 15, "pady": 5,
        "highlightbackground": "black", "highlightthickness": 1, "relief": "flat"
    }

    # Participant Name Box
    tk.Label(left_panel, text="PARTICIPANT NAME", bg=PANEL, font=("Helvetica", 13, "bold"), fg=ACCENT_PINK).pack(pady=(5, 0))
    participant_var = tk.StringVar()
    participant_entry = tk.Entry(left_panel, textvariable=participant_var, font=("Helvetica", 12), bg="white", fg="black")
    participant_entry.pack(fill="x", padx=10, pady=5)
    
    def on_start_session():
        session_logger.start_session(participant_var.get())
        if camera and record_video_var.get() and session_logger.log_file:
            log_path = session_logger.log_file
            log_dir = os.path.dirname(log_path)
            base_dir = os.path.dirname(log_dir)
            vid_dir = os.path.join(base_dir, "videos")
            os.makedirs(vid_dir, exist_ok=True)
            vid_filename = os.path.basename(log_path).replace('.log', '.avi')
            vid_path = os.path.join(vid_dir, vid_filename)
            camera.start_recording(vid_path)
            session_logger.log(f"[UI] Started video recording to {vid_path}")
            
    tk.Button(left_panel, text="Start Logging", command=on_start_session, **button_style).pack(pady=(5, 5))

    record_video_var = tk.BooleanVar(value=True)
    tk.Checkbutton(left_panel, text="Record Video?", variable=record_video_var, bg=PANEL, fg=PRIMARY, selectcolor="white", activebackground=PANEL, font=("Helvetica", 10)).pack(anchor="w", padx=10, pady=(0, 15))

    # VOLUME at the top
    tk.Label(left_panel, text="VOLUME", bg=PANEL, font=("Helvetica", 13, "bold"), fg=ACCENT_PINK).pack(pady=(10, 0))
    volume_slider = tk.Scale(
        left_panel, from_=0, to=100, orient="horizontal", bg=PANEL,
        highlightthickness=0, bd=0, command=lambda v: robot.set_volume(v),
        fg="black"
    )
    volume_slider.set(25) # Default volume
    volume_slider.pack(fill="x", padx=10, pady=(0, 20))

    # Condition Dropdown
    tk.Label(left_panel, text="STUDY CONDITION", bg=PANEL, font=("Helvetica", 13, "bold"), fg=ACCENT_PINK).pack(pady=(0, 5))
    
    CONDITION_COLORS = {
        "Implicit":  "#ffb3ff",  # pink (as before)
        "Explicit":  "#a8c8f8",  # blue
        "Control":   "#a8e6a8",  # green
    }

    condition_var = tk.StringVar(value=state.condition)
    conditions = ["Control", "Explicit", "Implicit"]

    def on_condition_change(v):
        setattr(state, 'condition', v)
        color = CONDITION_COLORS.get(v, SECONDARY)
        cond_menu.config(bg=color)
        session_logger.log(f"[UI] Study Condition changed to: {v}")

    cond_menu = tk.OptionMenu(left_panel, condition_var, *conditions,
                              command=on_condition_change)
    
    initial_color = CONDITION_COLORS.get(state.condition, SECONDARY)
    cond_menu.config(bg=initial_color, fg=PRIMARY, font=("Helvetica", 12), width=15, anchor="center", justify="center", indicatoron=False)
    cond_menu.pack(pady=(0, 20))

    # Sequence Length Dropdown
    tk.Label(left_panel, text="SEQUENCE LENGTH", bg=PANEL, font=("Helvetica", 13, "bold"), fg=ACCENT_PINK).pack(pady=(0, 5))
    seq_length_var = tk.IntVar(value=state.sequence_length) 
    state.seq_length_var_ref = seq_length_var
    len_options = [2, 3, 4, 5, 6, 7, 8, 9]
    len_dropdown = tk.OptionMenu(left_panel, seq_length_var, *len_options, 
                             command=lambda v: (setattr(state, 'sequence_length', int(v)), session_logger.log(f"[UI] Sequence Length changed to: {v}")))
    len_dropdown.config(bg=SECONDARY, fg=PRIMARY, font=("Helvetica", 12), width=15, anchor="center", justify="center", indicatoron=False)
    len_dropdown.pack(pady=(0, 20))

    # Wait Time Dropdown
    tk.Label(left_panel, text="WAIT TIME (S)", bg=PANEL, font=("Helvetica", 13, "bold"), fg=ACCENT_PINK).pack(pady=(0, 5))
    wait_time_var = tk.IntVar(value=state.wait_time)
    wait_options = [2, 3, 4, 6, 8, 10, 16] # Merged with config options
    wait_dropdown = tk.OptionMenu(left_panel, wait_time_var, *wait_options,
                                  command=lambda v: (setattr(state, 'wait_time', int(v)), session_logger.log(f"[UI] Wait Time changed to: {v}")))
    wait_dropdown.config(bg=SECONDARY, fg=PRIMARY, font=("Helvetica", 12), width=15, anchor="center", justify="center", indicatoron=False)
    wait_dropdown.pack(pady=(0, 20))

    tk.Label(left_panel, text="COMMANDS", bg=PANEL, font=("Helvetica", 13, "bold"), fg=ACCENT_PINK).pack(pady=(0, 10))
    tk.Button(left_panel, text="Intro", command=lambda: (session_logger.log("[UI] Clicked Intro"), state.transition(State.INTRO, robot, ui)), **button_style).pack(pady=5)
    tk.Button(left_panel, text="New Sequence", command=lambda: (session_logger.log("[UI] Clicked New Sequence"), state.transition(State.NEW_SEQUENCE, robot, ui)), **button_style).pack(pady=5)
    tk.Button(left_panel, text="Say Bye", command=lambda: (session_logger.log("[UI] Clicked Say Bye"), state.transition(State.SAY_GOODBYE, robot, ui), camera.stop_recording() if camera else None), **button_style).pack(pady=5)

    def on_abort_click():
        session_logger.log("[UI] Clicked Abort Current")
        ui.cancel_all()
        robot.stop_all_audio()
        state.is_hint_active = False
        if hasattr(state, 'hint_countdown'): state.hint_countdown.set("")
        state.transition(State.IDLE, robot, ui)

    abort_style = {"bg": "#ffffff", "fg": "red", "font": ("Helvetica", 12, "bold"), "width": 12, "relief": "ridge"}
    tk.Button(left_panel, text="Abort Current", command=on_abort_click, **abort_style).pack(pady=(15, 5))
    tk.Button(left_panel, text="Early Start", command=lambda: (session_logger.log("[UI] Clicked Early Start"), state.transition(State.EARLY_START, robot, ui)), **button_style).pack(pady=5)
    tk.Button(left_panel, text="Forgot Sequence?", command=lambda: (session_logger.log("[UI] Clicked Forgot Sequence"), state.transition(State.FORGOT_SEQUENCE, robot, ui)), **button_style).pack(pady=5)
    
    # Status Toggles
    tk.Label(left_panel, text="BOARD STATUS", bg=PANEL, font=("Helvetica", 13, "bold"), fg=ACCENT_PINK).pack(pady=(25, 10))
    cb_style = {"bg": PANEL, "fg": PRIMARY, "selectcolor": "white", "activebackground": PANEL, "font": ("Helvetica", 12)}
    
    cb_board_clean = tk.BooleanVar(value=True)
    state.clean_board_var_ref = cb_board_clean
    tk.Checkbutton(left_panel, text="Board Clean?", variable=cb_board_clean, command=lambda: session_logger.log(f"[UI] Board Clean toggled: {cb_board_clean.get()}"), **cb_style).pack(anchor="w")

    p_var = tk.BooleanVar()
    state.p_var_ref = p_var
    tk.Checkbutton(left_panel, text="Picked Up Cube", variable=p_var, command=lambda: on_picked_up_toggle(robot, state, ui, p_var), **cb_style).pack(anchor="w")
    
    pl_var = tk.BooleanVar()
    state.pl_var_ref = pl_var
    tk.Checkbutton(left_panel, text="Placed Cube", variable=pl_var, command=lambda: on_placed_toggle(robot, state, ui, pl_var), **cb_style).pack(anchor="w")

    # Touched Wrong Block
    twb_var = tk.BooleanVar()
    state.twb_var_ref = twb_var
    tk.Checkbutton(
        left_panel, text="Touched Wrong Block", variable=twb_var, 
        command=lambda: on_wrong_block_toggle(robot, state, ui, twb_var), 
        **cb_style
    ).pack(anchor="w")

    # Dynamic Sequence List container
    state.sequence_container = tk.Frame(left_panel, bg=PANEL)
    state.sequence_container.pack(pady=10)

    # Right Column
    right_panel = tk.Frame(content, bg=BG)
    right_panel.pack(side="right", fill="both", expand=True, padx=(20, 0))

    status_frame = tk.Frame(right_panel, bg=STATUS_BG, pady=15)
    status_frame.pack(fill="x")
    status_var = tk.StringVar(value="IDLE")
    # Kept slightly larger (size 16) as it's the main status, but Helvetica
    tk.Label(status_frame, textvariable=status_var, bg=STATUS_BG, font=("Helvetica", 16), fg=ACCENT_PINK).pack()
    
    # Hint Countdown Label
    state.hint_countdown = tk.StringVar(value="")
    tk.Label(status_frame, textvariable=state.hint_countdown, bg=STATUS_BG, font=("Helvetica", 12, "italic"), fg="#555555").pack()

    cam_label = tk.Label(right_panel, bg="black", width=800, height=480)
    cam_label.pack(pady=30)

    def update_status():
        status_var.set(f"STATE: {state.current_state.name}")
        app.after(500, update_status)
    update_status()

    return cam_label, status_var