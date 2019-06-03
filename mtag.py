#!/usr/bin/env python3

from __future__ import print_function
from collections import defaultdict
from collections import OrderedDict
from io import open
import os
import sys
import re
import time
import argparse
import logging
import fileinput

#=head1 Multitagger
#Multitagger er eit program som setter inn grammatiske merker i ein tekst.

#=head1 Ide
#Teksten som skal leses skal vere normalisert norsk.

#head1 Versjon 0.1a21, 17. desember 1999
#Endra databasekopling frå DOK til USDPROD

#head1 Versjon 0.1a20, 9. februar 1999
#Samasettingsmodulen: Startar oppatt samansettingsmodulen dersom
#            modulen av ein eller annan grunn har stoppa.

#head1 Versjon 0.1a19, 5. november 1998
#Kommentarar:Fleire kommentarar i same periode fungerer no.
#            Kommentarar i periodar med delte ord fungerer
#SGML-tagger:Endra litt på tolkinga av SGML-taggar slik at det
#            kan eksistere fleire tagger i same periode.
#Hermeteikn: Har tatt bort ' som mogleg hermeteikn


#head1 Versjon 0.1a18, 3. november 1998
#Tal:        Problema med romartal og "VI" er retta opp.
#Store bokstavar: Problema med at store bokstavar som einskildord ikkje
#            vart tagga, er retta opp.
#Namn:       Ved initialer der ordet etter ikkje sikkert er eit namn,
#            vert ordet framfor testa for stort bokstav
#Samantrekking. Samantrekkingar må bestå av minst to bokstavar etter
#            skråstrek. Dette løyser a/s og c/o, men lar m/løk fungere

#head1 Versjon 0.1a17, 30. oktober 1998
#Tal:        Problema med tal i samansettingar, og tal med spesialteikn
#            etter seg er retta opp.
#Hermeteikn: Problem med namn i hermeteikn er retta opp. Problema med
#            samansettingar i hermeteikn er retta opp. Problema med at
#            hermeteikn vert borte og skiftar "retning" er løyst. Hermeteikn
#            blir no tagga uansett om det berre er eit hermeteikn i
#            perioden.
#Samatrekking: Samantrekkingar som td. m/løk vert berre analysert som
#            samantrekking dersom det berre er eit teikn framfor skråstrek

#head1 Versjon 0.1a16, 29. oktober 1998
#Hermeteikn: Hermeteikn rundt einskildord vert ikkje tagga med eigen tag.
#            Dette bør løyse problemet med "vardre"-utstilling.
#            Hermeteikn rundt fleire uforståelege ord vert tolka som eit
#            SUBST PROP. Dette skjer dersom fleirtalet av ord innanfor
#            hermeteikna ikkje vert tolka ved oppslag i basen. Samansetningar
#            vil bli tolka som ukjende ord i denne samanhengen.
#Genitiv:    Problemet med at "Sokrates'" vart tagga som genitiv av
#            "Sokrate" er løyst
#            Problemet med at "Jesus" vart tagga som "subst gen prop gen"
#            er løyst.
#            Ikkje genitiv på pronomen, interjeksjonar, preposisjonar
#Tal:        Takler no beløp som 20.000,-. Innført tag "subst <beløp>"
#            Takler no blanda tal som "1 1/5"
#            Takler "34x21"
#            Takler 2.4.7
#Språk:      Endra "ent" til "eint" og "ordenstall" til "ordenstal" for
#            nynorsk
#Romartal:   Har lagt inn støtte for romartal med meir enn eit teikn
#Forkorting: Forkortingar kan avslutte periodar dersom ordet som kjem
#            etterpå starter med stor bokstav, og ikkje er eit
#            kjent namn. (Fører til ein del endringar i tolkinga av
#            periodeslutt, noko som kan ha generert nye feil)
#Samatrekking: Samantrekkingar som "karbonade m/løk" blir no delt opp til
#            "karbonade m/ løk". m/ må inn i leksikon som versjon av "med"
#Bindestrek: Takler at siste linje i fila sluttar med bindestrek
#Setningslutt: CLB er tatt bort for bindestrek og parantes

#=cut

propHash = defaultdict(lambda: False)

feat = [ 'inf-merke', 'interj', 'interj+adv', '@interj', '<anf>', 'prep',
         'adv+prep', 'adv+adv+prep', 'subst+prep', 'prep+konj+prep', 'prep+subst+prep',
         'adv', 'det+subst+prep+subst', 'prep+prep', 'prep+subst+subst',
         'prep+adv+subst', 'prep+subst+konj+subst', 'subst+prep+subst', 'adv+adj',
         'adj+kon+adj', 'adj+verb', 'ukjent', 'konj', 'pron', 'det', '<romertall>',
         'dem', 'verb', 'pret', 'imp', 'pres', 'n4/til', 'n4', 'inf', 'pass',
         'perf-part', 'adj', 'komp', '<pres-part>', 'clb', '<semi>', '<komma>',
         '<kolon>', '<overskrift>', 'subst', 'subst+subst', 'det+subst', 'subst+kvant',
         'subst+konj+subst', '<klokke>', 'symb', '<dato>', 'appell', 'prop', '<*fjord>',
         '<<<', '<ellipse>', '<spm>', '<utrop>', '<punkt>', '<*museum>', '<*sund>',
         'nøyt', 'mask', '<*fred>', 'fem', 'ub', 'be', 'sup', 'm/f', 'ent', '<*skog>',
         '<*ingeniør>', '<*hall>', 'fl', '<*film>', '<*strand>', '<*forum>',
         '<*kommune>', '<*avis>', '<*produsent>', '<*bolig>', '<*berg>', '<*hav>',
         '<*stad>', '<*tilsyn>', '<**institutt>', '<*sjø>', '<*kirke>', '<*krig>',
         '<*as>', '<*senter>', '<*gård>', '<*hjem>', 'fork', '@<subst',
         'pron+verb+verb', 'prep+subst', 'sbu', 'prep+det+sbu', 'prep+subst+prep+sbu',
         '@s-pred', '@o-pred', 'konj+adv+adj', 'prep+prop', '@tittel', 'prep+det+subst',
         '@adv>', 'prep+adj', '@adv', '<*forbund>', '<*direktør>', '<*formann>',
         '<*fjell>', '<*direktorat>', '<*lov>', '<*park>', '<*aksjon>', '<*sjef>',
         '<*verk>', 'poss', 'pos', '<*sal>', '<ordenstall>', '<adv>', 'pers', 'hum',
         'res', 'sp', '3', 'akk', 'refl', 'nom', '2', 'høflig', '1', 'kvant', 'adj+det',
         '@det>', '<adj>', 'forst', '<*elv>', '<perf-part>', 'k1', 'k2', 'tr1', 'ubøy',
         'tr21/til', 'tr22/til', 'a16', 'rl20', 'a17', 'i1', 'd11/til', 'i2', 'tr11',
         'pa1', 'rl4', 'd5', 'rl9', 'd8/til', 'pa1refl4', 'a3', 'pa4', 'rl5', 'd9/til',
         '<*bre>', 'rl10/til', 'tr2', 'tr', 'pa2', 'd1', 'a6', 'n', 'pa8', 'pa5',
         'tr11/til', 'a8', 'tr5', 'tr10', 'd5/til', 'd7/til', 'tr12', 'n3', 'i4', 'a7',
         'rl6', 'tr9', 'pa/til', 'pa', 'n1', 'a12', 'i3', 'd4', 'tr13/til', 'tr3',
         'rl8', 'd7', 'd3', 'pa1/til', 'pa3', 'tr6', 'rl9/til', 'd2', '<*styre>', 'rl1',
         'rl11', 'rl12', 'rl16', 'rl17', 'rl17/til', 'rl16/til', 'rl12/til', 'a11',
         'a4', 'pr8', 'a14', 'tr8', 'a5', 'tr12/til', 'rl14', 'rl14/til', 'a9', 'a2',
         'pa4/til', 'pr1', 'd6/til', 'pa3/til', 'rl3/til', 'rl2', 'rl18', 'rl15',
         'pa2/til', 'rl3', 'd6', 'tr18', 'rl7', 'pr9', 'pr10', 'd8', 'pr4/til',
         'pr10/til', 'a13', 'pr13', 'tr13', 'tr23', 'rl10', 'tr19', 'tr21', 'rl13',
         'pr7', 'pr6', 'pr3', 'pr4', 'tr16', 'tr17', 'a15', 'pr12', 'tr4', 'tr20/til',
         'tr7', 'pa5/til', 'pr11', 'tr15', '<s-verb>', '<*ås>', 'tr22', 'pr2', 'tr20',
         'tr14', '<aux1/perf_part>', '<aux1/infinitiv>', 'pa6', '<aux1/inf>', 'pa7',
         'gen', '<*dal>', '<*vik>', '<*misjon>', '<*minister>', 'samset-leks',
         'samset-analyse', 'forledd-samset', 'fuge-s', '<*by>', '<*vann>', '<*parti>',
         '<*hus>', '<*sang>', '<*øy>', '<*leilighet>', '<*klubb>', '<*program>',
         '<*leder>', '<*serie>', '<*stand>', '<*kontor>', '<*land>', '<*lokale>',
         '<*nes>', '<*bygning>', '<*fond>', '<*møte>', '<*råd>', '<*utvalg>',
         '<*bevegelse>', '<*ist>', '<*son>', '<*roman>', '<*bok>', '<*plass>',
         '<*pris>', '<*vei>', '<*kamp>', '<*skole>', '<*departement>', '<*avtale>',
         '<*gate>', '<*foretak>', '<*blad>', '<*log>', '<*rett>', '<*foss>',
         '<*forening>', '<*område>', '<*selskap>', '<*lag>', '<*forsker>',
         '<*organisasjon>', '<*sen>', '<*bedrift>', '<*gruppe>', '<*>' ]

