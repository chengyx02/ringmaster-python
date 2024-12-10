# ringmaster-python

python reimplementation of ringmaster project

## Installation

```bash
conda create -n pyringmaster python=3.9
conda activate pyringmaster
conda install -c conda-forge
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