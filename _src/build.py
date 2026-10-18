#!/usr/bin/env python3
"""CEL PARK website builder v2 (light theme). One source of truth (DATA) -> static pages in ./site/.
Run: python3 build.py            (full documents, for hosting)
     python3 build.py --artifact (index.html without the document skeleton, for the artifact preview; other pages full)"""
import json, os, re, sys, html, shutil
ART = "--artifact" in sys.argv
SRC = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(SRC, "site")

# ------------------------------------------------------------------ data
EMAIL = "sprzedaz@celpark.pl"; PHONE = "661 970 039"; PHONE_INTL = "+48661970039"
INVESTOR = "PHU Maciej Kaczmarek"; OFFICE = "ul. Polna 3, 62-069 Dąbrówka"
SITE_LL = (52.38764, 16.76154); OFFICE_LL = (52.38736, 16.75890)
MAPS_SITE = f"https://www.google.com/maps/search/?api=1&query={SITE_LL[0]},{SITE_LL[1]}"
MAPS_ROUTE = f"https://www.google.com/maps/dir/?api=1&destination={SITE_LL[0]},{SITE_LL[1]}"
MAPS_EMBED = f"https://maps.google.com/maps?q={SITE_LL[0]},{SITE_LL[1]}&z=15&hl=pl&t=m&output=embed"
MAPS_EMBED_OFFICE = f"https://maps.google.com/maps?q={OFFICE_LL[0]},{OFFICE_LL[1]}&z=16&hl=pl&t=m&output=embed"
ADDR = "ul. Poznańska / ul. Logistyczna, 62-069 Dąbrówka, gm. Dopiewo, powiat poznański"
STAGES = [("I", "AB", "II kwartał 2027", ["A", "B"]), ("II", "CD", "III kwartał 2027", ["C", "D"]), ("III", "EF", "IV kwartał 2027", ["E", "F"])]
UNITS = {
 "A": dict(hall="AB", stage="I", side="lokal zachodni hali AB — bliżej stacji CEL", deliv="II kw. 2027", wall="ściana wspólna z lokalem B", mirror=False, front="od ul. Poznańskiej"),
 "B": dict(hall="AB", stage="I", side="lokal wschodni hali AB", deliv="II kw. 2027", wall="ściana wspólna z lokalem A", mirror=True, front="od ul. Poznańskiej"),
 "C": dict(hall="CD", stage="II", side="lokal zachodni hali CD", deliv="III kw. 2027", wall="ściana wspólna z lokalem D", mirror=False, front="od ul. Poznańskiej"),
 "D": dict(hall="CD", stage="II", side="lokal wschodni hali CD — bliżej ul. Logistycznej", deliv="III kw. 2027", wall="ściana wspólna z lokalem C", mirror=True, front="od ul. Poznańskiej"),
 "E": dict(hall="EF", stage="III", side="lokal północny hali EF — przy ul. Poznańskiej", deliv="IV kw. 2027", wall="ściana wspólna z lokalem F", mirror=False, front="od ul. Logistycznej"),
 "F": dict(hall="EF", stage="III", side="lokal południowy hali EF", deliv="IV kw. 2027", wall="ściana wspólna z lokalem E", mirror=True, front="od ul. Logistycznej"),
}
HALL_IMG = {"AB": dict(day="ab-naroznik-dzien", front="ab-front-dzien", night="ab-front-wieczor", rear="ab-tyl-dzien", side="ab-bok-lewy", side2="ab-bok-prawy"),
            "CD": dict(day="cd-front-dzien", front="cd-front-dzien", night="cd-front-wieczor", rear="cd-tyl-dzien", side="cd-bok-lewy", side2="cd-bok-prawy"),
            "EF": dict(day="ef-front-dzien", front="ef-front-dzien", night="ef-front-wieczor", rear="ef-tyl-dzien", side="ef-bok-lewy", side2="ef-bok-prawy")}
# program per unit (KONTUR, projekt budowlany 07/2026)
PROGRAM = [("01", "Sala sprzedaży / ekspozycja", 125.56, "od frontu, za witryną na całej szerokości lokalu"), ("02", "Magazyn", 229.36, "za salą sprzedaży, doświetlony świetlikami"),
           ("03", "Serwis", 107.36, "przy tylnej ścianie, brama segmentowa 3 × 3 m i drzwi serwisowe"), ("04", "Toaleta dla klientów", 4.62, "przy sali sprzedaży, dostosowana dla osób z niepełnosprawnością"),
           ("05", "Biuro", 17.66, "pas zaplecza wzdłuż ściany bocznej"), ("06", "Pomieszczenie socjalne", 8.40, "pas zaplecza"), ("07", "Pomieszczenie porządkowe", 4.60, "pas zaplecza"),
           ("08", "Toaleta pracowników z prysznicem", 8.90, "pas zaplecza"), ("09", "Szatnia", 8.03, "pas zaplecza")]
USABLE = round(sum(a for _, _, a, _ in PROGRAM), 2)
SPEC = [("Konstrukcja", "słupy żelbetowe prefabrykowane 40 × 40 cm, stalowe dźwigary dachowe, dach z blachy trapezowej z izolacją PIR i membraną PVC"),
        ("Wysokość w świetle", "5,55 m pod dźwigar · 6,35 m pod dach · attyka +7,00 m"),
        ("Elewacja", "ścienna płyta warstwowa z rdzeniem PIR gr. 12 cm (Ruukki, zakład w Obornikach), montowana pionowo, z ukrytym mocowaniem, w kolorze grafitowym RAL 7016; cokół żelbetowy; obróbki attyki w kolorze elewacji"),
        ("Wnęka wejściowa", "cofnięcie witryny o 2,0 m na całej szerokości lokalu, jasna okładzina wnęki, liniowe oświetlenie LED w suficie i na krawędziach"),
        ("Witryna", "fasada słupowo-ryglowa aluminiowa na całe 18 m frontu i 6,1 m wysokości, szkło przyciemniane, stolarka czarna RAL 9005, drzwi wejściowe dla klientów"),
        ("Posadzka", "beton zacierany na gruncie, gr. 20 cm, nośność 5 t/m², z izolacją"),
        ("Zaplecze", "brama segmentowa 3,0 × 3,0 m i drzwi serwisowe 2,1 m od drogi dostawczej; okna w pomieszczeniach zaplecza"),
        ("Światło dzienne", "świetliki dachowe nad magazynem i serwisem, witryna od frontu"),
        ("Instalacje", "woda, kanalizacja, zasilanie 3 × 400 V z rozdzielnicą, oświetlenie przemysłowe LED, przygotowanie pod klimatyzację i wentylację"),
        ("Ogrzewanie", "pompa ciepła z jednostką zewnętrzną na dachu, nagrzewnice w hali"),
        ("Bezpieczeństwo", "ściana oddzielenia pożarowego REI 60 między lokalami, strefa ZL III, wyjścia ewakuacyjne"),
        ("Teren", "33 miejsca postojowe dla klientów, miejsca dla osób z niepełnosprawnością, stacja ładowania EV, stojaki rowerowe, oświetlenie LED, koszony trawnik i rabaty z trawami ozdobnymi, ogrodzenie")]
POIS = [("S11", "węzeł Poznań-Dąbrówka", "300 m", "minuta jazdy"), ("A2", "węzeł Poznań Zachód (A2/S11)", "ok. 6 km", "7 min"), ("Poznań", "centrum miasta", "ok. 15 km", "20 min"),
        ("Ławica", "lotnisko Poznań-Ławica", "ok. 9 km", "12 min"), ("Skórzewo", "osiedla i usługi", "ok. 3 km", "5 min"), ("Dopiewo", "siedziba gminy", "ok. 4 km", "6 min"), ("Obok", "stacja paliw CEL z OSKP, park logistyczny", "100 m", "pieszo")]
GALLERY = [("ab-naroznik-dzien", "Hala AB · narożnik od ul. Poznańskiej", True), ("ab-front-wieczor", "Hala AB · wieczór", False), ("cd-front-dzien", "Hala CD · front", False),
           ("ef-front-dzien", "Hala EF · front od ul. Logistycznej", False), ("cd-front-wieczor", "Hala CD · wieczór", False), ("ef-front-wieczor", "Hala EF · wieczór", False),
           ("detal-podcien", "Wnęka wejściowa · detal", False), ("detal-pylon", "Pylon z oznaczeniem lokali", False), ("ab-tyl-dzien", "Hala AB · zaplecze z bramami", False),
           ("cd-tyl-dzien", "Hala CD · zaplecze", False), ("ef-tyl-dzien", "Hala EF · zaplecze", False), ("ab-bok-lewy", "Hala AB · elewacja boczna", False),
           ("cd-bok-lewy", "Hala CD · elewacja boczna", False), ("ef-bok-lewy", "Hala EF · elewacja boczna", False), ("ab-bok-prawy", "Hala AB · elewacja wschodnia", False)]
USES = [("Salon i serwis", "samochody, motocykle, kampery, maszyny, rowery: ekspozycja za witryną, serwis z bramą od zaplecza"),
        ("Showroom", "kuchnie, meble, drzwi i okna, łazienki, oświetlenie, podłogi: 126 m² sali z pełnym przeszkleniem i magazyn pod ręką"),
        ("Sklep z magazynem", "branża budowlana, instalacyjna, ogrodnicza, motoryzacyjna: sprzedaż od frontu, 229 m² towaru za ścianą"),
        ("E-commerce", "magazyn, pakowanie, odbiory osobiste i punkt obsługi klienta w jednym miejscu, 300 m od S11"),
        ("Pracownia i produkcja lekka", "stolarnia, tapicernia, drukarnia, elektronika, montaż: 6,35 m wysokości, 5 t/m², 3 × 400 V"),
        ("Hurtownia z biurem", "magazyn z rampą od zaplecza, biuro i sala spotkań od frontu, antresola na archiwum lub ekspozycję")]
FAQ = [("Czy mogę kupić lokal, a nie tylko wynająć?", "Tak. Każdy lokal sprzedajemy jako odrębną własność z udziałem w gruncie i częściach wspólnych: parkingu, drodze dostawczej, zieleni i ogrodzeniu. Cena od 1 000 zł/m² netto + VAT. Najem długoterminowy jest drugą opcją; stawkę i okres ustalamy indywidualnie."),
       ("Czy mogę zmienić układ wnętrza?", "Tak, i zachęcamy do tego. Rzut według projektu budowlanego to punkt wyjścia. Na etapie budowy ustalamy z Tobą położenie ścian zaplecza, wielkość sali sprzedaży, antresolę, liczbę i miejsce punktów instalacyjnych. Zmiany, które wymagają projektu zamiennego, prowadzimy z naszym biurem projektowym."),
       ("W jakim stanie przekazujecie lokal?", "W stanie deweloperskim: posadzka z betonu zacieranego, witryna z drzwiami, brama segmentowa i drzwi serwisowe, instalacje wod-kan i elektryczna 3 × 400 V, ogrzewanie pompą ciepła, świetliki, oświetlenie hali. Ściany zaplecza, antresolę, klimatyzację i wykończenie sali sprzedaży wykonujemy na zamówienie albo zostawiamy Tobie."),
       ("Kiedy mogę wejść do lokalu?", "Hala AB (lokale A i B) w II kwartale 2027, hala CD w III kwartale, hala EF w IV kwartale 2027. Budowa rusza w 2026 roku; umowy podpisujemy na etapie budowy, co daje czas na dopasowanie układu."),
       ("Jak wygląda dojazd dla klientów i dostaw?", "Klienci wjeżdżają z ul. Poznańskiej i parkują przed witryną (33 miejsca). Dostawy obsługuje wewnętrzna droga wzdłuż tylnych elewacji z bramą 3 × 3 m do każdego lokalu. Z węzła S11 Poznań-Dąbrówka jest 300 m, z A2 ok. 6 km."),
       ("Czy mogę połączyć dwa lokale?", "Tak, sąsiednie lokale w jednej hali (A+B, C+D, E+F) można połączyć w jedną przestrzeń ok. 1 030 m² z witryną na 36 m. Najlepiej zdecydować o tym przed rozpoczęciem budowy danej hali."),
       ("Kto jest inwestorem?", f"{INVESTOR} — rodzinna firma z Dąbrówki, która od 2014 roku prowadzi stacje paliw CEL, serwis z okręgową stacją kontroli pojazdów i salon CELCAMP. CEL PARK budujemy obok naszych własnych obiektów, przy węźle, przez który sami jeździmy codziennie.")]

