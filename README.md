# ringmaster-python

python reimplementation of ringmaster project

## Installation

To set up the environment using `conda`:

```bash
conda create -n pyringmaster python=3.9
conda activate pyringmaster
conda install -c conda-forge gcc
pip install -r requirements.txt
```

Alternatively, to set up the environment using `venv`:

```bash
python -m venv pyringmaster
source pyringmaster/bin/activate  # On Windows use `pyringmaster\Scripts\activate`
pip install -r requirements.txt
```

## Usage

For video sender:
```bash
python app/video_sender.py 12345 ice_4cif_30fps.y4m
```

For video receiver:
```bash
python app/video_receiver.py 127.0.0.1 12345 704 576 --fps 30 --cbr 500
```