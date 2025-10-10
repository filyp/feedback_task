import random
from collections import OrderedDict
from copy import copy
from pathlib import Path
from textwrap import dedent

import numpy as np
from psychopy import core, event, logging, visual
from unidecode import unidecode

from feedback_task.triggers import TriggerTypes, get_trigger_name
from psychopy_experiment_helpers.show_info import show_info

message_dir = Path(__file__).parent.parent / "messages"
stimuli_dir = Path(__file__).parent.parent / "stimuli"

color_dict = dict(
    red="#FF0000",
    green="#00FF00",
    blue="#0000FF",
    yellow="#FFFF00",
)


# def prepare_stimuli(win, config):
#     incongruent_trials = []
#     congruent_trials = []
#     for text in ["CZERWONY", "ZIELONY", "NIEBIESKI", "ŻÓŁTY"]:
#         for color in ["red", "green", "blue", "yellow"]:
#             name = color + "_" + unidecode(text.lower())
#             stimulus = visual.TextStim(
#                 win=win,
#                 text=text,
#                 color=color_dict[color],
#                 height=config["Target_size"],
#                 name=name,
#             )
#             congruent = name in ["red_czerwony", "green_zielony", "blue_niebieski", "yellow_zolty" ]  # fmt: skip
#             trial = dict(
#                 target=stimulus,
#                 target_name=name,
#                 type="congruent" if congruent else "incongruent",
#                 font_color=color,
#                 text=text,
#                 correct_key=config["Response_key"][color],
#             )
#             if congruent:
#                 congruent_trials.append(trial)
#             else:
#                 incongruent_trials.append(trial)

#     return congruent_trials, incongruent_trials


def deg_to_height(deg, config):
    size_in_cm = (deg / 360) * (2 * 3.1415 * config["Screen_distance"])
    return size_in_cm / config["Screen_height"]


def load_img(name, size, win, config):
    return visual.ImageStim(
        win=win,
        image=stimuli_dir / name,
        size=deg_to_height(size, config),
        interpolate=True,
    )


def load_text(text, win, config):
    return visual.TextStim(
        win=win,
        text=text,
        color="black",
        # height=config["Text_feedback_font_size"],
        height=deg_to_height(config["Text_feedback_size"], config),
        font="Arial",
    )


