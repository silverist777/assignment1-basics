import regex as re
from collections import Counter
import os
from typing import BinaryIO


def train_bpe(input_path: str, vocab_size: int, special_tokens: list[str]):

    vocab = [] # store the encoded text which will be merged and updated
    initial_vocab = {} # the dict will return
    id = 256
    counts = Counter()  # store the frequency and the content of the pairs
    # get text file
    merges = [] # list of tuple will return
    with open(input_path,"r",encoding="utf-8") as f:
        text = f.read()

    # get the initial vocab
    
    initial_vocab = {i : bytes([i]) for i in range(256)}

    # add special token
    for st in special_tokens:
        initial_vocab[id] = st.encode("utf-8")
        id += 1
    # strip out all the special token
    # pre-tokenize
    if special_tokens:
        special_tokens= [re.escape(st) for st in special_tokens]
    
        text = re.split("|".join(special_tokens), text)
    else:
        text = [text]

    PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
    for subtext in text:
        matches = re.finditer(PAT, subtext) 

        """
    Expected output: 
    matches : an iterator of match objects of text
    piece: text object from match
    Example:
    <regex.Match object; span=(162754, 162761), match=' ground'>
    telephone
        """

        for match in matches:
            piece = match.group()
            encoded = piece.encode("utf-8")
            encode_piece = [encoded[i:i+1] for i in range(len(encoded))]
            vocab.append(encode_piece)
            count_pairs(counts,encode_piece)

    if not counts:
        return initial_vocab,merges


# Get pair information
    most_freq_pair = counts.most_common(1)[0]

# merge the pair

# check lexicographically greater pair logic
    ranked = counts.most_common()
    possible_equal = 0
    freq = ranked[possible_equal][1]
    most_freq_pair = (ranked[possible_equal][0],freq)
    while possible_equal < len(counts.most_common()) - 1 and ranked[possible_equal][1] == ranked[possible_equal+1][1] :
        freq = ranked[possible_equal][1]
        most_freq_pair = (max(most_freq_pair[0],max(ranked[possible_equal][0],ranked[possible_equal+1][0])),freq)
        possible_equal += 1

    if len(initial_vocab) >= vocab_size:
        return initial_vocab,merges
    merge_token = most_freq_pair[0][0] + most_freq_pair[0][1]
    merge_pair = (most_freq_pair[0][0],most_freq_pair[0][1])
    merges.append((most_freq_pair[0][0],most_freq_pair[0][1]))

# add to id-token vocab
    initial_vocab[id] = merge_token
    id += 1

# update vocab by merge_pair
    vocab = [merge_pairs(word,merge_pair) for word in vocab]
        
# multi-round update
    """
limit: vocab_size
TODO: count most freq pairs->merge pairs-> update vocab 
    """
    while len(initial_vocab) < vocab_size and len(counts.most_common()) != 0:   
        counts = Counter()
        for encode_piece in vocab:
            count_pairs(counts,encode_piece)
        if not counts:
            break
        most_freq_pair = counts.most_common(1)[0]
        
# check lexicographically greater pair logic
        ranked = counts.most_common()
        possible_equal = 0
        freq = ranked[possible_equal][1]
        most_freq_pair = (ranked[possible_equal][0],freq)
        while possible_equal < len(counts.most_common()) - 1 and ranked[possible_equal][1] == ranked[possible_equal+1][1] :
            freq = ranked[possible_equal][1]
            most_freq_pair = (max(most_freq_pair[0],max(ranked[possible_equal][0],ranked[possible_equal+1][0])),freq)
            possible_equal += 1

        if len(initial_vocab) >= vocab_size:
            return initial_vocab,merges
        merge_token = most_freq_pair[0][0] + most_freq_pair[0][1]
        merge_pair = (most_freq_pair[0][0],most_freq_pair[0][1])
        merges.append((most_freq_pair[0][0],most_freq_pair[0][1]))


        initial_vocab[id] = merge_token
        id += 1

        vocab = [merge_pairs(word,merge_pair) for word in vocab]



    return initial_vocab,merges

def count_pairs(counts: Counter, encode_piece: list[bytes]):
    for i in range(len(encode_piece)- 1):
        counts.update([(encode_piece[i],encode_piece[i+1])])
        
def merge_pairs(word:list[bytes],merge_pair):
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


def find_chunk_boundaries(
    file: BinaryIO,
    desired_num_chunks: int,
    split_special_token: bytes,
) -> list[int]:
    """
    Chunk the file into parts that can be counted independently.
    May return fewer chunks if the boundaries end up overlapping.
    """
    assert isinstance(split_special_token, bytes), "Must represent special token as a bytestring"

    # Get total file size in bytes
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    chunk_size = file_size // desired_num_chunks

    # Initial guesses for chunk boundary locations, uniformly spaced
    # Chunks start on previous index, don't include last index
    chunk_boundaries = [i * chunk_size for i in range(desired_num_chunks + 1)]
    chunk_boundaries[-1] = file_size

    mini_chunk_size = 4096  # Read ahead by 4k bytes at a time

    for bi in range(1, len(chunk_boundaries) - 1):
        initial_position = chunk_boundaries[bi]
        file.seek(initial_position)  # Start at boundary guess
        while True:
            mini_chunk = file.read(mini_chunk_size)  # Read a mini chunk

            # If EOF, this boundary should be at the end of the file
            if mini_chunk == b"":
                chunk_boundaries[bi] = file_size
                break

            # Find the special token in the mini chunk
            found_at = mini_chunk.find(split_special_token)
            if found_at != -1:
                chunk_boundaries[bi] = initial_position + found_at
                break
            initial_position += mini_chunk_size

    # Make sure all boundaries are unique, but might be fewer than desired_num_chunks
    return sorted(set(chunk_boundaries))