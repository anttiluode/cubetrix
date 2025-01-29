# CubeTrix

Imagine you woke up one day in a infinite world, larger than the known universe. Full of cubes. 

## Table of Contents

- [Features](#features)
- [Gameplay](#gameplay)
- [Controls](#controls)
- [Installation](#installation)
- [Running the Game](#running-the-game)
- [Dependencies](#dependencies)
- [Assets](#assets)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- **Dynamic Terrain Generation**: Explore procedurally generated landscapes that offer a unique experience every time you play.

## Gameplay

As the protagonist trapped in the Cubetrix, your objective is to survive as long as possible by eliminating enemies, collecting health and armor pickups, and navigating the dynamically generated terrain. 

## Controls

- **W/A/S/D**: Move Forward/Left/Backward/Right
- **Space**: Jump
- **Shift**: Run
- **Left Mouse Button**: Shoot
- **Escape**: Pause/Menu
- **R**: Restart Game (when Game Over)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/anttiluode/CubeTrix.git
   cd CubeTrix
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv cubetrix_env
   ```

   - **Activate the Virtual Environment:**
     - **Windows:**
       ```bash
       cubetrix_env\Scripts\activate
       ```
     - **macOS/Linux:**
       ```bash
       source cubetrix_env/bin/activate
       ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

After completing the installation steps:

```bash
python cubetrix.py
```

**Note**: Ensure that the `assets` directory contains all the necessary sound files and other assets as referenced in the code.

## Dependencies

The project relies on the following Python libraries:

- [Ursina Engine](https://www.ursinaengine.org/)
- [NumPy](https://numpy.org/)
- [SciPy](https://www.scipy.org/)
- [pyttsx3](https://pyttsx3.readthedocs.io/en/latest/)
- [Comtypes](https://pypi.org/project/comtypes/) (for TTS-related functionality)

All dependencies are listed in the `requirements.txt` file.

## Assets

Ensure that the `assets` directory includes all necessary files such as:

- **Sound Files**:
  - `start.ogg`
  - `game.ogg`
  - `shoot.ogg`
  - `step.ogg`
  - `death.ogg`
  - `cubedeath.ogg`
  - `jump.ogg`
  - `attack.ogg`
  - `nom.ogg`
  - `armor.ogg`

- **Fonts**:
  - `VeraMono.ttf`

- **Images** (optional):
  - `banner.png` (for the README banner)

**Directory Structure**:

```
CubeTrix/
├── assets/
│   ├── start.ogg
│   ├── game.ogg
│   ├── shoot.ogg
│   ├── step.ogg
│   ├── death.ogg
│   ├── cubedeath.ogg
│   ├── jump.ogg
│   ├── attack.ogg
│   ├── nom.ogg
│   ├── armor.ogg
│   ├── VeraMono.ttf
│   └── banner.png
├── main.py
├── README.md
└── requirements.txt
```



## License

This project is licensed under the [MIT License](LICENSE). See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Ursina Engine](https://www.ursinaengine.org/) for providing a fantastic framework for game development.
- [pyttsx3](https://pyttsx3.readthedocs.io/en/latest/) for enabling text-to-speech functionality.
- [NumPy](https://numpy.org/) and [SciPy](https://www.scipy.org/) for powerful scientific computing tools.
- The open-source community for their invaluable resources and support.

---

**Happy Gaming!** 🎮

