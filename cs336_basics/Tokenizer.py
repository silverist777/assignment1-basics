import regex as re
from collections.abc import Iterable, Iterator
import json

class Tokenizer():

    def __init__(self,vocab,merges,special_tokens = None):
        self.vocab = vocab
        self.merges = merges
        self.special_tokens = special_tokens
        

    @classmethod
    def from_files(cls,vocab_filepath, merges_filepath, special_tokens=None):
        with open(vocab_filepath, "r", encoding="utf-8") as f:
            raw_vocab = json.load(f)  # {"42": "th"}

            vocab = {
                int(token_id): token.encode("utf-8")
                for token_id, token in raw_vocab.items()
            }
        if special_tokens and vocab:
            for st in special_tokens:
                vocab[vocab_size] =st.encode("utf-8")
                vocab_size += 1
        with open(merges_filepath, "r", encoding="utf-8") as f:
            raw_merges = json.load(f)

            merges = [
                (left.encode("utf-8"), right.encode("utf-8"))
                for left, right in raw_merges
            ]
        return Tokenizer(vocab, merges, special_tokens)

    def encode(self, text:str) -> list[int]:
        token2id = {}
        encode_id = []
        vocab_size = len(self.vocab)
    # get token2id vocab
        for key,value in self.vocab.items():
            token2id[value] = key

    # process special token
        
        

        if self.special_tokens:

            ordered = sorted(self.special_tokens,key=len, reverse=True)
            special_pattern = "|".join(re.escape(st) for st in ordered)
            text = re.split(f"({special_pattern})",text)
        else:
            text = [text]

        PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
        
        for chunk in text:
            if self.special_tokens and chunk in ordered:
                chunk = chunk.encode("utf-8")
                encode_id.append(token2id[chunk])
            else:
                for match in re.finditer(PAT,chunk):
                    current_pieces = []
                    initial_length = 0
                    final_length = 1
                    piece = match.group()
                    piece = piece.encode("utf-8")
                    encode_piece = [piece[i:i+1] for i in range(len(piece))]

                    encode_pair = [(encode_piece[i],encode_piece[i+1]) for i in range(len(encode_piece)-1)]

                    for merge in self.merges:
                        if merge in encode_pair:
                            encode_piece = self.merge_pairs(encode_piece, merge)
                            encode_pair = [(encode_piece[i],encode_piece[i+1]) for i in range(len(encode_piece)-1)]

                    for current_piece in encode_piece:
                            encode_id.append(token2id[current_piece])
        return encode_id
# parameter is iterable string return value is a generator
    def encode_iterable(self,iterable: Iterable[str]) -> Iterator[int]: 
        for text in iterable:
            yield from self.encode(text)

    def decode(self,ids):
        
        cat_token = b"".join(self.vocab[idx] for idx in ids)
        cat_token = cat_token.decode(encoding="utf-8", errors="replace")

        return cat_token
            
    def merge_pairs(self,word:list[bytes],merge_pair):
        a,b = merge_pair
        i = 0
        merged = []

        while i < len(word):
            if i < len(word) -1 and word[i] == a and word[i+1] == b:
                merged.append(a+b)
                i+=2
            else:
                merged.append(word[i])
                i+=1
        return merged




