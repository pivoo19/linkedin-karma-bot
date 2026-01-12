# 🚀 Быстрый деплой

## Что обновлено
✅ Поддержка LinkedIn ссылок в виде Telegram entities (кликабельные ссылки и гиперссылки)  
✅ Обратная совместимость  
✅ Без миграций БД

---

## Деплой за 3 шага

### 1️⃣ Пуш в GitHub
```bash
git push origin main
```

### 2️⃣ Деплой на сервер
```bash
./deploy.sh
```

### 3️⃣ На VPS
```bash
ssh root@your-server.com
cd /root/linkedin-karma-bot
docker-compose build bot
docker-compose up -d bot
docker-compose logs -f bot
```

---

## Проверка
- [ ] `docker-compose ps` - оба контейнера "Up"
- [ ] `docker-compose logs bot` - нет ошибок
- [ ] Отправить LinkedIn ссылку в Telegram - бот отвечает

---

## Если что-то не так

```bash
# Полная пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f bot
```

---

## Тестирование в Telegram

Попробуйте все 3 способа:
1. **Текст:** `https://linkedin.com/posts/user-123`
2. **Вставка:** Ctrl+V ссылки (станет кликабельной)
3. **Гиперссылка:** Текст "мой пост" → добавить ссылку

Все должны работать! ✨

---

📖 Подробная инструкция: `docs/DEPLOYMENT_STEPS.md`
