let tg = window.Telegram.WebApp;

// Устанавливаем приветствие с именем пользователя
let user = tg.initDataUnsafe?.user;
if (user) {
    document.getElementById("welcome").innerText = `Привет, ${user.first_name}!`;
}

// Делаем кнопку Telegram видимой
tg.MainButton.text = "Закрыть миниапп";
tg.MainButton.show();

// Обработка нажатия Telegram-кнопки
tg.MainButton.onClick(() => {
    tg.close();
});

// Обработка нажатия нашей HTML-кнопки
document.getElementById("mainButton").addEventListener("click", () => {
    alert("Кнопка нажата!");
});
