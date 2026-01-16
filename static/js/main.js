document.addEventListener('mousemove', (e) => {
    const cards = document.querySelectorAll('.card');
    const xAxis = (window.innerWidth / 2 - e.pageX) / 50;
    const yAxis = (window.innerHeight / 2 - e.pageY) / 50;

    cards.forEach(card => {
        if (card.matches(':hover')) {
            card.style.transform = `translateY(-20px) rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
        }
    });
});

// Mobile menu toggle
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');

if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        mobileMenu.classList.toggle('active');
        
        if (mobileMenu.classList.contains('active')) {
            hamburger.innerHTML = '<i data-lucide="x"></i>';
        } else {
            hamburger.innerHTML = '<i data-lucide="menu"></i>';
        }
        lucide.createIcons();
    });

    document.addEventListener('click', (e) => {
        if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target) && mobileMenu.classList.contains('active')) {
            mobileMenu.classList.remove('active');
            hamburger.innerHTML = '<i data-lucide="menu"></i>';
            lucide.createIcons();
        }
    });
}