feat_nn = [ 'ukjent', 'sbu', 'inf-merke', 'symb', '<anf>', 'fork', 'interj',
            'interj+adv', 'adv+subst', 'prep', 'prep+prep', 'prep+subst+prep',
            'prep+konj+prep', 'adv', 'subst+prep', 'prep+subst+konj+subst', 'prep+adv',
            'prep+subst+subst', 'prep+adj', 'adj+kon+adj', 'konj+adv+prep',
            'prep+adv+subst', 'konj+adj', 'adj+verb', 'adv+adj', 'konj+adv+adj',
            'pron+verb+verb', 'prep+subst', '@s-pred', '@o-pred', '@adv>', 'konj', 'pron',
            'res', 'ikke-hum', 'pers', '2', '1', '3', 'det', '<beløp>', 'poss',
            '<romartal>', 'kvant', 'dem', '<adj>', 'verb', 'pret', 'perf-part', 'inf',
            'pres', 'imp', 'adj', 'subst+perf-part', 'komp', '<pres-part>', 'sup',
            '<perf-part>', 'pos', 'be', '<adv>', 'm/f', 'subst', '<klokke>', '<dato>',
            'mask', 'fem', 'adj+det', '@det>', 'nøyt', 'appell', '<tittel>', 'ub', 'eint',
            'fl', 'eint/fl', 'forst', 'hum', 'sp', 'akk', 'refl', 'refl1', 'nom', 'høflig',
            'tr1', 'pr4/til', 'i1', 'i2', 'rl4', 'tr11', 'pr10', 'pa1', '<att>', 'a3',
            'rl5', 'rl18', 'tr2', 'd9/til', 'd1', 'a6', 'n', 'tr11/til', 'tr10', 'd5',
            'tr5', 'i4', 'a8', 'd5/til', 'rl10/til', 'a7', 'tr', 'a10', 'rl6', 'tr9', 'n1',
            'a12', 'd4', 'i', 'pa1/til', 'tr3', 'pa4', 'i3', 'rl9', 'pa', 'd8/til', 'tr6',
            'pa2', 'rl1', 'tr7', 'rl11', 'pa11', 'd3', 'pa8', 'd2', 'd7/til', 'pr8', 'd8',
            'rl9/til', 'rl2', 'd6/til', 'a11', 'a4', 'a5', 'pa5', 'pa3/til', 'rl3/til',
            'tr8', 'rl12', 'rl16', 'rl17', 'rl12/til', 'rl17/til', 'rl16/til', 'tr15',
            'tr18', 'pa2/til', 'rl15', 'pa3', 'k1', 'k2', 'rl3', 'a9', 'pr9', 'tr12', 'n3',
            'a14', 'n2', 'tr19', 'rl8', 'd4/til', 'rl7', 'd7', 'tr13', 'tr21', 'pa4/til',
            'n4/til', 'n4', 'rl14', 'a13', 'rl14/til', 'pr7', 'pr6', 'tr16', 'tr17', 'pr3',
            'pr4', 'rl10', 'tr4', 'd6', 'tr20/til', 'rl13', 'tr14', 'tr20', 'tr23',
            'pa5/til', 'pr11', 'tr12/til', 'tr13/til', 'a15', 'pr12', 'pr1', 'pr2', 'a2',
            '<aux1/perf_part>', '<aux1/infinitiv>', '<st-verb>', 'sideform', 'tr22',
            'tr24', 'pa6', '<aux1/inf>', 'pa7', 'pr13', 'st-form', 'pass', 'prop',
            'adj+subst', '@interj', '@adv', 'gen', 'bu', 'i12', '<nulv1>', '@<subst',
            '<ordenstal>', 'samset-leks', 'samset-analyse', 'forledd-samset', 'fuge-s',
            '@tittel', '@adj>', 'clb', '<*>', '<ellipse>', '<semi>', '<utrop>', '<kolon>',
            '<spm>', '<punkt>', '<komma>', '<overskrift>', '<<<' ]

feat_idx = dict(zip(feat,range(len(feat))))
feat_idx_nn = dict(zip(feat_nn,range(len(feat_nn))))

suffixes = ['avtale', 'berg', 'blad', 'bok', 'bolig', 'bre', 'bukt', 'by',
            'dal', 'elv', 'film', 'fjell', 'fjord', 'foss', 'fred', 'fylke', 'gate',
            'hall', 'hav', 'hjem', 'hotell', 'hus', 'kirke', 'kommune', 'krig', 'kyst',
            'land', 'lov', 'løkke', 'minister', 'myr', 'nes', 'pakt', 'park', 'plass',
            'president', 'prinsipp', 'pris', 'program', 'protokoll', 'roman', 'sang',
            'sen', 'senter', 'serie', 'seter', 'sjø', 'skog', 'skole', 'smug', 'son',
            'stad', 'strand', 'sund', 'syndrom', 'teorem', 'torg', 'torv', 'torg', 'vann',
            'veg', 'vei', 'vei', 'verk', 'vidde', 'vik', 'ørken', 'øy', 'ås', 'aksjon',
            'bevegelse', 'direktorat', 'forbund', 'forening', 'forum', 'institutt',
            'kontor', 'lag', 'monopol', 'møte', 'nemnd', 'organisasjon', 'parti', 'rett',
            'revisjon', 'råd', 'stand', 'tilsyn', 'utvalg', 'A/S', 'as', 'AS', 'As.',
            'avis', 'bygning', 'departement', 'dir.', 'direktør', 'fond', 'formann',
            'forsker', 'gjeng', 'gruppe', 'gård', 'hytte', 'ingeniør', 'ist', 'kamp',
            'klubb', 'koordinator', 'leder', 'leilighet', 'list', 'log', 'lokale',
            'misjon', 'museum', 'område', 'produsent', 'sal', 'selskap', 'sjef',
            'spesialist', 'styre', 'bedrift', 'foretak', 'institutt']

omTagger = """\
Multitagger versjon 0.1a20, 9. februar 1999
Programmert av Lars Jørgen Tvedt
Modul for sammensetningsanalyse programmert av Helge Hauglin,
modifisert av Lars Jørgen Tvedt

For feilmeldingar og kommentarar, ta kontakt på e-post
l.j.tvedt\@dokpro.uio.no, eller telefon 22 85 49 84
ADVARSEL: Nye versjonar av programmet vil bli
installert utan varsel"""

PROG = os.path.basename(__file__)
DIR = os.path.dirname(os.path.realpath(__file__))

# Les parameterlinja
parser = argparse.ArgumentParser(description=omTagger)
parser.add_argument("-o", metavar='utfil')
parser.add_argument("-l", metavar='loggfil', default=PROG+".log")
parser.add_argument("-p", metavar='perioder')
parser.add_argument("-bm", dest='spraak', action='store_const', const='bm', default='bm')
parser.add_argument("-nn", dest='spraak', action='store_const', const='nn', default='bm')
parser.add_argument('-wxml', action='store_true')
parser.add_argument('-compat', action='store_true')
args, input_files = parser.parse_known_args()
sys.argv = sys.argv[:1] + input_files

UTFIL = args.o
LOGGFIL = args.l
PERIODEFIL = args.p
SPRAAK = args.spraak or 'bm'
WXML = args.wxml
COMPAT = args.compat

# initGlobal
CONSTsetningSlutt = "clb"
CONSTpunktum = "<punkt>"
CONSTkomma = "<komma>"
CONSTutrop = "<utrop>"
CONSTkolon = "<kolon>"
CONSTsemi = "<semi>"
CONSTspoersmaal = "<spm>"
CONSTstrek = "<strek>"
CONSTanfoersel = "<anf>"
CONSTparstart = "<parentes-beg>"
CONSTparslutt = "<parentes-slutt>"
CONSToverskrift = "<overskrift>"
CONSTellipse = "<ellipse>"

SUBST_PROP = "subst prop"
SUBST_DATO = "subst <dato>"
SUBST_KLOKKE = "subst <klokke>"
DET_BELOP = "det <beløp>"
DET_KVANT = "det kvant"
GEN = "gen"

if SPRAAK == 'bm':
    ADJ_ORDEN = "adj <ordenstall>"
    DET_ROMER = "det <romertall>"
    EINTAL = "ent"
    FLEIRTAL = "fl"
elif SPRAAK == 'nn':
    ADJ_ORDEN = "adj <ordenstal>"
    DET_ROMER = "det <romartal>"
    EINTAL = "eint"
    FLEIRTAL = "fl"

specLetters = "\!\?\.<>§@£\$%&/=*-"
#onlysmall="ÿ"
letterssm="abcdefghijklmnopqrstuvwxyzæøåàáâãäçèéêëìíîïñòóôõöùúûüý"
lettersla="ABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅÀÁÂÃÄÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ"
konsonanter="bcdfghjklmnpqrstvwxz"
letters = letterssm + lettersla
vocals = "aeiouyæøåàáâãäèéêëìíîïòóôõöùúûüýAEIOUYÆØÅÀÁÂÃÄÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝ"
terminator="\.\?\:\!\|"
# quots = "\x93\x94\"\'\«\»"
quots = "\x93\x94\"\«\»"
parantes = "\(\)"
quotsParantes = quots + parantes
stroke = "-\xB7\x95"
remove = "\xA0"
romartalU = 'IVXLCDM'
romartalL = 'ivxlcdm'

SAMSET_LEKS_WEIGHT = 0.75
TAG_LINE = '\t"{}" {}\n'

spesialTab = {}
spesialTabMin = float('inf')
spesialTabMax = float('-inf')
ikkjeTerminerForkMin = float('inf')
ikkjeTerminerForkMax = float('-inf')
ikkjeTerminerFork = {}
spesialTittel = []

if SPRAAK == "bm":
    from fullform_bm import fullformHash
    from root_bm import rootHash
    from compounds_bm import compoundHash
elif SPRAAK == "nn":
    from fullform_nn import fullformHash
    from root_nn import rootHash
    from compounds_nn import compoundHash
else:
    assert False, 'Ukjent språk ' + SPRAAK

if UTFIL is not None:
    print("\n", omTagger, "\n")
    print("Programnamn:            " + PROG)
    print("Språkkode:              " + SPRAAK)
    print("Loggfil:                " + LOGGFIL)
    print("Utfil:                  " + UTFIL)
    if PERIODEFIL is not None:
        print("Perioder:               " + PERIODEFIL)
    print("")

logging.basicConfig(filename=LOGGFIL, filemode='w')
if UTFIL is not None:
    tag_utfil = open(UTFIL, "w", encoding="utf-8") # FIXME: with open ... as
else:
    tag_utfil = sys.stdout

if PERIODEFIL is not None:
    tag_periodefil = open(PERIODEFIL, "w")

####################################
#
# Functions
#
####################################
# Shortcut for poor man's templates with global variables,
# compatible with older versions of Python
def q(string):
    return string.format(**globals())
####################################
def allcap2lower(string):
   return string.lower()
####################################
def initcap2lower(string):
    return re.sub(r'^.', lambda m: m.group(0).lower(), string)
#########################################
def stor2stjerne(word):
    # Rutina bytter ut alle store bokstaver med stjerne og liten bokstav

    #word = re.sub(q(r'([{lettersla}])'), r'*\1', word)
    #word = allcap2lower(word)
    return word
