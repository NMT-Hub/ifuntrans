import tiktoken

tokenizer = tiktoken.encoding_for_model("gpt-4")


def tokenize(string: str) -> str:
    tokens = tokenizer.encode(string)
    return " ".join([str(token) for token in tokens])


def detokenize(string: str) -> str:
    tokens = string.split(" ")
    tokens = [int(token) for token in tokens]
    return tokenizer.decode(tokens)
