# Промпт для браузерного агента

Открой в своём браузере https://my.telegram.org/apps и зарегистрируй от моего имени API-приложение для проекта NullWire. Я разрешаю создание этого приложения. Работай только с API development tools.

Если потребуется вход, дай мне самостоятельно ввести номер и код непосредственно на сайте. Если приложение NullWire уже создано, используй его без повторной регистрации. Если там находится другое существующее приложение, сообщи об этом перед его изменением.

Заполни форму:

- App title: `NullWire`
- Short name: `nullwireubuntu`
- URL: `https://github.com/lmdeuser/nullwire-ubuntu-obs`
- Platform: `Desktop`
- Description: `NullWire is an independent, non-commercial Telegram API desktop client for Ubuntu, built from Telegram Desktop sources. Native Debian packages with hardware video decoding enabled by default on compatible GPUs. No added ads or monetization.`

Проверь поля и выполни одну отправку Create application. Ранее портал отвечал `Too many attempts. Please try again later.` Если эта ошибка или другой flood limit повторится, остановись и сообщи точный текст. Не делай автоматических повторов и не меняй сеть ради обхода ограничения.

После успешного создания нужны api_id и api_hash. Не выводи их в чат, отчёт, скриншот или публичный репозиторий. Если у тебя есть доступ к этой же локальной папке проекта, сохрани JSON с полями `api_id` и `api_hash` в `/home/dennweiss/apps/telegram/.state/credentials/telegram-api.json`, проверив путь, с правами 600 на файл и 700 на каталог. Если общей файловой системы нет, оставь страницу созданного приложения открытой и сообщи только, что NullWire создано; реквизиты не публикуй.

В результате сообщи: создано ли приложение, его название и где безопасно сохранены реквизиты, либо точную причину остановки.
