# Персональна електронна бібліотека — Desktop GUI

Настільний застосунок на **Python 3 + PySide6** для особистої електронної бібліотеки. Бізнес-логіка, SQLite і читання PDF/EPUB живуть у сусідньому репозиторії `electronic-library-backend`; цей проєкт — графічний інтерфейс.

## Вимоги

- Windows 10+
- Python 3.11+ (рекомендовано)
- Сусідній каталог `../electronic-library-backend` (або змінна `LIBRARY_BACKEND_ROOT`)
- Для OCR (опційно): [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

## Встановлення

```bash
cd electronic-library-frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r ..\electronic-library-backend\requirements.txt
```

Можна використати вже наявне `.venv` бекенду:

```bash
pip install PySide6
```

У бекенді потрібен `bcrypt` (для акаунтів) — він є в `electronic-library-backend/requirements.txt`.

## Запуск

```bash
python run.py
```

Спочатку відкривається екран **входу / реєстрації**. Після успішного входу — головне вікно бібліотеки.

### Демо-акаунт

Після `python -m app.seed` у каталозі бекенду:

- логін: `demo`
- пароль: `demo1234`

За замовчуванням використовується каталог даних бекенду: `../electronic-library-backend/data`.

Змінні середовища:

| Змінна | Призначення |
|--------|-------------|
| `LIBRARY_BACKEND_ROOT` | Шлях до каталогу бекенду |
| `LIBRARY_DATA_DIR` | Власний каталог даних (БД, книги, обкладинки) |

## Структура frontend

```
gui/
  bootstrap.py
  ui/
    main_window.py
    pages/            # auth, library, reader, materials, analytics…
    navigation/       # іконки + згортання icon-only
    themes/           # light / dark
    dialogs/
    widgets/
run.py
```

## Можливості

- Локальні акаунти: реєстрація, вхід, вихід, зміна пароля; дані ізольовані по `user_id`
- Бібліотека: сітка з підписами / список, фільтри, вибране, статуси
- Імпорт PDF і EPUB (діалог, drag-and-drop, фон)
- Читач: PDF (сторінка + текстовий шар для виділення), EPUB (HTML + підсвітка цитат)
- Цитати, закладки, нотатки з прив’язкою до позиції; перехід із матеріалів у місце в книзі
- Відгуки про книги
- Повнотекстовий пошук (FTS)
- Колекції, теги, автори, жанри
- Статистика з графіками (QtCharts), календар, цілі
- Дублікати, bulk-edit, експорт, резервні копії
- Світла / темна тема (перемикач у верхній панелі та в налаштуваннях)
- Навігація з іконками; у згорнутому режимі — лише іконки

## Підтримувані формати

- PDF
- EPUB

## Відомі обмеження

- Теги не підтримують перейменування (лише створення / видалення).
- PDF-цитати працюють через текстовий шар сторінки; для сканів потрібен OCR.
- EPUB через `QTextBrowser` (без WebEngine).
- Відновлення з резервної копії рекомендує перезапуск.

## Тести бекенду

```bash
cd ..\electronic-library-backend
pytest -q
```
