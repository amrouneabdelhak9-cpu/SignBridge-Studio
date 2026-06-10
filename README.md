# SignBridge-Studio
Real-Time Sign Language Translation System using Computer Vision and Deep Learning
# SignBridge Studio

A real-time sign language translation system powered by Computer Vision and Deep Learning.

## Features

- Real-time hand tracking
- Sign language recognition
- Interactive learning modules
- Quiz and training system
- Modern desktop interface

## Technologies

- Python
- PyQt
- MediaPipe
- TensorFlow/Keras
- ONNX Runtime
- Computer Vision

## Installation
## Model Download

Due to GitHub file size limitations, the trained AI models are hosted on Hugging Face.

Create a folder named `models` in the project root and download the following files:

| Model                                                                                                                                       | Download                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| asl_alphabet_model.keras                                                                                                                    | https://huggingface.co/amrouneabdelhak9/SignBridge-Studio-Models/resolve/main/model/asl_alphabet_model.keras |
| custom_signs.pt                                                                                                                             |                                                                                                              |
| model_scripted.pt                                                                                                                           | https://huggingface.co/amrouneabdelhak9/SignBridge-Studio-Models/blob/main/model/model_scripted.pt           |
| model.onnx                                                                                                                                  | https://huggingface.co/amrouneabdelhak9/SignBridge-Studio-Models/blob/main/model/model.onnx                  |
| model.onnx.data                     https://huggingface.co/amrouneabdelhak9/SignBridge-Studio-Models/blob/main/model/model.onnx.data        |                                                                                                              |
all models                      here https://huggingface.co/amrouneabdelhak9/SignBridge-Studio-Models/tree/main/model
After downloading, place all files inside:

models/  

Then run:

pip install -r requirements.txt

python main.py

```bash
pip install -r requirements.txt
python main.py