# ------------------------------------------------------------------ assets
WORDMARK = re.sub(r"<title>.*?</title>|<desc>.*?</desc>", "", re.search(r"<svg[^>]*>(.*)</svg>", open(os.path.join(SRC, "logo.svg")).read(), re.S).group(1), flags=re.S).replace('fill="#ffffff"', 'fill="currentColor"').strip()

def site_svg(active=None, link=True):
    """Clean site plan with clickable units A-F (draw frame: x right, y down; front of AB/CD at y=0 facing ul. Poznańska)."""
    s = json.load(open(os.path.join(SRC, "site_pzt.json")))
    par = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in s["parcel_m"])
    pav = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in s["paving"]["outer_polygon_m"])
    units = {"A": (0, 0, 18, 30), "B": (18, 0, 18, 30), "C": (44.2, 0, 18, 30), "D": (62.2, 0, 18, 30), "E": (95.7, 0, 30, 18), "F": (95.7, 18, 30, 18)}
    o = [f'<svg class="siteplan" viewBox="-22 -42 200 112" role="img" aria-label="Plan zagospodarowania: lokale A–F">']
    o.append('<rect x="-22" y="-33" width="200" height="8" class="sp-road"/><text x="-14" y="-35.5" class="sp-lab">ul. Poznańska</text>')
    o.append('<rect x="156" y="-33" width="6" height="104" class="sp-road"/><text transform="translate(166 10) rotate(90)" class="sp-lab">ul. Logistyczna</text>')
    o.append(f'<polygon points="{par}" class="sp-parcel"/><polygon points="{pav}" class="sp-paving"/>')
    for g in s["parking"]:
        x0, y0, x1, y1 = g["rect_m"]; o.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" class="sp-park"/>')
        n = g["count"]
        if x1 - x0 > y1 - y0:
            for i in range(1, n): xx = x0 + (x1 - x0) * i / n; o.append(f'<line x1="{xx:.2f}" y1="{y0:.1f}" x2="{xx:.2f}" y2="{y1:.1f}" class="sp-stall"/>')
        else:
            for i in range(1, n): yy = y0 + (y1 - y0) * i / n; o.append(f'<line x1="{x0:.1f}" y1="{yy:.2f}" x2="{x1:.1f}" y2="{yy:.2f}" class="sp-stall"/>')
    for u, (x, y, w, h) in units.items():
        cls = "sp-unit" + (" is-active" if u == active else "")
        inner = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/><text x="{x + w/2:.1f}" y="{y + h/2 + 3.2:.1f}" class="sp-letter">{u}</text>'
        if u in "ABCD": inner += f'<rect x="{x + w/2 - 2.5:.1f}" y="{y - 1.2:.1f}" width="5" height="1.2" class="sp-door"/>'
        else: inner += f'<rect x="{x + w - 0.0:.1f}" y="{y + h/2 - 2.5:.1f}" width="1.2" height="5" class="sp-door"/>'
        if link: o.append(f'<a href="lokal-{u.lower()}.html" aria-label="Lokal {u}">{inner}</a>')
        else: o.append(f'<g>{inner}</g>')
    o.append('<g class="sp-north" transform="translate(172 -22) rotate(-10.6)"><line x1="0" y1="8" x2="0" y2="-8"/><polygon points="0,-10 -2.2,-5 2.2,-5"/><text x="0" y="14" class="sp-lab" text-anchor="middle">N</text></g>')
    o.append('<text x="60" y="52" class="sp-lab sp-dim">droga dostawcza · bramy od zaplecza</text></svg>')
    return "".join(o)

