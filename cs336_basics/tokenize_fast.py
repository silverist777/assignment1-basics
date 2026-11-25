import regex as re
from collections import Counter

def train_bpe(input_path:str, vocab_size: int, special_token: list[str]):
    with open(input_path, 'r',encoding = 'utf-8') as f:
        text = f.read()
    vocab = {}
    merges = []

    counts = Counter()

    # pre-tokenize





    # set-the pair-freq vocabulary
    

