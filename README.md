## Data collector
### Setup
Setup virtual enviroment
```cmd
python3 -m venv <venv_dir>
```

Activate virtual enviroment
```cmd
source <venv_dir>/bin/activate
```

Install the requirements:
```cmd
pip install -r requirements.txt
```
### How to use?
#### Data Collector
Run the next code to use the data collection tool:
```cmd
cd tools
python3 main.py [-C]
```
>`-C` indicates that there is a controller connected

#### Gesture Recognition
```cmd
cd gesture_recognition
python3 main.py
```

## TODO
- [ ] Implementar botones (solo tiene en cuenta movimiento)
- [ ] Detectar gestos de ambas manos (considerar performance)
- [ ] Reentrenar modelo con nuestros gestos (funciona con gestos por defecto)
- [ ] Arreglar contador de FPS (actualmente el reconocedor es asíncrono)