# ------------------------------------------------------------------ CSS / JS
CSS = r"""
/* CEL PARK — white page, graphite type, one accent (CEL yellow) as a marker. Display: Archivo (wide), body: Hanken Grotesk. */
:root{color-scheme:light;--bg:#ffffff;--bg-2:#f6f6f4;--fg:#1a1c20;--muted:#5d636b;--line:#e4e6e9;--ink:#15171a;--ink-2:#1d2024;--ink-fg:#f4f5f6;--ink-muted:#a9afb7;--accent:#f2c230;--accent-ink:#8a6a00;--unit:#2a2d32;
--display:"Archivo","Helvetica Neue",Arial,sans-serif;--body:"Hanken Grotesk","Helvetica Neue",Arial,sans-serif;--w:1240px;--gl:max(16px,env(safe-area-inset-left,0px));--gr:max(16px,env(safe-area-inset-right,0px))}
*{box-sizing:border-box}[hidden]{display:none!important}html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{animation:none!important;transition:none!important}}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--body);font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:60;background:var(--bg)}
img{max-width:100%;display:block;height:auto}a{color:inherit}p{margin:0}
h1,h2,h3{font-family:var(--display);font-variation-settings:"wdth" 112;letter-spacing:-.012em;line-height:1.06;margin:0;text-wrap:balance}
h1{font-size:clamp(2.3rem,5.6vw,4.4rem);font-weight:600}h2{font-size:clamp(1.75rem,3.4vw,2.7rem);font-weight:600}h3{font-size:1.2rem;font-weight:600}
.wrap{max-width:var(--w);margin-inline:auto;padding-left:var(--gl);padding-right:var(--gr)}
.eyebrow{font-family:var(--display);font-variation-settings:"wdth" 118;font-size:.72rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:.6rem}
.eyebrow::before{content:"";width:22px;height:3px;background:var(--accent);border-radius:2px;flex:none}
.lead{font-size:clamp(1.05rem,1.5vw,1.25rem);max-width:64ch;color:var(--muted)}
.prose{max-width:68ch;display:grid;gap:1rem;color:var(--fg)}.prose p{font-size:1.02rem}.prose b{font-weight:600}
.btn{display:inline-flex;align-items:center;gap:.5rem;font-family:var(--display);font-variation-settings:"wdth" 110;font-weight:600;font-size:.95rem;padding:.85rem 1.3rem;border-radius:999px;border:1px solid transparent;text-decoration:none;cursor:pointer;transition:transform .15s ease,background .15s ease}
.btn:hover{transform:translateY(-1px)}.btn:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.btn-solid{background:var(--fg);color:var(--bg)}.btn-ghost{border-color:currentColor;background:transparent}.btn-accent{background:var(--accent);color:#141618}
.on-ink .btn-solid{background:var(--ink-fg);color:var(--ink)}.on-ink .btn-ghost{color:var(--ink-fg)}
section{padding-block:clamp(3.5rem,8vw,7rem)}
.section-head{display:grid;gap:1rem;margin-bottom:clamp(2rem,4vw,3.5rem)}.section-head .lead{max-width:62ch}
.grid-2{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:clamp(1.2rem,3vw,3rem);align-items:start}.grid-2>*{min-width:0}
.grid-3{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:1.2rem}.grid-3>*{min-width:0}
.band{background:var(--bg-2);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.ink{background:var(--ink);color:var(--ink-fg)}.ink .eyebrow,.ink .lead,.ink .note{color:var(--ink-muted)}
.note{font-size:.85rem;color:var(--muted);max-width:72ch}
/* header (white) */
.top{position:sticky;top:env(safe-area-inset-top,0px);z-index:50;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:saturate(1.4) blur(10px);-webkit-backdrop-filter:saturate(1.4) blur(10px);color:var(--fg);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:1rem;height:68px}
html{scroll-padding-top:84px}section[id],div[id],h2[id]{scroll-margin-top:84px}
.logo{display:flex;align-items:center;gap:.9rem;text-decoration:none;color:inherit}.logo svg{height:22px;width:auto;fill:currentColor}
.logo span{font-family:var(--display);font-variation-settings:"wdth" 118;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding-left:.9rem;border-left:1px solid var(--line)}
nav ul{list-style:none;margin:0;padding:0;display:flex;gap:1.5rem;align-items:center}
nav a{text-decoration:none;font-size:.93rem;color:var(--muted);transition:color .15s}nav a:hover,nav a:focus-visible,nav a[aria-current="page"]{color:var(--fg)}
nav .cta{color:#141618;background:var(--accent);padding:.55rem 1rem;border-radius:999px;font-weight:600}nav .cta:hover{color:#141618}
.menu-btn{display:none;background:none;border:1px solid var(--line);color:var(--fg);border-radius:999px;padding:.45rem .9rem;font:inherit;font-size:.9rem;cursor:pointer}
details.inv{position:relative}details.inv summary{list-style:none;cursor:pointer;color:var(--muted);font-size:.93rem;display:flex;align-items:center;gap:.4rem}
details.inv summary::-webkit-details-marker{display:none}details.inv summary::after{content:"";width:.42rem;height:.42rem;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg) translateY(-2px)}
details.inv .dd{position:absolute;top:2.2rem;left:0;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:14px;min-width:300px;padding:.5rem;box-shadow:0 20px 50px rgba(0,0,0,.14);z-index:5}
details.inv .dd a{display:flex;justify-content:space-between;gap:1rem;padding:.7rem .8rem;border-radius:10px;text-decoration:none;font-size:.92rem;color:var(--fg)}details.inv .dd a:hover{background:var(--bg-2)}details.inv .dd small{color:var(--muted)}
.dot{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;background:var(--accent);margin-right:.45rem;vertical-align:middle}
@media (max-width:980px){nav{display:none;position:absolute;left:0;right:0;top:68px;background:var(--bg);border-bottom:1px solid var(--line);padding:1rem var(--gr) 1.4rem var(--gl)}
nav.open{display:block}nav ul{flex-direction:column;align-items:flex-start;gap:1rem}.menu-btn{display:inline-flex}details.inv .dd{position:static;margin-top:.6rem;box-shadow:none}}
/* hero */
.hero{position:relative;background:var(--ink);color:var(--ink-fg);overflow:hidden;padding-block:0}
.hero-media{position:relative;aspect-ratio:16/9;max-height:min(80vh,880px);width:100%}@media (max-width:700px){.hero-media{aspect-ratio:4/5;max-height:72vh}}
.hero-media img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:opacity .7s ease}.hero-media img.night{opacity:0}.hero.is-night .hero-media img.night{opacity:1}
.hero-media::after{content:"";position:absolute;inset:auto 0 0 0;height:60%;background:linear-gradient(to top,rgba(10,11,12,.9),rgba(10,11,12,0))}
.hero-copy{position:relative;margin-top:clamp(-9rem,-16vw,-4rem);padding-bottom:clamp(2.5rem,5vw,4rem);display:grid;gap:1.2rem;z-index:2}
.hero-copy .eyebrow{color:var(--ink-muted)}.hero-copy .lead{color:#d8dbdf}
.hero-actions{display:flex;flex-wrap:wrap;gap:.8rem;align-items:center}
.toggle{display:inline-flex;border:1px solid rgba(255,255,255,.3);border-radius:999px;overflow:hidden;font-family:var(--display);font-size:.78rem;letter-spacing:.06em;text-transform:uppercase}
.toggle button{background:none;border:0;color:var(--ink-muted);padding:.55rem .95rem;cursor:pointer;font:inherit}.toggle button[aria-pressed="true"]{background:var(--ink-fg);color:var(--ink)}.toggle button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.facts{background:var(--bg);border-bottom:1px solid var(--line)}
.facts .wrap{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1.4rem 2rem;padding-block:1.8rem}
.fact b{display:block;font-family:var(--display);font-variation-settings:"wdth" 112;font-size:1.5rem;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1}.fact span{font-size:.82rem;color:var(--muted)}
/* image bands */
.imgband{position:relative;background:var(--ink);color:var(--ink-fg);overflow:hidden}
.imgband img{width:100%;height:auto;aspect-ratio:21/9;object-fit:cover;display:block}.imgband.tall img{aspect-ratio:16/9}
@media (max-width:700px){.imgband img,.imgband.tall img{aspect-ratio:4/3}}
.imgband::after{content:"";position:absolute;inset:auto 0 0 0;height:60%;background:linear-gradient(to top,rgba(10,11,12,.85),rgba(10,11,12,0))}
.imgband .in{position:absolute;left:0;right:0;bottom:clamp(1.2rem,4vw,3rem);z-index:2;display:grid;gap:.4rem}
.imgband .t{font-family:var(--display);font-variation-settings:"wdth" 112;font-size:clamp(1.5rem,3.6vw,3rem);font-weight:600;line-height:1.08;max-width:22ch;text-wrap:balance}
.imgband .s{color:#d8dbdf;max-width:60ch;font-size:clamp(.95rem,1.3vw,1.1rem)}
/* content blocks */
.figure{margin:0;display:grid;gap:.6rem}.figure img{border-radius:18px;width:100%}.figure figcaption{font-size:.85rem;color:var(--muted)}
.list{list-style:none;margin:0;padding:0;display:grid;gap:.9rem}.list li{display:grid;grid-template-columns:auto 1fr;gap:.9rem;align-items:start;padding-bottom:.9rem;border-bottom:1px solid var(--line)}.list li:last-child{border-bottom:0}
.list .k{font-family:var(--display);font-variation-settings:"wdth" 118;font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding-top:.35rem;min-width:7.5rem}.list b{font-weight:600}
.spec{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:1.4rem 2rem}.spec div{border-top:2px solid var(--line);padding-top:.9rem;display:grid;gap:.25rem}.spec b{font-weight:600}.spec span{color:var(--muted);font-size:.95rem}
.pillars{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:1.2rem}
.pillar{border-top:2px solid var(--line);padding-top:1.1rem;display:grid;gap:.5rem}.pillar b{font-family:var(--display);font-variation-settings:"wdth" 112;font-size:1.35rem;font-weight:600;line-height:1.15}.pillar p{color:var(--muted);font-size:.97rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:1.2rem}
.card{position:relative;border-radius:20px;overflow:hidden;background:var(--ink);color:var(--ink-fg);aspect-ratio:4/3;display:grid;text-decoration:none}
.card img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .6s ease}.card:hover img{transform:scale(1.03)}
.card .in{position:relative;align-self:end;padding:1.4rem;background:linear-gradient(to top,rgba(10,11,12,.9),rgba(10,11,12,0));display:grid;gap:.35rem}
.card .in b{font-family:var(--display);font-variation-settings:"wdth" 112;font-size:1.5rem;font-weight:600}.card .in span{color:var(--ink-muted);font-size:.9rem}
.card.soon{background:var(--bg-2);color:var(--fg);border:1px dashed var(--line)}.card.soon .in{background:none;align-self:center;text-align:center}.card.soon .in span{color:var(--muted)}
.tag{display:inline-flex;align-items:center;gap:.45rem;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;font-family:var(--display);color:var(--ink-fg)}.tag::before{content:"";width:.55rem;height:.55rem;border-radius:50%;background:var(--accent)}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:1.2rem;counter-reset:step}
.step{border:1px solid var(--line);border-radius:18px;padding:1.3rem;display:grid;gap:.5rem;background:var(--bg)}.step::before{counter-increment:step;content:counter(step,decimal-leading-zero);font-family:var(--display);font-variation-settings:"wdth" 118;font-size:.8rem;letter-spacing:.14em;color:var(--accent-ink);font-weight:600}
.step b{font-family:var(--display);font-variation-settings:"wdth" 110;font-size:1.1rem;font-weight:600}.step p{color:var(--muted);font-size:.95rem}
/* units */
.units{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
.units th{text-align:left;font-family:var(--display);font-variation-settings:"wdth" 118;font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600;padding:.6rem .5rem;border-bottom:1px solid var(--line)}
.units td{padding:.8rem .5rem;border-bottom:1px solid var(--line);vertical-align:top}.units td.l{font-family:var(--display);font-variation-settings:"wdth" 112;font-size:1.5rem;font-weight:600;width:3.6rem}
.units td small{display:block;color:var(--muted);font-size:.85rem}.table-wrap{overflow-x:auto}
.price{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:1.2rem}
.price div{border:1px solid var(--line);border-radius:18px;padding:1.4rem;display:grid;gap:.35rem;background:var(--bg)}.price b{font-family:var(--display);font-variation-settings:"wdth" 112;font-size:1.55rem;font-weight:600}.price span{color:var(--muted);font-size:.95rem}
.siteplan{width:100%;height:auto;display:block;font-family:var(--display)}
.sp-road{fill:var(--line)}.sp-lab{font-size:3.2px;fill:var(--muted);letter-spacing:.3px}.sp-dim{font-size:2.8px}
.sp-parcel{fill:color-mix(in srgb,var(--accent) 12%,var(--bg));stroke:var(--fg);stroke-width:.35}.sp-paving{fill:var(--bg-2);stroke:none}
.sp-park{fill:var(--line);opacity:.9}.sp-stall{stroke:var(--bg);stroke-width:.3}
.sp-unit{fill:var(--unit);stroke:var(--bg);stroke-width:.5;transition:fill .15s}.sp-letter{font-size:8px;font-weight:600;fill:#ffffff;text-anchor:middle;pointer-events:none}
.siteplan a:hover .sp-unit,.siteplan a:focus-visible .sp-unit,.sp-unit.is-active{fill:var(--accent)}.siteplan a:hover .sp-letter,.sp-unit.is-active + .sp-letter,.siteplan a:focus-visible .sp-letter{fill:#141618}
.siteplan a:focus-visible{outline:none}.sp-door{fill:var(--accent)}.sp-north line,.sp-north polygon{stroke:var(--muted);fill:var(--muted);stroke-width:.4}
.picker{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:clamp(1.2rem,3vw,3rem);align-items:center}@media (max-width:820px){.picker{grid-template-columns:1fr}}
.ulist{list-style:none;margin:0;padding:0;display:grid;gap:.5rem}
.ulist a{display:grid;grid-template-columns:2.6rem 1fr auto;align-items:center;gap:1rem;padding:.75rem .9rem;border:1px solid var(--line);border-radius:14px;text-decoration:none;background:var(--bg);transition:border-color .15s,transform .15s}
.ulist a:hover{border-color:var(--fg);transform:translateX(3px)}.ulist .l{font-family:var(--display);font-variation-settings:"wdth" 112;font-size:1.4rem;font-weight:600}.ulist .m{font-size:.92rem;color:var(--muted)}.ulist .m b{color:var(--fg);font-weight:600;display:block}
.ulist .st{font-size:.8rem;display:inline-flex;align-items:center;gap:.4rem;white-space:nowrap}.ulist .st::before{content:"";width:.5rem;height:.5rem;border-radius:50%;background:var(--accent)}
/* gallery */
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:.9rem}
.gallery button{all:unset;cursor:pointer;display:block;position:relative;border-radius:14px;overflow:hidden;aspect-ratio:16/9;background:var(--line)}
.gallery button img{width:100%;height:100%;object-fit:cover;transition:transform .5s ease}.gallery button:hover img{transform:scale(1.03)}.gallery button:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.gallery button span{position:absolute;left:.9rem;bottom:.7rem;color:#fff;font-size:.8rem;letter-spacing:.04em;text-shadow:0 1px 8px rgba(0,0,0,.6)}
.gallery{grid-auto-flow:dense}.gallery .wide{grid-column:span 2;grid-row:span 2;aspect-ratio:auto;height:100%;min-height:0}@media (max-width:700px){.gallery .wide{grid-column:span 1;grid-row:span 1;aspect-ratio:16/9;height:auto}}
.lightbox{position:fixed;inset:0;background:rgba(8,9,10,.94);z-index:100;display:flex;align-items:center;justify-content:center;padding:max(16px,env(safe-area-inset-top,0px)) var(--gr) max(16px,env(safe-area-inset-bottom,0px)) var(--gl)}
.lightbox img{max-width:100%;max-height:82vh;border-radius:12px;box-shadow:0 30px 80px rgba(0,0,0,.6)}.lightbox figcaption{color:#d6d9dd;text-align:center;margin-top:.9rem;font-size:.95rem}
.lightbox .x{position:absolute;top:calc(14px + env(safe-area-inset-top,0px));right:calc(14px + env(safe-area-inset-right,0px));background:rgba(255,255,255,.12);color:#fff;border:0;border-radius:999px;width:44px;height:44px;font-size:1.3rem;cursor:pointer}
.lightbox .nav{position:absolute;top:50%;transform:translateY(-50%);background:rgba(255,255,255,.12);color:#fff;border:0;border-radius:999px;width:44px;height:44px;font-size:1.3rem;cursor:pointer}.lightbox .prev{left:calc(10px + env(safe-area-inset-left,0px))}.lightbox .next{right:calc(10px + env(safe-area-inset-right,0px))}
/* tabs / plans / maps */
.tabs{display:inline-flex;flex-wrap:wrap;gap:.3rem;border:1px solid var(--line);border-radius:999px;padding:.25rem;margin-bottom:1.2rem;max-width:100%}
@media (max-width:700px){.tabs{display:flex;flex-wrap:wrap;border-radius:22px}.tabs button{flex:1 1 auto;text-align:center}}
.tabs button{border:0;background:none;color:var(--muted);font:inherit;font-size:.9rem;padding:.5rem 1rem;border-radius:999px;cursor:pointer}.tabs button[aria-selected="true"]{background:var(--fg);color:var(--bg)}.tabs button:focus-visible{outline:2px solid var(--accent)}
.plan-img{border:1px solid var(--line);border-radius:18px;overflow:hidden;background:#fff}
.map{border:1px solid var(--line);border-radius:18px;overflow:hidden;background:var(--bg-2);aspect-ratio:4/3;position:relative}.map iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.map .fb{position:absolute;inset:0;display:grid;place-items:center;text-align:center;padding:1.5rem;color:var(--muted);font-size:.95rem;z-index:0}
.poi>:last-child:nth-child(odd){grid-column:1/-1}.poi{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:.8rem}
.poi div{border:1px solid var(--line);border-radius:14px;padding:.9rem 1rem;display:grid;gap:.15rem;background:var(--bg)}.poi b{font-family:var(--display);font-variation-settings:"wdth" 112;font-size:1.25rem;font-weight:600}.poi span{color:var(--muted);font-size:.88rem}.poi i{font-style:normal;font-size:.8rem;color:var(--accent-ink);font-weight:600}
.program{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:clamp(1.2rem,3vw,3rem);align-items:start}
.zones{display:grid;gap:.5rem}
.zone{display:grid;grid-template-columns:1fr auto;gap:1rem;align-items:center;padding:.9rem 1.1rem;border-radius:14px;background:var(--bg);border:1px solid var(--line)}
.zone b{font-weight:600}.zone span{display:block;color:var(--muted);font-size:.88rem}.zone .a{font-family:var(--display);font-variation-settings:"wdth" 112;font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap}
.zone.hi{border-color:var(--accent)}.zone.sum{background:var(--bg-2)}
.callout{border-left:4px solid var(--accent);background:var(--bg-2);border-radius:0 18px 18px 0;padding:1.3rem 1.5rem;display:grid;gap:.6rem}.callout b{font-family:var(--display);font-variation-settings:"wdth" 110;font-size:1.15rem;font-weight:600}.callout p{color:var(--muted);font-size:.97rem}
.uses{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:1rem}
.use{border:1px solid var(--line);border-radius:16px;padding:1.2rem;display:grid;gap:.4rem;background:var(--bg)}.use b{font-family:var(--display);font-variation-settings:"wdth" 110;font-weight:600;font-size:1.05rem}.use span{color:var(--muted);font-size:.92rem}
.faq{display:grid;gap:.5rem;max-width:880px}.faq details{border:1px solid var(--line);border-radius:14px;background:var(--bg);padding:0 1.1rem}
.faq summary{cursor:pointer;padding:1rem 0;font-weight:600;list-style:none;display:flex;justify-content:space-between;gap:1rem;align-items:center}.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";font-family:var(--display);font-size:1.3rem;color:var(--muted);flex:none}.faq details[open] summary::after{content:"–"}.faq details p{padding-bottom:1rem;color:var(--muted)}
.timeline{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:1.5rem}
.timeline div{position:relative;padding-top:1.2rem;border-top:2px solid var(--line);display:grid;gap:.25rem}.timeline div::before{content:"";position:absolute;top:-6px;left:0;width:10px;height:10px;border-radius:50%;background:var(--accent)}
.timeline b{font-family:var(--display);font-variation-settings:"wdth" 112;font-size:1.3rem;font-weight:600}.timeline span{color:var(--muted);font-size:.95rem}
.quote{font-family:var(--display);font-variation-settings:"wdth" 108;font-size:clamp(1.5rem,3.2vw,2.5rem);font-weight:500;line-height:1.2;max-width:26ch;text-wrap:balance}.quote em{font-style:normal;color:var(--accent-ink)}
/* contact */
.form{display:grid;gap:1rem}.form label{display:grid;gap:.35rem;font-size:.85rem;color:var(--muted)}
.form input,.form select,.form textarea{font:inherit;font-size:1rem;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:.8rem .95rem;width:100%}
.form input:focus-visible,.form select:focus-visible,.form textarea:focus-visible{outline:2px solid var(--accent);border-color:transparent}
.form .row{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:1rem}.form .row>*{min-width:0}
.sent{border:1px solid var(--line);border-radius:14px;padding:1rem 1.2rem;background:var(--bg-2);display:grid;gap:.6rem}
.copy{display:inline-flex;align-items:center;gap:.6rem;font-family:var(--display);font-size:1.05rem;font-weight:600;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:.7rem 1rem;max-width:100%;flex-wrap:wrap}
.copy button{all:unset;cursor:pointer;font-size:.8rem;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:.3rem .7rem}.copy button:focus-visible{outline:2px solid var(--accent)}
footer{background:var(--ink);color:var(--ink-muted);font-size:.85rem}footer .wrap{display:grid;gap:1.2rem;padding-block:2.4rem}footer .logo{color:var(--ink-fg)}footer .logo svg{height:16px}footer p{max-width:85ch}
footer .cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:1rem 2rem}footer .cols b{color:var(--ink-fg);display:block;margin-bottom:.4rem;font-weight:600}footer a{color:var(--ink-muted)}footer a:hover{color:var(--ink-fg)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.crumbs{font-size:.85rem;color:var(--muted);display:flex;gap:.5rem;flex-wrap:wrap}.crumbs a{text-decoration:none}.crumbs a:hover{text-decoration:underline}
"""

