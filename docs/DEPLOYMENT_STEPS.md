# Инструкция по деплою обновления на сервер

## 📋 Что было сделано

Добавлена поддержка извлечения LinkedIn URL из Telegram entities (кликабельных ссылок и гиперссылок).

### Изменённые файлы:
- `bot/services/linkedin.py` - новая функция `extract_linkedin_urls_from_message()`
- `bot/handlers/messages.py` - использование новой функции
- `tests/test_linkedin.py` - 16 новых тестов (+379 строк кода)
- `docs/CHANGELOG_URL_ENTITIES.md` - документация изменений

### Важно:
✅ Обратная совместимость сохранена  
✅ Миграции БД не требуются  
✅ Новые зависимости не добавлены  
✅ Все 75 тестов проходят успешно

---

## 🚀 Процесс деплоя

### Шаг 1: Запушить изменения в GitHub

```bash
# Проверяем статус
git status

# Изменения уже закоммичены, теперь пушим
git push origin main
```

### Шаг 2: Деплой на VPS (вариант А - автоматический)

Используйте скрипт деплоя:

```bash
# Убедитесь, что в .env настроены параметры деплоя:
# DEPLOY_REMOTE_USER=root
# DEPLOY_REMOTE_HOST=your-server.com
# DEPLOY_REMOTE_PATH=/root/linkedin-karma-bot
# DEPLOY_SSH_KEY=~/.ssh/id_rsa

# Запустите деплой
./deploy.sh
```

Скрипт выполнит:
- ✅ Синхронизацию файлов через rsync
- ✅ Исключение ненужных файлов (.git, __pycache__, tests, docs)
- ✅ Проверку конфликтов портов
- ✅ Показ следующих шагов

### Шаг 3: На VPS сервере

После успешного выполнения `deploy.sh`, подключитесь к серверу:

```bash
# SSH на сервер
ssh -i ~/.ssh/your_key root@your-server.com

# Перейдите в директорию проекта
cd /root/linkedin-karma-bot

# Проверьте, что файлы обновились
ls -la bot/services/linkedin.py
git log --oneline -3  # Если используете git на сервере

# Пересоберите Docker образ с новым кодом
docker-compose build bot

# Перезапустите бота
docker-compose up -d bot

# Проверьте логи
docker-compose logs -f bot
```

Должны увидеть:
```
bot_1       | INFO: Bot started successfully
bot_1       | INFO: Listening for messages...
```

### Шаг 4: Проверка работоспособности

1. **Проверьте статус контейнеров:**
   ```bash
   docker-compose ps
   ```
   Оба контейнера (bot и postgres) должны быть в состоянии "Up"

2. **Проверьте логи:**
   ```bash
   docker-compose logs --tail=50 bot
   ```
   Не должно быть ошибок импорта или runtime ошибок

3. **Тестирование в Telegram:**
   - Отправьте обычную текстовую ссылку LinkedIn
   - Вставьте ссылку (Telegram сделает её кликабельной)
   - Создайте гиперссылку через "@" → выберите текст → добавьте ссылку
   
   Все три варианта должны работать!

---

## 🔧 Деплой вручную (вариант Б)

Если скрипт `deploy.sh` не работает:

### 1. Синхронизация файлов

```bash
# Из локальной машины
rsync -avz --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='logs' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='tests' \
    --exclude='docs' \
    --exclude='*.db' \
    -e "ssh -i ~/.ssh/your_key" \
    ./ root@your-server.com:/root/linkedin-karma-bot/
```

### 2. На сервере

```bash
ssh root@your-server.com
cd /root/linkedin-karma-bot

# Остановите бота
docker-compose down

# Пересоберите образ
docker-compose build --no-cache bot

# Запустите снова
docker-compose up -d

# Проверьте логи
docker-compose logs -f bot
```

---

## 📊 Проверка обновления

### Быстрая проверка через логи:

```bash
# На сервере
docker-compose exec bot python -c "from bot.services.linkedin import extract_linkedin_urls_from_message; print('✅ New function imported successfully')"
```

Если команда успешна, новый код загружен.

### Функциональное тестирование:

В Telegram чате с ботом:
1. Отправьте пост с обычной ссылкой: `https://linkedin.com/posts/user-123`
2. Вставьте ссылку и дайте Telegram сделать её кликабельной
3. Напишите текст "мой пост" и сделайте из него гиперссылку на LinkedIn

Бот должен обработать все три варианта!

---

## 🔍 Troubleshooting

### Проблема: Бот не запускается после деплоя

```bash
# Проверьте логи на ошибки
docker-compose logs bot | tail -100

# Проверьте, что образ пересобран
docker images | grep karma_bot

# Принудительно пересоберите
docker-compose build --no-cache bot
docker-compose up -d
```

### Проблема: Ошибка импорта

```bash
# Проверьте, что файлы синхронизированы
docker-compose exec bot ls -la /app/bot/services/

# Проверьте содержимое файла
docker-compose exec bot cat /app/bot/services/linkedin.py | grep "extract_linkedin_urls_from_message"
```

### Проблема: Старая версия всё ещё работает

```bash
# Полная пересборка без кеша
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Или удалите образ и пересоберите
docker rmi linkedin-karma-bot-bot
docker-compose up -d --build
```

### Проблема: Не работают entities

Проверьте в логах, что бот получает entities:
```bash
docker-compose logs -f bot | grep -i "entity\|url"
```

Добавьте временный debug в `bot/handlers/messages.py`:
```python
logger.info(f"Message entities: {message.entities}")
```

---

## 📝 Rollback (если что-то пошло не так)

### Откатиться на предыдущий коммит:

```bash
# На локальной машине
git log --oneline -5  # Найдите хеш предыдущего коммита
git checkout <previous-commit-hash>

# Деплой старой версии
./deploy.sh

# На сервере
docker-compose build --no-cache bot
docker-compose up -d
```

### Или через GitHub:

```bash
git revert HEAD
git push origin main
./deploy.sh
# Пересоберите на сервере
```

---

## ✅ Checklist перед деплоем

- [ ] Все тесты проходят локально: `pytest tests/ -v`
- [ ] Изменения закоммичены: `git status`
- [ ] .env файл настроен с параметрами деплоя
- [ ] SSH ключ доступен: `ls -la ~/.ssh/`
- [ ] Сделан backup БД на сервере (если критичные данные)

## ✅ Checklist после деплоя

- [ ] Контейнеры запущены: `docker-compose ps`
- [ ] Нет ошибок в логах: `docker-compose logs bot`
- [ ] Бот отвечает в Telegram
- [ ] Проверены все три типа ссылок (текст, entity, hyperlink)
- [ ] База данных работает корректно

---

## 📞 Если нужна помощь

1. Проверьте логи: `docker-compose logs -f bot`
2. Проверьте статус: `docker-compose ps`
3. Проверьте .env файл на сервере
4. Убедитесь, что порты не заняты
5. Проверьте подключение к БД

**Последний коммит:** `18eac33 feat: Add support for LinkedIn URLs in Telegram message entities`
