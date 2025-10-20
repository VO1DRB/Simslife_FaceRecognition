def get_orientation_instructions(progress_step):
    """
    Returns instructions for face orientation based on the current progress step
    
    Args:
        progress_step: Current step in the registration process
    
    Returns:
        str: Instruction text
    """
    if progress_step == 0:
        return "Posisikan wajah menghadap ke kamera (depan)"
    elif progress_step == 1:
        return "Posisikan wajah menghadap ke kiri"
    elif progress_step == 2:
        return "Posisikan wajah menghadap ke kanan"
    else:
        return "Proses selesai"