JS = r"""
(function(){
  var hero=document.getElementById('hero'),tDay=document.getElementById('tDay'),tNight=document.getElementById('tNight');
  if(hero&&tDay&&tNight){var setNight=function(n){hero.classList.toggle('is-night',n);tDay.setAttribute('aria-pressed',String(!n));tNight.setAttribute('aria-pressed',String(n));};
    tDay.addEventListener('click',function(){setNight(false)});tNight.addEventListener('click',function(){setNight(true)});}
  var mb=document.getElementById('menuBtn'),nav=document.getElementById('mainNav');
  if(mb&&nav){mb.addEventListener('click',function(){var o=nav.classList.toggle('open');mb.setAttribute('aria-expanded',String(o));});}
  document.addEventListener('click',function(e){var d=document.getElementById('invDd');if(d&&d.open&&!d.contains(e.target))d.open=false;});
  document.querySelectorAll('.tabs').forEach(function(tl){var tabs=tl.querySelectorAll('[role=tab]');
    tabs.forEach(function(t){t.addEventListener('click',function(){tabs.forEach(function(x){x.setAttribute('aria-selected','false');var p=document.getElementById(x.getAttribute('aria-controls'));if(p)p.hidden=true;});t.setAttribute('aria-selected','true');var p=document.getElementById(t.getAttribute('aria-controls'));if(p)p.hidden=false;});});});
  var items=Array.prototype.slice.call(document.querySelectorAll('.gallery button')),lb=document.getElementById('lb');
  if(lb&&items.length){var lbImg=document.getElementById('lbImg'),lbCap=document.getElementById('lbCap'),cur=0,last=null;
    var show=function(i){cur=(i+items.length)%items.length;var b=items[cur];lbImg.src=b.getAttribute('data-full');lbImg.alt=b.querySelector('img').alt;lbCap.textContent=b.getAttribute('data-cap');};
    var open=function(i){last=document.activeElement;show(i);lb.hidden=false;document.body.style.overflow='hidden';document.getElementById('lbClose').focus();};
    var close=function(){lb.hidden=true;document.body.style.overflow='';if(last)last.focus();};
    items.forEach(function(b,i){b.addEventListener('click',function(){open(i)});});
    document.getElementById('lbClose').addEventListener('click',close);document.getElementById('lbPrev').addEventListener('click',function(){show(cur-1)});document.getElementById('lbNext').addEventListener('click',function(){show(cur+1)});
    lb.addEventListener('click',function(e){if(e.target===lb)close();});
    document.addEventListener('keydown',function(e){if(lb.hidden)return;if(e.key==='Escape')close();if(e.key==='ArrowLeft')show(cur-1);if(e.key==='ArrowRight')show(cur+1);});}
  function copyText(t,btn,ok){var done=function(){var o=btn.textContent;btn.textContent=ok;setTimeout(function(){btn.textContent=o},1600);};
    var fallback=function(){var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done();}catch(err){}document.body.removeChild(ta);};
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,fallback);}else fallback();}
  var cm=document.getElementById('copyMail');if(cm)cm.addEventListener('click',function(){copyText('__EMAIL__',cm,'skopiowano');});
  var form=document.getElementById('form');
  if(form){var sent=document.getElementById('sent'),sentTxt=document.getElementById('sentTxt'),mailto=document.getElementById('mailto'),lastMsg='';
    form.addEventListener('submit',function(e){e.preventDefault();var f=form.elements;
      if(!f.name.value.trim()||!f.email.value.trim()){document.getElementById('formHint').textContent='Podaj imię i nazwisko oraz adres e-mail.';(f.name.value.trim()?f.email:f.name).focus();return;}
      var subj='CEL PARK Dąbrówka.01 – zapytanie o lokal '+f.unit.value+' ('+f.mode.value+')';
      lastMsg='Imię i nazwisko: '+f.name.value.trim()+'\nTelefon: '+(f.phone.value.trim()||'-')+'\nE-mail: '+f.email.value.trim()+'\nLokal: '+f.unit.value+'\nInteresuje mnie: '+f.mode.value+'\n\n'+(f.msg.value.trim()||'');
      mailto.href='mailto:__EMAIL__?subject='+encodeURIComponent(subj)+'&body='+encodeURIComponent(lastMsg);
      var showFallback=function(){sentTxt.textContent='Temat: '+subj+'. Jeśli program pocztowy się nie otworzy, skopiuj treść i wyślij ją na __EMAIL__.';sent.hidden=false;sent.scrollIntoView({block:'nearest'});};
      var btn=form.querySelector('button[type=submit]');btn.disabled=true;
      var ctrl=new AbortController();var tm=setTimeout(function(){ctrl.abort()},6000);
      fetch('kontakt.php',{method:'POST',body:new FormData(form),signal:ctrl.signal}).then(function(r){return r.ok?r.json():Promise.reject()}).then(function(j){clearTimeout(tm);btn.disabled=false;
        if(j&&j.ok){sent.querySelector('b').textContent='Dziękujemy, zapytanie wysłane.';sentTxt.textContent='Odpowiemy w ciągu jednego dnia roboczego na adres '+f.email.value.trim()+'.';mailto.hidden=true;document.getElementById('copyMsg').hidden=true;sent.hidden=false;form.reset();}
        else showFallback();}).catch(function(){clearTimeout(tm);btn.disabled=false;showFallback();});});
    var cmsg=document.getElementById('copyMsg');if(cmsg)cmsg.addEventListener('click',function(){copyText(lastMsg,cmsg,'Skopiowano');});}
})();
""".replace("__EMAIL__", EMAIL)

# ------------------------------------------------------------------ components
def header(active=""):
    def a(href, label, key): return f'<li><a href="{href}"{" aria-current=\"page\"" if key == active else ""}>{label}</a></li>'
    return f'''<header class="top"><div class="wrap">
  <a class="logo" href="index.html" aria-label="CEL PARK – strona główna"><svg viewBox="0 0 559 105" aria-hidden="true"><use href="#wordmark"></use></svg><span>Dąbrówka.01</span></a>
  <button class="menu-btn" id="menuBtn" aria-expanded="false" aria-controls="mainNav">Menu</button>
  <nav id="mainNav" aria-label="Główne"><ul>
    <li><details class="inv" id="invDd"><summary>Inwestycje</summary><div class="dd">
      <a href="dabrowka-01.html"><span><i class="dot"></i>Dąbrówka.01</span><small>w sprzedaży · oddanie 2027</small></a>
      <a href="kontakt.html"><span>Kolejne lokalizacje</span><small>w przygotowaniu</small></a></div></details></li>
    {a("dabrowka-01.html#lokale", "Lokale", "lokale")}{a("dabrowka-01.html#standard", "Standard", "standard")}{a("dabrowka-01.html#lokalizacja", "Lokalizacja", "lokalizacja")}{a("o-nas.html", "O nas", "o-nas")}{a("kontakt.html", "Kontakt", "kontakt")}
    <li><a class="cta" href="kontakt.html">Zapytaj o lokal</a></li></ul></nav>
</div></header>'''

def footer():
    return f'''<footer><div class="wrap">
  <div class="cols">
    <div><a class="logo" href="index.html" aria-label="CEL PARK"><svg viewBox="0 0 559 105" aria-hidden="true"><use href="#wordmark"></use></svg></a><p style="margin-top:.8rem">Powierzchnie ekspozycyjno-magazynowe na sprzedaż i wynajem przy węzłach dróg ekspresowych. Marka rodzinnej firmy Kaczmarków z Dąbrówki.</p></div>
    <div><b>Inwestycje</b><a href="dabrowka-01.html">Dąbrówka.01 — w sprzedaży, oddanie 2027</a><br><a href="kontakt.html">Kolejne lokalizacje — w przygotowaniu</a></div>
    <div><b>Kontakt</b><a href="kontakt.html">{EMAIL}</a><br><a href="tel:{PHONE_INTL}">+48 {PHONE}</a><br>{INVESTOR}<br>biuro sprzedaży: {OFFICE}<br><a href="https://www.kaczmarki.eu/" target="_blank" rel="noopener">kaczmarki.eu</a></div>
  </div>
  <p>© 2026 CEL PARK · {INVESTOR}. Wizualizacje, rzuty i podane powierzchnie mają charakter poglądowy; ostateczny wygląd, powierzchnie i terminy mogą ulec zmianie w toku realizacji. Treść strony nie stanowi oferty w rozumieniu art. 66 Kodeksu cywilnego. Podkłady map: ortofotomapa i BDOT10k — Główny Urząd Geodezji i Kartografii.</p>
</div></footer>
<div class="lightbox" id="lb" hidden role="dialog" aria-modal="true" aria-label="Podgląd wizualizacji"><button class="x" id="lbClose" aria-label="Zamknij">×</button><button class="nav prev" id="lbPrev" aria-label="Poprzednia">‹</button><figure style="margin:0;max-width:1400px"><img id="lbImg" src="" alt=""><figcaption id="lbCap"></figcaption></figure><button class="nav next" id="lbNext" aria-label="Następna">›</button></div>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><symbol id="wordmark" viewBox="0 0 559 105">{WORDMARK}</symbol></defs></svg>
<script>{JS}</script>'''