####################################
def initDB():
    # Les data inn i spesialtabellane
    # (forkortingar, forkortingar som ser ut som ord med punktum etter, titlar, symboler, uttrykk)
    # Rutinane endrar følgande globale variable:
    #    spesialTabMin
    #    spesialTabMax
    #    spesialTab
    #    ikkjeTerminerForkMin
    #    ikkjeTerminerForkMax
    #    ikkjeTerminerFork
    #    spesialTittel
    global spesialTabMin, spesialTabMax, ikkjeTerminerForkMin, ikkjeTerminerForkMax
    for net_type in ["abbreviations", "expressions", "symbols", "titles", "word-like-abbreviations"]:
        nets_dir = DIR + '/data'
        nets_spraak = 'nny' if SPRAAK == 'nn' else 'nbo'
        with open("{nets_dir}/{nets_spraak}-{net_type}.txt".format(**vars()), "r", encoding="utf-8") as db:
            for linje in db:
                linje = linje.rstrip("\n")
                felt = linje.split(':')
                oppslag, grunnform, tag = felt
                oppslag = re.sub(r'^\s+', '', oppslag)
                oppslag = re.sub(r'\s+$', '', oppslag)
                grunnform = re.sub(r'^\s+', '', grunnform)
                grunnform = re.sub(r'\s+$', '', grunnform)
                grunnform = stor2stjerne(grunnform)
                spesialTabKey = '%d#%s ' % (len(oppslag)+1, oppslag)
                spesialTab[spesialTabKey] = (spesialTab.get(spesialTabKey, '') +
                                             '\t"{grunnform}" {tag}\n'.format(**vars()))
                if len(oppslag) < spesialTabMin:
                    spesialTabMin = len(oppslag)
                if len(oppslag) > spesialTabMax:
                    spesialTabMax = len(oppslag)

                if net_type == "abbreviations" and oppslag.endswith('.'): # Dersom forkortinga endar med punktum
                    oppslag = " " + oppslag
                    ikkjeTerminerForkKey = '%d#%s' % (len(oppslag), oppslag)
                    ikkjeTerminerFork[ikkjeTerminerForkKey] = \
                        (ikkjeTerminerFork.get(ikkjeTerminerForkKey, '') + oppslag)
                    if len(oppslag) < ikkjeTerminerForkMin:
                        ikkjeTerminerForkMin = len(oppslag)
                    if len(oppslag) > ikkjeTerminerForkMax:
                        ikkjeTerminerForkMax = len(oppslag)
                if net_type == "titles" and oppslag.endswith('.'): # Dersom tittel endar med punktum
                    oppslag = re.sub(r'(\W)', r'\\\1', oppslag)
                    spesialTittel.insert(0, oppslag)
####################################
def registrerStatistikk():
    # Rutina oppdaterer ein del globale variable, og skriv eventuelt ut
    # forloepsindikator
    # Rutina må kallast ein gong for kvart tagga ord

    global ordTellar, grenseTellar
    ordTellar += 1
    if UTFIL is not None:
        grenseTellar += 1
        if (time.time() - mellomTidStart) > 30:
            mellomTidSlutt = time.time()
            print("%d ord tagget, %.0f ord pr sekund" %
                  (ordTellar, grenseTellar/(mellomTidSlutt-mellomTidStart)))
            mellomTidStart = time.time()
            grenseTellar = 0
####################################
def erGenitiv(oppslag, tag):
    # Returnerer modifisert tag dersom oppslagsordet kan ta genitiv.
    # Verb i imperativsform og konjunksjoner kan ikkje ta genitiv

    resultat = None
    unwantedPOS = re.search(r'(verb.*imp)|(konj)|(pron)|(interj)|(prep)', tag)
    alreadyGenitive = re.search(r' %s ' % re.escape(GEN), tag)
    if tag != '' and not unwantedPOS and not alreadyGenitive:
        resultat = "%s %s" % (tag, GEN)
    return resultat
####################################
def databaseSearch(key):
    tag = ''

    if key in fullformHash:
        for funne in fullformHash[key].split("\n\t"):
            funne = re.sub(r'^\s*', '', funne)
            funne = re.sub(r'\s*$', '', funne)
            m = re.search(r'"(.*)"', funne)
            stjerneMarkert = stor2stjerne(m.group(1))
            funne = re.sub(r'^"(.*)"', '"{}"'.format(stjerneMarkert), funne)
            if stjerneMarkert in compoundHash:
                funne = re.sub(r'$', ' samset-leks', funne, flags=re.MULTILINE)
            tag += "\t" + funne + "\n"

    genKey = finnGenitivRot(key)
    if genKey and genKey in fullformHash:
        for funne in fullformHash[genKey].split("\n\t"):
            funne = re.sub(r'^\s*', '', funne)
            funne = re.sub(r'\s*$', '', funne)
            m = re.search(r'"(.*)"', funne)
            stjerneMarkert = stor2stjerne(m.group(1))
            funne = re.sub(r'^"(.*)"', '"{}"'.format(stjerneMarkert), funne)
            funne = erGenitiv(genKey, funne)
#            if stjerneMarkert in compoundHash:
#                funne = re.sub(r'$', ' samset-leks', funne, flags=re.MULTILINE)
            if funne:
                tag += "\t" + funne + "\n"

    return tag
####################################
def sok(key):
    if __debug__: logging.debug('sok(%(key)s)', vars())
    res = ''

    if key != '':
        res = databaseSearch(key)

    if not res:
        # Delete non-letter at the end
        key_rstrip = re.sub(q(r"[^'{letters}\d]+$"), '', key)
        if key_rstrip and key_rstrip != key:
            res = databaseSearch(key_rstrip)

    if not res:
        # Delete non-letter at the start
        key_lstrip = re.sub(q(r"^[^{letters}\d]+"), '', key)
        if key_lstrip and key_lstrip != key:
            if __debug__: logging.debug('databaseSearch(%(key_lstrip)s)', vars())
            res = databaseSearch(key_lstrip)

    return res
####################################
def konverterSkilleteikn(periode):
    konvertertPeriode = ''
    periodeDeltPaaSGML = re.split(r'(<.*?>)', periode)

    for periodeDel in periodeDeltPaaSGML:
        if not re.search(r'^<.*>$', periodeDel): # ikkje konverter innsiden av SGML-taggene
            # Konverter alle skilleteikn
            # legg inn ein blank foer og etter teiknet for aa sikre
            # at teiknet vert rekna for eit ord

            periodeDel = re.sub(q(r'([^$])(\.{{2,20}})([{quotsParantes}]*)'), r'\1 $\2\3 ', periodeDel)
            periodeDel = re.sub(q(r'([.|][{quotsParantes}]*)$'), r' $\1 ', periodeDel)
            periodeDel = re.sub(q(r'([?:!][{quotsParantes}]*)'), r' $\1 ', periodeDel)
            periodeDel = re.sub(q(r'([,;][{quotsParantes}]*)\s'), r' $\1 ', periodeDel)
            periodeDel = re.sub(q(r'\s--([{quotsParantes}]*)\s|^--([{quotsParantes}]*)'), r' $--\1 ', periodeDel)
            periodeDel = re.sub(q(r'\s([{stroke}][{quotsParantes}]*)\s|^([{stroke}][{quotsParantes}]*)'), r' $\1\2 ', periodeDel)
            periodeDel = re.sub(q(r'([()][{quots}]*)'), r' $\1 ', periodeDel)

            # Ta vare paa teikn som kan vere genitiv-apostrof
            periodeDel = re.sub(q(r"(s|z|sch|sh|sj|x|c)(')(s?)"), r'\1<MIDL GENITIV APOSTROF>\3', periodeDel)
            periodeDel = re.sub(q(r"([{letters}])'([{letters}])"), r'\1<MIDL GENITIV APOSTROF>\2', periodeDel)
            periodeDel = re.sub(q(r'([{quots}])([^{quots}\s]+)([{quots}])'), r'<HERMETEIKNMIDL\1> \2<HERMETEIKNMIDL\3> ', periodeDel)
            periodeDel = re.sub(q(r'([{quots}])'), r' $\1 ', periodeDel)
            periodeDel = re.sub(q(r'<HERMETEIKNMIDL \$([{quots}]) > '), r'\1', periodeDel)
            periodeDel = re.sub(r'<MIDL GENITIV APOSTROF>', "'", periodeDel)
        konvertertPeriode += periodeDel

    return konvertertPeriode
####################################
def sjekkNamn(key, sterkSjekk=False):

    # Rutina sjekker om foerste argumentet er eit namn.
    # Dersom andre argument er definert, krev rutina aa finne
    # foerste argumentet definert i basen med eigenskapen "prop".
    # Dersom andre argument ikkje er definert, vil rutina godta
    # foerste argument som eit namn ogsaa dersom det ikkje finns
    # i databasen.

    # Rutina vil ogsaa proeve diverse variantar med og utan bindestrek

    smallkey = re.sub(q(r'[{lettersla}]'), lambda m: m.group(0).lower(), key)
    erNamn = False

    # Proev foerst med eventuell bindestrek
    tag = databaseSearch(key) + databaseSearch(smallkey)
    if (tag == "" and not sterkSjekk) or re.search(r'\bprop\b', tag):
        erNamn = True

    # Proev saa utan alle bindestrekar
    if not erNamn:
       key = key.replace('-', '')           # Fjern bindestrek
       smallkey = smallkey.replace('-', '') # Fjern bindestrek
       tag = databaseSearch(key) + databaseSearch(smallkey)
       if (tag == "" and not sterkSjekk) or re.search(r'\bprop\b', tag):
           erNamn = True

    return erNamn
