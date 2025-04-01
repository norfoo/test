# Návod na nasazení HTML prezentační stránky

Připravil jsem pro vás statickou HTML webovou stránku, kterou můžete hostovat zdarma a sdílet s ostatními. Níže najdete podrobný návod, jak stránku nasadit:

## Obsah vytvořené webové stránky:

- **Futuristický design** odpovídající vašemu finančnímu dashboardu
- **Responzivní zobrazení** pro mobily a tablety
- **Interaktivní prvky** s animacemi
- **Prezentace funkcí** vašeho dashboardu
- **Aktuální cena zlata** s dynamickou aktualizací
- **Tlačítka** pro přístup k dashboardu

## Možnosti pro hosting zdarma (bez vlastní domény):

### 1. GitHub Pages (nejjednodušší)

1. Vytvořte si účet na [GitHub.com](https://github.com) (pokud ještě nemáte)
2. Vytvořte nový repozitář (pojmenujte ho např. "financni-dashboard")
3. Stáhněte si soubor `financni-dashboard-web.tar.gz` z vašeho Replit projektu
4. Rozbalte archiv a nahrajte všechny soubory do nového GitHub repozitáře
5. V nastavení repozitáře povolte GitHub Pages (Settings -> Pages)
6. Jako zdroj vyberte větev "main" a složku "/" (root)
7. Klikněte na "Save" a vyčkejte na nasazení
8. GitHub vám poskytne URL ve formátu `https://vaše-jméno.github.io/financni-dashboard/`

### 2. Netlify Drop (velmi jednoduché)

1. Přejděte na [Netlify Drop](https://app.netlify.com/drop)
2. Rozbalte archiv `financni-dashboard-web.tar.gz`
3. Přetáhněte složku "static_site" (nebo její obsah) do oblasti "Drag and drop your site folder here"
4. Netlify automaticky nahraje a nasadí vaši stránku
5. Získáte URL ve formátu `https://náhodné-jméno.netlify.app`
6. Můžete se zaregistrovat a získat možnost stránku dále upravovat nebo nastavit vlastní subdoménu

### 3. Vercel (pokročilejší, ale stále jednoduché)

1. Vytvořte si účet na [Vercel.com](https://vercel.com)
2. Klikněte na "New Project"
3. Vyberte "Upload" pro nahrání vlastních souborů
4. Nahrajte rozbalený obsah archivu `financni-dashboard-web.tar.gz`
5. Klikněte na "Deploy" a vyčkejte na nasazení
6. Získáte URL ve formátu `https://název-projektu.vercel.app`

## Úprava odkazů na váš dashboard

Než stránku nasadíte, nezapomeňte upravit odkazy v souboru `index.html`:

1. Otevřete soubor `index.html`
2. Vyhledejte všechny výskyty `https://replit.com/@replit/Financial-Dashboard`
3. Nahraďte je skutečnou URL adresou vašeho Replit projektu
4. Teprve poté stránku nasaďte

## Co dál?

Pro trvalou dostupnost vašeho dashboardu doporučuji využít funkci "Deploy" přímo v Replitu. Tím zajistíte, že váš dashboard bude dostupný i když vy sami nebudete mít Replit otevřený. 

1. Klikněte na tlačítko "Deploy" v horní části Replit editoru
2. Následujte instrukce pro nasazení aplikace
3. Po úspěšném nasazení obdržíte trvalou URL adresu
4. Tuto URL pak můžete použít ve vaší HTML prezentační stránce místo odkazu na Replit

Tímto způsobem vytvoříte kompletní řešení, kde prezentační stránka odkazuje na trvale běžící dashboard.