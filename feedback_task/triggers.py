class TriggerTypes:
    BLINK = "BLINK"
    TARGET_START = "TARGET_S"
    TARGET_END = "TARGET_E"
    REACTION = "REACTION"
    SECOND_REACTION = "SECOND_R"
    FIXATION = "FIXATION"
    BLOCK_START = "BLOCK_START"


def get_trigger_name(
    trigger_type,
    block,
    trial=None,
):
    block_type = block["type"]
    if trial is not None:
        target_name = trial["target_name"]
        correct_key = trial["correct_key"]
    else:
        target_name = "-"
        correct_key = "-"

    # response will be added later, on close_trial
    return "*".join([trigger_type, block_type[:3], target_name, correct_key, ""])
