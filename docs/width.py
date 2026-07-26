W = {' ':278,'!':278,'"':355,'#':556,'$':556,'%':889,'&':667,"'":191,
     '(':333,')':333,'*':389,'+':584,',':278,'-':333,'.':278,'/':278,
     ':':278,';':278,'<':584,'=':584,'>':584,'?':556,'@':1015,
     '[':278,'\\':278,']':278,'^':469,'_':556,'`':333,
     '{':334,'|':260,'}':334,'~':584}
for c in '0123456789': W[c] = 556
for c,w in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    [667,667,722,722,667,611,778,722,278,500,667,556,833,
     722,778,667,778,722,667,611,722,667,944,667,667,611]): W[c]=w
for c,w in zip('abcdefghijklmnopqrstuvwxyz',
    [556,556,500,556,556,278,556,556,222,222,500,222,833,
     556,556,556,556,333,500,278,556,500,722,500,500,500]): W[c]=w
W.update({'×':584,'≤':549,'≥':549,'≈':549,'–':556,'’':191,
          '·':278,'°':400,'²':333,'é':556,'ã':556,'õ':556})

def width(s): return sum(W.get(c,556) for c in s)
BUDGET = width("Surveyed 96 workers at a loss-making 560-worker NTC textile "
               "mill, diagnosing ~25% absence, 2x the norm")
def pct(s): return 100.0*width(s)/BUDGET

if __name__ == '__main__':
    import sys, re
    for line in sys.stdin:
        line = line.rstrip('\n')
        if line.strip():
            plain = line.replace('**','')
            p = pct(plain)
            bad = [ch for ch in ('₹','→','—') if ch in plain]
            flag = 'OK  ' if p <= 100.3 else 'OVER'
            note = f"  BANNED{bad}" if bad else ''
            print(f"{flag} {p:6.1f}%{note}  {line}")