####################################
def gaaGjennomPeriodeElementer(periode, inputOK, nestePeriode, periodeFullstendig):
    # global: periode (rw), inputOK (ro), nestePeriode (rw)
    # my (outside the loop): periodeElementer, muligPeriode, periodeFullstendig, needMoreData
    # my (inside the loop): muligReinPeriode, restAvMulig, erPeriodeSlutt, nesteOrd

    # Del opp det vi har i sine einskilde element
    periodeElementer = re.split(q(r'([{letterssm}\d{specLetters}]|[{letters}\d{specLetters}]\s*[{lettersla}])([{quotsParantes}]*[{terminator}][{quotsParantes}]*\s+[{quotsParantes}]*[{stroke}{lettersla}\d{specLetters}])'), periode)

    muligPeriode = ""
    needMoreData = len(periodeElementer) <= 1
    while len(periodeElementer) > 1 or not inputOK:
        muligPeriode += ''.join(periodeElementer[0:3])
        periodeElementer = periodeElementer[3:]
        m = re.search(q(r'(.*([{letterssm}\d{specLetters}]|[{letters}\d{specLetters}]\s*[{lettersla}])[{quotsParantes}]*[{terminator}][{quotsParantes}]*)\s+([{quotsParantes}]*.)$'), muligPeriode)

        needMoreData = len(periodeElementer) <= 1
        muligReinPeriode = None
        restAvMulig = None
        if m:
            muligReinPeriode = m.group(1)
            restAvMulig = m.group(3)

        if not inputOK and muligReinPeriode is None:
            m = re.search(q(r'(.*([{letterssm}\d{specLetters}]|[{letters}\d{specLetters}]\s*[{lettersla}])[{quotsParantes}]*[{terminator}][{quotsParantes}]*)\s*$'), muligPeriode)
            needMoreData = len(periodeElementer) <= 1 # FIXME: not needed?
            muligReinPeriode = m.group(1)
            restAvMulig = ""

        # Sjekk om verkeleg periode
        erPeriodeSlutt = True

        # Les neste ord. Trengs for å avgjere periodeslutt
        # Eit ord kan vere samasett av to periodeelement
        nesteOrd = restAvMulig + ''.join(periodeElementer[0:2])
        nesteOrd = re.sub(q(r'\s*([^\s$terminator]+).*'), r'\1', nesteOrd)


        # Sjekk om siste del av mulig periode er ei forkorting
        # som ikkje terminerer periode utan at neste ord
        # startar med stor bokstav, og ikkje er eit namn

        for count in range(ikkjeTerminerForkMax, ikkjeTerminerForkMin-1, -1):
            if count > len(muligReinPeriode)+1:
                continue

            if count == len(muligReinPeriode)+1:
                muligReinPeriodeLower = initcap2lower(muligReinPeriode)
                muligReinPeriodeLower = ' ' + muligReinPeriodeLower

                ikkjeTerminerForkKey = '%d#%s' % (count, muligReinPeriodeLower[len(muligReinPeriodeLower)-count:])
                if __debug__: logging.debug('ikkjeTerminerFork.get1(%(ikkjeTerminerForkKey)s)', vars())
                if ikkjeTerminerFork.get(ikkjeTerminerForkKey):
                    if __debug__: logging.debug(' == True!')
                    erNamn = sjekkNamn(nesteOrd)
                    if erNamn:
                        erPeriodeSlutt = False
                        break
                    else:
                        if __debug__: logging.debug('Legg på terminering')
                        muligReinPeriode += ' .' # Legg paa terminering

            sjekkFork = muligReinPeriode[len(muligReinPeriode)-count:]
            sjekkFork = re.sub(q(r'^[{quotsParantes}]'), ' ', sjekkFork)
            if __debug__: logging.debug('ikkjeTerminerFork.get2(%(count)s#%(sjekkFork)s)', vars())
            if ikkjeTerminerFork.get('%d#%s' % (count, sjekkFork)):
                if __debug__: logging.debug(' == True!')
                erNamn = sjekkNamn(nesteOrd)

                # Sjekk om ordet framfor forkortinga er eit namn. I så fall er
                # sannsynlegvis også ordet etter eit namn
                if erNamn or re.search(q(r'[{lettersla}][{letterssm}]*\s+[{lettersla}]\.$'), muligReinPeriode):
                    erPeriodeSlutt = False
                    break
                else:
                    if __debug__: logging.debug('Legg på terminering')
                    muligReinPeriode += ' .' # Legg paa terminering

        # Sjekk om siste ordet i perioden kan vere ein tittel
        # Dersom det er ein tittel maa ein sjekke om ordet etter
        # tittelen kan vere eit namn. I saa fall er det ikkje
        # slutten på ein periode

        # Problem med tittel i starten av periode

        if erPeriodeSlutt:
            for tittel in spesialTittel:
                if (re.search(r' {tittel}$'.format(**vars()), muligReinPeriode) or
                    re.search(r'^{tittel}$'.format(**vars()), initcap2lower(muligReinPeriode))):

                    # Les neste ord.
                    # Eit ord kan vere samasett av to periodeelement
                    nesteOrd = restAvMulig + ''.join(periodeElementer[0:2])
                    nesteOrd = re.sub(q(r'\s*([^\s{terminator}]+).*'), r'\1', nesteOrd)

                    erNamn = sjekkNamn(nesteOrd)
                    if erNamn:
                        erPeriodeSlutt = False
                    else:
                        muligReinPeriode += " ." # Legg paa terminering
                    break

        if erPeriodeSlutt:
            # Start neste periode med dei overfloedige elementa
            periode = muligReinPeriode
            nestePeriode = restAvMulig + ''.join(periodeElementer)
            periodeElementer = []

            if __debug__:
                logging.debug("before konverterSkilleteikn\n")
                logging.debug("periode = '%(periode)s'", vars())
            periode = konverterSkilleteikn(periode)
            periodeFullstendig = True

            break

    if __debug__:
        logging.debug("end of gaaGjennomPeriodeElementer")
        logging.debug("periode = '%(periode)s'", vars())
    return (needMoreData, periode, nestePeriode, periodeFullstendig)
####################################
def sjekkInterjeksjon(key):
    # Rutine returnerer med tag dersom ordet bestaar av tre eller
    # fleire vokalar etter kvarandre

    if re.search(q(r'[{vocals}][{vocals}][{vocals}]'), key):
        return '\t"' + stor2stjerne(key) + '" interj\n'
    else:
        return None
####################################
def finnGenitivRot(key):
    # Rutina tar eit ord, og dersom dette kan vere ein genitiv,
    # vert rota returnert
    # - Ord som slutter paa -s kan vere genitiv
    # - Ord som sluttar paa -ss er ikkje genitiv
    # - Ord som sluttar paa -s' -z', -sch', -sh', -sj', -x', -c' er genitiv
    # - Verb + imperativ + sluttar paa -s er ikkje genitiv
    # - Ord som sluttar paa -'s er ikkje normert genitiv, men maa tolkast slik

    genRot = key

    if key != "":
        if not key.endswith('ss'): # -ss er ikkje genitiv
            genRot, sub_count = re.subn(r"(s|z|sch|sh|sj|x|c)'s?$", r'\1', genRot)
            if sub_count == 0:
                genRot, sub_count = re.subn(r"([^'])s$", r'\1', genRot)
                if sub_count == 0:
                    genRot = re.sub(r"'s$", '', genRot)

    if genRot != key:
        return genRot
    else:
        return None
####################################
def finnTal(periode, periodeStart):
    # Rutina sjekker om dei første elementa i perioden kan vere
    # eit tal av eit eller anna slag.
    # Rutina returnerer taggene dersom eit tal vert funne, og
    # antal teikn i perioden som utgjer talet
    # Rutina finn den lengste strengen som kan vere eit tal

    periode = re.sub(r'^\s*', '', periode)
    tagTekst = ''
    antal = 0

    # Eit tal bestaar av ein minus eller pluss, etterfulgt av
    # tal som kan vere inndelt i grupper paa tre siffer
    # adskilt av blank eller punktum, eventuelt
    # avslutta med komma og fleire desimaler etter komma.
    # Til slutt kan det foelge eit punktum eller eit prosentteikn.

    if __debug__: logging.debug('periode = <<<%(periode)s>>>', vars())
    m = re.search(r'^(([+-]?\d{1,3}[. ]?(\d{3,3}[. ]?)*(,\d*)?[.%]?)([/-][+-]?\d{1,3}[. ]?(\d{3,3}[. ]?)*(,\d*)?[.%]?)?) ', periode)
    if m:
        word = m.group(1)
        if __debug__: logging.debug('word = <<<%(word)s>>>', vars())
        antal = len(word)+1
        if word.endswith('.'):
            tagTekst += TAG_LINE.format(word, ADJ_ORDEN)
        else:
            tag = '{} {}'.format(DET_KVANT, EINTAL if word == '1' else FLEIRTAL)
            tagTekst += TAG_LINE.format(word, tag)

    # Eit tal kan også vere eit spesialtall med punktum
    # som desimalskille
    m = re.search(r'^((\d+\.)*(\d+\.?))\s', periode)
    if m:
        word = m.group(1)
        if (len(word)+1) > antal:
            tagTekst = TAG_LINE.format(word, DET_KVANT)
            antal = len(word)+1
#        elif len(word)+1 == antal:
#            tagTekst += TAG_LINE.format(word, DET_KVANT)

    # Eit tal kan også vere eit flatemål, ol.
    m = re.search(r'^((\d+[xX]*)+)\s', periode)
    if m:
        word = m.group(1)
        if len(word)+1 > antal:
            tagTekst = TAG_LINE.format(word, DET_KVANT)
            antal = len(word)+1
#        elif len(word)+1 == antal:
#            tagTekst += TAG_LINE.format(word, DET_KVANT)

    # Eit tal kan også vere eit blanda heiltal og brøk
    m = re.search(r'^(\d*\s+\d+\s*/\s*\d+)\s', periode)
    if m:
        word = m.group(1)
        if len(word)+1 > antal:
            tagTekst = TAG_LINE.format(word, DET_KVANT)
            antal = len(word)+1
#        elif len(word)+1 == antal:
#            tagTekst += TAG_LINE.format(word, DET_KVANT)

    # Ein dato bestaar av grupper paa eit, to eller fire siffer,
    # skilt med skraastrek, bindestrek, blank eller punktum
    # Sjekk forst typen dd-mm-åååå
    m = re.search(r'^((\d{1,2})[./ -](\d{1,2})([./ -]\d{2,4})?)', periode)
    if m:
        word = m.group(1)
        if int(m.group(2)) > 0 and int(m.group(2)) <= 31 and int(m.group(3)) > 0 and int(m.group(3)) <= 12:
            if len(word)+1 > antal:
                tagTekst = TAG_LINE.format(word, SUBST_DATO)
                antal = len(word)+1
            elif len(word)+1 == antal:
                tagTekst += TAG_LINE.format(word, SUBST_DATO)

    # Sjekk saa åååå-mm-dd
    m = re.search(r'^(\d{2,4}[./ -](\d{1,2})[./ -](\d{1,2}))', periode)
    if m:
        word = m.group(1)
        if int(m.group(2)) > 0 and int(m.group(2)) <= 31 and int(m.group(3)) > 0 and int(m.group(3)) <= 12:
            if len(word)+1 > antal:
                tagTekst = TAG_LINE.format(word, SUBST_DATO)
                antal = len(word)+1
            elif len(word)+1 == antal:
                tagTekst += TAG_LINE.format(word, SUBST_DATO)

    # Eit klokkeslett bestaar av fire siffer, med punktum mellom
    m = re.search(r'^((\d{1,2})\.(\d\d))', periode)
    if m:
        word = m.group(1)
        if int(m.group(2)) >= 0 and int(m.group(2)) < 24 and int(m.group(3)) >= 0 and int(m.group(3)) < 60:
            if len(word)+1 > antal:
                tagTekst = TAG_LINE.format(word, SUBST_KLOKKE)
                antal = len(word)+1
            elif len(word)+1 == antal:
                tagTekst += TAG_LINE.format(word, SUBST_KLOKKE)

    # Eit beløp bestaar av siffer med punktum mellom, og avslutta med ,-
    m = re.search(r'^(\d{1,3}[. ]?(\d{3,3}[. ]?)*,-)', periode)
    if m:
        word = m.group(1)
        if len(word)+1 > antal:
            tagTekst = TAG_LINE.format(word, DET_BELOP)
            antal = len(word)+1
        elif len(word)+1 == antal:
            tagTekst += TAG_LINE(word, DET_BELOP)

    # Eit romartal består av I, V, X, L, C, D, M
    m = re.search(q(r'^([{romartalU}][{romartalU}]+)\s'), periode)
    if m:
        word = m.group(1)
        if len(word)+1 > antal:
            antal = len(word)+1
            tagTekst = TAG_LINE.format(word, DET_ROMER)
        elif len(word)+1 == antal:
            tagTekst += TAG_LINE.format(word, DET_ROMER)

    # I starten av ein periode kan romartal betså av små bokstavar,
    # og punktum eller parantes
    if periodeStart:
        m = re.search(q(r'^([{romartalL}]+\s*\$[.)])\s'), periode)
        if m:
            word = m.group(1)
            if len(word)+1 > antal:
                antal = len(word)+1
                word = re.sub(r'\s*\$([.)])$', r'\1', word)
                tagTekst = TAG_LINE.format(word, DET_ROMER)
            elif len(word)+1 == antal:
                word = re.sub(r'\s*\$([.)])$', r'\1', word)
                tagTekst += TAG_LINE.format(word, DET_ROMER)

    return (tagTekst, antal)