def hero(day, night, eyebrow, h1, lead, actions, toggle=True):
    t = '<div class="toggle" role="group" aria-label="Pora dnia"><button type="button" id="tDay" aria-pressed="true">Dzień</button><button type="button" id="tNight" aria-pressed="false">Wieczór</button></div>' if toggle and night else ""
    n = f'<img class="night" src="img/{night}.jpg" alt="" loading="lazy">' if night else ""
    return f'''<section class="hero on-ink" id="hero"><div class="hero-media"><img class="day" src="img/{day}.jpg" alt="" fetchpriority="high">{n}</div>
<div class="wrap hero-copy"><p class="eyebrow">{eyebrow}</p><h1>{h1}</h1><p class="lead">{lead}</p><div class="hero-actions">{actions}{t}</div></div></section>'''

def facts(items):
    return '<div class="facts" aria-label="Najważniejsze liczby"><div class="wrap">' + "".join(f'<div class="fact"><b>{b}</b><span>{s}</span></div>' for b, s in items) + '</div></div>'

FACTS_INV = [("3 hale", "6 lokali A–F"), (f"{USABLE:.0f} m²", "pow. użytkowej · witryna 18 m"), ("6,35 m", "wysokości pod dach"), ("od 1 000 zł/m²", "sprzedaż, netto + VAT"), ("300 m", "do węzła S11"), ("2027", "oddanie etapami II–IV kw.")]

def band_img(img, title, sub="", tall=False):
    return f'<div class="imgband{" tall" if tall else ""}"><img src="img/{img}.jpg" alt="" loading="lazy"><div class="wrap in"><p class="t">{title}</p>{f"<p class=\"s\">{sub}</p>" if sub else ""}</div></div>'

def gallery(items):
    b = "".join(f'<button{" class=\"wide\"" if w else ""} data-full="img/{n}.jpg" data-cap="{html.escape(c)}"><img src="img/{n}-s.jpg" alt="{html.escape(c)}" loading="lazy"><span>{html.escape(c)}</span></button>' for n, c, w in items)
    return f'<div class="gallery">{b}</div>'

def map_embed(src, title):
    return f'<div class="map"><div class="fb">Mapa Google — jeśli nie wyświetla się w podglądzie, <a href="{MAPS_SITE}" target="_blank" rel="noopener">otwórz ją w nowej karcie</a>.</div><iframe src="{src}" title="{title}" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe></div>'

def layout_callout():
    return '''<div class="callout"><b>Układ wnętrza ustalamy razem — na etapie budowy.</b>
<p>Rzut według projektu budowlanego to propozycja, nie zobowiązanie. Kupując lub wynajmując lokal w trakcie budowy, decydujesz o położeniu ścian zaplecza, wielkości sali sprzedaży, antresoli, miejscu bramy serwisowej i punktach instalacji. Zmiany wprowadzamy przed wykonaniem danego etapu, a te wymagające projektu zamiennego prowadzimy z naszym biurem projektowym. Dzięki temu w 2027 roku odbierasz lokal zaprojektowany pod Twoją działalność, nie pod „przeciętnego najemcę”.</p>
<p><b style="font-size:1rem">Co możesz ustalić:</b> ściany działowe i ich wysokość · antresolę ≈ 125 m² · drugie wejście lub bramę · układ instalacji elektrycznej i wod-kan · klimatyzację i wentylację · posadzkę w sali sprzedaży · wykończenie zaplecza.</p></div>'''

def contact_form(unit="dowolny"):
    opts = "".join(f'<option{" selected" if u == unit else ""}>{u}</option>' for u in ["dowolny", "A", "B", "C", "D", "E", "F"])
    return f'''<form class="form" id="form" novalidate>
  <div class="row"><label for="f-name">Imię i nazwisko<input id="f-name" name="name" autocomplete="name" required></label><label for="f-phone">Telefon<input id="f-phone" name="phone" type="tel" autocomplete="tel"></label></div>
  <label for="f-email">E-mail<input id="f-email" name="email" type="email" autocomplete="email" required></label>
  <div class="row"><label for="f-unit">Lokal<select id="f-unit" name="unit">{opts}</select></label><label for="f-mode">Interesuje mnie<select id="f-mode" name="mode"><option>zakup</option><option>najem</option><option>zakup lub najem</option></select></label></div>
  <label for="f-msg">Wiadomość<textarea id="f-msg" name="msg" rows="4" placeholder="np. rodzaj działalności, potrzebna antresola, termin"></textarea></label>
  <input type="text" name="website" id="f-website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">
  <div style="display:flex;gap:.8rem;flex-wrap:wrap;align-items:center"><button class="btn btn-solid" type="submit">Wyślij zapytanie</button><span class="note" id="formHint">Zapytanie trafia na {EMAIL}. Odpowiadamy w ciągu jednego dnia roboczego.</span></div>
  <div class="sent" id="sent" hidden><b>Treść zapytania gotowa.</b><span id="sentTxt" class="note"></span><div style="display:flex;gap:.6rem;flex-wrap:wrap"><a class="btn btn-solid" id="mailto" href="#">Otwórz w programie pocztowym</a><button class="btn btn-ghost" type="button" id="copyMsg">Skopiuj treść</button></div></div>
</form>'''

def contact_block(unit="dowolny", title="Zapytaj o lokal.", lead="Napisz, który lokal Cię interesuje i czy myślisz o zakupie, czy o najmie. Odpowiadamy w ciągu jednego dnia roboczego, a spotkanie na działce lub w biurze przy stacji CEL umawiamy od ręki."):
    return f'''<section id="kontakt" class="band"><div class="wrap grid-2">
  <div><div class="section-head"><p class="eyebrow">Kontakt</p><h2>{title}</h2><p class="lead">{lead}</p></div>
    <div style="display:flex;gap:.8rem;flex-wrap:wrap"><div class="copy"><span>{EMAIL}</span><button type="button" id="copyMail">kopiuj</button></div><div class="copy"><a href="tel:{PHONE_INTL}" style="text-decoration:none">+48 {PHONE}</a></div></div>
    <ul class="list" style="margin-top:1.4rem"><li><span class="k">Inwestor</span><span><b>{INVESTOR}</b> · rodzinna firma Kaczmarków · <a href="https://www.kaczmarki.eu/" target="_blank" rel="noopener">kaczmarki.eu</a></span></li>
    <li><span class="k">Biuro sprzedaży</span><span>{OFFICE} — przy serwisie CEL i stacji kontroli pojazdów, 400 m od placu budowy</span></li>
    <li><span class="k">Godziny</span><span>poniedziałek–piątek 8:00–16:00, w innych godzinach po umówieniu</span></li>
    <li><span class="k">Dojazd</span><span><a href="{MAPS_ROUTE}" target="_blank" rel="noopener">Wyznacz trasę do inwestycji w Mapach Google</a></span></li></ul></div>
  {contact_form(unit)}</div></section>'''

def doc(title, body, desc, active=""):
    head = f'''<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..700&family=Hanken+Grotesk:wght@400;500;600&display=swap">
<style>{CSS}</style>'''
    return head + header(active) + body + footer()

def full_doc(title, body, desc, active=""):
    return f'<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">{doc(title, body, desc, active)}</head></html>'.replace("</style>", "</style></head><body>", 1).replace("</html>", "</body></html>")

# ------------------------------------------------------------------ pages
def page_index():
    body = hero("cd-front-dzien", "cd-front-wieczor", "CEL PARK · nowa marka · pierwsza inwestycja w sprzedaży · oddanie 2027",
                "Przestrzeń ekspozycyjno-magazynowa.<br>Nie zwykła hala.",
                "CEL PARK to obiekty, w których elewacja, witryna i detal mają znaczenie: salon, showroom, serwis albo magazyn pod jednym dachem, przy węźle drogi ekspresowej. Pierwsza inwestycja — Dąbrówka.01 — powstaje 300 m od węzła S11 Poznań-Dąbrówka. Sześć lokali po ponad 500 m², do kupienia od 1 000 zł/m² albo do wynajęcia.",
                '<a class="btn btn-solid" href="dabrowka-01.html">Poznaj Dąbrówkę.01</a><a class="btn btn-ghost" href="dabrowka-01.html#lokale">Wybierz lokal A–F</a>')
    body += facts(FACTS_INV)
    body += f'''<section id="marka"><div class="wrap grid-2">
  <div><p class="eyebrow">Marka</p><h2 style="margin-top:1rem">Hala, która wygląda jak salon. I pracuje jak magazyn.</h2></div>
  <div class="prose">
    <p>Większość hal usługowych wygląda tak samo: jasna blacha, wąskie okna, brama na froncie. CEL PARK powstał z innego założenia. Klient, który podjeżdża pod Twój lokal, ma zobaczyć <b>witrynę na całe osiemnaście metrów frontu</b>, grafitową elewację z pionowych płyt, podświetloną wnękę wejściową i czysty, czytelny detal. To, co dzieje się za ścianą — magazyn, serwis, pakowanie, montaż — ma po prostu działać: 6,35 m wysokości, posadzka 5 t/m², brama od zaplecza, trzy fazy.</p>
    <p>Budujemy przy węzłach dróg ekspresowych, bo dla firm, które sprzedają i obsługują klientów, dojazd jest częścią oferty. Dąbrówka.01 leży 300 m od węzła Poznań-Dąbrówka na S11, sześć kilometrów od autostrady A2 i kwadrans od centrum Poznania — przy stacji paliw CEL, obok parku logistycznego, na trasie, którą codziennie jadą tysiące samochodów.</p>
    <p>Lokal możesz <b>kupić</b> jako odrębną własność albo <b>wynająć</b> długoterminowo. W obu przypadkach o układzie wnętrza decydujesz Ty — jeszcze na etapie budowy.</p>
  </div></div></section>
<section id="inwestycje" class="band"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Inwestycje</p><h2>Jedna marka, kolejne adresy.</h2><p class="lead">Każda inwestycja CEL PARK dostaje własny numer. Pierwsza powstaje w Dąbrówce, obok naszej stacji paliw i salonu CELCAMP. Kolejne lokalizacje przygotowujemy w tej samej formule: niewielki park, kilka hal, lokale z witryną, węzeł drogi ekspresowej w zasięgu wzroku.</p></div>
  <div class="cards">
    <a class="card" href="dabrowka-01.html"><img src="img/ab-naroznik-dzien.jpg" alt="Wizualizacja hali AB w CEL PARK Dąbrówka.01" loading="lazy"><div class="in"><span class="tag">w sprzedaży · oddanie 2027</span><b>Dąbrówka.01</b><span>6 lokali ekspozycyjno-magazynowych · {USABLE:.0f} m² pow. użytkowej · ul. Poznańska, 300 m od węzła S11</span></div></a>
    <div class="card soon"><div class="in"><b>Kolejne lokalizacje</b><span>w przygotowaniu. Masz działkę przy węźle drogi ekspresowej w Wielkopolsce albo szukasz lokalu w innym miejscu? Napisz do nas — zbieramy zapytania pod drugą inwestycję.</span><a class="btn btn-ghost" href="kontakt.html" style="justify-self:center;margin-top:.6rem">Porozmawiajmy</a></div></div>
  </div></div></section>
<section><div class="wrap">
  <div class="section-head"><p class="eyebrow">Dlaczego CEL PARK</p><h2>Cztery rzeczy, które odróżniają CEL PARK od zwykłej hali.</h2></div>
  <div class="pillars">
    <div class="pillar"><b>Design, nie standard.</b><p>Grafitowa elewacja z pionowych płyt warstwowych, czarna stolarka, witryna we wnęce z liniowym LED, logotyp na dachu. Obiekt, który pracuje na Twoją markę, zanim klient wejdzie do środka.</p></div>
    <div class="pillar"><b>300 m od S11.</b><p>Węzeł Poznań-Dąbrówka tuż obok, A2 w 6 km, centrum Poznania w kwadrans. Klient dojeżdża bez błądzenia, dostawa podjeżdża pod bramę od zaplecza.</p></div>
    <div class="pillar"><b>To Ty decydujesz.</b><p>Salon, showroom, serwis, magazyn, e-commerce, pracownia. Układ z projektu jest propozycją; ściany zaplecza, antresolę i instalacje ustalamy z Tobą na etapie budowy.</p></div>
    <div class="pillar"><b>Rodzinny inwestor.</b><p>{INVESTOR}: stacje CEL od 2014 roku, serwis z OSKP, salon CELCAMP. Budujemy u siebie, obok własnych obiektów, i zostajemy sąsiadami na lata.</p></div>
  </div></div></section>
{band_img("ab-front-wieczor", "Wieczorem obiekt pracuje na Twoją markę.", "Podświetlone wnęki wejściowe, linie LED wzdłuż witryn, logotyp na dachu. Z ul. Poznańskiej i z węzła S11 widać go z daleka.", tall=True)}
<section><div class="wrap">
  <div class="section-head"><p class="eyebrow">Jak to działa</p><h2>Od wyboru lokalu do kluczy w 2027.</h2><p class="lead">Umowę podpisujemy na etapie budowy. To nie tylko cena — to czas, w którym możesz dopasować lokal do swojej firmy.</p></div>
  <div class="steps">
    <div class="step"><b>Wybierz lokal</b><p>Sześć lokali w trzech halach, trzy terminy oddania. Pomożemy dobrać położenie — przy stacji, przy Logistycznej, z narożnikiem albo w środku hali.</p></div>
    <div class="step"><b>Kup albo wynajmij</b><p>Sprzedaż od 1 000 zł/m² netto jako odrębna własność z udziałem w gruncie, albo najem długoterminowy. Umowa rezerwacyjna, potem deweloperska lub najmu.</p></div>
    <div class="step"><b>Ustalmy układ wnętrza</b><p>Na etapie budowy decydujesz o ścianach zaplecza, antresoli, instalacjach i wykończeniu sali sprzedaży. Zmiany wprowadzamy przed wykonaniem danego etapu.</p></div>
    <div class="step"><b>Odbierz klucze</b><p>Hala AB w II kwartale 2027, CD w III, EF w IV kwartale 2027. Lokal w stanie deweloperskim albo wykończony pod Twoją działalność.</p></div>
  </div></div></section>
<section class="band"><div class="wrap grid-2">
  <div><p class="eyebrow">O nas</p><h2 style="margin-top:1rem">Firma rodzinna. Wspólny kierunek.</h2><p class="lead" style="margin-top:1rem">Od pierwszej stacji CEL w Dąbrówce w 2014 roku, przez serwis i stację kontroli pojazdów, po salon CELCAMP w 2025. CEL PARK to kolejny krok rodziny Kaczmarków: nieruchomości komercyjne projektowane tak, jakbyśmy sami mieli w nich pracować — bo w Dąbrówce pracujemy od lat.</p><p style="margin-top:1.4rem"><a class="btn btn-solid" href="o-nas.html">Poznaj Kaczmarków</a></p></div>
  <figure class="figure"><img src="img/detal-pylon.jpg" alt="Pylon CEL PARK przed wejściem do lokali" loading="lazy"><figcaption>Pylon z oznaczeniem lokali przy wjeździe od ul. Poznańskiej.</figcaption></figure>
</div></section>'''
    body += contact_block()
    return body

