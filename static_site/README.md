# Statická prezentační stránka pro Finanční Intelligence Dashboard

Tato statická stránka slouží jako prezentační web pro Finanční Intelligence Dashboard. Stránka byla vytvořena tak, aby mohla být hostována zdarma na různých platformách.

## Možnosti pro hosting zdarma

### 1. Hosting na GitHub Pages

1. Vytvořte nový GitHub repozitář
2. Nahrajte obsah složky `static_site` do repozitáře
3. V nastavení repozitáře povolte GitHub Pages a vyberte větev `main`
4. Vaše stránka bude dostupná na adrese `https://[váš-username].github.io/[název-repozitáře]/`

### 2. Hosting na Netlify

1. Zaregistrujte se na [Netlify](https://www.netlify.com/) (je to zdarma)
2. Vytvořte nový site a nahrajte obsah složky `static_site`
3. Netlify automaticky nasadí vaši stránku
4. Získáte adresu ve formátu `https://[náhodné-id].netlify.app`
5. Můžete nastavit vlastní doménu třetí úrovně, např. `financni-dashboard.netlify.app`

### 3. Hosting na Vercel

1. Zaregistrujte se na [Vercel](https://vercel.com/) (je to zdarma)
2. Vytvořte nový projekt a nahrajte obsah složky `static_site`
3. Vercel automaticky nasadí vaši stránku
4. Získáte adresu ve formátu `https://[název-projektu].vercel.app`

## Úprava odkazů

Před nasazením nezapomeňte upravit odkazy v souboru `index.html`, které směrují na vaši instanci dashboardu v Replitu. Nahraďte `https://replit.com/@replit/Financial-Dashboard` za skutečnou adresu vašeho projektu.