####################################
def finnUttrykk(periode, periodeStart):
   # Rutina sjekker om dei første elementa i perioden kan vere
   # eit uttrykk
   # Rutina returnerer taggene dersom eit uttrykk vert funne, og
   # antal teikn i perioden som utgjer uttrykket
   # Rutina finn den lengste strengen som kan vere eit uttrykk

    tagTekst = ''
    periodeLiten = initcap2lower(periode)

    for antal in range(spesialTabMax, spesialTabMin-1, -1):
        if antal > len(periode):
            continue

        periode = re.sub(r'^\s*', '', periode)
        sjekkTekst = '%d#%s' % (antal, periode[0:antal])
        tagTekst += spesialTab.get(sjekkTekst, '')
        if periodeStart:
            sjekkTekst = '%d#%s' % (antal, periodeLiten[0:antal])
            tagTekst += spesialTab.get(sjekkTekst, '')
        if tagTekst != '':
            break
    return (tagTekst, antal)
####################################
def finnUforstaeleg(periode, periodeStart):
    # Rutina sjekker om dei første elementa i perioden kan vere
    # uforståelege ord i hermeteikn
    # Rutina returnerer "subst prop" dersom teksten er innhylla i
    # hermeteikn, og det er umogleg å tolke dei fleste orda.

    ukjent = 0
    kjent = 0
    antal = 0
    tagTekst = ''

    m = re.search(r'(^\$" ([^($")]*) \$")', periode)
    if m:
        sjekkTekst = m.group(1)
        antal = len(sjekkTekst)+1
        omhylla = m.group(2)
        if periodeStart:
            omhylla = initcap2lower(omhylla)
        elementer = re.split(r'\s+', omhylla.strip())
        for element in elementer:
            tagTekst = sok(element) # Sjekk om ordet finns
            if tagTekst:
                kjent += 1
            else:
                ukjent += 1
        if ukjent > kjent:
            tagTekst = TAG_LINE.format(omhylla, SUBST_PROP)
        else:
            tagTekst = ''
            antal = 0

    return (tagTekst, antal)
####################################
# Samansetningsmodul

def sokEtterledd(etterledd, sokOrd):
    m = re.search(r'(.*){}$'.format(re.escape(etterledd)), sokOrd)
    forledd = stor2stjerne(m.group(1))
    if etterledd.startswith('-'):
         etterledd = etterledd[1:]
         forledd += '-'
    if __debug__:
        logging.debug("forledd = '%(forledd)s'", vars())
        logging.debug("etterledd = '%(etterledd)s'", vars())
        logging.debug("sokOrd = '%(sokOrd)s'", vars())
    tagTekstOrig = ''
    if not forledd.endswith('-'):
        tagTekstOrig = sok('-' + etterledd)
        # Ta bort bindestrek fra evnt. suffiks
        tagTekstOrig = re.sub(r'(\s*")-', r'\1', tagTekstOrig, flags=re.MULTILINE)
        tagTekstOrig = tagTekstOrig.rstrip()
        tagTekstOrig += "\n"
    tagTekstOrig += sok(etterledd)

    tagTekst = ''
    for grammatikk in re.split(r'\n\t', tagTekstOrig):
        grammatikk = grammatikk.strip()
        grammatikk = re.sub(r'^"(.*)"', r'"{}\1"'.format(forledd), grammatikk)
        wantedPOS = re.search(r'^".*"\s+(subst|verb(?! imp)|adj|det\s+kvant\s+fl|prep|sbu|adv)\b', grammatikk)
        unwantedPOS = re.search(r'^".*"\s+verb\b.*\bperf-part\b', grammatikk)
        if wantedPOS and not unwantedPOS:
            if tagTekst == "":
               tagTekst += "\t"
            else:
               tagTekst += "\n\t"
            grammatikk = re.sub(r'\s+samset-leks\b', '', grammatikk)
            tagTekst += grammatikk + " samset-analyse"

    return tagTekst

def rootOrdklasser(root):
    result = databaseSearch(root)
    rootTags = [resultLine
                for resultLine in result.split("\n")
                if re.search('"{}"'.format(re.escape(root)), resultLine, flags=re.I)]
    if not rootTags:
        rootTags.append('andre')
    rootWordClasses = map(lambda s: re.sub(r'^\s*".*?"\s+(\S+).*$', r'\1', s), rootTags)
    return list(rootWordClasses)

def alleOrdklasser(root):
    result = databaseSearch(root)
    tags = result.rstrip("\n").split("\n")
    wordClasses = map(lambda s: re.sub(r'^\s*".*?"\s+(\S+).*$', r'\1', s), tags)
    return wordClasses

def analyserForledd(forledd):
    rootOrdklasseList = []
    normalisertForledd = forledd

    if forledd in rootHash:
        normalisertForledd = forledd
    elif initcap2lower(forledd) in rootHash:
        normalisertForledd = initcap2lower(forledd)
    elif allcap2lower(forledd) in rootHash:
        normalisertForledd = allcap2lower(forledd)

    rootVal = rootHash.get(normalisertForledd)
    if rootVal:
        numLedd, *rootOrdklasseList = rootVal

    rootOrdklasseList.extend(rootOrdklasser(normalisertForledd))
    rootOrdklasseList = [pos for pos in rootOrdklasseList
                             if pos != 'interj' and pos != 'symb']

    if forledd in compoundHash:
        numLedd = compoundHash[forledd][0] * SAMSET_LEKS_WEIGHT
        if numLedd < 1:
            numLedd = 1

    if re.search(r'^\d+-$', forledd):
        return [1, 'num']
    if re.search(q(r'^[{lettersla}].*-$'), forledd):
        return [1, 'subst']
    if re.search(r'^[^$\s]+-\s+(og|eller)(/(og|eller))?\s+$', forledd):
        return [1, 'koord']

    if len(forledd) <= 1 and forledd != "u":
        return []
    if forledd in rootHash and not rootHash[forledd]:
        return []

    if rootVal and rootOrdklasseList:
        if __debug__:
            logging.debug('forledd=%(forledd)s, numLedd = %(numLedd)s, ' +
                          'rootOrdklasseList=%(rootOrdklasseList)s',
                          vars())
        rootHash[forledd] = [numLedd, *set(rootOrdklasseList)]
        return rootHash[forledd]

    resultater = []
    for i in range(1, len(forledd)):
        ledd1 = forledd[0:i]
        ledd2 = forledd[i:]
        ledd1kort = forledd[0:i-1]

        ledd1Analyse = analyserForledd(ledd1)
        ledd2Analyse = analyserForledd(ledd2)
        ledd1OK = ledd1Analyse and ledd1Analyse[0]
        ledd2OK = ledd2Analyse and ledd2Analyse[0]

        if ledd1OK and ledd2OK:
            if __debug__:
                logging.debug('%(ledd1)s + %(ledd2)s', vars())
                logging.debug('%(ledd1Analyse)s', vars())
                logging.debug('%(ledd2Analyse)s', vars())

            numLedd = ledd1Analyse[0] + ledd2Analyse[0]
            rootOrdklasseList = rootOrdklasser(ledd2)
            if __debug__:
                logging.debug("rootHash[%(forledd)s] = [%(numLedd)s, %(rootOrdklasseList)s]", vars())
            resultater.append([numLedd, *rootOrdklasseList])

        ledd1kortAnalyse = analyserForledd(ledd1kort)
        ledd1kortOK = ledd1kortAnalyse and ledd1kortAnalyse[0]
        fugeFormativ = forledd[i-1]
        fugeFormativOK = re.search(r'^[es-]$', fugeFormativ)

        if ledd1kortOK and fugeFormativOK and ledd2OK:
            if __debug__:
                logging.debug("%(ledd1kort)s + fuge + %(ledd2)s", vars())
                logging.debug("%(ledd1kortAnalyse)s", vars())
                logging.debug("%(ledd2Analyse)s", vars())

            numLedd = ledd1kortAnalyse[0] + ledd2Analyse[0]
            resultater.append([numLedd, *rootOrdklasser(ledd2)])

    if resultater:
        resultater.sort(key=lambda result: result[0])
        ordklasser = sum((result[1:] for result in resultater
                                     if result[0] == resultater[0][0]),
                         [])
        if __debug__: logging.debug('ordklasser = %(ordklasser)s', vars())
        retVal = [resultater[0][0], *ordklasser]
        if __debug__: logging.debug('retVal = %(retVal)s', vars())
        rootHash[forledd] = retVal
        return retVal

    if __debug__: logging.debug("didn't work after all")
    rootHash[forledd] = []
    return []

def databaseSearchForSuffixOrWord(string):
    suffixResult = databaseSearch('-' + string)
    if suffixResult:
        return suffixResult
    else:
        return databaseSearch(string)