def page_inv():
    stages = "".join(f'<div><b>{d}</b><span>etap {s} · hala {h} · lokale {" i ".join(u)}</span></div>' for s, h, d, u in STAGES)
    ulist = "".join(f'<li><a href="lokal-{u.lower()}.html"><span class="l">{u}</span><span class="m"><b>{v["side"]}</b>{USABLE:.0f} m² · witryna {v["front"]} · oddanie {v["deliv"]}</span><span class="st">dostępny</span></a></li>' for u, v in UNITS.items())
    spec = "".join(f'<div><b>{k}</b><span>{v}</span></div>' for k, v in SPEC)
    pois = "".join(f'<div><b>{dist}</b><span>{k} — {d}</span><i>{t}</i></div>' for k, d, dist, t in POIS)
    prog = "".join(f'<div class="zone{" hi" if nr == "01" else ""}"><div><b>{nr} · {nm}</b><span>{where}</span></div><span class="a">{a:.2f} m²</span></div>' for nr, nm, a, where in PROGRAM[:4]) + \
           f'<div class="zone"><div><b>05–09 · Zaplecze pracownicze</b><span>biuro, pomieszczenie socjalne, szatnia, toaleta z prysznicem, pomieszczenie porządkowe — pas 3,07 m wzdłuż ściany bocznej</span></div><span class="a">{sum(a for nr, nm, a, w in PROGRAM[4:]):.2f} m²</span></div>' + \
           f'<div class="zone sum"><div><b>Razem — powierzchnia użytkowa</b><span>w obrysie 18 × 30 m = 540 m²</span></div><span class="a">{USABLE:.2f} m²</span></div>' + \
           '<div class="zone hi"><div><b>Antresola — opcja</b><span>konstrukcja stalowa na +3,30 m nad zapleczem i częścią magazynu: biuro, ekspozycja, magazyn lekki</span></div><span class="a">≈ 125 m²</span></div>'
    uses = "".join(f'<div class="use"><b>{t}</b><span>{d}</span></div>' for t, d in USES)
    faq = "".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ)
    body = hero("hero-dzien", "hero-wieczor", "Dąbrówka.01 · ul. Poznańska · 300 m od węzła S11 · oddanie 2027",
                "To nie jest zwykła hala.",
                f"Sześć lokali ekspozycyjno-magazynowych po {USABLE:.0f} m² powierzchni użytkowej w trzech halach. Witryna na całe 18 m frontu, magazyn i serwis z bramą od zaplecza, elewacja z grafitowych płyt. Kup od 1 000 zł/m² albo wynajmij. Co tu powstanie i jak będzie wyglądać wnętrze — to Ty decydujesz, jeszcze na etapie budowy.",
                '<a class="btn btn-solid" href="#lokale">Wybierz lokal</a><a class="btn btn-ghost" href="#lokalizacja">Zobacz, jak dojechać</a>')
    body += facts(FACTS_INV)
    body += f'''<section id="o-inwestycji"><div class="wrap grid-2">
  <div><p class="eyebrow">O inwestycji</p><h2 style="margin-top:1rem">Elegancja na zewnątrz. Czysta, wysoka przestrzeń w środku.</h2>
    <ul class="list" style="margin-top:1.6rem">
      <li><span class="k">Lokal</span><span><b>18 × 30 m, {USABLE:.0f} m² pow. użytkowej</b> (540 m² w obrysie), wysokość 6,35 m pod dach, posadzka 5 t/m²</span></li>
      <li><span class="k">Front</span><span>witryna słupowo-ryglowa we wnęce 2 m na całej szerokości, czarna stolarka, wejście dla klientów, podświetlenie LED</span></li>
      <li><span class="k">Zaplecze</span><span>brama segmentowa 3 × 3 m i drzwi serwisowe od wewnętrznej drogi dostawczej, miejsce na kontener</span></li>
      <li><span class="k">Forma</span><span>sprzedaż jako odrębna własność lokalu z udziałem w gruncie (od 1 000 zł/m² netto) albo najem długoterminowy</span></li>
      <li><span class="k">Etapy</span><span>hala AB — II kw. 2027 · hala CD — III kw. 2027 · hala EF — IV kw. 2027</span></li>
      <li><span class="k">Inwestor</span><span>{INVESTOR}, Dąbrówka — właściciel stacji CEL, serwisu z OSKP i salonu CELCAMP</span></li>
    </ul></div>
  <div class="prose">
    <p>Dąbrówka.01 to kameralny park trzech hal przy ul. Poznańskiej w Dąbrówce pod Poznaniem — między stacją paliw CEL a parkiem logistycznym, 300 m od węzła Poznań-Dąbrówka na drodze ekspresowej S11. Każda hala mieści dwa lokale po około 18 × 30 m, rozdzielone ścianą oddzielenia pożarowego. Hale AB i CD otwierają się witrynami na ul. Poznańską i parking dla klientów, hala EF — na ul. Logistyczną.</p>
    <p>Lokal powstał dla firm, dla których budynek jest wizytówką: salonów i showroomów, serwisów, sklepów z zapleczem magazynowym, e-commerce, pracowni. Przeszklony front sprzedaje, zaplecze pracuje. Z przodu sala sprzedaży na całej szerokości lokalu (125 m²), za nią magazyn (229 m²) doświetlony świetlikami, przy tylnej ścianie serwis z bramą (107 m²), a wzdłuż ściany bocznej pas zaplecza pracowniczego: biuro, socjal, szatnia, toaleta z prysznicem. Toaleta dla klientów jest przy sali sprzedaży.</p>
    <p>Budowa rusza w 2026 roku, a umowy podpisujemy w jej trakcie. To ważne: na etapie budowy wspólnie ustalamy układ ścian, antresolę i instalacje, więc w 2027 roku odbierasz lokal dopasowany do swojej działalności.</p>
  </div></div></section>
{band_img("ab-front-dzien", "Witryna na całe 18 metrów frontu.", "Fasada słupowo-ryglowa we wnęce 2 m, czarna stolarka, wejście dla klientów na wprost parkingu. Hala AB od strony ul. Poznańskiej.", tall=True)}
<section id="lokalizacja" class="band"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Lokalizacja i dojazd</p><h2>300 m od węzła S11. Kwadrans od Poznania.</h2><p class="lead">Działka leży przy ul. Poznańskiej w Dąbrówce (gmina Dopiewo), między stacją paliw CEL z okręgową stacją kontroli pojazdów a parkiem logistycznym. Z węzła Poznań-Dąbrówka na S11 jedzie się tu minutę: zjazd, rondo, ul. Poznańska i wjazd na parking. Z Poznania, Skórzewa i Dopiewa dojeżdżasz bez wjeżdżania w osiedla, a dostawy obsługuje ul. Logistyczna i wewnętrzna droga za halami.</p></div>
  <figure class="figure"><img src="img/aerial-wide.jpg" width="2400" height="1504" alt="Zdjęcie lotnicze: węzeł S11 Poznań-Dąbrówka, stacja CEL, CEL PARK przy ul. Poznańskiej, park logistyczny" loading="lazy"><figcaption>Zdjęcie lotnicze z naniesionym projektem: węzeł S11, stacja CEL, wjazd z ul. Poznańskiej, park logistyczny. Podkład: ortofotomapa GUGiK.</figcaption></figure>
  <figure class="figure" style="margin-top:2rem"><img src="img/aerial-local.jpg" width="2400" height="1504" alt="Zdjęcie lotnicze działki z projektem: wjazd z ul. Poznańskiej, parking, trzy hale, droga dostawcza" loading="lazy"><figcaption>Zbliżenie: wjazd dla klientów z ul. Poznańskiej, 33 miejsca postojowe przed witrynami, droga dostawcza i bramy od zaplecza.</figcaption></figure>
  <div class="grid-2" style="margin-top:3rem">
    <div><p class="eyebrow">Dojazd</p><h3 style="margin:.8rem 0 1.2rem;font-size:1.5rem">Z węzła S11: zjazd, rondo, ul. Poznańska, wjazd.</h3><div class="poi">{pois}</div>
      <p class="note" style="margin-top:1rem">Czasy przejazdu poza godzinami szczytu. Adres: {ADDR}. Współrzędne: {SITE_LL[0]}, {SITE_LL[1]}.</p>
      <p style="margin-top:1.2rem;display:flex;gap:.6rem;flex-wrap:wrap"><a class="btn btn-solid" href="{MAPS_ROUTE}" target="_blank" rel="noopener">Wyznacz trasę</a><a class="btn btn-ghost" href="{MAPS_SITE}" target="_blank" rel="noopener">Otwórz w Mapach Google</a></p></div>
    {map_embed(MAPS_EMBED, "Mapa Google: CEL PARK Dąbrówka.01")}
  </div>
</div></section>
<section id="lokale"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Lokale A–F</p><h2>Wybierz lokal na planie.</h2><p class="lead">Wszystkie lokale mają ten sam program i powierzchnię. Różnią się halą, terminem oddania, kierunkiem witryny i stroną ściany wspólnej. Lokale A, C i E odpowiadają rysunkowi projektu, B, D i F są jego lustrzanym odbiciem. Kliknij lokal, aby zobaczyć kartę z rzutem.</p></div>
  <div class="picker"><div>{site_svg()}</div><ul class="ulist">{ulist}</ul></div>
  <div class="price" style="margin-top:2.5rem">
    <div><span>Sprzedaż</span><b>od 1 000 zł/m²</b><span>netto + VAT · odrębna własność lokalu z udziałem w gruncie, parkingu i częściach wspólnych</span></div>
    <div><span>Najem</span><b>zapytaj o stawkę</b><span>umowa długoterminowa, lokal w stanie deweloperskim albo wykończony pod najemcę</span></div>
    <div><span>Połączenie lokali</span><b>≈ 1 030 m²</b><span>dwa sąsiednie lokale w jednej hali jako jedna przestrzeń z witryną na 36 m</span></div>
  </div>
  <p class="note" style="margin-top:1.2rem">Powierzchnie użytkowe wg zestawienia projektanta (KONTUR, projekt budowlany 07/2026); wartości ostateczne wynikną z inwentaryzacji powykonawczej. Cena dotyczy stanu deweloperskiego.</p>
</div></section>
<section id="standard" class="band"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Standard wykończenia</p><h2>Jakość, którą widać z drogi i czuć w środku.</h2><p class="lead">Elewacja z pionowych grafitowych płyt warstwowych, czarna stolarka, LED we wnękach i prosta, wysoka przestrzeń bez zbędnych słupów. Obiekt zaprojektowany jak salon, zbudowany jak hala.</p></div>
  <div class="grid-2"><div class="spec">{spec}</div>
    <div style="display:grid;gap:1rem"><figure class="figure"><img src="img/detal-podcien.jpg" alt="Detal wnęki wejściowej: czarna stolarka, jasna wnęka, trawy ozdobne" loading="lazy"><figcaption>Wnęka wejściowa głębokości 2 m: jasna okładzina, czarna stolarka, liniowy LED, rabaty z trawami ozdobnymi.</figcaption></figure>
    <figure class="figure"><img src="img/ab-tyl-dzien.jpg" alt="Tylna elewacja hali AB z bramami segmentowymi i drogą dostawczą" loading="lazy"><figcaption>Zaplecze: brama 3 × 3 m i drzwi serwisowe do każdego lokalu, okna pomieszczeń zaplecza, droga dostawcza.</figcaption></figure></div></div>
</div></section>
<section id="wnetrze"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Wnętrze i układ</p><h2>Układ z projektu to punkt wyjścia. Resztę ustalamy razem.</h2><p class="lead">Beton zacierany na posadzce, żelbetowe słupy tuż za witryną, stalowe dźwigary pod dachem, światło ze świetlików. Projekt budowlany (KONTUR) dzieli lokal na salę sprzedaży, magazyn, serwis i pas zaplecza wzdłuż ściany bocznej. Każdy z tych elementów można przesunąć, powiększyć albo pominąć — decyzje zapadają na etapie budowy.</p></div>
  <div class="program"><div class="zones">{prog}</div>
    <div style="display:grid;gap:1.4rem">{layout_callout()}
    <p class="quote">Salon, serwis, showroom, magazyn, pracownia. <em>To Ty decydujesz,</em> co będzie za witryną.</p></div></div>
  <div style="margin-top:2.5rem">
    <div class="tabs" role="tablist" aria-label="Rysunki"><button role="tab" aria-selected="true" aria-controls="p1" id="t1">Plan zagospodarowania</button><button role="tab" aria-selected="false" aria-controls="p2" id="t2">Rzut lokalu — parter</button><button role="tab" aria-selected="false" aria-controls="p3" id="t3">Rzut lokalu — z antresolą</button></div>
    <div class="plan-img" id="p1" role="tabpanel" aria-labelledby="t1"><img src="img/plan-zagospodarowania.jpg" width="3200" height="2000" alt="Plan zagospodarowania terenu: trzy hale A–F, parking od ul. Poznańskiej, droga dostawcza z tyłu" loading="lazy"></div>
    <div class="plan-img" id="p2" role="tabpanel" aria-labelledby="t2" hidden><img src="img/rzut-lokal-a-parter.jpg" width="2400" height="1702" alt="Rzut lokalu A wg projektu budowlanego: sala sprzedaży, magazyn, serwis, pas zaplecza" loading="lazy"></div>
    <div class="plan-img" id="p3" role="tabpanel" aria-labelledby="t3" hidden><img src="img/rzut-lokal-a-antresola.jpg" width="2400" height="1702" alt="Rzut lokalu A z antresolą ≈125 m² na poziomie +3,30 m" loading="lazy"></div>
    <p class="note" style="margin-top:1rem">Pliki: <a href="pdf/plan-zagospodarowania.pdf" target="_blank" rel="noopener">plan zagospodarowania (PDF)</a> · karty lokali A–F z rzutami do pobrania na stronach poszczególnych lokali.</p></div>
</div></section>
{band_img("ef-front-wieczor", "Etap III. Hala EF od ul. Logistycznej.", "Lokale E i F z witrynami na wschód, bramy od wewnętrznej drogi dostawczej. Oddanie: IV kwartał 2027.")}
<section id="dla-kogo"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Dla kogo</p><h2>Co będzie za witryną? To Ty decydujesz.</h2><p class="lead">Lokal łączy ekspozycję z zapleczem, które naprawdę pracuje. Kilka scenariuszy, które pasują od razu, bez przebudowy — i każdy można jeszcze dopasować na etapie budowy.</p></div>
  <div class="uses">{uses}</div>
</div></section>
<section id="galeria" class="band"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Galeria</p><h2>Każda elewacja. Dzień i wieczór.</h2><p class="lead">Wizualizacje projektowe trzech hal. Kliknij, aby powiększyć.</p></div>{gallery(GALLERY)}
</div></section>
<section id="faq"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Pytania</p><h2>Najczęstsze pytania.</h2></div>
  <div class="faq">{faq}</div>
</div></section>
<section id="harmonogram" class="band"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Harmonogram</p><h2>Budowa rusza w 2026. Klucze w 2027.</h2><p class="lead">Trzy hale, trzy etapy, trzy kwartały 2027 roku. Rezerwacje i umowy podpisujemy już teraz — im wcześniej, tym więcej decyzji o wnętrzu zostaje po Twojej stronie.</p></div>
  <div class="timeline"><div><b>2026</b><span>pozwolenie na budowę, start budowy, rezerwacje i umowy na etapie budowy, ustalanie układów wnętrz</span></div>{stages}</div>
</div></section>'''
    body += contact_block()
    return body

