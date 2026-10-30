"""Offline SpeechBrain ECAPA embedding adapter.

Optional dependency: speechbrain + torch. Model files MUST already be present
on disk. This adapter never downloads a model or makes a network request.
"""
from pathlib import Path


class LocalECAPAExtractor:
    def __init__(self, model_directory):
        directory = Path(model_directory).expanduser().resolve()
        if not directory.is_dir():
            raise FileNotFoundError("local ECAPA model directory not found")
        self.model_directory = directory
        try:
            import torch
            try:
                from speechbrain.inference.speaker import EncoderClassifier
            except ImportError:
                from speechbrain.pretrained import EncoderClassifier
        except ImportError as exc:
            raise RuntimeError("SpeechBrain and PyTorch are required for ECAPA") from exc
        self._torch = torch
        # source and savedir are the SAME local directory; no remote model ID.
        self._model = EncoderClassifier.from_hparams(
            source=str(directory), savedir=str(directory),
            run_opts={"device": "cpu"},
        )
        self.model_id = "speechbrain-ecapa:" + directory.name

    def __call__(self, pcm16, sample_rate):
        if sample_rate != 16000:
            raise ValueError("ECAPA requires 16000 Hz mono PCM")
        if not isinstance(pcm16, bytes) or len(pcm16) < 16000 or len(pcm16) % 2:
            raise ValueError("ECAPA requires at least 0.5s of PCM16")
        import array
        import sys
        samples = array.array("h")
        samples.frombytes(pcm16)
        if sys.byteorder != "little":
            samples.byteswap()
        signal = self._torch.tensor(samples, dtype=self._torch.float32).div_(32768.0)
        with self._torch.inference_mode():
            embedding = self._model.encode_batch(signal.unsqueeze(0))
        return embedding.reshape(-1).detach().cpu().tolist()