def analyserForleddOgEtterledd(sokOrd):
    resultater = []
    for i in range(1, len(sokOrd)):
        forledd = sokOrd[0:i]
        etterledd = sokOrd[i:]
        kortEtterledd = sokOrd[i+1:]
        if __debug__: logging.debug("forledd+etterledd = %(forledd)s + %(etterledd)s", vars())
        forleddAnalyse = analyserForledd(forledd)
        if __debug__: logging.debug("forleddAnalyse = %(forleddAnalyse)s", vars())
        if not (forleddAnalyse and forleddAnalyse[0]):
            continue
        etterleddOK = len(etterledd) > 1 and databaseSearchForSuffixOrWord(etterledd)
        kortEtterleddOK = (re.search(r'^[es-]', etterledd) and len(kortEtterledd) > 1 and
                           databaseSearchForSuffixOrWord(kortEtterledd))

        if etterledd.startswith('s') and kortEtterleddOK:
            # Lexical compounding is preferable to compounding with epenthetic phones.
            lengreForleddAnalyse = analyserForledd(forledd + 's')
            if __debug__:
                logging.debug('lengreForledd = %(forledd)ss', vars())
                logging.debug('lengreForleddAnalyse = %(lengreForleddAnalyse)s', vars())
            if lengreForleddAnalyse and lengreForleddAnalyse[0] == 1:
                continue # FIXME: wouldn't "kortEtterleddOK = False" be better here?
            # Epenthetic -s- can only follow noun stems.
            if 'subst' not in forleddAnalyse:
                kortEtterleddOK = False
            # Epenthetic -s- cannot occur after a sibilant or a final consonant sequence containing a sibilant (Akø 1989)
            forleddFinalSibilant = re.search(q(r's[{konsonanter}]*$'), forledd)
            # ... except when the consonant sequence belongs to a compound
            if forleddFinalSibilant and forleddAnalyse[0] == 1:
                kortEtterleddOK = False

        if etterledd.startswith('e') and kortEtterleddOK:
            # Epenthetic -e- can only be attached to a stem that is monosyllabic.
            forleddMonosyllabic = re.search(q(r'^[{konsonanter}]*[^{konsonanter}]+[{konsonanter}]*$'),
                                            forledd, flags=re.I)
            # Other possible stems can be prior to the stem preceding the -e-,
            # if they do not form a compound with that stem. (FIXME: not implemented)

            # "Flyktning" is apparently an exception (cf. "flyktningerett").
            if not forleddMonosyllabic and forledd != 'flyktning':
                kortEtterleddOK = False

        if etterleddOK and kortEtterleddOK:
            if __debug__: logging.debug('sokEtterledd1(%(etterledd)s, %(sokOrd)s)', vars())
            etterleddTagger = sokEtterledd(etterledd, sokOrd)
            verbalEtterledd = re.search(r'\bverb\b', etterleddTagger)
            substantiviskEtterledd = re.search(r'\bsubst\b', etterleddTagger)
            if verbalEtterledd and not substantiviskEtterledd and etterledd.startswith('s'):
                # Epenthetic -s- is preferred to lexical compounding
                # when the -s- can be ambiguous between epenthetic use
                # and the first letter of a verbal last member.
                etterleddOK = False
            elif forleddAnalyse[0] > 1 and etterledd.startswith('s'):
                # Epenthetic -s- is preferred to lexical compounding when the first member is itself a compound.
                etterleddOK = False
            else:
                # Lexical compounding is preferable to compounding
                # with epenthetic phones.
                kortEtterleddOK = False

        if forleddAnalyse and forleddAnalyse[0] and (etterleddOK or kortEtterleddOK):
            minEtterledd = etterledd if etterleddOK else kortEtterledd
            if __debug__: logging.debug("sokEtterledd2(%(minEtterledd)s, %(sokOrd)s)", vars())
            tagger = sokEtterledd(minEtterledd, sokOrd)

            if tagger:
                if __debug__: logging.debug("OK!")
                etterleddRoots = set()
                for m in re.finditer(r'^\s*"(.*?)"\s+', tagger, flags=re.MULTILINE):
                    etterleddRoot = m.group(1)
                    if etterleddOK:
                        etterleddRoot = re.sub(r'^{}'.format(re.escape(forledd)), '', etterleddRoot)
                    elif kortEtterleddOK:
                        etterleddRoot = re.sub(r'^{}.'.format(re.escape(forledd)), '', etterleddRoot)
                    else:
                        assert False, '!etterleddOK && !kortEtterleddOK'
                    etterleddRoots.add(etterleddRoot)
                if __debug__: logging.debug("etterleddRoots = %(etterleddRoots)s", vars())
                sortedEtterleddRoots = sorted(etterleddRoots, key=lambda k: compoundHash.get(k, [1])[0])
                numForledd = forleddAnalyse[0]
                if len(sortedEtterleddRoots) > 0:
                    numEtterledd = compoundHash.get(sortedEtterleddRoots[0], [1])[0] * SAMSET_LEKS_WEIGHT
                else:
                    numEtterledd = 1
                if __debug__:
                    logging.debug("numEtterledd = %(numEtterledd)s", vars())
                    logging.debug("sortedEtterleddRoots = %(sortedEtterleddRoots)s", vars())
                if numEtterledd < 1:
                    numEtterledd = 1
                # If two analyses are equal with respect to epenthesis
                # and part of speech, and one has a first member that
                # is itself a compound, then choose that one.
                if etterleddOK and numEtterledd > 1.5:
                    continue
                forleddOrdklasse = ", ".join(set(forleddAnalyse[1:]))
                etterleddOrdklasse = ", ".join(set(alleOrdklasser(minEtterledd)))
                if numForledd > 1:
                    tagger = re.sub(r'$', ' forledd-samset', tagger, flags=re.MULTILINE)
                if kortEtterleddOK and etterledd.startswith('s'):
                    tagger = re.sub(r'$', ' fuge-s', tagger, flags=re.MULTILINE)
                resultater += ([ numForledd+numEtterledd, minEtterledd,
                                 etterleddOrdklasse, tagLine ]
                               for tagLine in tagger.rstrip("\n").split("\n"))
                # If two analyses have the same number of members and
                # there is no epenthesis involved, choose the one, if
                # any, that is a noun.
                isNoun = re.search(r'^\s*".*"(\s*<.*?>)?\s+subst\b', tagger, flags=re.MULTILINE)
                if isNoun and not (kortEtterleddOK and etterledd.startswith('e')) and numEtterledd < 1.5:
                    if __debug__: logging.debug('break')
                    break
    return resultater

def analyserBareEtterledd(sokOrd):
    # If the first member is unknown, choose the analysis with the longest last member.
    resultater = []
    # Det er mange usannsylige sammensetninger med korte ord, så vi antar at
    # forleddet må ha minst 2 bokstaver, og etterleddet - minst 3 bokstaver
    for i in range(2, len(sokOrd)):
        etterledd = sokOrd[i:]
        if len(etterledd) > 2:
            searchResult = databaseSearchForSuffixOrWord(etterledd)
            if re.search(r'\b(subst|adj)\b', searchResult):
                if __debug__: logging.debug("sokEtterledd3(%(etterledd)s, %(sokOrd)s)", vars())
                tagger = sokEtterledd(etterledd, sokOrd)
                if tagger:
                    if etterledd in compoundHash:
                        numEtterledd = compoundHash[etterledd][0] * SAMSET_LEKS_WEIGHT
                    else:
                        numEtterledd = 1
                    if numEtterledd < 1:
                        numEtterledd = 1
                    etterleddOrdklasse = ", ".join(set(alleOrdklasser(etterledd)))
                    resultater += ([ numEtterledd+1, etterledd,
                                     etterleddOrdklasse, tagLine ]
                                   for tagLine in tagger.rstrip("\n").split("\n"))
                    break
    return resultater

def analyserSammensetning(sokOrd, periodeStart):
    resultTagTekst = ''
    resultater = analyserForleddOgEtterledd(sokOrd)

    # Det er ikke et egennavn, så prøv å matche bare etterleddet
    if not resultater and not periodeStart:
        resultater = analyserBareEtterledd(sokOrd)

    if resultater:
        # Choose the analysis (or analyses) with the fewest compound members
        sortedeResultater = sorted(resultater, key=lambda k: k[0])
        forleddSamsetFugeSResultater = [result for result in sortedeResultater
                                               if re.search(r'\bforledd-samset\b.*\bfuge-s\b',
                                                            result[3])]
        greppedeResultater = []
        if forleddSamsetFugeSResultater:
            greppedeResultater += (result for result in forleddSamsetFugeSResultater
                                          if result[0] == forleddSamsetFugeSResultater[0][0])
        greppedeResultater += (result for result in sortedeResultater
                                      if result[0] == sortedeResultater[0][0])
        resHash = defaultdict(list)
        for result in greppedeResultater:
            tekst = result[3]
            etterledd = result[1]
            tekst = re.sub(r'\s+fuge-s\b', '', tekst)
            tekst = re.sub(r'\s+forledd-samset\b', '', tekst)
            if COMPAT:
                resHash[tekst].append('')
            else:
                resHash[tekst].append("<+{}>".format(etterledd))
        for resultTekst in resHash.keys():
            resultTagTekst += "{} {}\n".format(resultTekst, ' '.join(resHash[resultTekst]))
        if __debug__: logging.debug('resultater: %(resultater)s', vars())
    return resultTagTekst
####################################
def abbrFeat(fult, forkortet, tt):
    return re.sub(r'<{}([^/>]*(/til)?)(/[^>]*)?>'.format(fult), r'{}\1'.format(forkortet),
                  tt, flags=re.IGNORECASE)

def uniq_prefix(lines):
    lines_uniq = list(set(lines))
    result = []
    for i in range(len(lines_uniq)):
        line = lines_uniq[i]
        lineRegex = re.sub(r'([()])', r'\\\1', line)
        otherLines = lines_uniq[0:i] + lines_uniq[i+1:]
        supersetLines = [otherLine for otherLine in otherLines
                                   if re.search(r'^{}\b(?!\sclb$)'.format(lineRegex),
                                                otherLine)]
        if not any(supersetLines):
            result.append(line)
    return result

def sort_feat(line, periodeStart):
    if __debug__: logging.debug('sort_feat(%(line)s, %(periodeStart)s)', vars())
    wordPattern = r'^\s*"(.*)"\s+'
    m = re.search(wordPattern, line)
    line = re.sub(wordPattern, '', line)
    word = m.group(1)
    feats = list(OrderedDict.fromkeys(re.split(r'\s+', line)))
    if SPRAAK == "bm":
        for suffix in suffixes:
            if re.search(r'\S+{}$'.format(re.escape(suffix)), word, flags=re.IGNORECASE):
                feats.append("<*{}>".format(suffix))
    startsWithCapitalLetter = re.search(q(r'^[{lettersla}]'), word)
    # FIXME: not sure what the condition for outputting <*> should be.
    # According to multi-tagger.lisp it should be something more like:
    # startsWithCapitalLetter and (not periodeStart or 'prop' in feats)
    addStar = (startsWithCapitalLetter and not periodeStart and
               ('prop' in feats or not 'fork' in feats))
    if addStar:
        feats.append("<*>")
    result = '\t"{}" '.format(word)
    if __debug__: logging.debug('feats = <<<%(feats)s>>>', vars())
    if SPRAAK == 'bm':
        result += ' '.join(sorted(feats, key=lambda k: feat_idx.get(k, float('inf'))))
    elif SPRAAK == 'nn':
        result += ' '.join(sorted(feats, key=lambda k: feat_idx_nn.get(k, float('inf'))))
    else:
        assert False, 'Ukjent språk'
    return result

