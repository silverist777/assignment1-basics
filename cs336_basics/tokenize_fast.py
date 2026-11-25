import regex as re
from collections import Counter,defaultdict
from .tokenize_slow import *


def train_bpe(input_path:str, vocab_size: int, special_tokens: list[str]):
    with open(input_path, 'r',encoding = 'utf-8') as f:
        text = f.read()
    initial_vocab = {}
    merges = []
    pair_ind = defaultdict(set) # {pair:{sequence_id}}
    counts = Counter()
    id = 256
    word_sequence = [] #[(word,freq)]
    word_count = Counter()
    pair_count = Counter()
    seq_id = 0
    # pre-tokenize

    initial_vocab = {i : bytes([i]) for i in range(id)}

    for st in special_tokens:
        st = st.encode("utf-8")
        initial_vocab[id] = st
        id += 1

    if special_tokens:
        pattern = "|".join(re.escape(st) for st in special_tokens)
        chunk = re.split(pattern, text) # chunk: list[str] text: str
    else:
        chunk = [text]
    PAT = PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
    for subchunk in chunk:
        matches = re.finditer(PAT,subchunk)
        """
    Difference : We iterate over all the match object to build word_count get word-frequency
    then build word_sequence then pair_ind
        """
        for match in matches:
            piece = match.group()
            encode = piece.encode("utf-8")
            encode_piece = tuple(encode[i:i+1] for i in range(len(encode)))

            word_count[encode_piece] += 1

    for word, freq in word_count.items():
        word_sequence.append((word,freq))

        pair_count = count_pairs(word)
        for pair, pair_freq in pair_count.items():
            pair_ind[pair].add(seq_id)
            counts[pair] += freq * pair_freq
        seq_id +=1
    """
    Now we have:
    pair_ind : which words to update
    word_count: 
    counts : freq of all pairs


    """
    most_freq_pair = counts.most_common(1)[0]

# merge the pair

# check lexicographically greater pair logic
    while len(initial_vocab) < vocab_size and len(counts.most_common()) != 0:
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
        print("ranked:", ranked[:3])
        print("most_freq_pair:", most_freq_pair)
        print("counts keys:", list(counts.keys())[:3])
        merge_token = most_freq_pair[0][0] + most_freq_pair[0][1]
        merge_pair = (most_freq_pair[0][0],most_freq_pair[0][1])

        affect_ids = pair_ind[merge_pair].copy()
        for word_id in affect_ids:
            word,freq = word_sequence[word_id] #get old sequence
            old_count =  count_pairs(word)
            for pair,pair_freq in old_count.items():
                counts[pair] -= pair_freq*freq
                pair_ind[pair].remove(word_id)

            
            word_sequence[word_id] = (merge_pairs(word_sequence[word_id], merge_pair),word_sequence[word_id][1])
            pair_count = count_pairs(word_sequence[word_id][0])
            for pair, pair_freq in pair_count.items():
                pair_ind[pair].add(seq_id)
                counts[pair] += freq * pair_freq
            

        

        # update merges and vocab

        merges.append((most_freq_pair[0][0],most_freq_pair[0][1]))
        initial_vocab[id] = merge_token
        id +=1

    print("best_pair:", merge_pair)
    print("affected_ids:", affect_ids)
    print("counts:", counts)
    print("pair_ind:", pair_ind)

    return initial_vocab, merges



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



        
        