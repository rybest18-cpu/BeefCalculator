import os
import io
import random
import PySimpleGUI as sg
import pyperclip
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- Each picture and its secret weight (lbs) ----
# Put these image files in the same folder as this script.
BEEF_PICTURES = [
    ("1lbsbeef.png",         1),
    ("5lbsgroundbeef.png",   5),
    ("10lbsgroundbeef.png", 10),
]
TOLERANCE = 0.25   # how close a guess must be to count as correct (lbs)
IMAGE_SIZE = 280   # max picture width/height in pixels

# ---- Red / pink colour scheme ----
PINK_BG    = '#ffe4ec'   # window background
PINK_LIGHT = '#fff5f8'   # input box
DEEP_RED   = '#7a0026'   # text
HOT_PINK   = '#e64980'   # "Guess" button
RASPBERRY  = '#c2255c'   # hover colour
WRONG_RED  = '#e03131'   # "Try again" button
WIN_GREEN  = '#2f9e44'   # "Next beef" button
FONT       = 'Helvetica'

sg.LOOK_AND_FEEL_TABLE['BeefPink'] = {
    'BACKGROUND': PINK_BG, 'TEXT': DEEP_RED,
    'INPUT': PINK_LIGHT, 'TEXT_INPUT': DEEP_RED,
    'SCROLL': HOT_PINK, 'BUTTON': ('white', HOT_PINK),
    'PROGRESS': (HOT_PINK, PINK_LIGHT),
    'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0,
}
sg.theme('BeefPink')

# The main button's three "looks": (text, colour)
BUTTON_GUESS = ("GUESS!", HOT_PINK)
BUTTON_WRONG = ("TRY AGAIN", WRONG_RED)
BUTTON_NEXT  = ("NEXT BEEF  >>", WIN_GREEN)


def load_image(path, size=IMAGE_SIZE):
    """Open any image type, shrink it, and return PNG data PySimpleGUI can show."""
    img = Image.open(path)
    img.thumbnail((size, size))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# Load every picture that exists and opens properly
rounds = []
for filename, weight in BEEF_PICTURES:
    try:
        rounds.append((filename, load_image(os.path.join(HERE, filename)), weight))
    except Exception:
        print(f"Skipping {filename}: missing or not an image")

if not rounds:
    sg.popup_error("No beef pictures found!\nPut the beef images next to this script.")
    raise SystemExit

random.shuffle(rounds)   # new order every time you play

layout = [
    [sg.Text("GUESS THE BEEF", font=(FONT, 26, 'bold'), text_color=RASPBERRY,
             justification='center', expand_x=True)],
    [sg.Text("", key='-COUNTER-', font=(FONT, 11), justification='center',
             expand_x=True)],
    [sg.Push(), sg.Frame("", [[sg.Image(data=rounds[0][1], key='-PIC-', pad=8)]],
                         background_color='white', border_width=0), sg.Push()],
    [sg.Text("How much does this beef weigh (lbs)?", font=(FONT, 12),
             justification='center', expand_x=True)],
    [sg.Push(),
     sg.Input(key='-INPUT-', size=(8, 1), font=(FONT, 18), justification='center',
              border_width=0, enable_events=True),
     sg.Text("lbs", font=(FONT, 14)),
     sg.Push()],
    [sg.Push(),
     sg.Button(BUTTON_GUESS[0], key='-ACTION-', font=(FONT, 16, 'bold'),
               size=(14, 1), border_width=0, bind_return_key=True,
               button_color=('white', BUTTON_GUESS[1]),
               mouseover_colors=('white', RASPBERRY)),
     sg.Push()],
    [sg.Text("", key='-RESULT-', font=(FONT, 14, 'bold'), justification='center',
             expand_x=True)],
    [sg.Text("", key='-SCORE-', font=(FONT, 12), justification='center',
             expand_x=True)],
    [sg.Push(),
     sg.Button('Copy result', key='-COPY-', font=(FONT, 10), border_width=0,
               button_color=('white', DEEP_RED), mouseover_colors=('white', RASPBERRY)),
     sg.Button('Skip', key='-SKIP-', font=(FONT, 10), border_width=0,
               button_color=(DEEP_RED, '#ffc2d4'), mouseover_colors=('white', RASPBERRY)),
     sg.Push()],
]

window = sg.Window('Beef Weight Guessing Game', layout, finalize=True,
                   element_justification='center', margins=(25, 20))

current = 0      # which picture we're on
tries = 0        # guesses on this picture
score = 0        # pictures guessed correctly
solved = False   # has this picture been guessed?


def set_button(look):
    """Change the big button's text and colour."""
    text, colour = look
    window['-ACTION-'].update(text, button_color=('white', colour))


def show_round():
    """Display the current picture and reset everything for a new guess."""
    window['-PIC-'].update(data=rounds[current][1])
    window['-COUNTER-'].update(f"Beef {current + 1} of {len(rounds)}")
    window['-INPUT-'].update("")
    window['-RESULT-'].update("")
    window['-SCORE-'].update(f"Score: {score} / {len(rounds)}")
    set_button(BUTTON_GUESS)
    window['-INPUT-'].set_focus()


def next_round():
    global current, tries, solved
    current = (current + 1) % len(rounds)   # loops back to the first picture
    tries = 0
    solved = False
    show_round()


show_round()

# Window interaction loop
while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break

    # The big button does two jobs: check a guess, or move to the next beef
    if event == '-ACTION-':
        if solved:
            next_round()
            continue

        try:
            guess = float(values['-INPUT-'])
        except ValueError:
            window['-RESULT-'].update("Please enter a number!", text_color=WRONG_RED)
            set_button(BUTTON_WRONG)
            continue

        tries += 1
        answer = rounds[current][2]
        if abs(guess - answer) <= TOLERANCE:
            solved = True
            score += 1
            window['-RESULT-'].update(
                f"Correct! It's {answer} lbs ({tries} {'try' if tries == 1 else 'tries'})",
                text_color=WIN_GREEN)
            window['-SCORE-'].update(f"Score: {score} / {len(rounds)}")
            set_button(BUTTON_NEXT)
        elif guess > answer:
            window['-RESULT-'].update(f"{guess:g} lbs is too HIGH", text_color=WRONG_RED)
            set_button(BUTTON_WRONG)
        else:
            window['-RESULT-'].update(f"{guess:g} lbs is too LOW", text_color=WRONG_RED)
            set_button(BUTTON_WRONG)

    # Typing a new guess puts the button back to "GUESS!"
    if event == '-INPUT-' and not solved:
        set_button(BUTTON_GUESS)

    if event == '-SKIP-':
        next_round()

    if event == '-COPY-':
        text = window['-RESULT-'].get()
        if text:
            pyperclip.copy(text)
            sg.popup("Copied to clipboard!", background_color=PINK_BG,
                     text_color=DEEP_RED, button_color=('white', HOT_PINK))
        else:
            sg.popup("Nothing to copy yet. Make a guess first!",
                     background_color=PINK_BG, text_color=DEEP_RED,
                     button_color=('white', HOT_PINK))

window.close()