def prepareTagTekst(tagTekst, periodeStart):
    tagTekst = abbrFeat("ditrans", "d", tagTekst)
    tagTekst = abbrFeat("intrans", "i", tagTekst)
    tagTekst = abbrFeat("kaus", "k", tagTekst)
    tagTekst = abbrFeat("nullv", "n", tagTekst)
    tagTekst = abbrFeat("part", "pa", tagTekst)
    tagTekst = abbrFeat("predik", "pr", tagTekst)
    tagTekst = abbrFeat("ref15", "rl15", tagTekst)
    tagTekst = abbrFeat("ref9", "rl9", tagTekst)
    tagTekst = abbrFeat("refl", "rl", tagTekst)
    tagTekst = abbrFeat("trans", "tr", tagTekst)
    tagTekst = abbrFeat("adv", "a", tagTekst)
    tagTekst = re.sub(r'^(\t".*".*)\ba\b', r'\1<adv>', tagTekst, flags=re.M | re.I)
    tagTekst = re.sub(r'^(\t".*".*)\s\@ADV\b', r'\1 @adv', tagTekst, flags=re.M)
    tagTekst = re.sub(r'^(\t".*".*)\s\@S-PRED\b', r'\1 @s-pred', tagTekst, flags=re.M)
    tagTekst = re.sub(r'^(\t".*".*)\s\@O-PRED\b', r'\1 @o-pred', tagTekst, flags=re.M)
    tagTekst = re.sub(r'^(\t".*".*)\s\@TITTEL\b', r'\1 @tittel', tagTekst, flags=re.M)
    tagTekst = re.sub(r'^(\t".*".*)\s\@INTERJ\b', r'\1 @interj', tagTekst, flags=re.M)
    tagTekst = re.sub(r'^(\t".*".*)\s\@DET>\b', r'\1 @det>', tagTekst, flags=re.M)
    tagTekst = re.sub(r'^(\t".*".*)\bCLB\b', r'\1clb', tagTekst, flags=re.M)
    tagTekst = re.sub(r'^(\t".*".*)\s+(normert|unormert|klammeform)\b', r'\1', tagTekst, flags=re.M | re.I)
    if __debug__: logging.debug('tagTekstBeforeSort = %(tagTekst)s', vars())
    tagTekst = ''.join(sort_feat(tagLine, periodeStart) + "\n"
                       for tagLine in tagTekst.rstrip("\n").split("\n"))
    if __debug__: logging.debug('tagTekstAfterSort = %(tagTekst)s', vars())

    nyTagTekst = tagTekst
    for m in re.finditer(r'^\s*"(.*)"\s+adj\b.*\b(nøyt|adv)\b', tagTekst, flags=re.M):
        baseForm = m.group(1)
        nyTagTekst = re.sub(r'^\s*"{}"\s+adv\b.*$'.format(baseForm), '', nyTagTekst, flags=re.M)
        nyTagTekst = re.sub(r'\n+', r'\n', nyTagTekst)
        nyTagTekst = re.sub(r'^\n', '', nyTagTekst)
    tagTekst = nyTagTekst

    if COMPAT:
        tagTekst = re.sub(r'^(\s*".*".*)\s+samset-leks\b', r'\1', tagTekst, flags=re.M)
        tagTekst = re.sub(r'^(\s*".*".*)\s+samset-analyse\b', r'\1 samset', tagTekst, flags=re.M)

    if not COMPAT:
        while True:
            tagTekst, subst_count = re.subn(r'^(\s*".*".*)\s+[a-z]+[0-9]+(/[a-z]+)?\b',
                                            r'\1', tagTekst, flags=re.M)
            if subst_count == 0:
                break

    if __debug__: logging.debug('tagTekstBefore = <<<%(tagTekst)s>>>', vars())
    tagTekst = "\n".join(sorted(uniq_prefix(tagTekst.rstrip("\n").split("\n")))) + "\n"
    if __debug__: logging.debug('tagTekstAfter = <<<%(tagTekst)s>>>', vars())
    return tagTekst

def printTag(word, wordOrig, tagTekst):
    wordWithoutDollar = re.sub(r'^\$(.)', r'\1', allcap2lower(word))
    wordOrigWithoutDollar = re.sub(r'^\$(.)', r'\1', wordOrig)
    wordOrigWithoutDollar = re.sub(r'&', r'&amp;', wordOrigWithoutDollar)
    if wordWithoutDollar != '':
        if re.search(r'^[^$\s]+-\s+(og|eller)(/(og|eller))?\s+\S+$', wordOrigWithoutDollar):
            splitWordOrigWithoutDollar = re.split(r'\s+', wordOrigWithoutDollar)
            splitWordWithoutDollar = re.split(r'\s+', wordWithoutDollar)
            for minWordOrig, minWord in zip(splitWordOrigWithoutDollar, splitWordWithoutDollar):
                if WXML:
                    print('<word>{minWordOrig}</word>'.format(**vars()), file=tag_utfil)
                if minWordOrig == 'og' or minWordOrig == 'eller':
                    print('"<{minWord}>"\n\t"{minWord}" konj'.format(**vars()), file=tag_utfil)
                else:
                    print('"<{minWord}>"\n{tagTekst}'.format(**vars()), end='', file=tag_utfil)
        else:
            if WXML:
                print("<word>{wordOrigWithoutDollar}</word>".format(**vars()), file=tag_utfil)
            print('"<{wordWithoutDollar}>"\n{tagTekst}'.format(**vars()), end='', file=tag_utfil)
####################################
def tagTekstSkille(word, periode):
    if re.search(r'\$\.{2,20}$', word):
        result = q('\t"$..." {CONSTsetningSlutt} {CONSTellipse}\n')
    elif re.search(r'\$\|$', word):
        result = q('\t"$|" {CONSTsetningSlutt} {CONSToverskrift}\n')
    elif re.search(r'\$\.$', word):
        result = q('\t"$." {CONSTsetningSlutt} {CONSTpunktum}\n')
    elif re.search(r'\$\,$', word):
        result = q('\t"$," {CONSTsetningSlutt} {CONSTkomma}\n\t"$," {CONSTkomma}\n')
    elif re.search(r'\$\!$', word):
        result = q('\t"$!" {CONSTsetningSlutt} {CONSTutrop}\n')
    elif re.search(r'\$\:$', word):
        result = q('\t"$:" {CONSTsetningSlutt} {CONSTkolon}\n')
    elif re.search(r'\$\;$', word):
        result = q('\t"$;" {CONSTsetningSlutt} {CONSTsemi}\n')
    elif re.search(r'\$\?$', word):
        result = q('\t"$?" {CONSTsetningSlutt} {CONSTspoersmaal}\n')
    elif re.search(r'\$\--$', word):
        result = q('\t"$--" {CONSTstrek}\n')
    elif re.search(q(r'\$[{stroke}]$'), word):
        result = q('\t"$-" {CONSTstrek}\n')
    elif re.search(q(r'\$([{quots}])$'), word):
        result = q('\t"$%s" {CONSTanfoersel}\n' % re.sub(r'^.*\$', '', word))
    elif re.search(r'\$\($', word):
        result = q('\t"$(" {CONSTparstart}\n')
    elif re.search(r'\$\)$', word):
        result = q('\t"$)" {CONSTparslutt}\n')
    else:
        result = ''

    if re.search(r'^\s*$', periode):
        result = re.sub(r'(.)$', r'\1 <<<', result, flags=re.MULTILINE)
    return result
####################################
def sokVarianter(sokOrd, periode, periodeStart, forrigeAnf):
    if __debug__:
        logging.debug('sokVarianter(%(sokOrd)s, %(periode)s, %(periodeStart)s, %(forrigeAnf)s', vars())
    tagTekst = ''
    wordLower = initcap2lower(sokOrd)
    wordAllLower = allcap2lower(sokOrd)

    # Soek etter ordet slik det er
    tagTekst += sok(sokOrd)

    # Periodestart eller foerste ord etter hermeteikn
    if (wordLower != sokOrd) and (periodeStart or forrigeAnf):
        tagTekst += sok(wordLower)

    # Periode paa slutten av ordet kan ha vaert tatt bort
    if re.search(r'^\s*\$\.', periode):
        tagTekst += sok(sokOrd + '.')

    # Meir enn ein stor bokstav i ordet
    if wordAllLower != wordLower and wordAllLower != sokOrd:
        tagTekst += sok(wordAllLower)

    # Berre ein stor bokstav
    if re.search(q(r'^[{lettersla}]$'), sokOrd):
        tagTekst += TAG_LINE.format(stor2stjerne(sokOrd), SUBST_PROP)
        if not periodeStart and not forrigeAnf:
            tagTekst += sok(wordAllLower)
        propHash[sokOrd] = True

    # Spesialbehandle apostroftilfeller
    if tagTekst == "":
        withoutApostrophe = sokOrd.translate(str.maketrans('ÓÉóé', 'OEoe'))
        if withoutApostrophe != sokOrd:
            tagTekst += sok(withoutApostrophe)
            if periodeStart or forrigeAnf:
                wordLower = initcap2lower(withoutApostrophe)
                wordAllLower = allcap2lower(withoutApostrophe)
                if wordLower != sokOrd:
                    tagTekst += sok(wordLower)
                if wordAllLower != wordLower and tagTekst == "":
                    tagTekst += sok(wordAllLower)
    return tagTekst
####################################
def taggPeriode(periode):
    global substProp, fuge, ukjent
    #Spesialbehamndling av samantrekningar
    periode = re.sub(q(r'(\s[{letters}]/)([{letters}]{{2}})'), r'\1 \2', periode)
    periodeStart = True
    forrigeAnf = False
    # FIXME: count=1 is compatible with Perl mtag, but looks like a bug
    periode = re.sub(r'\s+', ' ', periode.lstrip(), count=1)

    if PERIODEFIL is not None:
        print(periode + "\n", file=tag_periodefil)

    while periode != '':
        ferdig = False
        tagTekst = ''

        registrerStatistikk()

        # Ta bort eventuell SGML-tag i starten av perioden
        periodeSjekkstreng = periode.lstrip() # FIXME: lstrip not needed
        m = re.search(r'(^<.*?>)', periodeSjekkstreng)
        if m:
            word = m.group(1)
            count = len(word) + 1
            periode = periode[count:]
            if WXML:
                print(word, file=tag_utfil)
            continue # Sjekk neste element

        # Sjekk om dei foerste periodeelementa utgjer anten eit tal, eit
        # uttrykk eller uforståeleg tekst i hermeteikn

        tagTekstTal, lengdeTal = finnTal(periode, periodeStart)
        if __debug__:
            logging.debug('tagTekstTal = %(tagTekstTal)s, lengdeTal = %(lengdeTal)s', vars())
        if COMPAT:
            tagTekstUttrykk, lengdeUttrykk = finnUttrykk(periode, periodeStart)
            tagTekstUforstaeleg, lengdeUforstaeleg = finnUforstaeleg(periode, periodeStart)

        if not COMPAT or (lengdeTal >= lengdeUttrykk and lengdeTal >= lengdeUforstaeleg):
            if __debug__: logging.debug('going in')
            tagTekst += tagTekstTal
            count = lengdeTal

            # Må jukse litt med perioden her for å få uttrykket rett
            if re.search(r'\$[.)]\s$', periode[0:count]):
                periode = re.sub(r'\s\$', '', periode, count=1)
                count -= 2
        elif COMPAT:
            if lengdeUttrykk >= lengdeTal and lengdeUttrykk >= lengdeUforstaeleg:
                tagTekst += tagTekstUttrykk
                count = lengdeUttrykk
            elif lengdeUforstaeleg >= lengdeTal and lengdeUforstaeleg >= lengdeUttrykk:
                tagTekst += tagTekstUforstaeleg
                count = lengdeUforstaeleg

                # Må jukse litt med perioden her for å få uttrykket rett
                periode = re.sub(r'^\$" ([^($")]*) \$"', r'"\1" ', periode, count=1)
                count -= 4

        if tagTekst != '':
            word = periode[0:count-1]
            periode = periode[count:]
        else:
            ogEllerCompoundRegex = r'^([^$\s]+-\s+(og|eller)(/(og|eller))?\s+\S+)\s*'
            m = re.search(ogEllerCompoundRegex, periode)
            if m:
                word = m.group(1) # Plukk ut sammensetninger med og eller eller
                periode = re.sub(ogEllerCompoundRegex, '', periode)
            else:
                m = re.search(r'(\S*)\s*', periode)
                if m:
                    word = m.group(1)
                    periode = re.sub(r'(\S*)\s*', '', periode, count=1)
                else:
                    word = ''
        wordOrig = word

        # Sjekk om ordet er eit skilleteikn
        if not tagTekst:
            tagTekstSkilleStr = tagTekstSkille(word, periode)
            if tagTekstSkilleStr != "":
                if __debug__: logging.debug('ferdig = %(ferdig)s', vars())
                ferdig = True
            tagTekst += tagTekstSkilleStr

        # Soek i databasen etter ordet
        if not ferdig:
            word = word.strip() # FIXME: just strip one whitespace character at each side?
            # Fordi vi godtar hermeteikn rundt ord, må vi ta dei bort før søk
            sokOrd = re.sub(q(r'^[{quots}](.*)[{quots}]$'), r'\1', word)
