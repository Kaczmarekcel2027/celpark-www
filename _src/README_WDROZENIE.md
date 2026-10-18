# celpark.pl — wdrożenie strony

Strona jest statyczna (HTML/CSS/JS, bez CMS). Folder `site/` to gotowa zawartość serwera.

## Co wgrać
Cały folder `site/` do katalogu głównego domeny (np. `public_html/`):
- `index.html` (marka CEL PARK), `dabrowka-01.html` (inwestycja), `lokal-a.html` … `lokal-f.html`, `o-nas.html`, `kontakt.html`
- `img/` (wizualizacje, mapy, rzuty), `pdf/` (karty lokali, plan), `favicon.svg`, `robots.txt`, `sitemap.xml`, `.htaccess`
- `kontakt.php` — backend formularza (wymaga PHP ≥ 7.4 i działającej funkcji `mail()` lub SMTP na hostingu).

## Domena i poczta (po Twojej stronie)
1. Domena `celpark.pl` → rekord A/CNAME na serwer hostingu.
2. Skrzynka `sprzedaz@celpark.pl` (odbiera zapytania) i nadawca `formularz@celpark.pl` (PHP wysyła z tego adresu; jeśli hosting wymaga, zmień nadawcę w `kontakt.php`).
3. Certyfikat SSL (Let's Encrypt w panelu hostingu) — strona zakłada `https://`.

## Formularz
`kontakt.php` przyjmuje POST z formularza, sprawdza pole-pułapkę (honeypot), waliduje e-mail i wysyła wiadomość. Jeśli serwer nie obsługuje PHP, formularz automatycznie przełącza się na otwarcie programu pocztowego użytkownika z gotową treścią (działa także bez PHP).

## Aktualizacja treści i zdjęć
Strony generuje skrypt `build.py` (Python 3, bez dodatkowych bibliotek):
- dane lokali, etapy, ceny, teksty i lista zdjęć są na górze pliku (`UNITS`, `STAGES`, `SPEC`, `POIS`, `GALLERY`);
- nowe wizualizacje wrzucasz do `img/` pod istniejącymi nazwami (podmiana 1:1) albo dodajesz nową nazwę do `GALLERY`;
- `python3 build.py` → odświeżony folder `site/`.

## Analityka i cookies
Strona nie ustawia cookies ani nie używa zewnętrznych skryptów śledzących (tylko Google Fonts). Jeśli dodasz Google Analytics/Meta Pixel, potrzebny będzie baner zgody.

## Źródła danych
Mapy: BDOT10k i ortofotomapa (Główny Urząd Geodezji i Kartografii). Modele 3D otoczenia: Poly Haven (CC0), ambientCG (CC0), Objaverse/Sketchfab (CC-BY — lista autorów w `data/objaverse_selected_meta.json`).
