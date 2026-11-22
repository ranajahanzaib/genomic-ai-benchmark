# Model adapters

The registry seeds Evo 2 7B with upstream model name `evo2_7b`. `research/models/evo2.py` implements a lazy adapter for the official `Evo2.score_sequences` scoring call and the official forward-hook embedding interface. It does not download or load weights during status checks, and first-use downloads require explicit opt-in. Tests exercise the interface with a controlled adapter double; they do not claim real inference.

The upstream repository documents local inference on Linux (or limited WSL2), Python 3.11 or 3.12, CUDA 12.1+, and cuDNN 9.3+, with a compatible PyTorch runtime. The 7B model can run in bfloat16 on supported GPU hardware without Transformer Engine; CPU inference is not supported. The API reports runtime findings and keeps capabilities unavailable unless a compatible runtime and weights have been loaded. [Official Evo 2 repository and setup guide](https://github.com/ArcInstitute/evo2).

The registry reports upstream-disclosed architecture, checkpoint family, context, and pretraining source separately from unknown checkpoint revision/digest and model-weight license terms. This project has not produced an Evo 2 score or representation. Users evaluating those weights should verify the applicable license, checkpoint digest, and software versions for their chosen release.
