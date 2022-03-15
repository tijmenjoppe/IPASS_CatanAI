# CatanAI

CatanAI is a digital online-multiplayer recreation of Settlers of Catan.

But it's mainly aimed at the implementation of **Monte Carlo Tree Search** for the AI opponents.

This is my IPASS project for ICT-AI at Utrecht University of Applied Sciences.

## Installation

Make sure you use python 3.7  
Install the requirements using pip.

```bash
pip install -r requirements.txt --user
```

## Usage

You only need to run the menu that gives options in joining and hosting Catan games.

```bash
python Menu.py
```

### Graphical User Interface

Who's turn it is will be displayed in the top left corner.
The player's resources index will be shown at the bottom.
The last actions taken are logged in the top right corner.

When it's your turn, you'll be be shown white dot's for every possible action. The closest dot to the mouse will be selected when clicked.

## Documentation

### Read
Open ```docs/_build/html/index.html``` in your favorite browser.

### Make
```bash
cd docs
make html
```

## License
[GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/)

## Notice

I just found out that Windows is being stupid and flags the pygame-window as "Not responding", multiple Linux devices had no problem.
Will try to fix this soon.