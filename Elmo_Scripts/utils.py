def get_unselected_positions(position_check_vars):
    """
    Returns a list of 1-indexed positions that have NOT been checked.
    Example: If positions 1 and 2 are checked, returns.
    """
    if not position_check_vars:
        return []
        
    return [
        i + 1
        for i, var in enumerate(position_check_vars)
        if not var.get()
    ]

def get_unselected_blocks(block_check_vars):
    """
    Returns a list of 1-indexed blocks that have NOT been checked.
    """
    if not block_check_vars:
        return []

    return [
        i + 1 
        for i, var in enumerate(block_check_vars) 
        if not var.get()
    ]

def get_current_target_index(check_vars):
    """
    Helper to find the index of the FIRST item that hasn't been completed.
    Useful for behaviors to know which block the participant is currently 
    supposed to be handling.
    """
    for i, var in enumerate(check_vars):
        if not var.get():
            return i
    return None