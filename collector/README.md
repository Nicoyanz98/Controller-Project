# Collector script

## Setup

### Creating virtual enviroment
```bash
python -m venv .collector
```
`.collector` can be changed to a custom directory

### Opening virtual enviroment
#### Windows
```bash
.collector\Scripts\activate
```
#### Linux
```bash
source .collector/bin/activate
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

## Running
```bash
python collector --save_dir <data_dir> --t_input <seconds> --t_idle <seconds>
```
`data_dir` will hold every image obtained. By defaults its created on `./data`.

`t_input`and `t_idle`are the waiting time in seconds before taking a picture between inputs and while idle respectively.

Images will be saved in numbered directories (0, 1, 2, etc), for each time it was executed on the same directory.
 
## Sending images
Zip `data_dir` with 7-zip as `.7z` file and upload it to the Google Drive URL provided by the author.