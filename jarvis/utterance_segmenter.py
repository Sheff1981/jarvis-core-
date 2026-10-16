"""Bounded offline utterance segmentation before speech recognition."""


class UtteranceSegmenter:
    def __init__(self, detector, sample_rate=16000, frame_ms=20,
                 start_frames=3, end_frames=25, max_seconds=15):
        if sample_rate != 16000 or frame_ms != 20:
            raise ValueError("16kHz and 20ms frames required")
        self.detector = detector
        self.frame_size = sample_rate * frame_ms * 2 // 1000
        self.start_frames = start_frames
        self.end_frames = end_frames
        self.max_size = sample_rate * 2 * max_seconds
        self.reset()

    def reset(self):
        self.pending = bytearray()
        self.audio = bytearray()
        self.preroll = []
        self.active = False
        self.consecutive = 0
        self.quiet = 0

    def push(self, chunk):
        self.pending.extend(chunk)
        completed = []
        while len(self.pending) >= self.frame_size:
            frame = bytes(self.pending[:self.frame_size])
            del self.pending[:self.frame_size]
            speech = bool(self.detector(frame))
            if not self.active:
                self.preroll.append(frame)
                self.preroll = self.preroll[-10:]
                self.consecutive = self.consecutive + 1 if speech else 0
                if self.consecutive >= self.start_frames:
                    self.active = True
                    self.audio = bytearray(b"".join(self.preroll))
                continue
            self.audio.extend(frame)
            self.quiet = 0 if speech else self.quiet + 1
            if len(self.audio) > self.max_size:
                self.reset()
                continue
            if self.quiet >= self.end_frames:
                completed.append(bytes(self.audio))
                self.audio.clear()
                self.preroll.clear()
                self.active = False
                self.consecutive = 0
                self.quiet = 0
        return completed