#            sokOrd = re.sub(r"'([^s]+)", r'\1', sokOrd) # Dersom fnutt, og ikkje genitiv, ta bort

            tagTekst += sokVarianter(sokOrd, periode, periodeStart, forrigeAnf)

            # Vi har saa langt ikkje funne ordet
            if tagTekst == '':
                # Dersom ein er midt inne i ein periode, og ordet startar
                # med stor bokstav, og ikkje inneheld bindestrek
                # og så liten bokstav , skal det markerast som eigenamn
                # dersom det ikkje vert funne i fullformslistene

                logLine = '{:16}%s (omtrent linje %d)' % (word, linjeNr)
                if ((not periodeStart or propHash[sokOrd]) and
                    re.search(q(r'^[{lettersla}]'), sokOrd) and
                    not re.search(q(r'-[{letterssm}]'), sokOrd)):

                    # Sjekk om namnet kan vere genitiv
                    genOrd = finnGenitivRot(sokOrd)
                    if genOrd:
                        # Sjekk om namnet ender paa s,
                        # det kan daa vere ein ikkje-genitiv
                        if re.search(r'[^s]s$', sokOrd):
                            logging.info(logLine.format('SUBST PROP:'))
                            tagTekst = TAG_LINE.format(stor2stjerne(sokOrd), SUBST_PROP)
                        logging.info(logLine.format('SUBST PROP GEN:'))
                        tagTekst += TAG_LINE.format(stor2stjerne(genOrd), q("{SUBST_PROP} {GEN}"))
                    else:
                        logging.info(logLine.format('SUBST PROP:'))
                        tagTekst = TAG_LINE.format(stor2stjerne(sokOrd), SUBST_PROP)
                    propHash[sokOrd] = True
                    substProp += 1
                else:
                    samsetTagTekst = analyserSammensetning(sokOrd, periodeStart)
                    if samsetTagTekst:
                        tagTekst += samsetTagTekst
                        fuge += 1
                    else:
                        tagInterjeksjon = sjekkInterjeksjon(sokOrd)
                        if tagInterjeksjon:
                            tagTekst += tagInterjeksjon
                        elif periodeStart:
                            logging.info(logLine.format('SUBST PROP:'))
                            tagTekst = TAG_LINE.format(stor2stjerne(sokOrd), SUBST_PROP)
                            propHash[sokOrd] = True
                            substProp += 1
                            # Sjekk om mogleg genitiv
                            genOrd = finnGenitivRot(sokOrd)
                            if genOrd:
                                tagTekst += TAG_LINE.format(stor2stjerne(genOrd), q("{SUBST_PROP} {GEN}"))
                                logging.info(logLine.format('SUBST PROP GEN:'))
                        elif re.search(r'^\P{Letter}+$', word):
                            tagTekst += TAG_LINE.format(stor2stjerne(word), 'symb')
                        else:
                            tagTekst += TAG_LINE.format(stor2stjerne(word), 'ukjent')
                            logging.info(logLine.format('UKJENT'))
                            ukjent += 1
        forrigeAnf = bool(re.search(q(r'({CONSTanfoersel}|{CONSTparstart})( <<<)?$'),
                                    tagTekst))

        outTagTekst = prepareTagTekst(tagTekst, periodeStart)
        printTag(word, wordOrig, outTagTekst)

        if not re.search(q(r'^\$[{stroke}{quots}]'), word):
            periodeStart = False
####################################
def main():
    inputfile = fileinput.input()
    initDB()
    global spesialTabMin, spesialTabMax, ikkjeTerminerForkMin
    spesialTabMin += 1
    spesialTabMax += 1
    if ikkjeTerminerForkMin < 1:
        ikkjeTerminerForkMin = 1

#######################################
# Saa starter vi tagginga
#######################################
    if UTFIL is not None:
        print("Initialisering ferdig. Starter tagging ...")

    global ordTellar, grenseTellar, startTid, mellomTidStart
    ordTellar = 0
    grenseTellar = 0
    startTid = time.time()
    mellomTidStart = time.time()

    periode = ""
    nestePeriode = ""
    sisteLesteLinje = ""
    periodeFullstendig = False
    inputOK = True
    needMoreData = True

    global substProp, ukjent, fuge, linjeNr
    substProp = 0
    ukjent = 0
    fuge = 0
    linjeNr = 0

    while inputOK:
        periodeFullstendig = False
        periode = nestePeriode
        if __debug__: logging.debug("(neste)periode = <<<%(periode)s>>>", vars())

        # Ein vil alltid ha lest ei linje meir enn naudsynt.
        # Dersom linja som sist er lest er identisk med den perioden
        # vi no skal jobbe med, tyder det på at denne neste perioden startar
        # paa ei ny linje. Daa kan denne vere ein mellomtittel.

        muligOverskrift = ""
        terminatorInLastLine = re.search(q(r'[{terminator}\,]'), sisteLesteLinje)
        if periode != "" and sisteLesteLinje == periode and not terminatorInLastLine:
            overskriftElementer = re.split(r'\s+', periode)
            if len(overskriftElementer) <= 7:
                muligOverskrift = periode
            # Sett inn backslash foer eventuelle meta-teikn.
            #Variabelen skal brukast i regulaere uttrykk
            muligOverskrift = re.escape(muligOverskrift)
            if __debug__: logging.debug('muligOverskrift = <<<%(muligOverskrift)s>>>', vars())

        periode = re.sub(r'\n', ' ', periode)
        periode = re.sub(r'\s+', ' ', periode)
        periode = re.sub(r'^\s*', '', periode)
        periode = re.sub(r'\s*$', '', periode)

        # Finn ein periode
        while not periodeFullstendig:
            # Bygg opp det som skal bli ein periode
            if needMoreData: # Treng meir data fraa fila
                line = inputfile.readline()
                linjeNr += 1

                while re.search(r'/\*', line): # Les heile kommentarar
                    if re.search(r'/\*.*\*/', line):
                        break
                    line = re.sub(r'\n', ' ', line)
                    line += inputfile.readline()
                    linjeNr += 1

                line = re.sub(q(r'[{remove}]'), ' ', line) # Fjern ulovlege teikn

                sisteLesteLinje = line # Hold dette for aa sjekke titlar
                sisteLesteLinje = re.sub(r'^\s*', '', sisteLesteLinje)
                sisteLesteLinje = sisteLesteLinje.rstrip("\n")

                if not line:
                    inputOK = False

                # Ta hand om bindestreker paa slutten av linje
                while line:
                    line, subst_count = re.subn(r'(\S)-\s*$', r'\1', line)
                    if subst_count == 0:
                        break
                    m = re.search(r'(\S+)$', line)
                    word = m.group(1)
                    holdLinje = line
                    line = inputfile.readline()
                    linjeNr += 1

                    if not line:
                        inputOK = False
                    if not inputOK:
                        break

                    # Sjekk om koordinert frase
                    if re.search(r'(^\s*og\s)|(^\s*eller\s)', line):
                        line = holdLinje + '- ' + line # Koordinert frase
                    else:
                        m = re.search(r'^(\S*)\s', line) # Sett saman ord
                        word += m.group(1)
                        tagTekst = sok(word) # Sjekk om ordet finns
                        word = initcap2lower(word)
                        tagTekst += sok(word) # Sjekk om ordet finns
                        # FIXME: bug-for-bug implementation of the Perl code,
                        # tagTekst is never None
                        # We should probably check for compounds above
                        if tagTekst is not None:
                            line = holdLinje + line # Ordet finns i basen
                        else:
                            line = holdLinje + '-' + line

                if not line or not inputOK: # Slutten av fila
                    inputOK = False

                    # Terminer siste periode som mangler punktum
                    if periode != "" and not re.search(q(r'[{terminator}]\s*$'), periode):
                        periode += '.'
                    periode += ' END OF FILE'
                elif not re.search(r'\S', line): # Dersom blank linje
                    # Periode som mangler punktum på slutten er overskrift
                    terminatorQuoteInLine = re.search(q(r'[{terminator}][{quotsParantes}]*\s*$'), periode)
                    if periode != "" and not terminatorQuoteInLine:
                        periode += "|"
                else:
                    # Fortsett bygginga av ein periode
                    periode += " " + line
                    periode = re.sub(r'\n', ' ', periode)
                    periode = re.sub(r'\s+', ' ', periode)
                    periode = re.sub(r'^\s*', '', periode)
                    periode = re.sub(r'\s*$', '', periode)

            periode = re.sub(r'/\*.*?\*/', ' ', periode) # Fjern kommentarer

            # Sjekk overskrift
            if muligOverskrift != "":
                periode = re.sub(q(r'(%s)\s+([{quotsParantes}]*[-{lettersla}\d{specLetters}])' % muligOverskrift),
                                 r'\1| \2', periode)

            if __debug__: logging.debug("(before gaaGjennom)periode = <<<%(periode)s>>>", vars())
            needMoreData, periode, nestePeriode, periodeFullstendig = \
                gaaGjennomPeriodeElementer(periode, inputOK, nestePeriode, periodeFullstendig)

        if __debug__: logging.debug("taggPeriode(%(periode)s)", vars())
        taggPeriode(periode)

    sluttTid = time.time()
    tidBrukt = (sluttTid-startTid)/60

    msg = q("""
    Tagga {ordTellar} ord
    Fann {fuge} ukjende ord som vart tolka av samansetningsmodulen
    Fann {ukjent} ukjende ord
    Fann {substProp} ukjente ord som vart tolka som "{SUBST_PROP}"
    Tid brukt: {tidBrukt:10.2f} minutt
    """)

    for logline in msg.strip().split("\n"):
        logging.info(logline)

    if UTFIL is not None:
        print(msg, end='')
        print(q("Liste over problemorda ligg i fila {LOGGFIL}"))

if __name__ == '__main__':
    main()
