// JavaScript pro vylepšení interaktivity webové stránky

document.addEventListener('DOMContentLoaded', function() {
    // Animace pro feature karty
    const featureCards = document.querySelectorAll('.feature-card');
    
    featureCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        }, index * 100);
    });
    
    // Aktualizace data v patičce
    const footerYear = document.querySelector('footer');
    if (footerYear) {
        const currentYear = new Date().getFullYear();
        footerYear.innerHTML = footerYear.innerHTML.replace('2025', currentYear);
    }
    
    // Efekt při najetí na tlačítka
    const buttons = document.querySelectorAll('.button');
    buttons.forEach(button => {
        button.addEventListener('mouseover', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(108, 34, 223, 0.7)';
        });
        
        button.addEventListener('mouseout', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.3)';
        });
    });
    
    // Simulace aktualizace cen v reálném čase (pouze pro ukázku)
    let counter = 0;
    const priceValueElements = document.querySelectorAll('.price-value');
    const priceChangeElement = document.querySelector('.price-change-positive, .price-change-negative');
    
    if (priceValueElements.length > 0 && priceChangeElement) {
        setInterval(() => {
            // Pro ukázkové účely - mění hodnotu nahoru/dolů v malém rozsahu
            counter += 1;
            const direction = Math.sin(counter / 10); // Simuluje pohyb nahoru a dolů
            
            // Aktualizace hlavní ceny zlata
            if (priceValueElements[0]) {
                const currentPrice = parseFloat(priceValueElements[0].textContent.replace(',', '').replace('USD', '').trim());
                const newPrice = (currentPrice + direction * 0.1).toFixed(2);
                priceValueElements[0].textContent = numberWithCommas(newPrice) + ' USD';
            }
            
            // Aktualizace změny ceny
            if (priceChangeElement) {
                const change = (direction * 0.1).toFixed(2);
                const percentChange = ((direction * 0.1) / 3130 * 100).toFixed(2);
                
                if (direction >= 0) {
                    priceChangeElement.textContent = `↑ ${change} (+${percentChange}%)`;
                    priceChangeElement.className = 'price-change-positive';
                } else {
                    priceChangeElement.textContent = `↓ ${Math.abs(change)} (${percentChange}%)`;
                    priceChangeElement.className = 'price-change-negative';
                }
            }
        }, 5000); // Aktualizace každých 5 sekund
    }
});

// Pomocná funkce pro formátování čísel s oddělovači tisíců
function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}