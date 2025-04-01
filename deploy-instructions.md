# Pokyny pro sdílení finančního dashboardu

Existují dva způsoby, jak můžete sdílet tento finanční dashboard s ostatními uživateli, aniž byste museli platit za nasazení v Replitu.

## 1. Sdílení přímého odkazu na Replit (pouze pro dobu, kdy je Replit spuštěný)

Když spustíte tento projekt v Replitu, bude dostupný na dočasné URL adrese po dobu, kdy máte Replit otevřený a spuštěný. Tuto URL můžete najít v pravém horním rohu Replit editoru, kde je náhled aplikace.

**Omezení:**
- Dashboard bude dostupný pouze po dobu, kdy máte Replit otevřený v prohlížeči
- Když zavřete prohlížeč nebo se odhlásíte z Replitu, dashboard nebude dostupný
- Více uživatelů může způsobit zpomalení aplikace

## 2. Export statické verze (pro trvalé sdílení)

Pro trvalé sdílení dashboardu můžete vytvořit jeho statickou verzi, kterou lze hostovat na jakékoli bezplatné platformě pro statický web (GitHub Pages, Netlify, Vercel apod.).

### Jak exportovat statickou verzi:

1. Spusťte v Replitu skript pro export statické verze:
   ```bash
   python export_static_site.py
   ```

2. Po dokončení exportu budete mít:
   - Adresář `static_site` obsahující statickou verzi dashboardu
   - Soubor `financni-dashboard-web.tar.gz` - komprimovaný archiv tohoto adresáře

3. Stáhněte soubor `financni-dashboard-web.tar.gz` do svého počítače kliknutím pravým tlačítkem v navigačním panelu Replitu a vybráním "Download".

### Jak nahrát statickou verzi na bezplatný hosting:

#### GitHub Pages (zdarma):
1. Vytvořte nový repozitář na GitHubu
2. Rozbalte stažený archiv na svém počítači
3. Nahrajte rozbalené soubory do vašeho GitHub repozitáře
4. V nastavení repozitáře povolte GitHub Pages z hlavní větve
5. Vaše aplikace bude dostupná na adrese `https://vase-uzivatelske-jmeno.github.io/nazev-repozitare`

#### Netlify (zdarma):
1. Zaregistrujte se na Netlify.com
2. Přetáhněte a pusťte rozbalený adresář `static_site` přímo na stránku Netlify
3. Netlify automaticky nasadí váš web a poskytne vám URL adresu

#### Vercel (zdarma):
1. Zaregistrujte se na Vercel.com
2. Vytvořte nový projekt a nahrajte rozbalené soubory
3. Vercel automaticky rozpozná a nasadí statický web

## Omezení statické verze
Statická verze dashboardu bude mít některá omezení:
- Nebude reagovat na nová data (ukazuje pouze data k času exportu)
- Interaktivní prvky vyžadující server (např. AI chat) nebudou fungovat
- Pro získání aktualizovaných dat budete muset vytvořit novou statickou verzi

## Alternativa: Nasazení pomocí Streamlit Community Cloud (zdarma)
Další možností je použít Streamlit Community Cloud (https://streamlit.io/cloud), který nabízí bezplatné hostování pro Streamlit aplikace. Tato možnost by zachovala plnou interaktivitu a aktuální data.