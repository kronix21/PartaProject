document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. ЛОГИКА СЛАЙДЕРА ---
    const track = document.getElementById('sliderTrack');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const prev = document.getElementById('prevImg');
    const next = document.getElementById('nextImg');
    
    // Получаем все картинки внутри трека
    const slides = Array.from(track.children);
    let currentIndex = 0;

    function updateSlider() {
        // Сдвигаем трек на ширину одного слайда (100%)
        track.style.transform = `translateX(-${currentIndex * 100}%)`;
    }

    nextBtn.addEventListener('click', () => {
        if (currentIndex < slides.length - 1) {
            currentIndex++;
        } else {
            currentIndex = 0; // Возврат к началу (циклический)
        }
        updateSlider();
    });

    prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
        } else {
            currentIndex = slides.length - 1; // С конца в начало
        }
        updateSlider();
    });

    // Автопрокрутка (опционально, каждые 5 сек)
    setInterval(() => {
        if (currentIndex < slides.length - 1) {
            currentIndex++;
        } else {
            currentIndex = 0;
        }
        updateSlider();
    }, 5000);


    // --- 2. ЛОГИКА БУРГЕР-МЕНЮ ---
    const burger = document.getElementById('burger');
    const nav = document.getElementById('nav');
    const nav1 = document.getElementById('nav1');

    burger.addEventListener('click', () => {
        // Переключаем класс active у меню
        nav.classList.toggle('active');
        nav1.classList.toggle('active');
    });

});