def page_unit(u):
    v = UNITS[u]; im = HALL_IMG[v["hall"]]; other = [x for x in UNITS if UNITS[x]["hall"] == v["hall"] and x != u][0]; L = u.lower()
    prog_rows = "".join(f'<tr><td>{nr}</td><td>{nm}<small>{where}</small></td><td style="text-align:right">{a:.2f} m²</td></tr>' for nr, nm, a, where in PROGRAM)
    gal = [(im["day"], f"Hala {v['hall']} · front", True), (im["night"], f"Hala {v['hall']} · wieczór", False), (im["rear"], f"Hala {v['hall']} · zaplecze z bramami", False),
           (im["side"], f"Hala {v['hall']} · elewacja boczna", False), (im["side2"], f"Hala {v['hall']} · elewacja boczna", False), ("detal-podcien", "Wnęka wejściowa · detal", False), ("detal-pylon", "Pylon z oznaczeniem lokali", False)]
    body = hero(im["day"], im["night"], f"Dąbrówka.01 · hala {v['hall']} · etap {v['stage']} · oddanie {v['deliv']}",
                f"Lokal {u}.<br>{'Z własnym narożnikiem.' if u in 'ACE' else 'Z witryną na całą szerokość.'}",
                f"{v['side'][0].upper() + v['side'][1:]}, {v['wall']}. {USABLE:.0f} m² powierzchni użytkowej: sala sprzedaży za witryną {v['front']}, magazyn i serwis z bramą od zaplecza, pas zaplecza pracowniczego. Oddanie: {v['deliv']}. Układ wnętrza ustalamy z Tobą na etapie budowy.",
                f'<a class="btn btn-solid" href="#kontakt">Zapytaj o lokal {u}</a><a class="btn btn-ghost" href="dabrowka-01.html#lokale">Inne lokale</a>')
    body += facts([(f"Lokal {u}", f"hala {v['hall']} · etap {v['stage']} · dostępny"), (f"{USABLE:.0f} m²", "pow. użytkowej · 540 m² w obrysie"), ("18 × 30 m", "witryna × głębokość"), ("6,35 m", "wysokości pod dach"), (v["deliv"], "oddanie"), ("od 1 000 zł/m²", "sprzedaż, netto + VAT")])
    body += f'''<section><div class="wrap"><p class="crumbs"><a href="index.html">CEL PARK</a> › <a href="dabrowka-01.html">Dąbrówka.01</a> › <a href="dabrowka-01.html#lokale">Lokale</a> › Lokal {u}</p>
  <div class="picker" style="margin-top:2rem"><div>{site_svg(active=u)}</div>
  <div><p class="eyebrow">Położenie</p><h2 style="margin-top:1rem">Lokal {u} w hali {v["hall"]}.</h2><p class="lead" style="margin-top:1rem">{v["side"][0].upper() + v["side"][1:]}, {v["wall"]}. {"Wejście dla klientów i witryna od ul. Poznańskiej, parking bezpośrednio przed lokalem, brama od wewnętrznej drogi dostawczej z tyłu działki." if u in "ABCD" else "Witryna i wejście od strony ul. Logistycznej, parking przed lokalem, brama od wewnętrznej drogi dostawczej."}</p>
  <ul class="list" style="margin-top:1.2rem"><li><span class="k">Sąsiad</span><span>lokal {other} (ściana oddzielenia pożarowego REI 60; możliwe połączenie lokali {u}+{other} w ≈ 1 030 m²)</span></li><li><span class="k">Parking</span><span>miejsca dla klientów przed witryną, stacja ładowania EV i stojaki rowerowe przy wejściu</span></li><li><span class="k">Etap</span><span>{v["stage"]} · oddanie {v["deliv"]}</span></li><li><span class="k">Dojazd</span><span><a href="{MAPS_ROUTE}" target="_blank" rel="noopener">wyznacz trasę</a> · 300 m od węzła S11</span></li></ul></div></div>
</div></section>
<section class="band"><div class="wrap grid-2">
  <div><div class="section-head"><p class="eyebrow">Program lokalu</p><h2>Układ wg projektu budowlanego. Do zmiany, jeśli chcesz.</h2><p class="lead">Powierzchnie pomieszczeń wg zestawienia projektanta (KONTUR). Lokal {u} {"jest zgodny z rysunkiem projektu" if not v["mirror"] else "jest lustrzanym odbiciem rysunku projektu"} — pas zaplecza biegnie wzdłuż ściany {"zewnętrznej" if u in "ACE" else "zewnętrznej (od strony lokalu sąsiedniego hali)" if False else "zewnętrznej"}. Antresola (+3,30 m, ≈ 125 m²) jest opcją.</p></div>
    <div class="table-wrap"><table class="units"><thead><tr><th>Nr</th><th>Pomieszczenie</th><th style="text-align:right">Pow.</th></tr></thead><tbody>{prog_rows}<tr><td></td><td><b>Razem — powierzchnia użytkowa</b></td><td style="text-align:right"><b>{USABLE:.2f} m²</b></td></tr><tr><td></td><td>Antresola — opcja</td><td style="text-align:right">≈ 125 m²</td></tr></tbody></table></div>
    <div style="margin-top:1.4rem">{layout_callout()}</div></div>
  <div><div class="tabs" role="tablist" aria-label="Rzut lokalu"><button role="tab" aria-selected="true" aria-controls="p2" id="t2">Parter</button><button role="tab" aria-selected="false" aria-controls="p3" id="t3">Z antresolą</button></div>
    <div class="plan-img" id="p2" role="tabpanel" aria-labelledby="t2"><img src="img/rzut-lokal-{L}-parter.jpg" width="2400" height="1702" alt="Rzut lokalu {u}, wariant parterowy" loading="lazy"></div>
    <div class="plan-img" id="p3" role="tabpanel" aria-labelledby="t3" hidden><img src="img/rzut-lokal-{L}-antresola.jpg" width="2400" height="1702" alt="Rzut lokalu {u} z antresolą" loading="lazy"></div>
    <p class="note" style="margin-top:.8rem">Do pobrania: <a href="pdf/karta-lokal-{L}.pdf" target="_blank" rel="noopener">karta lokalu {u} — parter (PDF)</a> · <a href="pdf/karta-lokal-{L}-antresola.pdf" target="_blank" rel="noopener">wariant z antresolą (PDF)</a> · <a href="pdf/plan-zagospodarowania.pdf" target="_blank" rel="noopener">plan zagospodarowania (PDF)</a></p></div>
</div></section>
<section><div class="wrap"><div class="section-head"><p class="eyebrow">Hala {v["hall"]}</p><h2>Wizualizacje hali {v["hall"]}.</h2></div>{gallery(gal)}</div></section>
<section class="band"><div class="wrap"><div class="section-head"><p class="eyebrow">Standard</p><h2>Co dostajesz z lokalem {u}.</h2></div><div class="spec">{"".join(f'<div><b>{k}</b><span>{x}</span></div>' for k, x in SPEC)}</div></div></section>'''
    body += contact_block(unit=u, title=f"Zapytaj o lokal {u}.", lead=f"Napisz, czy interesuje Cię zakup, czy najem i jaką działalność planujesz — podpowiemy, jak dopasować układ. Odpowiadamy w ciągu jednego dnia roboczego.")
    return body

