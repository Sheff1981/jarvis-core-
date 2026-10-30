"""CPU-friendly, dependency-free trainable intent classifier for JARVIS.

This tiny neural network is a stepping stone, not a replacement for the LLM.
Training data must be explicitly labeled; prediction never trains itself.
"""
import json
import math
import random
import re
from collections import Counter


def tokenize(text):
    return re.findall(r"[\wа-яё]+", text.lower(), flags=re.UNICODE)


class IntentNetwork:
    def __init__(self, labels, vocabulary, weights=None, bias=None):
        self.labels = tuple(labels)
        self.vocabulary = tuple(vocabulary)
        self.weights = weights or [[0.0] * len(self.vocabulary) for _ in self.labels]
        self.bias = bias or [0.0] * len(self.labels)

    @classmethod
    def train(cls, examples, *, epochs=80, rate=0.15, seed=42, max_words=512):
        examples = list(examples)
        if len(examples) < 4 or any(not isinstance(text, str) or not isinstance(label, str) or
                                    not text.strip() or not label.strip() for text, label in examples):
            raise ValueError("At least four labeled examples required")
        if not 1 <= epochs <= 500 or not 0 < rate <= 1 or not 8 <= max_words <= 4096:
            raise ValueError("Invalid training parameters")
        labels = sorted({label for _, label in examples})
        if len(labels) < 2:
            raise ValueError("At least two classes required")
        counts = Counter(token for text, _ in examples for token in set(tokenize(text)))
        vocabulary = sorted(counts, key=lambda token: (-counts[token], token))[:max_words]
        model = cls(labels, vocabulary)
        index = {word: i for i, word in enumerate(vocabulary)}
        order = list(range(len(examples)))
        rng = random.Random(seed)
        for _ in range(epochs):
            rng.shuffle(order)
            for sample in order:
                text, label = examples[sample]
                features = {index[word] for word in tokenize(text) if word in index}
                scores = [model.bias[k] + sum(model.weights[k][i] for i in features)
                          for k in range(len(labels))]
                peak = max(scores)
                exps = [math.exp(s - peak) for s in scores]
                total = sum(exps)
                for k in range(len(labels)):
                    error = exps[k] / total - (1 if labels[k] == label else 0)
                    model.bias[k] -= rate * error
                    for i in features:
                        model.weights[k][i] -= rate * error
        return model

    def predict(self, text):
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
        index = {word: i for i, word in enumerate(self.vocabulary)}
        features = {index[word] for word in tokenize(text) if word in index}
        if not features:
            return {"label": None, "confidence": 0.0}
        scores = [self.bias[k] + sum(self.weights[k][i] for i in features)
                  for k in range(len(self.labels))]
        peak = max(scores)
        probs = [math.exp(s - peak) for s in scores]
        best = max(range(len(scores)), key=lambda k: probs[k])
        return {"label": self.labels[best], "confidence": probs[best] / sum(probs)}

    def evaluate(self, examples):
        examples = list(examples)
        if not examples:
            raise ValueError("Holdout examples required")
        return sum(self.predict(text)["label"] == label for text, label in examples) / len(examples)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump({"format": 1, "labels": self.labels, "vocabulary": self.vocabulary,
                       "weights": self.weights, "bias": self.bias}, file, ensure_ascii=False)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        if data.get("format") != 1:
            raise ValueError("Unsupported model format")
        return cls(data["labels"], data["vocabulary"], data["weights"], data["bias"])
