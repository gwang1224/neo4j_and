import re
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()
PUNCT_RE = re.compile(r'[!“”"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~—～]+')

raw_stop = ['at','based','in','of','for','on','and','to','an','using','with','the','method','algrithom','by','model']
STOP = {stemmer.stem(w) for w in raw_stop}

def clean_and_stem(title: str):
    t = PUNCT_RE.sub(' ', title or '').lower().replace('\t',' ')
    tokens = [w for w in t.split(' ') if len(w) > 1]
    stemmed = [stemmer.stem(w) for w in tokens]
    kept = [s for s in stemmed if s not in STOP]
    return tokens, kept  # (original words), (stemmed+filtered)


title = "Building a graph database in neo4j for name disambiguation"
print(clean_and_stem(title))