def page_about():
    body = f'''<section class="hero on-ink" id="hero" style="padding-block:0"><div class="hero-media" style="aspect-ratio:21/9;max-height:620px"><img class="day" src="img/ab-front-wieczor.jpg" alt=""></div>
<div class="wrap hero-copy"><p class="eyebrow">O nas</p><h1>Firma rodzinna.<br>Wspólny kierunek.</h1><p class="lead">CEL PARK to marka nieruchomości komercyjnych rodziny Kaczmarków z Dąbrówki — tej samej, która od 2014 roku prowadzi stacje paliw CEL, serwis z okręgową stacją kontroli pojazdów i salon CELCAMP. Inwestorem Dąbrówki.01 jest {INVESTOR}.</p></div></section>
<section><div class="wrap grid-2">
  <div class="prose"><p class="eyebrow">Skąd pomysł</p><h2 style="margin-top:.4rem">Budujemy to, czego sami szukaliśmy.</h2>
    <p>Przez lata rozwijania stacji, serwisu i salonu kamperów szukaliśmy lokali, które łączą trzy rzeczy: reprezentacyjny front dla klienta, zaplecze, w którym da się pracować, i dojazd, którego nie trzeba tłumaczyć przez telefon. Zwykle trzeba było wybierać — albo hala przy drodze bez witryny, albo lokal usługowy bez bramy i wysokości. CEL PARK powstał, żeby tego wyboru nie było.</p>
    <p>Dąbrówka.01 powstaje na naszej działce, obok naszej stacji, przy węźle, przez który sami jeździmy codziennie. Projekt wykonało poznańskie biuro KONTUR, a wykonawcą są firmy, z którymi budowaliśmy wcześniejsze obiekty. Zostajemy sąsiadami kupujących i najemców na lata — dlatego zależy nam na detalu: od elewacji po koszony trawnik.</p></div>
  <div class="timeline" style="grid-template-columns:1fr;gap:1.2rem">
    <div><b>2014</b><span>pierwsza stacja paliw CEL w Dąbrówce, ul. Polna 1</span></div>
    <div><b>2016</b><span>serwis samochodowy i Okręgowa Stacja Kontroli Pojazdów, ul. Polna 3</span></div>
    <div><b>2018</b><span>stacja CEL w Biedrusku ze sklepem i myjniami</span></div>
    <div><b>2022</b><span>CEL Czapury: stacja z galerią handlowo-usługową i myjnią; przedstawicielstwo HOTOMOBIL</span></div>
    <div><b>2025</b><span>salon CELCAMP w Dąbrówce, autoryzowany dealer WEINSBERG (Knaus Tabbert)</span></div>
    <div><b>2026–2027</b><span>CEL PARK Dąbrówka.01: trzy hale, sześć lokali ekspozycyjno-magazynowych</span></div>
  </div></div></section>
<section class="band"><div class="wrap">
  <div class="section-head"><p class="eyebrow">Marki</p><h2>CEL · CELCAMP · CEL PARK</h2></div>
  <div class="pillars">
    <div class="pillar"><b>CEL</b><p>Stacje paliw w Dąbrówce, Biedrusku i Czapurach, serwis samochodowy i OSKP. Miejsca, do których chce się wracać.</p></div>
    <div class="pillar"><b>CELCAMP</b><p>Sprzedaż, wynajem i serwis kamperów, przyczep kempingowych i kapsuł HOTOMOBIL. Salon przy ul. Polnej 2 w Dąbrówce.</p></div>
    <div class="pillar"><b>CEL PARK</b><p>Powierzchnie ekspozycyjno-magazynowe na sprzedaż i wynajem przy węzłach dróg ekspresowych. Pierwsza inwestycja: Dąbrówka.01.</p></div>
  </div>
  <div class="pillars" style="margin-top:2.5rem">
    <div class="pillar"><b>Własny grunt, własne pieniądze.</b><p>Inwestycję realizujemy na własnej działce i z własnych środków. Nie zależymy od tempa sprzedaży, żeby dokończyć budowę.</p></div>
    <div class="pillar"><b>Sąsiad, nie fundusz.</b><p>Po oddaniu nie znikamy. Stacja, serwis i salon CELCAMP są 400 m dalej, więc o każdej sprawie można porozmawiać na miejscu.</p></div>
    <div class="pillar"><b>Decyzje na miejscu.</b><p>Zmiana układu, termin, forma umowy — rozmawiasz z właścicielem, nie z działem obsługi.</p></div>
  </div>
  <p class="note" style="margin-top:2rem">Więcej o firmie i wszystkich lokalizacjach: <a href="https://www.kaczmarki.eu/" target="_blank" rel="noopener">kaczmarki.eu</a>.</p>
</div></section>'''
    body += contact_block(title="Porozmawiajmy.", lead="O lokalu w Dąbrówce.01, o najmie dla Twojej firmy albo o kolejnej lokalizacji CEL PARK.")
    return body

def page_contact():
    body = f'''<section style="padding-bottom:0"><div class="wrap"><p class="crumbs"><a href="index.html">CEL PARK</a> › Kontakt</p></div></section>'''
    body += contact_block(title="Zapytaj o lokal. Albo o cokolwiek innego.", lead="Sprzedaż i najem lokali w Dąbrówce.01, współpraca przy kolejnych lokalizacjach, pytania o budowę i układ wnętrza. Odpowiadamy w ciągu jednego dnia roboczego; spotkanie na działce umawiamy od ręki.")
    body += f'''<section><div class="wrap grid-2">
  <div><p class="eyebrow">Biuro sprzedaży</p><h2 style="margin-top:1rem">Przy stacji CEL w Dąbrówce.</h2><p class="lead" style="margin-top:1rem">{OFFICE} — przy serwisie CEL i stacji kontroli pojazdów, 400 m od placu budowy CEL PARK. Z węzła S11 Poznań-Dąbrówka: minuta. Telefon: <a href="tel:{PHONE_INTL}">+48 {PHONE}</a>, e-mail: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
    <p style="margin-top:1.4rem;display:flex;gap:.6rem;flex-wrap:wrap"><a class="btn btn-solid" href="https://www.google.com/maps/dir/?api=1&destination={OFFICE_LL[0]},{OFFICE_LL[1]}" target="_blank" rel="noopener">Trasa do biura</a><a class="btn btn-ghost" href="{MAPS_ROUTE}" target="_blank" rel="noopener">Trasa na plac budowy</a></p></div>
  {map_embed(MAPS_EMBED_OFFICE, "Mapa Google: biuro sprzedaży CEL PARK, ul. Polna 3, Dąbrówka")}
</div></section>'''
    return body

# ------------------------------------------------------------------ build
PAGES = {
 "index.html": ("CEL PARK", page_index, "CEL PARK — powierzchnie ekspozycyjno-magazynowe na sprzedaż i wynajem przy węzłach dróg ekspresowych. Pierwsza inwestycja: Dąbrówka.01 przy S11, oddanie 2027.", ""),
 "dabrowka-01.html": ("CEL PARK Dąbrówka.01", page_inv, f"Dąbrówka.01: sześć lokali ekspozycyjno-magazynowych po {USABLE:.0f} m², 300 m od węzła S11 Poznań-Dąbrówka. Sprzedaż od 1 000 zł/m² lub najem. Oddanie 2027. To Ty decydujesz o układzie.", "lokale"),
 "o-nas.html": ("O nas — CEL PARK", page_about, f"CEL PARK to marka nieruchomości komercyjnych rodziny Kaczmarków: stacje CEL od 2014, CELCAMP, teraz Dąbrówka.01. Inwestor: {INVESTOR}.", "o-nas"),
 "kontakt.html": ("Kontakt — CEL PARK", page_contact, f"Zapytaj o lokal w CEL PARK Dąbrówka.01: {EMAIL}, +48 {PHONE}. Biuro sprzedaży: {OFFICE}.", "kontakt"),
}
for u in UNITS: PAGES[f"lokal-{u.lower()}.html"] = (f"Lokal {u} — CEL PARK Dąbrówka.01", (lambda uu: (lambda: page_unit(uu)))(u), f"Lokal {u} w CEL PARK Dąbrówka.01: {USABLE:.0f} m² pow. użytkowej, hala {UNITS[u]['hall']}, oddanie {UNITS[u]['deliv']}. Sprzedaż od 1 000 zł/m² lub najem.", "lokale")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fn, (title, fnc, desc, active) in PAGES.items():
        body = fnc()
        htmlx = full_doc(title, body, desc, active)
        open(os.path.join(OUT, fn), "w").write(htmlx)
        print(fn, len(htmlx) // 1024, "KB")
    for d in ("img", "pdf"):
        dst = os.path.join(OUT, d)
        if os.path.isdir(dst): shutil.rmtree(dst)
        shutil.copytree(os.path.join(SRC, d), dst)
    for f in ("kontakt.php", "favicon.svg"):
        if os.path.exists(os.path.join(SRC, f)): shutil.copy(os.path.join(SRC, f), OUT)
    open(os.path.join(OUT, "robots.txt"), "w").write("User-agent: *\nAllow: /\nSitemap: https://celpark.pl/sitemap.xml\n")
    open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>https://celpark.pl/{fn}</loc></url>\n" for fn in PAGES) + "</urlset>\n")
    open(os.path.join(OUT, ".htaccess"), "w").write("AddDefaultCharset UTF-8\nErrorDocument 404 /index.html\n<IfModule mod_deflate.c>\nAddOutputFilterByType DEFLATE text/html text/css application/javascript image/svg+xml\n</IfModule>\n<IfModule mod_expires.c>\nExpiresActive On\nExpiresByType image/jpeg \"access plus 30 days\"\nExpiresByType image/svg+xml \"access plus 30 days\"\n</IfModule>\n")
    print("done ->", OUT)