def feedback_task(exp, config, data_saver):
    # unpack necessary objects for easier access
    win = exp.win
    clock = exp.clock

    # EEG triggers
    if config["Trigger_type"] == "usb":
        from psychopy_experiment_helpers.triggers_common_usb import (
            TriggerHandler,
            create_eeg_port,
        )
    elif config["Trigger_type"] == "parport":
        from psychopy_experiment_helpers.triggers_common_parport import (
            TriggerHandler,
            create_eeg_port,
        )
    else:
        raise ValueError("Invalid trigger type: {}".format(config["Trigger_type"]))
    port_eeg = create_eeg_port() if config["Send_EEG_trigg"] else None
    trigger_handler = TriggerHandler(port_eeg, data_saver=data_saver)
    exp.trigger_handler = trigger_handler

    # load stimuli
    fixation = load_img("dot.png", config["Fixation_size"], win, config)
    star = load_img("star.png", config["Star_size"], win, config)
    too_slow = load_text("zbyt wolno", win, config)
    too_fast = load_text("zbyt szybko", win, config)

    _v = config["Experiment_version"]
    feedback = dict(
        number=dict(
            pos=load_text("+1", win, config),
            neg=load_text("-1", win, config),
            neu=load_text("J", win, config),
        ),
        facesimple=dict(
            pos=load_img("smiley_face.png", config["Feedback_size"], win, config),
            neg=load_img("sad_face.png", config["Feedback_size"], win, config),
            neu=load_img("empty_face.png", config["Feedback_size"], win, config),
        ),
        facecomplex=dict(
            pos=load_img(f"{_v}/pos.png", config["Face_feedback_size"], win, config),
            neg=load_img(f"{_v}/neg.png", config["Face_feedback_size"], win, config),
            neu=load_img(f"{_v}/neu.png", config["Face_feedback_size"], win, config),
        ),
        symbol=dict(
            pos=load_img("tick.png", config["Feedback_size"], win, config),
            neg=load_img("cross.png", config["Feedback_size"], win, config),
            neu=load_img("equal.png", config["Feedback_size"], win, config),
        ),
        color=dict(
            pos=load_img("green_square.png", config["Feedback_size"], win, config),
            neg=load_img("red_square.png", config["Feedback_size"], win, config),
            neu=load_img("blue_square.png", config["Feedback_size"], win, config),
        ),
        text=dict(
            pos=load_text("dobrze", win, config),
            neg=load_text("błędnie", win, config),
            neu=load_text("żyrafa", win, config),
        ),
        training=dict(
            pos=load_img("thumbs_up.png", config["Feedback_size"], win, config),
            neg=load_img("thumbs_down.png", config["Feedback_size"], win, config),
            neu=None,
        ),
    )

    block_order = config["Feedback_types"]
    random.shuffle(block_order)
    logging.data(f"Block order: {block_order}")

    def trial(speed_feedback, neutral_feedback=False):
        nonlocal allowed_error

        # ! open trial
        trigger_handler.open_trial()
        trial = dict(
            block_num=block_num,
            trial_num=trial_num,
            rt="-",
            allowed_error=allowed_error,
            block_type=block_type,
        )
        # * prepare inter-trial interval
        trial["iti_time"] = random.uniform(config["ITI_min"], config["ITI_max"])

        # ! draw inter-trial interval fixation
        trigger_name = get_trigger_name(TriggerTypes.FIXATION)
        trigger_handler.prepare_trigger(trigger_name)
        fixation.setAutoDraw(True)
        win.flip()
        trigger_handler.send_trigger()
        core.wait(trial["iti_time"])
        fixation.setAutoDraw(False)
        data_saver.check_exit()

        # ! draw star (start)
        trigger_name = get_trigger_name(TriggerTypes.STAR_START)
        trigger_handler.prepare_trigger(trigger_name)
        event.clearEvents()
        win.callOnFlip(clock.reset)
        star.setAutoDraw(True)
        win.flip()
        trigger_handler.send_trigger()
        core.wait(config["Star_duration"])

        trigger_name = get_trigger_name(TriggerTypes.STAR_END)
        trigger_handler.prepare_trigger(trigger_name)
        star.setAutoDraw(False)
        win.flip()
        trigger_handler.send_trigger()
        data_saver.check_exit()

        # ! wait for press
        keys = event.waitKeys(
            keyList=[config["Response_key"]],
            maxWait=config["Max_wait"],
            timeStamped=clock,
        )
        if keys is not None:
            assert len(keys) == 1
            assert keys[0][0] == config["Response_key"]
            trial["rt"] = keys[0][1]
            trigger_name = get_trigger_name(TriggerTypes.REACTION)
            trigger_handler.prepare_trigger(trigger_name)
            trigger_handler.send_trigger()
        data_saver.check_exit()

        if trial["rt"] == "-":
            trial["feedback"] = "neg"
            trial["acc"] = -1
        else:
            if abs(trial["rt"] - 1) <= allowed_error / 1000:
                trial["feedback"] = "pos"
                trial["acc"] = 1
                allowed_error -= 10
            else:
                trial["feedback"] = "neg"
                trial["acc"] = 0
                allowed_error += 10

        if neutral_feedback:
            trial["feedback"] = "neu"

        # ! draw feedback
        feedback_stim = feedback[block_type][trial["feedback"]]
        feedback_trig = {
            "pos": TriggerTypes.FEEDBACK_POS,
            "neg": TriggerTypes.FEEDBACK_NEG,
            "neu": TriggerTypes.FEEDBACK_NEU,
        }[trial["feedback"]]
        trigger_name = get_trigger_name(feedback_trig)
        trigger_handler.prepare_trigger(trigger_name)
        feedback_stim.setAutoDraw(True)
        win.flip()
        trigger_handler.send_trigger()
        core.wait(config["Feedback_duration"])
        # hide feedback
        feedback_stim.setAutoDraw(False)
        win.flip()
        data_saver.check_exit()

        if speed_feedback and trial["feedback"] == "neg":
            # ! draw speed feedback
            if trial["rt"] == "-" or trial["rt"] > 1:
                s_feedback_stim = too_slow
                s_feedback_trig = TriggerTypes.TOO_SLOW
            else:
                s_feedback_stim = too_fast
                s_feedback_trig = TriggerTypes.TOO_FAST

            trigger_name = get_trigger_name(s_feedback_trig)
            trigger_handler.prepare_trigger(trigger_name)
            s_feedback_stim.setAutoDraw(True)
            win.flip()
            trigger_handler.send_trigger()
            core.wait(config["Speed_feedback_duration"])
            # hide feedback
            s_feedback_stim.setAutoDraw(False)
            win.flip()
            data_saver.check_exit()

        # save beh
        data_saver.beh.append(trial)
        trigger_handler.close_trial(trial["acc"])

        logging.data("Trial data: {}\n".format(trial))
        logging.flush()

    # ! greeting texts
    for greeting_text in config["Greeting_texts"]:
        show_info(exp, greeting_text, duration=None)

    # ! training block
    block_num = 0  # block 0 is training
    block_type = "training"
    allowed_error = 100  # in milliseconds
    for trial_num in range(config["N_train_trials"]):
        trial(speed_feedback=True)

    show_info(exp, config["Post_training_text"], duration=None)

    allowed_error = 100  # reset allowed error
    for _ in range(3):
        for block_type in block_order:
            block_num += 1
            f_expl = config["Feedback_explanations"][block_type]
            txt = config["New_block_text"].format(block_num=block_num, f_expl=f_expl)
            show_info(exp, txt, duration=None)

            # ! choose which trials will have neutral feedback
            indexes = list(range(config["N_trials_per_block"]))
            logging.data(f"Indexes: {indexes}")
            indexes = random.sample(indexes, config["N_neutral_trials_per_block"])
            logging.data(f"Indexes: {indexes}")
            logging.flush()

            trigger_name = get_trigger_name(TriggerTypes.BLOCK_START)
            trigger_handler.prepare_trigger(trigger_name)
            trigger_handler.send_trigger()

            for trial_num in range(config["N_trials_per_block"]):
                trial(
                    speed_feedback=config["Speed_feedback"],
                    neutral_feedback=trial_num in indexes,
                )
    
    show_info(exp, config["End_text"], duration=None)

    # for block in config["Experiment_blocks"]:
    #     trigger_name = get_trigger_name(TriggerTypes.BLOCK_START, block)
    #     trigger_handler.prepare_trigger(trigger_name)
    #     trigger_handler.send_trigger()
    #     logging.data("Entering block: {}".format(block))
    #     logging.flush()
    #     untimed = False  # that's the default

    #     if block["type"] == "break":
    #         text = "Zakończyłeś jeden z bloków sesji eksperymentalnej."
    #         show_info(exp, text, duration=3)

    #         text = """\
    #         Zrób sobie PRZERWĘ.

    #         Przerwa na odpoczynek nr {num}.

    #         (wciśnij spację kiedy będziesz gotowy kontynuować badanie)"""
    #         text = dedent(text).format(num=block["num"])
    #         show_info(exp, text, duration=None)

    #         text = """Za chwilę rozpocznie się kolejny blok sesji eksperymentalnej."""
    #         show_info(exp, text, duration=5)
    #         continue

    #     elif block["type"] == "msg":
    #         # all the other messages, instructions, info
    #         text = (message_dir / block["file_name"]).read_text()
    #         text = text.format(**config)
    #         duration = block.get("duration", None)
    #         show_info(exp, text, duration=duration)
    #         continue

    #     elif block["type"] == "1training":
    #         trials = congruent_trials
    #         untimed = True
    #         assert len(trials) == 4

    #     elif block["type"] == "2training":
    #         trials = congruent_trials * 2
    #         assert len(trials) == 8

    #     elif block["type"] == "3training":
    #         trials = random.sample(incongruent_trials, 4)
    #         untimed = True
    #         assert len(trials) == 4

    #     elif block["type"] == "4training":
    #         trials = random.sample(incongruent_trials, 4) + congruent_trials * 2
    #         assert len(trials) == 12

    #     elif block["type"] == "experiment":
    #         # prepare 24 congruent trials and 12 incongruent trials
    #         trials = congruent_trials * 6 + incongruent_trials

    #     else:
    #         raise ValueError("{} is a bad block type in config".format(block["type"]))

    #     random.shuffle(trials)
    #     for trial in trials:
    #         trigger_handler.open_trial()
    #         trial["response"] = "-"
    #         trial["rt"] = "-"
    #         trial["reaction"] = "-"

    #         # ! draw empty screen
    #         win.flip()
    #         core.wait(1)

    #         # ! draw fixation
    #         trigger_name = get_trigger_name(TriggerTypes.FIXATION, block, trial)
    #         trigger_handler.prepare_trigger(trigger_name)
    #         fixation.setAutoDraw(True)
    #         win.flip()
    #         trigger_handler.send_trigger()
    #         core.wait(0.5)
    #         fixation.setAutoDraw(False)

    #         data_saver.check_exit()

    #         # ! draw target
    #         trigger_name = get_trigger_name(TriggerTypes.TARGET_START, block, trial)
    #         trigger_handler.prepare_trigger(trigger_name)
    #         event.clearEvents()
    #         win.callOnFlip(clock.reset)
    #         trial["target"].setAutoDraw(True)
    #         win.flip()
    #         trigger_handler.send_trigger()
    #         if untimed:
    #             event.waitKeys(keyList=[trial["correct_key"]])
    #         else:
    #             while clock.getTime() < 0.2:
    #                 check_response(config, trial, clock, trigger_handler, block)
    #                 win.flip()
    #         trial["target"].setAutoDraw(False)

    #         if not untimed:
    #             # ! draw fixation and await response
    #             trigger_name = get_trigger_name(TriggerTypes.TARGET_END, block, trial)
    #             trigger_handler.prepare_trigger(trigger_name)
    #             fixation.setAutoDraw(True)
    #             win.flip()
    #             trigger_handler.send_trigger()
    #             while clock.getTime() < 0.2 + 0.8:
    #                 check_response(config, trial, clock, trigger_handler, block)
    #                 win.flip()
    #             fixation.setAutoDraw(False)
    #             win.flip()

    #         # if incorrect and training, show feedback
    #         if ("training" in block["type"]) and (not untimed):
    #             if trial["reaction"] == "incorrect":
    #                 text = "Reakcja niepoprawna.\nWciskaj klawisz odpowiadający KOLOROWI CZCIONKI."
    #                 show_info(exp, text, duration=5)
    #             elif trial["reaction"] == "-":
    #                 text = "Reakcja zbyt późna."
    #                 show_info(exp, text, duration=5)

    #         # save beh
    #         # fmt: off
    #         behavioral_data = OrderedDict(
    #             # predefined
    #             block_type=block["type"],
    #             trial_type=trial["type"],
    #             font_color=trial["font_color"],
    #             text=trial["text"],
    #             correct_key=trial["correct_key"],
    #             # based on response
    #             response=trial["response"],
    #             rt=trial["rt"],
    #             reaction=trial["reaction"],
    #         )
    #         # fmt: on
    #         data_saver.beh.append(behavioral_data)
    #         trigger_handler.close_trial(trial["response"])

    #         logging.data("Behavioral data: {}\n".format(behavioral_data))
    #         logging.flush()
