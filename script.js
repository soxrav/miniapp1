const tg = Telegram.WebApp;

tg.expand(); // Раскрыть на весь экран
tg.enableClosingConfirmation(); // Подтверждение закрытия

document.getElementById('status').textContent = 
    `App loaded! Theme: ${tg.colorScheme}`;

document.getElementById('btn').addEventListener('click', () => {
    tg.showAlert(`Hello, ${tg.initDataUnsafe.user?.first_name || 'User'}!`);
    // Можно отправить данные боту:
    // tg.sendData(JSON.stringify({ action: "button_click" }));
});