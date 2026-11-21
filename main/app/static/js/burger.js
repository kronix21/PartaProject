const burger = document.getElementById('burger');
const nav = document.getElementById('nav');
const nav1 = document.getElementById('nav1');

burger.addEventListener('click', () => {
    nav.classList.toggle('active');
    nav1.classList.toggle('active');
});